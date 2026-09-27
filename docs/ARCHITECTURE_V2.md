# Architecture Money V2 — Système de Lead Intelligence B2B & OSINT Multi-Providers

## 1. Vision et Objectifs V2

Money V2 opère la transition d'un pipeline séquentiel procédural à une architecture modulaire orientée **Providers**, hautement testable, traçable et extensible. 
Le système cible la qualification déterministe d'agences web françaises (2 à 20 salariés) avec un budget d'infrastructure strict de **0 €**.

### Principes Directeurs Inviolables
1. **Vérité Légale vs Observation OSINT** : Les registres officiels de l'État (INSEE / SIRENE via `recherche-entreprises.api.gouv.fr`) constituent l'unique autorité de niveau 1/2 pour l'identité (`siren`, `company_name`), la taille (`company_size`) et la gouvernance (`decision_maker`). Aucune donnée issue d'un provider OSINT ou navigateur (Niveau 4) ne peut écraser un champ légal.
2. **Visibilité des Pannes d'Infrastructure** : Interdiction formelle d'assimiler une panne réseau (`NETWORK_ERROR`), un blocage anti-bot (`BLOCKED`), un dépassement de délai (`TIMEOUT`) ou un outil absent (`TOOL_MISSING`) à une absence de résultat (`NO_RESULT`).
3. **Traçabilité Universelle par Évidence** : Toute donnée enrichie est modélisée par une structure `Evidence` à 11 dimensions auditables (champ, valeur, source, URL, timestamp ISO 8601 UTC, méthode, provider, statut, extrait de preuve, niveau de confiance, ID du lead).
4. **Indépendance de Données & Zéro Hardcoding** : Le pipeline est découplé de listes fermées d'agences historiques et traite dynamiquement de nouveaux lots, villes et requêtes sans modifier le code source.

---

## 2. Cartographie des Flux V2

```
                       [SOURCING & NOUVELLES ENTRÉES]
             (Google Maps Scraper / Annuaire / Batch CSV arbitraire)
                                     │
                                     ▼
                     [1. PIPELINE DE DÉCOUVERTE DYNAMIQUE]
                     (money_v2.discovery.discovery_pipeline)
                     - Normalisation stricte téléphones et domaines
                     - Filtrage par catégorie métier web
                     - Exclusion paramétrable des leads déjà traités
                     - Ordonnancement objectif (avis DESC, note DESC)
                     - Pagination déterministe (--offset / --limit)
                                     │
                                     ▼
                   [2. REQUALIFICATION LÉGALE & VÉRIFICATION ICP]
                     (requalify_leads.py & API Recherche Entreprises)
                     - Matching déterministe & télémétrie d'ambiguïté
                     - Tranche effectif INSEE (exclusion stricte NN / 00)
                     - Extraction dirigeant officiel & personne morale
                                     │
                                     ▼
                  [3. ORCHESTRATEUR CENTRAL D'ENRICHISSEMENT]
                  (money_v2.orchestrator.enrichment_orchestrator)
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
[CHAÎNE DE REPLI SITE]       [OSINT EMAILS PASSIF]        [DÉLIVRABILITÉ & CMS]
1. HttpProvider              TheHarvesterProvider         1. DnsMxProvider
   (urllib / SSL / regex)    (CLI passive sans quota)        (UDP -> getaddrinfo -> DoH)
2. FirecrawlProvider         - Emails canoniques          2. CmsTechnologyProvider
   (API/MCP markdown)        - Banishment adresses perso     (Signatures HTML/headers)
3. Consignation Technique    - Patterns séparés           [STAGING HORS CHAÎNE HTTP]
   (Échec explicite tracé)                                - InvisiblePlaywrightProvider
                                                            (MCP stdio subprocess Firefox)
                                                          - agent-reach (opérateur)
                                     │
                                     ▼
                  [4. REGISTRE D'APIs & CATALOGUE MEGA-LIST]
                  (money_v2.providers.api_registry_provider)
                  - Google DNS DoH (ACTIVE)
                  - SIRENE API (ACTIVE)
                  - Nominatim / Wappalyzer (DOCUMENTED / INACTIVE)
                                     │
                                     ▼
                 [5. COUCHE DE RÉCONCILIATION & ÉTANCHÉITÉ]
                 (money_v2.truth.reconciliation & truth_evaluator)
                 - Barrière d'étanchéité SealingViolationError
                 - Évaluation de vérité multi-dimensionnelle
                                     │
                                     ▼
                 [6. SCORING DÉTERMINISTE & AUDIT QUALITÉ]
                 (qa_check.py — 24 contrôles métier + 21 fixtures négatives)
                 (tests/test_v2_architecture.py — 24 tests comportementaux)
                                     │
                                     ▼
                 [7. LEAD INTELLIGENCE ROOM & RESTITUTION]
                 (build_notion_markdown.py -> data/lead_intelligence_room.md)
```

