# Guide Opérationnel du Pipeline d'Enrichissement — Money V2

## 1. Enchaînement Complet du Pipeline

Le pipeline Money V2 s'exécute de façon déterministe via la séquence suivante :

```bash
# 1. Dédoublonnage & Shortlist dynamique (sourcing initial ou nouveau lot)
python3 dedupe_and_shortlist.py --raw-csv data/gmaps_agences_web_raw.csv --output-csv data/gmaps_agences_web_shortlist.csv

# 2. Requalification légale SIRENE & Audit d'éligibilité ICP
python3 requalify_leads.py --offset 0 --limit 30

# 3. Orchestration d'enrichissement multi-providers V2 (HTTP, theHarvester, DNS, CMS, MCP)
python3 enrichment_orchestrator.py --offset 0 --limit 30

# 4. Restitution Notion & Lead Intelligence Room
python3 build_notion_markdown.py

# 5. Audit Qualité & Vérification des Invariants (24 contrôles + 21 fixtures négatives)
python3 qa_check.py

# 6. Exécution de la suite de tests comportementaux V2 (24 tests)
python3 -m unittest tests/test_v2_architecture.py
```

---

## 2. Options de l'Orchestrateur V2 (`enrichment_orchestrator.py`)

| Argument | Description | Valeur par défaut |
| :--- | :--- | :--- |
| `--offset` | Index de départ dans le dataset | `0` |
| `--limit` | Nombre de leads à enrichir dans le lot | `30` |
| `--input` | Fichier source des leads requalifiés | `data/top30_leads_requalified.json` |
| `--output` | Fichier de destination consolidé | `data/top30_leads_requalified.json` |
| `--explain <LEAD_ID>` | Diagnostique pourquoi un lead spécifique n'a pas été enrichi | `None` |

### Exemple de Diagnostic Instantané d'un Lead
```bash
python3 enrichment_orchestrator.py --explain "Agence Web Exemple"
```
Sortie générée automatiquement :
```json
{
  "lead_id": "Agence Web Exemple",
  "diagnosis": "ENRICHISSEMENT_PARTIEL_OU_ECHOUE",
  "successful_providers": ["http_provider", "dns_mx_provider"],
  "failed_attempts": [
    {
      "provider": "theharvester_provider",
      "status": "TOOL_MISSING",
      "error_type": "ToolMissing",
      "error_message": "L'outil theHarvester est indisponible sur le système"
    }
  ],
  "detailed_causes": [
    "L'outil sous-jacent pour 'theharvester_provider' est manquant (non installé dans le PATH)."
  ],
  "recommendation": "Vérifier la connectivité réseau, l'installation des outils nécessaires ou solliciter le palier de repli (Invisible Playwright)."
}
```

---

## 3. Garanties d'Étanchéité en Production

L'orchestrateur exécute la réconciliation via `LegalReconciliationLayer` :
- Toute tentative d'un provider d'écraser un champ légal protégé (`siren`, `company_size`, `decision_maker`, `decision_maker_role`) lève immédiatement une exception critique `SealingViolationError`.
- L'audit qualité de niveau 24 (`qa_check.py`) confirme de façon automatisée qu'aucune donnée de niveau 4 n'a fuité dans les attributs d'état civil de l'entreprise.
