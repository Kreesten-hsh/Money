#!/usr/bin/env python3
"""
[DEPRECATED — ARCHITECTURE V1] harvest_osint.py — Orchestrateur theHarvester Staging

AVERTISSEMENT D'ARCHITECTURE :
Ce script autonome écrivait un fichier staging intermédiaire data/osint_emails_staging.json.
Dans l'architecture V2 intégrée, theHarvester est encapsulé dans :
  `money_v2/providers/theharvester_provider.py`
et piloté directement par `EnrichmentOrchestrator` au sein de `run_pipeline_v2.py`.
Ce script est conservé uniquement pour la rétro-compatibilité manuelle et est DÉPRÉCIÉ.

Usage historique :
  python3 harvest_osint.py [--offset 0] [--limit 30] [--config config/theHarvester.yaml]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent

# Domaines personnels à rejeter formellement
BANNED_EMAIL_DOMAINS = {
    'gmail.com', 'googlemail.com', 'yahoo.com', 'yahoo.fr', 'hotmail.com',
    'hotmail.fr', 'outlook.com', 'outlook.fr', 'live.com', 'live.fr',
    'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr', 'laposte.net',
    'icloud.com', 'me.com', 'msn.com', 'bbox.fr', 'aol.com'
}

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def get_current_iso_timestamp() -> str:
    """Génère dynamiquement un horodatage ISO 8601 UTC."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def extract_canonical_domain(url: str) -> str:
    """Extrait le nom de domaine canonique sans sous-domaine www."""
    if not url:
        return ''
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        netloc = urllib.parse.urlsplit(url).netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc.split(':')[0]
    except Exception:
        return ''


def find_theharvester_binary() -> str:
    """Vérifie la présence du binaire theHarvester dans le PATH système."""
    for candidate in ['theHarvester', 'theharvester']:
        found = shutil.which(candidate)
        if found:
            return found
    return ""