---

## 3. Matrice de Responsabilité des Composants

| Composant | Package / Fichier | Rôle V2 | Dépendance externe |
| :--- | :--- | :--- | :--- |
| **Evidence Contract** | `money_v2.contracts.evidence` | Modèle immuable de preuve à 11 dimensions | 0 (stdlib) |
| **Provider Contracts** | `money_v2.contracts.provider_result` | Statuts, erreurs et télémétrie d'exécution | 0 (stdlib) |
| **HttpProvider** | `money_v2.providers.http_provider` | Palier 1 inspection web standard | 0 (stdlib urllib/ssl) |
| **FirecrawlProvider** | `money_v2.providers.firecrawl_provider` | Palier 2 extraction markdown avancée | Optionnel (FIRECRAWL_API_KEY) |
| **InvisiblePlaywright** | `money_v2.providers.playwright_provider` | Enrichissement furtif annuaires/WAF & LinkedIn ADR-008 (Staging/Hors chaîne synchrone) | `uv` / `uvx invisible-playwright-mcp` (subprocess isolé) |
| **TheHarvesterProvider** | `money_v2.providers.theharvester_provider` | OSINT passif emails sans détection | theHarvester CLI |
| **DnsMxProvider** | `money_v2.providers.dns_mx_provider` | Résolution MX 3 paliers (UDP / addr / DoH) | 0 (stdlib socket/urllib) |
| **CmsTechnologyProvider**| `money_v2.providers.cms_provider` | Empreinte CMS observable | 0 (stdlib urllib) |
| **ApiRegistryProvider** | `money_v2.providers.api_registry_provider` | Catalogue d'APIs issues d'API-mega-list | 0 (stdlib urllib) |
| **EnrichmentOrchestrator**| `money_v2.orchestrator` | Routage des champs, fusion & étanchéité | 0 (stdlib) |
| **ObservabilityHub** | `money_v2.orchestrator.observability` | Diagnostic 'Pourquoi ce lead non enrichi ?' | 0 (stdlib) |
| **DiscoveryPipeline** | `money_v2.discovery.discovery_pipeline` | Découverte dynamique, pagination, exclusion | 0 (stdlib) |
| **LegalReconciliation** | `money_v2.truth.reconciliation` | Garantie inviolable d'étanchéité légale | 0 (stdlib) |
| **TruthEvaluator** | `money_v2.truth.truth_evaluator` | Évaluation multi-dimensionnelle de vérité | 0 (stdlib) |
| **LeadIntelligenceService** | `money_v2.services.lead_intelligence_service` | Conformité ICP, score Lead Gen, outreach sans hallucination | 0 (stdlib) |
| **GhostwritingIntelligenceService** | `money_v2.services.ghostwriting_service` | Éligibilité dirigeant physique, score neutralisé, angles B2B | 0 (stdlib) |
| **MoneyPipelineV2** | `money_v2.pipeline` | Pipeline unifié E2E découverte -> qualification -> enrichissement -> dual output | 0 (stdlib) |
| **CLI run_pipeline_v2.py** | `run_pipeline_v2.py` | Point d'entrée de traitement batch dynamique et QA | 0 (stdlib) |

---

## 4. Architecture Dual-Product & Couche de Vérité Partagée

L'architecture V2.2 unifie deux offres commerciales à haute valeur ajoutée sur le même socle d'évidence et de registres légaux :

```
                        ┌──────────────────────────────┐
                        │      EVIDENCE & TRUTH        │
                        │    RECONCILIATION LAYER      │
                        │ (SIRENE + OSINT multi-source)│
                        └──────────────┬───────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
  ┌───────────────────────────┐                 ┌───────────────────────────┐
  │   AI Lead Intelligence    │                 │ Founder LinkedIn          │
  │   Service                 │                 │ Ghostwriting Service      │
  │───────────────────────────│                 │───────────────────────────│
  │ - Score Lead Gen /100     │                 │ - Score Ghostwriting /100 │
  │ - Validation ICP 2-20     │                 │ - Neutralisation à 0/100  │
  │ - Accroche personnalisée  │                 │   sans activité observée  │
  │ - Salutation personne     │                 │ - Angles éditoriaux B2B   │
  │   morale institutionnelle │                 │   ciblés sur la stack CMS │
  └───────────────────────────┘                 └───────────────────────────┘
```
