# Journal des Modifications (Changelog) — Money

Toutes les évolutions significatives du code, de la documentation et des données sont consignées ici.

## [2026-09-27] — Architecture V2 : Intégration Complète OSINT, Providers, Chaîne de Repli & Observabilité (Branche feat/architecture-v2-provider-integration)
### Ajouté
- **[Architecture V2 & Modèle d'Évidence]** :
  - Création du package `money_v2` structuré en 5 modules : `contracts`, `providers`, `orchestrator`, `discovery`, `truth`.
  - Spécification du contrat `Evidence` répondant aux 11 dimensions d'auditabilité formelle (champ, valeur, source, URL, timestamp ISO 8601 UTC, méthode, provider, statut, extrait de preuve, confiance, lead_id).
  - Implémentation des 11 statuts normalisés `ProviderStatus` interdisant formellement de masquer une panne technique (`RATE_LIMITED`, `BLOCKED`, `TIMEOUT`, `NETWORK_ERROR`, `TOOL_MISSING`) en absence de résultat (`NO_RESULT`).
- **[Adapters de Providers Dédiés]** :
  - `BaseProvider` : classe abstraite universelle avec mesure télémétrique automatique et gestion des exceptions.
  - `HttpProvider` : audit web standard Niveau 1 (pur stdlib urllib/ssl) avec extraction de `main_offer` et `target_clients`.
  - `FirecrawlProvider` : adaptateur Niveau 2 pour l'extraction markdown et l'analyse de structure.
  - `InvisiblePlaywrightProvider` : navigateur furtif Niveau 3 basé sur `patchright` (Turnstile/anti-bot bypass) et consultation LinkedIn encadrée (ADR-008 ≤ 5/jour) avec interdiction stricte de toucher aux champs légaux.
  - `TheHarvesterProvider` : moissonnage OSINT passif avec politique de confiance (pattern vs email vérifié) et détection binaire.
  - `DnsMxProvider` : résolution MX déterministe à 3 paliers (UDP RFC 1035 -> getaddrinfo -> DoH dns.google).
  - `CmsTechnologyProvider` : détection d'empreinte CMS observable sur signatures HTML et en-têtes HTTP.
  - `CrawleeProvider` : moteur de batch crawling industriel avec file d'attente, retries, limitation de concurrence et backoff exponentiel (`crawlee_runner.js`).
  - `ApiRegistryProvider` : adaptateur interfaçant les APIs sélectionnées du catalogue API-mega-list via `config/providers.yaml`.
- **[Orchestration, Chaîne de Repli & Diagnostic]** :
  - `FallbackStrategy` : chaîne ordonnée `HTTP -> Firecrawl -> Invisible Playwright -> ERROR`.
  - `EnrichmentOrchestrator` & CLI `enrichment_orchestrator.py` : pilotage par configuration, fusion sans écrasement légal et diagnostic instantané `--explain <LEAD_ID>`.
  - `ObservabilityHub` : persistance télémétrique dans `data/telemetry_events.json` traçant le motif exact de non-enrichissement.
- **[Pipeline de Découverte Dynamique]** :
  - `DiscoveryPipeline` dans `money_v2.discovery` : découplage intégral de listes statiques, support de nouveaux lots (`--raw-csv`, `--output-csv`), dédoublonnage, ordonnancement objectif et exclusion de leads déjà traités (`--exclude-processed`).
- **[Garantie Légale & Réconciliation]** :
  - `LegalReconciliationLayer` : exception `SealingViolationError` bloquant toute tentative d'écrasement des données SIRENE.
  - `TruthEvaluator` : évaluation multi-dimensionnelle de vérité (`VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `REQUIRES_REVIEW`, `NO_MATCH`, `ERROR`).
- **[Documentation V2 & Tests]** :
  - Rédaction de `docs/ARCHITECTURE_V2.md`, `docs/PROVIDER_ARCHITECTURE.md`, `docs/PROVIDER_CONTRACTS.md`, `docs/API_PROVIDER_REGISTRY.md`, `docs/ENRICHMENT_PIPELINE.md`.
  - Suite de tests unitaires et comportementaux `tests/test_v2_architecture.py` (24/24 PASS).
  - Maintien rigoureux des 24 contrôles et 21 tests négatifs de `qa_check.py` (0 régression).

## [2026-09-27] — Automatisation theHarvester, Runbook Opérateur MCP & QA 24 Points (Branche feat/mcp-runbook-and-harvest-automation)
### Ajouté
- **[Écart 1 — Runbook Opérateur MCP & Contrat de Staging]** :
  - Création de `docs/OPERATOR_RUNBOOK_MCP.md` définissant le cadre opérationnel pour l'agent IA exploitant `invisible_playwright_mcp` selon 2 déclencheurs exclusifs :
    - *Repli Annuaires / Mentions Légales* : sollicitation ciblée en lecture seule lors d'échecs HTTP/Cloudflare (403, challenge) pour extraire l'offre principale et la page équipe, sans jamais déduire l'identité du dirigeant ou l'effectif.
    - *Consultation LinkedIn (ADR-008)* : vérification unitaire passive de l'activité éditoriale publique récente (≤ 5 profils/jour, sans compte connecté, zéro extraction de réseau) uniquement pour les dirigeants au statut `MATCH_CONFIRMED` au registre SIRENE.
  - Définition du contrat JSON `data/mcp_audit_staging.json` (`schema_version`, `generated_by`, `entries[]` avec `field_target`, `extracted_value`, `source_url`, `evidence_text`, `collected_at`).
  - Règle d'or absolue formalisée : interdiction d'écrire dans ce staging tout champ alimentant `decision_maker*` ou `company_size*` (réservés au Niveau 1/2 légal).
- **[Écart 2 — Automatisation theHarvester CLI]** :
  - Création de l'orchestrateur `harvest_osint.py` (pur stdlib Python, exécution par `subprocess`, zéro dépendance externe).
  - Lecture dynamique des sources actives depuis `config/theHarvester.yaml` (aucun hardcoding de la liste).
  - Support du batching (`--offset`, `--limit`) et validation formelle de l'existence du binaire dans le PATH (échec explicite avec code 1 et message d'erreur clair si introuvable, aucun staging vide factice généré).
  - Normalisation et écriture directe dans `data/osint_emails_staging.json`.
- **[Écart 3 — Résilience MX via DNS-over-HTTPS (DoH)]** :
  - Intégration d'un 3ème palier de résolution MX dans `resolve_mx_records()` (`enrich_leads_osint.py`) via l'API publique `https://dns.google/resolve?name=<domain>&type=MX` (pur `urllib.request`).
  - Justification documentée dans `docs/TOOLING.md` ("stdlib insuffisant sur réseaux filtrant UDP:53").
- **[Ingestion MCP & Schéma]** :
  - Extension d'enrichissement déterministe dans `enrich_leads_osint.py` via `ingest_mcp_staging()` : alimentation de `main_offer` (si manquant) et des 3 nouveaux champs informatifs LinkedIn (`decision_maker_linkedin_activity`, `decision_maker_linkedin_source`, `decision_maker_linkedin_checked_at`).
  - Spécification des 3 nouveaux champs dans `docs/LEAD_DATA_SCHEMA.md`.
- **[Contrôle Qualité & Test Négatif 24]** :
  - Ajout du **Contrôle 24 (Étanchéité Staging MCP vs Registre Légal)** dans `qa_check.py` vérifiant programmatiquement l'absence totale de fuite de valeurs de staging MCP dans les champs légaux (`decision_maker`, `decision_maker_role`, `company_size`, `company_size_code`).
  - Ajout du test négatif unitaire `MCP 1` dans `run_negative_tests()`.
  - Passage formel du protocole QA à 24 contrôles et 21 tests négatifs (100% PASS).
- **[Documentation]** :
  - Mise à jour de `docs/TOOLING.md` avec `invisible_playwright_mcp` (statut USE NOW encadré ADR-008) et `harvest_osint.py`.
  - Mise à jour de `docs/QA_PROTOCOL.md` et `README.md`.

## [2026-09-27] — Intégration OSINT Déterministe, Cadre LinkedIn & QA 23 Points (Branche feat/lead-osint-enrichment)
### Ajouté
- **[Pipeline] Module déterministe `enrich_leads_osint.py`** : Étape 4 insérée dans le pipeline. Valide les emails candidats par résolution MX native RFC 1035 en pur Python stdlib (socket/UDP direct sans `dnspython`), impose la concordance stricte de domaine avec le site audité en Niveau 1, et détecte de façon observable l'empreinte CMS via signatures HTML et en-têtes HTTP.
- **[Contrat de Données] Schéma de Staging OSINT** : Définition formelle de `data/osint_emails_staging.json` consommant les extractions passives gratuites de theHarvester exécuté hors code.
- **[Schéma] Extension Traçabilité Emails & CMS** : Adjonction de 7 nouveaux champs dans `docs/LEAD_DATA_SCHEMA.md` (`email_source`, `email_evidence`, `email_checked_at`, `cms_detected`, `cms_source`, `cms_evidence`, `cms_checked_at`).
- **[Configuration] `config/theHarvester.yaml`** : Restriction stricte aux 8 sources passives 100% gratuites (`crt.sh`, moteurs de recherche, DNS) et désactivation formelle des modules payants / à quotas (`shodan`, `censys`, `hunter`).
- **[Gouvernance] Enregistrement d'ADR-008 et ADR-009** : Adoption au statut NOW d'ADR-008 (encadrement strict de la consultation LinkedIn passive en lecture seule) et d'ADR-009 (enrichissement OSINT déterministe et traçabilité emails).
- **[QA] Contrôles 22 et 23 + Fixtures OSINT 1 et 2** : Extension de `qa_check.py` à 23 contrôles métier (Contrôle 22: Auditabilité & Concordance Email; Contrôle 23: Preuve & Auditabilité CMS) et 20 tests négatifs unitaires.

### Corrigé
- **[Gouvernance] Amendement d'ADR-003 & Politique RGPD** : Alignement de `docs/DECISIONS.md` et `docs/DATA_POLICY.md` §B sur la doctrine ADR-008 (consultation unitaire passive ≤ 5/jour, zéro stockage de données privées, maintien absolu de l'interdiction du spam et de l'automatisation).
- **[Intégrité de Preuve] Faille sur `public_professional_email`** : Élimination du champ orphelin non audité au profit d'une exigence de preuve systématique et de validation MX.
- **[Documentation] Resynchronisation globale QA** : Réalignement de `README.md`, `docs/QA_PROTOCOL.md` et `docs/TOOLING.md` sur le standard réel de 23 contrôles métier et 20 fixtures corrompues.

## [2026-09-27] — Audit Externe (Commit 039319f) : Filtrage Dirigeants & Salutation Personne Morale
### Ajouté
- **[Pipeline] Champ `decision_maker_is_person`** : Intégration du booléen obligatoire dans `requalify_leads.py` et spécification dans `docs/LEAD_DATA_SCHEMA.md` pour distinguer formellement personne physique et personne morale.
- **[QA] Contrôle 21 (Salutation Personne Morale)** : Contrôle automatisé dans `qa_check.py` vérifiant qu'aucune salutation nominative n'est générée sur une entité morale (`decision_maker_is_person == False`), complété par un test négatif dédié dans la suite de validation (`Outreach 4`).

### Corrigé
- **[Pipeline] Exclusion des rôles non-décisionnaires** : Filtrage strict des commissaires aux comptes (titulaires et suppléants) au registre SIRENE dans `requalify_leads.py`.
- **[Pipeline] Priorisation des personnes physiques et détection personne morale** : Choix prioritaire d'une personne physique avec mandat exécutif réel (Gérant, Président, Directeur Général). Si seule une personne morale existe, conservation pour traçabilité légale avec `decision_maker_is_person: false`.
- **[Outreach] Neutralisation des salutations corporate erronées** : Dans `build_notion_markdown.py`, bascule systématique vers la formule institutionnelle (`Bonjour l'équipe {clean_name},`) dès que `decision_maker_is_person == False`, éradiquant définitivement les hallucinations de type "Bonjour Wattz".
- **[Documentation] Sécurisation terrain KWANTIC** : Mise à jour de `docs/TRUTH_AUDIT_TEMPLATE.md` actant la neutralisation du risque par le code source.

## [2026-09-27] — Audit Externe (Commit 612e53d), Purge RGPD & Durcissement Déterministe
### Ajouté
- **[RGPD] Purge complète de l'historique Git** : Élimination définitive de l'historique des données personnelles (avis et profils individuels sous `data/gmaps_agences_web_raw.csv`) via `git-filter-repo`, force-push sur `origin/main` et consignation sous ADR-007 dans `docs/DECISIONS.md`.
- **[Pipeline] Pagination CLI** : Ajout des arguments `--offset` et `--limit` dans `requalify_leads.py` pour permettre le traitement batch itératif sur l'intégralité du vivier sans être bloqué sur les 30 premiers prospects.
- **[Résilience API] Traitement distinct des pannes** : Distinction stricte entre échec technique de communication API SIRENE (`notes = "ÉCHEC TECHNIQUE API — À RE-VÉRIFIER"`) et absence réelle d'entité au registre, avec reporting d'incidents en fin d'exécution.
- **[Détection Fermetures] Entreprises radiées / fermées** : Détection formelle des structures inactives (`company_closed: true`) forçant immédiatement le statut `DISQUALIFIED` (score de confiance 0/100).
- **[Audit de Vérité] Matrice de contrôle terrain** : Création de `docs/TRUTH_AUDIT_TEMPLATE.md` auditant rigoureusement les 10 leads `VERIFIED` sur 11 points de contrôle manuel (dont l'alerte sur la personne morale dirigeante de KWANTIC).

### Corrigé
- **[Pipeline] Suppression de la cohorte en dur** : Élimination intégrale de `BENCHMARK_COHORT_DOMAINS` dans `dedupe_and_shortlist.py` au profit d'un tri pur et objectif (`review_count DESC`, `review_rating DESC`, `title ASC`).
- **[Documentation] Nettoyage LaTeX** : Remplacement des formules LaTeX brutes (`$\ge$`, `$\text{Delta}$`) par des caractères simples (`≥`, `delta`) dans `docs/ICP.md` et `docs/LEAD_QUALIFICATION_SPEC.md`.

## [2026-09-26] — Refonte Méthodologique & Audit Qualité Fondateur
### Ajouté
- Création de l'arborescence `/docs/` complète servant de mémoire permanente du projet :
  - `PRD.md`, `BUSINESS_MODEL.md`, `ICP.md`, `LEAD_QUALIFICATION_SPEC.md`, `LEAD_DATA_SCHEMA.md`
  - `DATA_POLICY.md`, `TOOLING.md`, `RESEARCH_SOURCES.md`, `OUTREACH_PLAYBOOK.md`, `GHOSTWRITING_SPEC.md`
  - `DELIVERY_SPEC.md`, `QA_PROTOCOL.md`, `ROADMAP.md`, `DECISIONS.md`, `EXPERIMENT_LOG.md`, `CHANGELOG.md`
- Mise en place d'un référentiel de scoring déterministe découplant `lead_gen_score`, `ghostwriting_score` et `confidence_score`.
- Intégration de l'API publique de Recherche d'Entreprises de l'État français pour la vérification légale des SIREN et tranches d'effectif.

### Corrigé
- Suppression des scores artificiels 100/100 par défaut dans les datasets.
- Correction de la faille méthodologique déduisant la taille d'une agence à partir des avis Google.
- Alignement strict entre le statut `REQUIRES REVIEW` / `PARTIALLY VERIFIED` et les scores de confiance réalistes.
- Élimination des données hardcodées dans le script de synchronisation Notion.

## [2026-09-26] — Initialisation du MVP & Premier Crawl
### Ajouté
- Extraction brute de 340 agences web françaises via Google Maps Scraper (Docker).
- Fichiers initiaux `data/gmaps_agences_web_raw.csv`, `top30_leads_qualified.csv`, `top30_leads_qualified.json`.
- Script initial `build_notion_markdown.py` et déploiement de la première Lead Intelligence Room Notion.
