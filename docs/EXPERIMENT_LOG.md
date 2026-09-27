# Journal des Expérimentations & Tests Terrain — Money

## Structure d'un Log d'Expérimentation
Chaque test commercial ou technique est consigné avec :
- Date & ID de l'expérience
- Hypothèse testée
- Protocole & Outils
- Données produites
- Résultats chiffrés réels
- Conclusion & Décision

---

### [EXP-001] Extraction multi-villes via Google Maps Scraper (Docker local)
- **Date** : 2026-09-26
- **Hypothèse** : Il est possible de collecter >300 agences web françaises sans dépenser de capital en proxies payants.
- **Protocole** : 21 requêtes ciblées sur Paris, Marseille, Lyon, Toulouse, Bordeaux, Nantes exécutées via un conteneur local Docker.
- **Résultats** : 340 extractions brutes, 334 agences uniques. Taux de complétude initial : 98% site web, 92% téléphone direct.
- **Conclusion** : **Hypothèse Validée**. Le gisement de prospection primaire est abondant et gratuit.

---

### [EXP-002] Requalification institutionnelle & Détection d'incohérences
- **Date** : 2026-09-26
- **Hypothèse** : La simple découverte Google Maps produit des faux positifs d'effectif et de statut légal.
- **Protocole** : Confrontation du lot des 30 leads avec les registres d'entreprises officiels et extraction DOM des mentions légales.
- **Résultats** : Révélation d'incohérences majeures (scores 100/100 attribués par défaut, confusion entre nombre d'avis et nombre d'employés).
- **Conclusion** : **Hypothèse Validée**. Nécessité absolue d'une requalification institutionnelle systématique avec découplage des scores avant tout contact commercial.

---

### [EXP-003] Déploiement de la Lead Intelligence Room sous Notion
- **Date** : 2026-09-26
- **Hypothèse** : Notion permet d'offrir une expérience de restitution premium immédiatement exploitable sans développer d'application dédiée.
- **Protocole** : Génération automatisée via Notion MCP d'une structure en 8 modules avec fiches décisionnelles enrichies.
- **Résultats** : Page Notion synchronisée en direct avec le dataset local.
- **Conclusion** : **Hypothèse Validée**. Format hautement lisible et valorisant pour des décideurs B2B.

---

### [EXP-004] Audit de Vérité, Élimination des Biais de Cohorte & Durcissement Déterministe
- **Date** : 2026-09-27
- **Hypothèse** : L'automatisation du contrôle QA sans audit de vérité terrain manuel induit des biais d'échantillonnage (cohorte codée en dur) et des angles morts (personnes morales dirigeantes, tranches 01 ambiguës, pannes API masquées).
- **Protocole** :
  1. Purge intégrale de l'historique Git via `git-filter-repo` (mise en conformité RGPD irréversible).
  2. Remplacement du pipeline de sélection par un tri pur déterministe (`review_count DESC`, `review_rating DESC`, `title ASC`) et support du découpage par lots CLI (`--offset`, `--limit`).
  3. Audit manuel des 10 leads `VERIFIED` consigné dans `docs/TRUTH_AUDIT_TEMPLATE.md` sur 11 dimensions de contrôle indépendantes.
  4. Séparation explicite des erreurs techniques de communication API et détection systématique des fermetures au registre officiel.
- **Résultats** : Identification concrète d'une anomalie critique sur le lead 09 (KWANTIC : président = société `WATTZ OFFICE`, interdisant l'outreach "Bonjour Wattz"). Vivier de 249 agences qualifiées désormais navigable par tranches successives sans biais.
- **Conclusion** : **Hypothèse Validée**. L'automatisation ne remplace jamais le contrôle de vérité terrain. Le gel des données et l'audit humain constituent le seul rempart crédible avant toute prise de contact commerciale.

