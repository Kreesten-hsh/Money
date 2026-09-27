# Journal des Modifications (Changelog) — Money

Toutes les évolutions significatives du code, de la documentation et des données sont consignées ici.

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
