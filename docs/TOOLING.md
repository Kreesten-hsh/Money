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
| **theHarvester (CLI local)** | Découverte passive d'emails professionnels publics et hôtes DNS | 0 € (Sources ouvertes passives) | Binaire requis dans le PATH système. En cas d'absence : signale `TOOL_UNAVAILABLE` sans feindre de résultat | **USE NOW** | Intégré via `TheHarvesterProvider` avec classification d'email stricte (générique vs nominatif vs dirigeant). |
| **invisible_playwright_mcp (MCP stdio)** | Navigation furtive de repli secondaire, contournement WAF & consultation ADR-008 | 0 € (Open source local) | Moteur Firefox patché stealth (Linux/Windows uniquement, macOS non supporté). Téléchargement initial via `uvx invisible-playwright fetch`. Traçabilité `browser_usage_reason`, quota 5/jour, zéro écrasement SIRENE | **USE NOW** | Piloté via `InvisiblePlaywrightProvider` invoquant en sous-processus isolé le client MCP stdio `mcp_playwright_client.py` (`uv run --with mcp`), encadré par `docs/OPERATOR_RUNBOOK_MCP.md`. |
| **API-mega-list (Index 11 860 APIs)** | Catalogue et registre de découverte de services d'enrichissement | 0 € (Index public open data) | Catalogue de découverte, PAS un provider monolithique. Adaptateur isolé requis (ex: `google_dns_doh`) | **USE NOW** | Spécifié sous `docs/API_PROVIDER_REGISTRY.md` via `ApiRegistryProvider` (rejet strict des APIs inactives). |
| **Proxies Résidentiels Payants** | Évitement de blocages à grande échelle | ~50 à 150 € / mois | Dépense inutile au stade MVP (< 500 leads) | **EXCLUDE** | Banni : non justifié tant qu'aucun client n'a payé. |
| **OpenOutreach / Mass Emailing Automatisé** | Séquences de cold email automatisées | Variable | Risque élevé de spam, dégradation de domaine | **EXCLUDE** | Banni : la prospection MVP doit rester 100% manuelle et personnalisée. |
| **Scraping LinkedIn massif / non régulé** | Collecte massive de profils personnels | Risque légal / blocage | Violation des CGU et des règles du projet | **EXCLUDE** | Strictement interdit par ADR-003. La consultation passive unitaire est encadrée par ADR-008. |

---

## 1.1 Matrice d'Intégration Opérationnelle des Outils Externes (Money V2.2)

| Outil | Rôle Money V2 | Méthode d'appel | Modèle d'évidence | Statut si absent |
|---|---|---|---|---|
| **invisible_playwright_mcp** | Extraction anti-bot/WAF (Palier 3) & Consultation éditoriale LinkedIn dirigeant certifié (ADR-008) | `FallbackStrategy.execute_inspection_chain` & `enrich_lead` via `InvisiblePlaywrightProvider` (subprocess client stdio MCP) | `Evidence(field='main_offer'|'target_clients'|'decision_maker_linkedin_activity')` avec `browser_usage_reason` obligatoire | `TOOL_MISSING` / `TOOL_UNAVAILABLE` |
| **theHarvester** | Moissonnage passif d'emails professionnels et sous-domaines sans interroger le serveur cible | `EnrichmentOrchestrator.enrich_lead` via `TheHarvesterProvider.execute` | `Evidence(field='public_professional_email')` avec `email_classification` rigoureuse (générique vs nominatif vs dirigeant) | `TOOL_MISSING` / `TOOL_UNAVAILABLE` |
| **agent-reach** | Investigation opérateur multi-plateformes hors code (jugement IA ponctuel, pas de batch synchrone) | Opérateur / Session IA injectant via `data/mcp_audit_staging.json` (`trigger_type="agent_reach_research"`) | `Evidence(field='decision_maker_linkedin_activity'|'target_clients')` audité via staging | `TOOL_MISSING` / Non applicable (hors code) |
| **API-mega-list** | Adaptateur normalisé d'APIs publiques ouvertes sans clé (`google_dns_doh`) | `EnrichmentOrchestrator.enrich_lead` via `ApiRegistryProvider.execute(api_name='google_dns_doh')` | `Evidence(field='api_doh_record')` rattaché à l'endpoint DNS-over-HTTPS | `TOOL_MISSING` / `CONFIG_ERROR` |

> [!IMPORTANT]
> **Intégration Réelle de `invisible_playwright_mcp`** :  
> Le composant `invisible_playwright_mcp` est exécuté via le serveur MCP officiel (`uvx invisible-playwright-mcp`), piloté par le SDK officiel `mcp` dans un sous-processus isolé (`mcp_playwright_client.py`).  
> Il utilise le moteur Firefox patché stealth (téléchargé au préalable via `uvx invisible-playwright fetch`).  
> Aucun import direct de playwright/patchright n'est présent dans le code applicatif Money, garantissant une étanchéité totale du cœur applicatif.

