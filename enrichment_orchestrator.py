#!/usr/bin/env python3
"""
enrichment_orchestrator.py — Orchestrateur d'enrichissement Money V2

Rôle :
1. Charge les leads issus de la requalification (JSON / CSV).
2. Détermine pour chaque lead les champs à enrichir selon les politiques actives.
3. Exécute les providers V2 avec chaîne de repli, télémétrie et capture d'erreurs.
4. Préserve inconditionnellement l'intégrité des champs légaux SIRENE.
5. Sauvegarde le dataset enrichi et le journal d'observabilité.

Usage :
  python3 enrichment_orchestrator.py [--offset 0] [--limit 30] [--input data/top30_leads_requalified.json] [--output data/top30_leads_requalified.json]
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from money_v2.contracts.evidence import Evidence
from money_v2.orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
from money_v2.orchestrator.observability import ObservabilityHub

BASE_DIR = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description="Orchestrateur d'Enrichissement Multi-Providers Money V2")
    parser.add_argument("--offset", type=int, default=0, help="Index de départ dans le batch")
    parser.add_argument("--limit", type=int, default=30, help="Nombre de leads à traiter")
    parser.add_argument("--input", type=str, default=str(BASE_DIR / "data" / "top30_leads_requalified.json"), help="Fichier d'entrée JSON")
    parser.add_argument("--output", type=str, default=str(BASE_DIR / "data" / "top30_leads_requalified.json"), help="Fichier de sortie JSON")
    parser.add_argument("--explain", type=str, default=None, help="Diagnostique pourquoi un lead spécifique n'a pas été enrichi")
    return parser.parse_args()


def main():
    args = parse_args()
    hub = ObservabilityHub(log_path=BASE_DIR / "data" / "telemetry_events.json")

    if args.explain:
        diag = hub.explain_lead_enrichment(args.explain)
        print(json.dumps(diag, indent=2, ensure_ascii=False))
        return

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"Erreur : fichier d'entrée introuvable : {in_path}", file=sys.stderr)
        sys.exit(1)

    with open(in_path, "r", encoding="utf-8") as f:
        leads = json.load(f)

    batch = leads[args.offset:args.offset + args.limit]
    print(f"=== ORCHESTRATEUR D'ENRICHISSEMENT V2 (Total: {len(leads)}, Batch: {len(batch)}) ===")

    orchestrator = EnrichmentOrchestrator(observability_hub=hub)
    all_evidences_count = 0
    enriched_batch: List[Dict[str, Any]] = []

    for idx, lead in enumerate(batch, 1):
        brand = lead.get("brand_name") or lead.get("title") or "Inconnu"
        enriched_lead, evidences = orchestrator.enrich_lead(lead)
        enriched_batch.append(enriched_lead)
        all_evidences_count += len(evidences)
        print(f"  [{idx:02d}/{len(batch):02d}] {brand} : {len(evidences)} nouvelles preuves collectées.")

    leads[args.offset:args.offset + args.limit] = enriched_batch

    # Sauvegarde JSON
    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # Sauvegarde CSV équivalent
    csv_path = out_path.with_suffix(".csv")
    if leads:
        fieldnames = list(leads[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)

    # Persistance de la télémétrie
    hub.persist()

    print(f"\nSuccès : {len(batch)} leads traités, {all_evidences_count} preuves enregistrées.")
    print(f"Télémétrie persistée sous {hub.log_path}.")


if __name__ == "__main__":
    main()
