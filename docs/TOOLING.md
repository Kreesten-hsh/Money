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
| **Proxies Résidentiels Payants** | Évitement de blocages à grande échelle | ~50 à 150 € / mois | Dépense inutile au stade MVP (< 500 leads) | **EXCLUDE** | Banni : non justifié tant qu'aucun client n'a payé. |
| **OpenOutreach / Mass Emailing Automatisé** | Séquences de cold email automatisées | Variable | Risque élevé de spam, dégradation de domaine | **EXCLUDE** | Banni : la prospection MVP doit rester 100% manuelle et personnalisée. |
| **Scraping LinkedIn automatisé** | Collecte de profils personnels | Risque légal / blocage | Violation des CGU et des règles du projet | **EXCLUDE** | Strictement interdit par la charte éthique et légale du projet. |

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