---

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

### `harvest_osint.py`
- **Rôle** : Orchestrateur automatisé de theHarvester en ligne de commande locale pour le moissonnage d'emails passifs gratuits.
- **Entrées** : `data/top30_leads_requalified.json`, `config/theHarvester.yaml`.
- **Options CLI** : `--offset` (défaut: 0), `--limit` (défaut: 30), `--config`, `--output-staging`.
- **Sortie** : `data/osint_emails_staging.json`.
- **Règles appliquées** :
  1. **Pur Subprocess & Zéro Dépendance** : Exécuté exclusivement via les modules standard Python (`subprocess`, `json`, `argparse`). Aucune dépendance externe ajoutée.
  2. **Extraction Dynamique des Sources** : Lecture de `active_sources` depuis `config/theHarvester.yaml` sans duplication ni hardcoding.
  3. **Contrôle d'Intégrité Binaire** : Vérification de la présence de `theHarvester` dans le PATH (installé via `uv tool install theHarvester`). En cas d'absence, arrêt immédiat avec erreur explicite et refus de générer un staging vide.

### `enrich_leads_osint.py`
- **Rôle** : Enrichissement OSINT déterministe, validation MX native, repli MCP et traçabilité des emails et CMS.
- **Entrées** : `data/top30_leads_requalified.json` (ou `.csv`), `data/osint_emails_staging.json`, `data/mcp_audit_staging.json`.
- **Options CLI** : `--offset` (défaut: 0), `--limit` (défaut: 30), `--staging-file`, `--mcp-staging-file`.
- **Sorties** : `data/top30_leads_requalified.csv` et `data/top30_leads_requalified.json` enrichis.
- **Règles appliquées** :
  1. **Concordance Stricte de Domaine** : Le domaine de l'adresse email candidate doit correspondre strictement au nom de domaine du site audité en Niveau 1.
  2. **Résolution MX Native & Fallback DoH** : Requête DNS UDP / getaddrinfo vérifiant l'existence réelle d'un serveur de messagerie actif, complétée d'un palier 3 DNS-over-HTTPS (DoH via `dns.google` pur `urllib.request`). Justification technique : *stdlib insuffisant sur réseaux filtrant UDP:53*.
  3. **Détection CMS Observable** : Identification par signatures HTML (`meta[name=generator]`, chemins de thèmes) et en-têtes HTTP (`X-Powered-By`).
  4. **Ingestion Staging MCP (`invisible_playwright_mcp`)** : Repli d'offre principale si absent et capture d'activité éditoriale LinkedIn en lecture seule. Étanchéité absolue (Contrôle QA 24) : interdiction formelle d'altérer les attributs légaux `decision_maker` ou `company_size`.
  5. **Triplet de Preuve Structuré** : Chaque email, CMS ou donnée MCP enrichie reçoit obligatoirement son URL source, son extrait de preuve textuel et son horodatage ISO 8601 dynamique.
  6. **Non-Régression du Scoring** : Les scores Lead Gen, Ghostwriting et Confiance demeurent strictement inchangés.

### `enrichment_orchestrator.py` (Architecture V2)
- **Rôle** : Orchestrateur central d'enrichissement multi-providers avec chaîne de repli, télémétrie, diagnostic et étanchéité absolue.
- **Entrées** : `data/top30_leads_requalified.json`, `config/providers.yaml`.
- **Options CLI** : `--offset`, `--limit`, `--input`, `--output`, `--explain <LEAD_ID>`.
- **Sortie** : `data/top30_leads_requalified.json` enrichi et `data/telemetry_events.json`.

### `build_notion_markdown.py`
- **Rôle** : Restitution client et génération de la Lead Intelligence Room.
- **Entrée** : `data/top30_leads_requalified.json`.
- **Sortie** : `data/lead_intelligence_room.md`.
- **Règles appliquées** :
  1. **Sélection Dynamique du Top 5** : Réservée aux leads `VERIFIED` avec `MATCH_CONFIRMED`.
  2. **Vérité d'Outreach** : Messages personnalisés sans hallucination (zéro "besoin urgent", zéro "échantillon préparé", salutations nominatives vérifiées).

### `qa_check.py`
- **Rôle** : Contrôle qualité automatisé à 24 points de contrôle métier + banc de 21 tests négatifs sur fixtures altérées.
- **Entrées** : `data/top30_leads_requalified.csv`, `data/top30_leads_requalified.json`, `data/lead_intelligence_room.md`.
- **Exécution** : Bloque toute livraison si un contrôle échoue ou si une anomalie n'est pas détectée sur fixture négative.
