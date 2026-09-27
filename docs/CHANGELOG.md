# Journal des Modifications (Changelog) — Money

Toutes les évolutions significatives du code, de la documentation et des données sont consignées ici.

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
