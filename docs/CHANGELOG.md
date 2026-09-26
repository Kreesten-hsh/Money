# Journal des Modifications (Changelog) — Money

Toutes les évolutions significatives du code, de la documentation et des données sont consignées ici.

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