def parse_yaml_active_sources(yaml_path: Path) -> List[str]:
    """
    Extrait dynamiquement la liste active_sources depuis config/theHarvester.yaml.
    Ne hardcode jamais la liste une seconde fois. Fonctionne sans dépendance externe obligatoire.
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Fichier de configuration YAML introuvable : {yaml_path}")

    # Tentative avec module yaml si disponible
    try:
        import yaml
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            sources = data.get('active_sources', [])
            if sources:
                return [str(s).strip() for s in sources if str(s).strip()]
    except Exception:
        pass

    # Fallback robuste stdlib ligne par ligne
    sources: List[str] = []
    in_active_section = False
    with open(yaml_path, 'r', encoding='utf-8') as f:
        for line in f:
            clean = line.strip()
            if not clean or clean.startswith('#'):
                continue
            if clean.startswith('active_sources:'):
                in_active_section = True
                continue
            if in_active_section:
                if clean.startswith('-'):
                    item = clean.lstrip('-').split('#')[0].strip()
                    if item:
                        sources.append(item)
                elif re.match(r'^[a-zA-Z_]+:', clean):
                    break

    if not sources:
        raise ValueError(f"Aucune source active trouvée dans {yaml_path}.")

    return sources


def run_theharvester_on_domain(
    domain: str,
    active_sources: List[str],
    binary_path: str,
    timeout: int = 45
) -> List[str]:
    """
    Exécute theHarvester en CLI sur un domaine cible et parse les emails retournés.
    """
    sources_arg = ','.join(active_sources)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_base = Path(tmp_dir) / f"th_{domain.replace('.', '_')}"
        cmd = [
            binary_path,
            '-d', domain,
            '-b', sources_arg,
            '-l', '100',
            '-f', str(output_base)
        ]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
        except subprocess.TimeoutExpired:
            print(f"  [WARN] Timeout theHarvester dépassé ({timeout}s) pour {domain}.")
            return []
        except Exception as e:
            print(f"  [WARN] Échec exécution theHarvester pour {domain} : {e}")
            return []

        # theHarvester génère un fichier <output_base>.json
        json_file = Path(f"{output_base}.json")
        if not json_file.exists():
            # Chercher dans le dossier temporaire au cas où l'extension diffère
            matches = list(Path(tmp_dir).glob("*.json"))
            if matches:
                json_file = matches[0]
            else:
                return []

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_emails = data.get('emails', [])
                valid_emails = []
                for email in raw_emails:
                    email_str = str(email).strip().lower()
                    if not EMAIL_REGEX.match(email_str):
                        continue
                    email_domain = email_str.split('@')[1]
                    if email_domain in BANNED_EMAIL_DOMAINS:
                        continue
                    if domain and (email_domain != domain and not email_domain.endswith('.' + domain)):
                        continue
                    valid_emails.append(email_str)
                return sorted(list(set(valid_emails)))
        except Exception as e:
            print(f"  [WARN] Erreur de lecture JSON pour {domain} : {e}")
            return []


def harvest_batch(
    input_json_path: Path,
    output_staging_path: Path,
    config_path: Path,
    offset: int = 0,
    limit: int = 30
) -> int:
    """
    Orchestre la récolte OSINT sur le lot de prospects sélectionné.
    """
    binary_path = find_theharvester_binary()
    if not binary_path:
        print("=" * 60, file=sys.stderr)
        print("ERREUR CRITIQUE : Le binaire 'theHarvester' est introuvable dans le PATH.", file=sys.stderr)
        print("Installation requise hors dépôt : 'uv tool install theHarvester' (voir docs/TOOLING.md).", file=sys.stderr)
        print("Arrêt immédiat : aucun staging vide ou fictif ne sera généré.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)

    active_sources = parse_yaml_active_sources(config_path)
    print(f"Binaire theHarvester détecté : {binary_path}")
    print(f"Sources passives actives ({len(active_sources)}) : {', '.join(active_sources)}")

    if not input_json_path.exists():
        raise FileNotFoundError(f"Fichier d'entrée JSON introuvable : {input_json_path}")

    with open(input_json_path, 'r', encoding='utf-8') as f:
        leads: List[Dict[str, Any]] = json.load(f)

    batch = leads[offset:offset + limit]
    domains: List[str] = []
    for lead in batch:
        dom = extract_canonical_domain(lead.get('website', ''))
        if dom and dom not in domains:
            domains.append(dom)

    print(f"Lot sélectionné (offset {offset}, limit {limit}) : {len(domains)} domaines uniques à explorer.")

    # Chargement du staging existant pour mise à jour incrémentale
    existing_entries: Dict[str, Dict[str, Any]] = {}
    if output_staging_path.exists():
        try:
            with open(output_staging_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                for entry in content.get('entries', []):
                    d_key = extract_canonical_domain(entry.get('domain', ''))
                    if d_key:
                        existing_entries[d_key] = entry
        except Exception:
            existing_entries = {}

    found_count = 0
    now_ts = get_current_iso_timestamp()

    for idx, domain in enumerate(domains, 1):
        print(f"[{idx:02d}/{len(domains):02d}] Moissonnage theHarvester : {domain}...")
        emails = run_theharvester_on_domain(domain, active_sources, binary_path)

        if emails:
            found_count += len(emails)
            print(f"  -> {len(emails)} adresse(s) trouvée(s) : {', '.join(emails)}")
            existing_entries[domain] = {
                "domain": domain,
                "candidate_emails": emails,
                "source": f"theHarvester:{','.join(active_sources)}",
                "source_url": f"theHarvester:cli",
                "collected_at": now_ts
            }
        else:
            print(f"  -> Aucun email public passif trouvé.")

        # Temporisation polie entre requêtes
        time.sleep(1.0)

    # Écriture du fichier de staging final
    staging_output = {
        "schema_version": "1.0",
        "contract_type": "OSINT_EMAIL_STAGING",
        "generated_by": f"theHarvester (CLI automatisé via harvest_osint.py)",
        "generated_at": now_ts,
        "active_sources": active_sources,
        "entries": list(existing_entries.values())
    }

    output_staging_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_staging_path, 'w', encoding='utf-8') as f:
        json.dump(staging_output, f, ensure_ascii=False, indent=2)

    print(f"\nMoissonnage terminé avec succès : {found_count} adresses trouvées sur {len(domains)} domaines.")
    print(f"Fichier de staging mis à jour : {output_staging_path}")
    return found_count


def main():
    parser = argparse.ArgumentParser(description="Automatisation du moissonnage theHarvester pour Money.")
    parser.add_argument('--offset', type=int, default=0, help="Offset de départ pour traitement batch")
    parser.add_argument('--limit', type=int, default=30, help="Nombre de prospects à traiter dans le lot")
    parser.add_argument('--input-json', type=str, default=str(BASE_DIR / 'data' / 'top30_leads_requalified.json'))
    parser.add_argument('--output-staging', type=str, default=str(BASE_DIR / 'data' / 'osint_emails_staging.json'))
    parser.add_argument('--config', type=str, default=str(BASE_DIR / 'config' / 'theHarvester.yaml'))

    args = parser.parse_args()

    harvest_batch(
        input_json_path=Path(args.input_json),
        output_staging_path=Path(args.output_staging),
        config_path=Path(args.config),
        offset=args.offset,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
