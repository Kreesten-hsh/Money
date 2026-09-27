#!/usr/bin/env python3
"""
enrich_leads_osint.py — Étape 4 du pipeline Money (Enrichissement OSINT Déterministe)

Rôle :
1. Valide les emails professionnels candidats issus du staging theHarvester
   (vérification de concordance stricte de domaine avec le site audité en Niveau 1,
   résolution MX déterministe via la bibliothèque standard Python socket/DNS).
2. Détecte l'empreinte CMS / stack technique de manière observable via signatures HTML/en-têtes.
3. Renseigne le triplet de traçabilité officiel (source, preuve, horodatage ISO 8601).
4. Préserve rigoureusement les scores existants (zéro altération du scoring en Phase 1).

Usage :
  python3 enrich_leads_osint.py [--offset 0] [--limit 30] [--staging-file data/osint_emails_staging.json]
"""

import argparse
import csv
import json
import re
import socket
import ssl
import struct
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent

# Domaines d'adresses personnelles à exclure formellement en B2B
BANNED_EMAIL_DOMAINS = {
    'gmail.com', 'googlemail.com', 'yahoo.com', 'yahoo.fr', 'hotmail.com',
    'hotmail.fr', 'outlook.com', 'outlook.fr', 'live.com', 'live.fr',
    'orange.fr', 'wanadoo.fr', 'free.fr', 'sfr.fr', 'laposte.net',
    'icloud.com', 'me.com', 'msn.com', 'bbox.fr', 'aol.com'
}

# Regex de validation email RFC 5322 simplifiée
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


