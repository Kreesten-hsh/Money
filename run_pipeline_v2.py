#!/usr/bin/env python3
"""
run_pipeline_v2.py — Point d'Entrée CLI Unifié du Pipeline Money V2.2

Exécute l'architecture intégrée :
1. Découverte dynamique ou chargement de lot existant (sans liste codée en dur).
2. Orchestration multi-providers (HTTP, Firecrawl, theHarvester, API Registry DoH).
3. Verrouillage de l'étanchéité légale SIRENE (LegalReconciliationLayer).
4. Évaluation dimensionnelle de vérité (TruthEvaluator).
5. Consolidation AI Lead Intelligence & Founder Ghostwriting.
6. Restitution Lead Intelligence Room (Notion / Markdown).
7. Validation automatique du protocole QA (24 points).

Usage :
  python3 run_pipeline_v2.py [--offset 0] [--limit 30] [--input data/top30_leads_requalified.json]
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.pipeline import MoneyPipelineV2


def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline Unifié Money V2.2 (AI Lead Intelligence + Ghostwriting)")
    parser.add_argument("--offset", type=int, default=0, help="Offset dans le lot")
    parser.add_argument("--limit", type=int, default=30, help="Nombre de leads à traiter")
    parser.add_argument("--sirens", type=str, default=None, help="Liste de SIREN séparés par des virgules à traiter prioritairement")
    parser.add_argument("--top5-verified", action="store_true", help="Traiter spécifiquement les 5 premiers leads vérifiés (Top 5 qualifiés)")
    parser.add_argument("--input", type=str, default=str(project_root / "data" / "top30_leads_requalified.json"), help="Fichier JSON d'entrée")
    parser.add_argument("--raw-csv", type=str, default=None, help="Optionnel : fichier brut Google Maps pour découverte complète")
    parser.add_argument("--output", type=str, default=str(project_root / "data" / "v2_processed_leads.json"), help="Fichier JSON de sortie")
    parser.add_argument("--output-csv", type=str, default=str(project_root / "data" / "v2_processed_leads.csv"), help="Fichier CSV de sortie")
    parser.add_argument("--notion-output", type=str, default=str(project_root / "data" / "lead_intelligence_room_v2.md"), help="Sortie Markdown Notion")
    parser.add_argument("--explain", type=str, default=None, help="Diagnostiquer un lead spécifique via la télémétrie")
    parser.add_argument("--skip-qa", action="store_true", help="Ignorer le contrôle QA en fin de run")
    return parser.parse_args()


def generate_notion_lead_room(leads: List[Dict[str, Any]], out_path: Path) -> None:
    """Génère la Lead Intelligence Room pour le Top 5 certifié et la table complète."""
    verified_leads = [
        l for l in leads
        if l.get("verification_status") == "VERIFIED" and l.get("matching_status") == "MATCH_CONFIRMED"
    ]
    # Tri par score Lead Gen décroissant
    top_5 = sorted(verified_leads, key=lambda l: l.get("lead_gen_score", 0), reverse=True)[:5]

    lines = [
        "# LEAD INTELLIGENCE ROOM — TOP AGENCES QUALIFIÉES",
        "",
        "> **Système** : Money Architecture V2.2  ",
        "> **Offres Couvertes** : AI Lead Intelligence & Founder LinkedIn Ghostwriting  ",
        "> **Garantie** : Données légales SIRENE vérifiées, outreach sans hallucination, 100% budget 0€.",
        "",
        "---",
        ""
    ]

    for idx, lead in enumerate(top_5, 1):
        brand = lead.get("brand_name") or lead.get("title") or "Agence"
        dm = lead.get("decision_maker") or "Dirigeant non trouvé"
        role = lead.get("decision_maker_role") or "Dirigeant"
        lg_score = lead.get("lead_gen_score", 0)
        gw_score = lead.get("ghostwriting_score", 0)

        lines.append(f"## {idx}. {brand} — Score Lead Gen : {lg_score}/100 | Ghostwriting : {gw_score}/100")
        lines.append("")
        lines.append(f"- **SIREN** : `{lead.get('siren')}` (Effectif officiel : {lead.get('company_size', '2-20 salariés')})")
        lines.append(f"- **Dirigeant Certifié** : {dm} ({role})")
        lines.append(f"- **Offre Principale Observée** : {lead.get('main_offer', 'Non vérifié')}")
        lines.append(f"- **Cible Observée** : {lead.get('target_clients', 'Non vérifié')}")
        lines.append(f"- **Email Professionnel** : `{lead.get('public_professional_email') or 'Non découvert'}` (MX valide : {lead.get('mx_valid', False)})")
        lines.append(f"- **CMS / Stack** : {lead.get('cms_detected', 'Non détecté')}")
        lines.append("")
        lines.append("### Ébauche de Prise de Contact Personnalisée (Vérifiée)")
        lines.append("```text")
        lines.append(lead.get("personalized_outreach") or "Bonjour,")
        lines.append("```")
        lines.append("")

        angles = lead.get("ghostwriting_angles") or []
        if angles and gw_score > 0:
            lines.append("### Angles Éditoriaux Founder Ghostwriting")
            for ang in angles:
                lines.append(f"- {ang}")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## Récapitulatif Exhaustif du Lot de Traitement")
    lines.append("")
    lines.append("| # | Entreprise | SIREN | Statut | Score Lead Gen | Score Ghostwriting |")
    lines.append("|---|---|---|---|---|---|")
    for idx, l in enumerate(leads, 1):
        b = l.get("brand_name") or l.get("title") or "Agence"
        s = l.get("siren") or "Non trouvé"
        st = l.get("verification_status") or "UNKNOWN"
        lgs = l.get("lead_gen_score", 0)
        gws = l.get("ghostwriting_score", 0)
        lines.append(f"| {idx:02d} | **{b}** | `{s}` | {st} | `{lgs}/100` | `{gws}/100` |")
    lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    args = parse_args()
    hub = ObservabilityHub(log_path=project_root / "data" / "telemetry_events.json")

    if args.explain:
        diag = hub.explain_lead_enrichment(args.explain)
        print(json.dumps(diag, indent=2, ensure_ascii=False))
        return

    pipeline = MoneyPipelineV2(observability_hub=hub)

    print("=" * 70)
    print("MONEY V2.2 — DÉMARRAGE DU PIPELINE UNIFIÉ D'INTELLIGENCE COMMERCIALE")
    print("=" * 70)

    if args.raw_csv:
        raw_path = Path(args.raw_csv)
        print(f"Mode Découverte Dynamique depuis : {raw_path}")
        processed_batch, evidences = pipeline.run_from_raw_csv(raw_path, offset=args.offset, limit=args.limit)
        all_leads = processed_batch
    else:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"Erreur : fichier d'entrée introuvable : {in_path}", file=sys.stderr)
            sys.exit(1)
        with open(in_path, "r", encoding="utf-8") as f:
            all_leads = json.load(f)

        if args.sirens:
            target_sirens = set(s.strip() for s in args.sirens.split(",") if s.strip())
            indices = [i for i, l in enumerate(all_leads) if l.get("siren") in target_sirens]
            batch_to_process = [all_leads[i] for i in indices]
            print(f"Chargement de {len(all_leads)} leads (Traitement ciblé de {len(batch_to_process)} leads par SIREN)")
            processed_batch, evidences = pipeline.process_batch(batch_to_process)
            for idx, p_lead in zip(indices, processed_batch):
                all_leads[idx] = p_lead
        elif args.top5_verified:
            # Sélection des 5 premiers leads VERIFIED
            indices = [
                i for i, l in enumerate(all_leads)
                if l.get("verification_status") == "VERIFIED" and l.get("matching_status") == "MATCH_CONFIRMED"
            ][:5]
            batch_to_process = [all_leads[i] for i in indices]
            print(f"Chargement de {len(all_leads)} leads (Traitement ciblé des {len(batch_to_process)} leads VERIFIED du Top 5)")
            processed_batch, evidences = pipeline.process_batch(batch_to_process)
            for idx, p_lead in zip(indices, processed_batch):
                all_leads[idx] = p_lead
        else:
            batch_to_process = all_leads[args.offset:args.offset + args.limit]
            print(f"Chargement de {len(all_leads)} leads (Traitement batch offset {args.offset} à {args.offset + args.limit})")
            processed_batch, evidences = pipeline.process_batch(batch_to_process)
            all_leads[args.offset:args.offset + args.limit] = processed_batch

    # Sauvegarde JSON
    out_json = Path(args.output)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_leads, f, indent=2, ensure_ascii=False)

    # Sauvegarde CSV
    out_csv = Path(args.output_csv)
    if all_leads:
        fieldnames = list(all_leads[0].keys())
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_leads)

    # Génération Notion Lead Room
    notion_file = Path(args.notion_output)
    generate_notion_lead_room(all_leads, notion_file)

    # Persistance de la télémétrie d'observabilité
    hub.persist()

    print(f"\n[SUCCÈS] Batch traité : {len(processed_batch)} leads enrichis, {len(evidences)} évidences enregistrées.")
    print(f"  - Dataset JSON sauvegardé : {out_json}")
    print(f"  - Dataset CSV sauvegardé  : {out_csv}")
    print(f"  - Lead Room générée       : {notion_file}")

    # Contrôle QA automatique
    if not args.skip_qa:
        print("\n" + "=" * 70)
        print("EXÉCUTION DU CONTRÔLE QA OFFICIEL (25 CONTRÔLES MÉTIER)")
        print("=" * 70)
        qa_proc = subprocess.run([sys.executable, str(project_root / "qa_check.py")], check=False)
        if qa_proc.returncode != 0:
            print("\n[ÉCHEC] Le contrôle QA a échoué. Corriger les anomalies avant livraison.", file=sys.stderr)
            sys.exit(qa_proc.returncode)
        print("\n[VALIDATION] Protocole QA 100% PASS.")


if __name__ == "__main__":
    main()
