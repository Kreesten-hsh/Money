# Matrice des Outils & Stratégie Technologique — Money

## 1. Registre des Outils Évalués

| Outil / Skill | Rôle dans l'Architecture | Coût | Limites & Risques | Statut Actuel | Justification Décisionnelle |
|---|---|---|---|---|---|
| **Skill `google-maps-scraper`** | Sourcing géolocalisé via conteneur local Docker | 0 € (Open source local) | Données déclaratives commerciales (reviews, tél standard), ne prouve pas l'effectif réel | **USE NOW** | Validé : fournit le vivier brut initial géociblé sans proxy payant. |
| **API Recherche Entreprises (`api.gouv.fr` / INSEE)** | Vérification légale, SIREN, tranche effectif, dirigeants | 0 € (API publique d'État) | Limité à la France, cadence requise pour éviter les 429 | **USE NOW** | Indispensable : source institutionnelle de vérité pour la taille et le dirigeant. |
| **Firecrawl MCP** | Scraping profond et extraction structurée (DOM/Markdown) | Inclus | Coût en crédits sur très gros volumes | **USE NOW** | Idéal pour auditer l'offre exacte, les mentions légales et les études de cas. |
| **Skill `agent-reach`** | Investigation contextuelle multi-plateformes à 0 € d'API | 0 € (CLI open-source) | Utilisation chirurgicale ciblée, pas de scraping de profils privés | **USE NOW** | Utilisé pour capter les signaux publics de marché et les actualités du secteur. |
| **Skill `linkedin-ghostwriting`** | Moteur méthodologique de copywriting B2B conversion-focused | 0 € (Skill d'ingénierie prompt) | Nécessite de la matière brute authentique du dirigeant | **USE NOW** | Référentiel obligatoire pour l'offre Founder Ghostwriting (interviews, hooks, structures). |
| **Python Standard Library (scripts dédiés)** | Déduplication, scoring, calculs déterministes, exports | 0 € | Nécessite du code testé | **USE NOW** | Garantie de reproductibilité et traçabilité mathématique. |
| **Notion MCP** | Interface de restitution et Lead Intelligence Room client | Inclus | Risque de saturation en cas de design surchargé | **USE NOW** | Interface premium, claire et immédiatement partageable avec un client pilote. |
| **Scrapling** | Scraping de contournement si blocage ou rendu complexe | 0 € (Open source Python) | Complexité supérieure à un fetch simple | **TEST** | À activer uniquement en repli si Firecrawl échoue sur un site stratégique. |
| **theHarvester (CLI local)** | Découverte passive d'emails professionnels publics et hôtes DNS | 0 € (Sources ouvertes passives) | Limité aux sources gratuites. Exécuté hors code (`uv tool`) | **USE NOW** | Configuré via `config/theHarvester.yaml` pour alimenter `data/osint_emails_staging.json`. |
| **Proxies Résidentiels Payants** | Évitement de blocages à grande échelle | ~50 à 150 € / mois | Dépense inutile au stade MVP (< 500 leads) | **EXCLUDE** | Banni : non justifié tant qu'aucun client n'a payé. |
| **OpenOutreach / Mass Emailing Automatisé** | Séquences de cold email automatisées | Variable | Risque élevé de spam, dégradation de domaine | **EXCLUDE** | Banni : la prospection MVP doit rester 100% manuelle et personnalisée. |
| **Scraping LinkedIn massif / non régulé** | Collecte massive de profils personnels | Risque légal / blocage | Violation des CGU et des règles du projet | **EXCLUDE** | Strictement interdit par ADR-003. La consultation passive unitaire est encadrée par ADR-008. |

## 2. Règle d'Intégration d'un Nouvel Outil
Tout ajout d'outil payant ou complexe exige au préalable :
1. Une preuve d'inefficacité des alternatives gratuites (INSEE, Scraper local, Python).
2. Un calcul de rentabilité montrant que le coût est absorbé par un contrat client signé.

## 3. Scripts Opérationnels Internes

### `dedupe_and_shortlist.py`
- **Rôle** : Nettoyage, filtrage et dédoublonnage strict du vivier brut issu de Google Maps.
- **Entrée** : `data/gmaps_agences_web_raw.csv` (nettoyé des colonnes personnelles / RGPD).
- **Sortie** : `data/gmaps_agences_web_shortlist.csv`.
- **Règles appliquées** :
  1. **Présence d'un site web** : Élimination des fiches sans URL.
  2. **Catégorie d'activité** : Filtrage strict sur les libellés relatifs à la création web/digitale.
  3. **Dédoublonnage domaine** : Unicité sur le domaine canonique (sans sous-domaine `www`).
  4. **Dédoublonnage téléphone** : Unicité sur le numéro normalisé (standard national `0X...`).
  5. **Ordonnancement objectif et déterministe** : Tri pur du vivier par `review_count DESC`, `review_rating DESC`, `title ASC` (élimination intégrale de toute cohorte ou liste de domaines en dur).

### `requalify_leads.py`
- **Rôle** : Requalification légale SIRENE, audit technique web HTTP/HTTPS direct, et calcul des scores découplés.
- **Entrée** : `data/gmaps_agences_web_shortlist.csv`.
- **Options CLI** : `--offset` (défaut: 0) et `--limit` (défaut: 30) pour permettre le traitement batch itératif (0-30, 30-60, etc.) sans blocage sur la première cohorte.
- **Sorties** : `data/top30_leads_requalified.csv` et `data/top30_leads_requalified.json`.
- **Règles appliquées** :
  1. **Matching SIRENE Déterministe & Télémétrie** : Évaluation croisée identité (normalisation, suppression des suffixes), localisation (code postal strict + voie) et NAF.
  2. **Statut de Rapprochement** : `MATCH_CONFIRMED`, `MATCH_PLAUSIBLE`, `MATCH_UNCERTAIN`, `NO_MATCH`.
  3. **Distinction Échec Technique vs 0 Résultat** : Signalement explicite des pannes ou timeouts d'API (`notes = "ÉCHEC TECHNIQUE API — À RE-VÉRIFIER"`) vs absence réelle d'entreprise au registre, avec reporting récapitulatif en fin de traitement.
  4. **Détection Formelle des Fermetures** : Identification explicite des entités radiées ou inactives (`company_closed: true`) forçant immédiatement le statut `DISQUALIFIED` (score de confiance 0/100).
  5. **ICP Strict (2 à 20 salariés)** : Tranches 02, 03, 11 admises. Tranche 01 admise en VERIFIED uniquement avec preuve secondaire (co-dirigeants déclarés au greffe). Tranches NN, 00 et >20 disqualifiées d'office.
  6. **Audit Web HTTP** : Contrôle réel du certificat SSL HTTPS et du code de réponse HTTP 200 avec extraction de l'offre observable (`main_offer`) et de la cible (`target_clients`), ou mention `Non vérifié`.
  7. **Scoring Découplé & Plafonds** : Lead Gen (0-100), Ghostwriting (0/100 neutralisé en Phase 1), Confidence (0-100 avec plafond strict à 60 si non vérifié et 40 si matching incertain).
  8. **Justifications `reasons`** : Décomposition explicite des composantes Lead Gen, GW et Confidence avec renvoi aux sources.

### `enrich_leads_osint.py`
- **Rôle** : Enrichissement OSINT déterministe, validation MX native et traçabilité des emails et CMS.
- **Entrées** : `data/top30_leads_requalified.json` (ou `.csv`), `data/osint_emails_staging.json`.
- **Options CLI** : `--offset` (défaut: 0) et `--limit` (défaut: 30), `--staging-file`.
- **Sorties** : `data/top30_leads_requalified.csv` et `data/top30_leads_requalified.json` enrichis.
- **Règles appliquées** :
  1. **Concordance Stricte de Domaine** : Le domaine de l'adresse email candidate doit correspondre strictement au nom de domaine du site audité en Niveau 1.
  2. **Résolution MX Native (Stdlib Python)** : Requête DNS UDP / getaddrinfo vérifiant l'existence réelle d'un serveur de messagerie actif avant d'enregistrer l'adresse.
  3. **Détection CMS Observable** : Identification par signatures HTML (`meta[name=generator]`, chemins de thèmes) et en-têtes HTTP (`X-Powered-By`).
  4. **Triplet de Preuve Structuré** : Chaque email ou CMS enrichi reçoit obligatoirement son URL source, son extrait de preuve textuel et son horodatage ISO 8601 dynamique.
  5. **Non-Régression du Scoring** : Les scores Lead Gen, Ghostwriting et Confiance demeurent strictement inchangés.

### `build_notion_markdown.py`
- **Rôle** : Restitution client et génération de la Lead Intelligence Room.
- **Entrée** : `data/top30_leads_requalified.json`.
- **Sortie** : `data/lead_intelligence_room.md`.
- **Règles appliquées** :
  1. **Sélection Dynamique du Top 5** : Réservée aux leads `VERIFIED` avec `MATCH_CONFIRMED`.
  2. **Vérité d'Outreach** : Messages personnalisés sans hallucination (zéro "besoin urgent", zéro "échantillon préparé", salutations nominatives vérifiées).

### `qa_check.py`
- **Rôle** : Contrôle qualité automatisé à 23 points de contrôle métier + banc de 20 tests négatifs sur fixtures altérées.
- **Entrées** : `data/top30_leads_requalified.csv`, `data/top30_leads_requalified.json`, `data/lead_intelligence_room.md`.
- **Exécution** : Bloque toute livraison si un contrôle échoue ou si une anomalie n'est pas détectée sur fixture négative.