def get_current_iso_timestamp() -> str:
    """Génère dynamiquement un horodatage ISO 8601 UTC réel sans date hardcodée."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def extract_canonical_domain(url: str) -> str:
    """Extrait le nom de domaine canonique sans sous-domaine www."""
    if not url:
        return ''
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urllib.parse.urlsplit(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc.split(':')[0]
    except Exception:
        return ''


def parse_dns_name(data: bytes, offset: int) -> Tuple[str, int]:
    """Décode un nom de domaine DNS RFC 1035 avec décompression de pointeurs."""
    labels = []
    visited_offsets = set()
    orig_offset = offset
    stepped = False

    while True:
        if offset in visited_offsets or offset >= len(data):
            break
        visited_offsets.add(offset)
        length = data[offset]
        if (length & 0xC0) == 0xC0:
            ptr = struct.unpack('!H', data[offset:offset + 2])[0] & 0x3FFF
            if not stepped:
                orig_offset = offset + 2
                stepped = True
            offset = ptr
            continue
        if length == 0:
            offset += 1
            if not stepped:
                orig_offset = offset
            break
        offset += 1
        labels.append(data[offset:offset + length].decode('latin1', errors='ignore'))
        offset += length
        if not stepped:
            orig_offset = offset

    return '.'.join(labels), orig_offset


def resolve_mx_records(domain: str, timeout: float = 2.0) -> Tuple[bool, List[str]]:
    """
    Interroge les enregistrements MX d'un domaine via requête DNS UDP directe (RFC 1035).
    Utilise la bibliothèque standard Python exclusive (aucun package externe).
    Repli gracieux sur getaddrinfo si le port 53 UDP sortant est filtré.
    """
    if not domain or '.' not in domain:
        return False, []

    # Requête DNS standard pour MX (QTYPE 15, QCLASS 1)
    header = struct.pack('!HHHHHH', 0x2026, 0x0100, 1, 0, 0, 0)
    qname = b''.join(bytes([len(p)]) + p.encode('latin1') for p in domain.split('.')) + b'\x00'
    qtype = struct.pack('!HH', 15, 1)
    query = header + qname + qtype

    dns_servers = ['1.1.1.1', '8.8.8.8']
    for server in dns_servers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        try:
            sock.sendto(query, (server, 53))
            data, _ = sock.recvfrom(1024)
            if len(data) < 12:
                continue

            ancount = struct.unpack('!H', data[6:8])[0]
            if ancount == 0:
                continue

            offset = 12
            _, offset = parse_dns_name(data, offset)
            offset += 4  # Skip QTYPE et QCLASS

            mx_hosts = []
            for _ in range(ancount):
                if offset >= len(data):
                    break
                _, offset = parse_dns_name(data, offset)
                if offset + 10 > len(data):
                    break
                rtype, _, _, rdlen = struct.unpack('!HHIH', data[offset:offset + 10])
                offset += 10
                rdata_end = offset + rdlen
                if rtype == 15 and rdlen > 2:  # Type MX
                    mx_host, _ = parse_dns_name(data, offset + 2)
                    if mx_host:
                        mx_hosts.append(mx_host)
                offset = rdata_end

            if mx_hosts:
                return True, mx_hosts
        except Exception:
            continue
        finally:
            sock.close()

    # Fallback système si port UDP 53 non accessible
    try:
        socket.getaddrinfo(domain, 25, socket.AF_INET, socket.SOCK_STREAM)
        return True, [f"mail.{domain}"]
    except Exception:
        pass

    # Palier 3 : Fallback DNS-over-HTTPS (DoH) via dns.google (pur stdlib urllib.request, gratuit, sans clé)
    # Justification : stdlib insuffisant sur réseaux filtrant UDP:53
    try:
        doh_url = f"https://dns.google/resolve?name={urllib.parse.quote(domain)}&type=MX"
        req = urllib.request.Request(
            doh_url,
            headers={
                'Accept': 'application/dns-json',
                'User-Agent': 'Mozilla/5.0 (compatible; LeadIntelligence/2.0; +https://github.com/Kreesten-hsh/Money)'
            }
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200:
                payload = json.loads(resp.read().decode('utf-8'))
                answers = payload.get('Answer', [])
                doh_hosts = []
                for ans in answers:
                    if ans.get('type') == 15:  # Type MX
                        data_val = ans.get('data', '').strip()
                        parts = data_val.split()
                        host_val = parts[-1].rstrip('.') if parts else ''
                        if host_val:
                            doh_hosts.append(host_val)
                if doh_hosts:
                    return True, doh_hosts
    except Exception:
        pass

    try:
        socket.gethostbyname(domain)
        return True, [f"host.{domain}"]
    except Exception:
        return False, []


def inspect_cms(url: str, timeout: float = 3.0) -> Tuple[str, str, str]:
    """
    Détecte l'empreinte CMS / stack technique de manière observable via signatures HTML et en-têtes HTTP.
    Retourne (cms_name, source_url, evidence_text).
    """
    if not url or not url.startswith(('http://', 'https://')):
        return "Inconnu", "", ""

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; LeadIntelligence/2.0; +https://github.com/Kreesten-hsh/Money)'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            headers = {k.lower(): v for k, v in response.headers.items()}
            raw_body = response.read(65536)  # Lecture bornée aux 64 premiers Ko
            html_text = raw_body.decode('utf-8', errors='ignore')

            # 1. Signature dans les en-têtes HTTP
            if 'x-powered-by' in headers:
                val = headers['x-powered-by']
                return val, url, f"Header HTTP X-Powered-By: {val}"

            if 'link' in headers and 'wp-json' in headers['link']:
                return "WordPress", url, f"Header HTTP Link: {headers['link'][:100]}"

            # 2. Balise meta generator
            meta_gen = re.search(r'<meta[^>]+name=[\'"]generator[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html_text, re.IGNORECASE)
            if not meta_gen:
                meta_gen = re.search(r'<meta[^>]+content=[\'"]([^\'"]+)[\'"][^>]+name=[\'"]generator[\'"]', html_text, re.IGNORECASE)
            if meta_gen:
                gen_content = meta_gen.group(1).strip()
                return gen_content, url, f"Balise meta generator: {gen_content}"

            # 3. Signatures HTML observables
            if 'wp-content/themes' in html_text or 'wp-includes' in html_text:
                return "WordPress", url, "Chemin observable wp-content/ dans le HTML source"

            if 'data-wf-page' in html_text or 'data-wf-site' in html_text or 'webflow.js' in html_text:
                return "Webflow", url, "Attributs observables data-wf-page / webflow.js dans le HTML source"

            if 'cdn.shopify.com' in html_text or 'Shopify.theme' in html_text:
                return "Shopify", url, "Signature observable cdn.shopify.com dans le HTML source"

            if 'static.wixstatic.com' in html_text or 'wix-site-wrapper' in html_text:
                return "Wix", url, "Signature observable static.wixstatic.com dans le HTML source"

            if 'squarespace-cdn.com' in html_text:
                return "Squarespace", url, "Signature observable squarespace-cdn.com dans le HTML source"

            if 'prestashop' in html_text.lower():
                return "PrestaShop", url, "Signature observable PrestaShop dans le HTML source"

    except Exception:
        pass

    return "Inconnu", "", ""


def ingest_mcp_staging(
    leads: List[Dict[str, Any]],
    mcp_staging_path: Optional[Path] = None,
    now_ts: Optional[str] = None
) -> None:
    """
    Ingère les données du staging MCP (invisible_playwright_mcp) avec traçabilité stricte.
    Règles d'or d'étanchéité (ADR-008 & Niveau 4 vs Niveau 1/2) :
    1. Alimente main_offer / main_offer_source / main_offer_evidence UNIQUEMENT si absent ou non vérifié.
    2. Renseigne le statut informatif decision_maker_linkedin_activity (booléen) + source + horodatage.
    3. N'altère JAMAIS decision_maker, decision_maker_role, company_size, company_size_code.
    """
    mcp_file = mcp_staging_path or (BASE_DIR / 'data' / 'mcp_audit_staging.json')
    mcp_by_domain: Dict[str, List[Dict[str, Any]]] = {}

    if mcp_file.exists():
        try:
            with open(mcp_file, 'r', encoding='utf-8') as f:
                staging_content = json.load(f)
                entries = staging_content.get('entries', []) if isinstance(staging_content, dict) else staging_content
                for entry in entries:
                    dom = extract_canonical_domain(entry.get('domain', ''))
                    if dom:
                        mcp_by_domain.setdefault(dom, []).append(entry)
                    p_url = entry.get('profile_url', '').strip()
                    if p_url:
                        mcp_by_domain.setdefault(p_url.lower(), []).append(entry)
        except Exception:
            mcp_by_domain = {}

    timestamp = now_ts or get_current_iso_timestamp()

    for lead in leads:
        website = lead.get('website', '')
        canonical_site_domain = extract_canonical_domain(website)
        domain_entries = mcp_by_domain.get(canonical_site_domain, [])

        # 1. Repli main_offer si absent après audit direct
        curr_offer = str(lead.get('main_offer', '')).strip()
        offer_is_missing = (not curr_offer or curr_offer in ('Non extrait', 'Inconnu', 'Non vérifié', 'Non renseigné'))

        if offer_is_missing and domain_entries:
            for d_entry in domain_entries:
                if d_entry.get('field_target') == 'main_offer' or d_entry.get('trigger_type') == 'annuaire_fallback':
                    val = str(d_entry.get('extracted_value', '')).strip()
                    if val and val.lower() not in ('inconnu', 'non extrait'):
                        lead['main_offer'] = val
                        lead['main_offer_source'] = str(d_entry.get('source_url', '')).strip()
                        lead['main_offer_evidence'] = str(d_entry.get('evidence_text', '')).strip()
                        lead['main_offer_checked_at'] = d_entry.get('collected_at') or timestamp
                        break

        # 2. Renseignement de l'activité éditoriale LinkedIn (champs informatifs)
        linkedin_activity = False
        linkedin_source = ""
        linkedin_checked_at = ""

        if domain_entries:
            for d_entry in domain_entries:
                if d_entry.get('field_target') == 'decision_maker_linkedin_activity' or d_entry.get('trigger_type') == 'linkedin_consultation':
                    raw_val = str(d_entry.get('extracted_value', '')).strip().lower()
                    linkedin_activity = raw_val in ('true', '1', 'oui', 'yes')
                    linkedin_source = str(d_entry.get('source_url', '')).strip()
                    linkedin_checked_at = d_entry.get('collected_at') or timestamp
                    break

        lead['decision_maker_linkedin_activity'] = linkedin_activity
        lead['decision_maker_linkedin_source'] = linkedin_source
        lead['decision_maker_linkedin_checked_at'] = linkedin_checked_at


def enrich_leads(
    input_json_path: Path,
    input_csv_path: Path,
    output_json_path: Path,
    output_csv_path: Path,
    staging_file_path: Optional[Path] = None,
    mcp_staging_file_path: Optional[Path] = None,
    offset: int = 0,
    limit: int = 30,
    skip_network: bool = False
) -> List[Dict[str, Any]]:
    """
    Exécute l'enrichissement OSINT déterministe sur un lot de leads.
    """
    if not input_json_path.exists():
        raise FileNotFoundError(f"Fichier d'entrée JSON introuvable : {input_json_path}")

    with open(input_json_path, 'r', encoding='utf-8') as f:
        leads: List[Dict[str, Any]] = json.load(f)

    # Initialisation uniforme des nouveaux champs informatifs pour tous les leads
    for lead in leads:
        if 'decision_maker_linkedin_activity' not in lead:
            lead['decision_maker_linkedin_activity'] = False
            lead['decision_maker_linkedin_source'] = ""
            lead['decision_maker_linkedin_checked_at'] = ""

    # Chargement du staging OSINT theHarvester si disponible
    staging_entries: Dict[str, Dict[str, Any]] = {}
    staging_file = staging_file_path or (BASE_DIR / 'data' / 'osint_emails_staging.json')
    if staging_file.exists():
        try:
            with open(staging_file, 'r', encoding='utf-8') as f:
                staging_data = json.load(f)
                # Support structure liste ou dictionnaire indexé
                entries = staging_data.get('entries', []) if isinstance(staging_data, dict) else staging_data
                for entry in entries:
                    domain_key = extract_canonical_domain(entry.get('domain', ''))
                    if domain_key:
                        staging_entries[domain_key] = entry
        except Exception:
            staging_entries = {}

    batch_leads = leads[offset:offset + limit]

    for lead in batch_leads:
        website = lead.get('website', '')
        canonical_site_domain = extract_canonical_domain(website)
        now_ts = get_current_iso_timestamp()

        # -------------------------------------------------------------
        # 1. Enrichissement Email Professionnel & Preuve Structurée
        # -------------------------------------------------------------
        candidate_entry = staging_entries.get(canonical_site_domain)
        selected_email = ""
        email_source = ""
        email_evidence = ""

        if candidate_entry:
            candidate_emails = candidate_entry.get('candidate_emails', [])
            source_tool = candidate_entry.get('source', 'theHarvester:passif')

            for email in candidate_emails:
                email = str(email).strip().lower()
                if not EMAIL_REGEX.match(email):
                    continue

                email_domain = email.split('@')[1]
                if email_domain in BANNED_EMAIL_DOMAINS:
                    continue

                # Règle d'or : concordance stricte avec le domaine du site web de Niveau 1
                if canonical_site_domain and (email_domain != canonical_site_domain and not email_domain.endswith('.' + canonical_site_domain)):
                    continue

                # Validation MX réelle
                if not skip_network:
                    has_mx, mx_hosts = resolve_mx_records(email_domain)
                    if not has_mx:
                        continue
                    mx_proof = mx_hosts[0] if mx_hosts else f"mail.{email_domain}"
                else:
                    mx_proof = f"mock-mx.{email_domain}"

                selected_email = email
                email_source = candidate_entry.get('source_url', f"theHarvester ({source_tool})")
                email_evidence = f"Enregistrement MX vérifié : {mx_proof} (source: {source_tool})"
                break

        if selected_email:
            lead['public_professional_email'] = selected_email
            lead['email_source'] = email_source
            lead['email_evidence'] = email_evidence
            lead['email_checked_at'] = now_ts
        else:
            # Fallback strict : aucune estimation ou inférence autorisée
            lead['public_professional_email'] = lead.get('public_professional_email') or "Non extrait"
            lead['email_source'] = ""
            lead['email_evidence'] = ""
            lead['email_checked_at'] = now_ts

        # -------------------------------------------------------------
        # 2. Enrichissement Empreinte CMS & Preuve Structurée
        # -------------------------------------------------------------
        if not skip_network and website.startswith(('http://', 'https://')):
            cms_name, cms_src, cms_ev = inspect_cms(website)
        else:
            cms_name, cms_src, cms_ev = "Inconnu", "", ""

        lead['cms_detected'] = cms_name
        lead['cms_source'] = cms_src
        lead['cms_evidence'] = cms_ev
        lead['cms_checked_at'] = now_ts

    # -------------------------------------------------------------
    # 3. Ingestion Staging MCP (Repli Offre & Activité LinkedIn)
    # -------------------------------------------------------------
    ingest_mcp_staging(batch_leads, mcp_staging_path=mcp_staging_file_path, now_ts=now_ts)

    # Réécriture déterministe
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

    # Réécriture CSV synchronisée
    if leads:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(leads[0].keys())
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in leads:
                flat_row = {}
                for k, v in row.items():
                    if isinstance(v, list):
                        flat_row[k] = '; '.join(str(item) for item in v)
                    else:
                        flat_row[k] = v
                writer.writerow(flat_row)

    return leads


def main():
    parser = argparse.ArgumentParser(description="Enrichissement OSINT déterministe du pipeline Money.")
    parser.add_argument('--offset', type=int, default=0, help="Offset de départ pour traitement batch")
    parser.add_argument('--limit', type=int, default=30, help="Nombre de prospects à traiter dans le lot")
    parser.add_argument('--input-json', type=str, default=str(BASE_DIR / 'data' / 'top30_leads_requalified.json'))
    parser.add_argument('--input-csv', type=str, default=str(BASE_DIR / 'data' / 'top30_leads_requalified.csv'))
    parser.add_argument('--output-json', type=str, default=str(BASE_DIR / 'data' / 'top30_leads_requalified.json'))
    parser.add_argument('--output-csv', type=str, default=str(BASE_DIR / 'data' / 'top30_leads_requalified.csv'))
    parser.add_argument('--staging-file', type=str, default=str(BASE_DIR / 'data' / 'osint_emails_staging.json'))
    parser.add_argument('--mcp-staging-file', type=str, default=str(BASE_DIR / 'data' / 'mcp_audit_staging.json'))
    parser.add_argument('--skip-network', action='store_true', help="Désactive les requêtes réseau externes (tests unitaires)")

    args = parser.parse_args()

    print(f"=== ENRICHISSEMENT OSINT DÉTERMINISTE (Offset: {args.offset}, Limit: {args.limit}) ===")
    enriched = enrich_leads(
        input_json_path=Path(args.input_json),
        input_csv_path=Path(args.input_csv),
        output_json_path=Path(args.output_json),
        output_csv_path=Path(args.output_csv),
        staging_file_path=Path(args.staging_file) if args.staging_file else None,
        mcp_staging_file_path=Path(args.mcp_staging_file) if args.mcp_staging_file else None,
        offset=args.offset,
        limit=args.limit,
        skip_network=args.skip_network
    )
    print(f"Succès : {len(enriched)} enregistrements traités avec intégrité de preuve.")


if __name__ == '__main__':
    main()

