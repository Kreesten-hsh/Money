# Matrice des Outils & Stratégie Technologique — Money

## 1. Registre des Outils Évalués

| Outil | Rôle dans l'Architecture | Coût | Limites & Risques | Statut Actuel | Justification Décisionnelle |
|---|---|---|---|---|---|
| **Google Maps Scraper (Docker)** | Moteur de découverte primaire géolocalisé | 0 € (Open source local) | Données déclaratives commerciales (reviews, tél standard), ne prouve pas l'effectif réel ni le SIREN | **USE NOW** | Validé : fournit un volume brut rapide et fiable sans proxy payant. |
| **API Recherche Entreprises (Gouv.fr / INSEE)** | Vérification légale, SIREN, tranche effectif, dirigeant | 0 € (API publique de l'État) | Limité à la France, cadence requise pour éviter les 429 | **USE NOW** | Indispensable : source institutionnelle de vérité pour la taille et le dirigeant. |
| **Firecrawl MCP** | Scraping profond et extraction de texte propre (DOM/Markdown) | Inclus dans l'environnement agentique | Coût en crédits sur très gros volumes | **USE NOW** | Idéal pour auditer l'offre exacte, les mentions légales et les études de cas. |
| **Python Standard Library (scripts dédiés)** | Déduplication, scoring, calculs déterministes, exports | 0 € | Nécessite du code propre et testé | **USE NOW** | Garantie de reproductibilité et traçabilité mathématique. |
| **Notion MCP** | Interface de restitution et Lead Intelligence Room client | Inclus | Risque de saturation en cas de design surchargé | **USE NOW** | Interface premium, claire et immédiatement partageable avec un client pilote. |
| **Scrapling** | Scraping de contournement si blocage ou rendu complexe | 0 € (Open source Python) | Complexité supérieure à un fetch simple | **TEST** | À activer uniquement en fallback si Firecrawl échoue sur un site stratégique. |
| **Agent-Reach** | Découverte d'angles éditoriaux et prises de parole | 0 € (Recherche web/réseaux ouverts) | Doit être utilisé avec parcimonie | **TEST** | Utile pour qualifier l'angle Ghostwriting des fondateurs identifiés. |
| **Proxies Résidentiels Payants** | Évitement de blocages à grande échelle | ~50 à 150 € / mois | Dépense inutile au stade MVP (< 500 leads) | **EXCLUDE** | Banni : non justifié tant qu'aucun client n'a payé. |
| **OpenOutreach / Mass Emailing Automatisé** | Séquences de cold email automatisées | Variable | Risque élevé de spam, dégradation de domaine | **EXCLUDE** | Banni : la prospection MVP doit rester 100% manuelle et personnalisée. |
| **Scraping LinkedIn automatisé** | Collecte de profils personnels | Risque légal / blocage | Violation des CGU et des règles du projet | **EXCLUDE** | Strictement interdit par la charte éthique et légale du projet. |

## 2. Règle d'Intégration d'un Nouvel Outil
Tout ajout d'outil payant ou complexe exige au préalable :
1. Une preuve d'inefficacité des alternatives gratuites (INSEE, Scraper local, Python).
2. Un calcul de rentabilité montrant que le coût est absorbé par un contrat client signé.
