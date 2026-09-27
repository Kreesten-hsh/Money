# Audit Architectural & Évaluation des Outils Candidats — Pipeline Money

> **Statut du document** : PROPOSITION ARCHITECTURALE & AUDIT PRÉALABLE  
> **Auteur** : Senior Principal Engineer & Product Architect  
> **Date** : 2026-09-27  
> **Conformité** : Budget 0 €, Zéro Dépendance Payante, Vérité Légale Républicaine (INSEE/SIRENE), RGPD Strict.  
> **Avertissement** : Phase d'architecture pure. Aucune installation, aucune modification du code source ni de `requirements.txt` n'est effectuée sans l'approbation formelle de Kreesten.

---

## 1. Audit Factuel du Répertoire

### 1.1 État des Lieux des Scripts et Étapes du Pipeline
Le dépôt [Money](https://github.com/Kreesten-hsh/Money) opère un pipeline déterministe d'intelligence commerciale B2B ciblant les agences web françaises de 2 à 20 collaborateurs. L'exécution est séquentielle et repose sur 4 scripts Python autonomes :

| Étape | Script | Fichier d'Entrée | Fichiers de Sortie | Mode d'Exécution & CLI |
|---|---|---|---|---|
| **1. Filtrage & Dédoublonnage** | `dedupe_and_shortlist.py` | `data/gmaps_agences_web_raw.csv` | `data/gmaps_agences_web_shortlist.csv` | Déterministe direct. Élimine les sans-URL, filtre par mot-clé métier, dédoublonne sur domaine canonique et téléphone national normalisé, ordonnance par `review_count DESC`, `review_rating DESC`, `title ASC`. |
| **2. Requalification Légale & Scoring** | `requalify_leads.py` | `data/gmaps_agences_web_shortlist.csv` | `data/top30_leads_requalified.csv`<br>`data/top30_leads_requalified.json` | CLI avec pagination batch : `--offset <int>` (défaut 0), `--limit <int>` (défaut 30). Rapprochement SIRENE multi-critères, audit HTTP direct, calcul des 3 scores découplés. |
| **3. Restitution Client & Intelligence Room** | `build_notion_markdown.py` | `data/top30_leads_requalified.json` | `data/lead_intelligence_room.md` | Déterministe direct. Génération de la vue consolidée, extraction du Top 5 vérifié, templates d'outreach personnalisés sans hallucination. |
| **4. Contrôle Qualité Pré-Livraison** | `qa_check.py` | `data/top30_leads_requalified.csv`<br>`data/top30_leads_requalified.json`<br>`data/lead_intelligence_room.md` | Code retour `0` ou `1` + logs stdout/stderr | Audit de conformité des données réelles + banc de tests négatifs sur fixtures délibérément corrompues. |

### 1.2 Volumétrie et Structure du Schéma de Données
Le schéma de données officiel défini dans `docs/LEAD_DATA_SCHEMA.md` comporte **exactement 51 attributs** structurés :
- **Identification & Localisation** (8 champs) : `company_name`, `brand_name`, `siren`, `siren_source`, `siren_checked_at`, `website`, `country`, `city`.
- **Vérité Légale & Effectif** (8 champs) : `company_size`, `company_size_code`, `company_size_source`, `company_size_interpretation`, `company_size_checked_at`, `has_secondary_size_proof`, `secondary_size_proof_source`, `secondary_size_proof_details`.
- **Prestation & Cible Observables** (8 champs) : `main_offer`, `main_offer_source`, `main_offer_evidence`, `main_offer_checked_at`, `target_clients`, `target_clients_source`, `target_clients_evidence`, `target_clients_checked_at`.
- **Gouvernance & Dirigeant Officiel** (5 champs) : `decision_maker`, `decision_maker_role`, `decision_maker_is_person`, `decision_maker_source`, `decision_maker_checked_at`.
- **Coordonnées Publiques** (2 champs) : `public_professional_email`, `public_phone`.
- **Sources & Preuves Primaires** (2 champs) : `source_url`, `evidence_url`.
- **Télémétrie Déterministe SIRENE** (8 champs) : `matching_status`, `sirene_candidate_selected`, `sirene_candidate_score`, `sirene_second_candidate_score`, `sirene_score_delta`, `sirene_matching_concordant_criteria`, `sirene_matching_contradictory_criteria`, `sirene_matching_decision_reason`.
- **Signaux d'Affaires & Scoring Découplé** (7 champs) : `commercial_signal`, `signal_source`, `signal_date`, `lead_gen_score`, `ghostwriting_score`, `confidence_score`, `verification_status`.
- **Traçabilité & Notes** (3 champs) : `reasons`, `last_checked`, `notes`.

### 1.3 Audit Factuel de la Synchronisation QA (Code vs Documentation)
L'inspection du code source de `qa_check.py` et de l'historique `docs/CHANGELOG.md` révèle une désynchronisation flagrante avec la documentation opérationnelle :

1. **Nombre Réel de Contrôles Métier** :
   - Le script `qa_check.py` implémente et exécute **21 contrôles métier** (Contrôles 01 à 21). Le Contrôle 21 (`Contrôle 21 (Salutation Personne Morale)`) a été introduit au commit `039319f` pour bloquer toute salutation nominative sur des holdings ou personnes morales (ex: "Bonjour Wattz").
   - À l'inverse, `docs/QA_PROTOCOL.md` (section 2) s'intitule encore *"Checklist Obligatoire Pré-Livraison (20 Contrôles Métier)"* et omet le Contrôle 21. La même anomalie figure dans `docs/TOOLING.md` (ligne 61) et `README.md` (ligne 59).
2. **Nombre Réel de Tests Négatifs sur Fixtures Corrompues** :
   - La fonction `run_negative_tests()` dans `qa_check.py` instancie **18 fixtures corrompues** au total :
     - 14 fixtures tabulaires CSV (`fixtures`) couvrant SIRENE (3), Preuves (5), Temporalité (2), Scoring (3), Redondance (1).
     - 4 fixtures textuelles Markdown (`md_fixtures`) couvrant l'outreach : `Outreach 1` (besoin non observé), `Outreach 2` (prestataires recherchés), `Outreach 3` (placeholder corrompu), et `Outreach 4` (salutation nominative sur personne morale `Bonjour Wattz,`).
   - À l'inverse, `docs/QA_PROTOCOL.md` (section 3) affiche *"Banc de Tests Négatifs (17 Fixtures Corrompues)"* et ne documente que 3 tests d'outreach.
3. **Action Corrective Immédiate** : Le protocole de QA et la documentation doivent acter officiellement le standard **21 contrôles métier** et **18 tests négatifs**.

### 1.4 Synthèse des Règles Non-Négociables en Vigueur
- **Budget 0 € strict** : Zéro dépendance payante, zéro proxy payant, aucune utilisation d'API imposant un moyen de paiement (`README.md`).
- **Vérité Légale Républicaine** : Seules les données issues de la base SIRENE/INSEE (via `recherche-entreprises.api.gouv.fr`) établissent l'effectif, l'activité légale et les mandataires sociaux officiels (`ADR-004`). Interdiction de déduire l'effectif depuis les avis Google (`ADR-002`).
- **RGPD & Minimisation** : Collecte restreinte aux données professionnelles publiques des personnes morales. Élimination des avis clients nominatifs (`ADR-007`).
- **Doctrine Actuelle LinkedIn** : Interdiction du scraping automatisé des profils personnels LinkedIn (`ADR-003` et `docs/DATA_POLICY.md` §B).
- **Zéro Extrapolation / Zéro Hallucination** : Une donnée absente ou non vérifiable est formellement consignée comme `"Non vérifié"` ou `"Incertain"`. Interdiction absolue de combler un vide par inférence probabiliste (`docs/DATA_POLICY.md` §C).

---

## 2. Inventaire des Outils Existants

La matrice ci-dessous reprend l'intégralité du registre de `docs/TOOLING.md`, en intégrant la séparation formelle entre les briques embarquées dans le code Git et les briques pilotées hors code par l'opérateur IA :

| Outil / Skill | Rôle dans l'Architecture | Périmètre d'Exécution | Coût Réel | Limites & Risques | Statut Actuel | Justification Décisionnelle |
|---|---|---|---|---|---|---|
| **Skill `google-maps-scraper`** | Sourcing géolocalisé de leads bruts via conteneur local Docker | **Invoqué hors code par l'opérateur IA** (CLI Docker) | 0 € (Open source local) | Données déclaratives commerciales (reviews, tél standard), ne prouve pas l'effectif réel | **USE NOW** | Fournit le vivier brut initial géociblé sans proxy payant. |
| **API Recherche Entreprises (`api.gouv.fr` / INSEE)** | Vérification légale, SIREN, tranche effectif, dirigeants | **Dans le code git** (consommé par `requalify_leads.py`) | 0 € (API publique d'État) | Limité à la France, cadence requise pour éviter les 429 | **USE NOW** | Source institutionnelle de vérité pour la taille et le dirigeant légal. |
| **Firecrawl MCP** | Scraping profond et extraction structurée (DOM/Markdown) | **Invoqué hors code par l'opérateur IA** (Serveur MCP) | Inclus | Quota de crédits sur très gros volumes | **USE NOW** | Idéal pour auditer l'offre exacte, les mentions légales et les études de cas. |
| **Skill `agent-reach`** | Investigation contextuelle multi-plateformes à 0 € d'API | **Invoqué hors code par l'opérateur IA** (CLI agent-reach) | 0 € (CLI open-source) | Utilisation chirurgicale ciblée, pas de scraping de profils privés | **USE NOW** | Utilisé pour capter les signaux publics de marché et les actualités du secteur. |
| **Skill `linkedin-ghostwriting`** | Moteur méthodologique de copywriting B2B conversion-focused | **Invoqué hors code par l'opérateur IA** (Prompts / Skill) | 0 € (Skill prompt) | Nécessite de la matière brute authentique issue du dirigeant | **USE NOW** | Référentiel obligatoire pour l'offre Founder Ghostwriting (interviews, hooks). |
| **Python Standard Library (scripts dédiés)** | Déduplication, scoring, calculs déterministes, exports | **Dans le code git** (`dedupe_and_shortlist.py`, `requalify_leads.py`, `build_notion_markdown.py`, `qa_check.py`) | 0 € | Nécessite du code testé | **USE NOW** | Garantie de reproductibilité, traçabilité mathématique et portabilité stricte. |
| **Notion MCP** | Interface de restitution et Lead Intelligence Room client | **Invoqué hors code par l'opérateur IA** (Serveur MCP) | Inclus | Risque de saturation en cas de design surchargé | **USE NOW** | Interface premium, claire et immédiatement partageable avec un client pilote. |
| **Scrapling** | Scraping de contournement si blocage ou rendu complexe | **Invoqué hors code par l'opérateur IA** (Bibliothèque Python locale) | 0 € (Open source Python) | Complexité supérieure à un fetch simple | **TEST** | À activer uniquement en repli si Firecrawl échoue sur un site stratégique. |
| **Proxies Résidentiels Payants** | Évitement de blocages à grande échelle | N/A | ~50 à 150 € / mois | Dépense inutile au stade MVP (< 500 leads) | **EXCLUDE** | Banni : non justifié tant qu'aucun contrat client n'a été encaissé. |
| **OpenOutreach / Mass Emailing Automatisé** | Séquences de cold email automatisées | N/A | Variable | Risque élevé de spam, dégradation de domaine | **EXCLUDE** | Banni : la prospection MVP doit rester 100% manuelle et personnalisée. |
| **Scraping LinkedIn automatisé** | Collecte massive de profils personnels | N/A | Risque juridique / blocage de compte | Violation des CGU et des règles du projet | **EXCLUDE** | Strictement interdit par la charte éthique et légale du projet (ADR-003). |

---

## 3. Vérification Exhaustive des Quatre Projets Candidats

### 3.1 `invisible_playwright_mcp` (feder-cr)
- **Maintenance & Santé** : Actif (septembre 2026), sous licence MIT, écrit en Python. Projet initialement standalone, désormais adossé à l'écosystème AIHawk de `feder-cr` avec shims de compatibilité PyPI. Dépendance d'installation principale : runtime Python (3.10+) géré via `uv` et navigateur Firefox patché.
- **Structure de Coût** : 0 € de coût direct. Auto-hébergé sur la machine locale. Aucun proxy payant requis pour des volumes modérés. Consomme des ressources locales (CPU/RAM pour l'instance Firefox headless stealth).
- **Fonctionnement Technique** : Émulation furtive d'actions humaines (déplacement de souris non linéaire par courbes de Bézier, pauses aléatoires, frappes clavier natives du système d'exploitation) contournant les heuristiques de détection anti-bot (Cloudflare Turnstile, DataDome, Akamai) sans injecter d'attributs JavaScript suspects (`navigator.webdriver`).
- **Cas d'usage 1 (Annuaires protégés)** : Scraping ciblé de répertoires professionnels B2B protégés par Cloudflare (ex: Sortlist, Malt, PagesJaunes). Conforme au RGPD (données publiques d'entreprises morales).
- **Cas d'usage 2 (LinkedIn & Décideurs) — POINT BLOQUANT MAJEUR** :
  > **Contradiction bloquante avec la doctrine actuelle du projet** :  
  > La navigation et l'extraction automatisée sur LinkedIn contredisent frontalement :  
  > 1. `ADR-003` (`docs/DECISIONS.md`) : *"Interdiction formelle du scraping LinkedIn et du spam d'emails... Respect strict du RGPD et des CGU des plateformes."*  
  > 2. `docs/DATA_POLICY.md` §B : *"Le scraping des profils personnels LinkedIn est banni de l'architecture. L'identification de profils LinkedIn se limite à la consultation humaine de profils publics..."*  
  > 
  > L'utilisation d'un navigateur furtif pour tromper les défenses de LinkedIn constitue un contournement délibéré de leurs conditions d'utilisation. Même si Kreesten formule l'orientation *"levons l'interdiction formelle du Scraping LinkedIn"*, cette levée **ne peut pas être appliquée silencieusement**. Elle exige l'adoption formelle d'un amendement d'architecture (Draft ADR-008) définissant un protocole strict : consultation passive en session non connectée (ou compte dédié isolé), débit unitaire chirurgical (max 5 profils/jour), exclusion du stockage de données privées, et absence totale d'automatisation de messages.

### 3.2 `theHarvester` (laramies)
- **Maintenance & Santé** : Projet OSINT de référence, activement maintenu sur GitHub (Python 3.12+/3.14), géré via `uv`, licence GPL-3.0.
- **Structure de Coût par Source** :
  - **Sources 100% Gratuites (0 €)** : `crt.sh` (journaux de transparence de certificats SSL), `duckduckgo`, `bing`, `yahoo`, `baidu`, `hackertarget`, `dnsdumpster`, `anubis`, `rapiddns`.
  - **Sources Payantes ou Quotas Restrictifs (À BANNIR DU CONFIG)** : `shodan`, `censys`, `hunter` (limité à 10 crédits/mois sans CB), `securityTrails`, `virustotal`.
- **Compatibilité Légale & RGPD** :
  - La collecte d'emails professionnels génériques (`contact@agence.fr`, `direction@agence.fr`) ou de conventions d'adresses (`prenom.nom@agence.fr`) exposés publiquement sur le web ouvert est licite en prospection B2B en France (article L.34-5 du CPCE), à la condition expresse que le message soit en rapport direct avec la profession du destinataire et qu'un lien d'opposition immédiat soit fourni.
  - **Risque d'intégrité** : `theHarvester` extrait du texte brut sans vérifier la validité de la boîte de réception. Risque de remonter des données issues d'anciennes fuites de données (breaches) ou des emails privés.
  - **Point bloquant sur le schéma de données** : Le champ `public_professional_email` dans `docs/LEAD_DATA_SCHEMA.md` est actuellement dépourvu de triplet de traçabilité (`email_source`, `email_evidence`, `email_checked_at`). L'alimenter sans combler cette lacune violerait la règle de traçabilité intégrale du projet.

### 3.3 `agent-reach` (Panniantong)
- **Maintenance & Santé** : Maintenu, open source, licence MIT, écrit en Python. Configuré comme un skill local opérationnel dans `/home/hasashi/.gemini/config/skills/agent-reach/`.
- **Structure de Coût** : 0 € d'API. Exploite des proxys publics légers et des API non authentifiées (passerelle Jina Reader `r.jina.ai`, Exa web search, crawlers ouverts).
- **Statut Architectural Réel** : Cet outil n'est pas un nouveau candidat. Il est **déjà intégré et classé "USE NOW"** dans `docs/TOOLING.md` et référencé en Niveau 4 dans `docs/RESEARCH_SOURCES.md`.
- **Rôle Confirmé** : Outil d'investigation contextuelle hors code utilisé ponctuellement par l'opérateur IA pour auditer les publications récentes, les fils Twitter/X de l'agence, et les mentions presse afin d'alimenter `commercial_signal` avec des faits d'actualité réels et horodatés.

### 3.4 `API-mega-list` (cporter202)
- **Nature du Projet** : Ce n'est **pas un logiciel**, pas un package Python, ni un outil exécutable. Il s'agit d'un répertoire GitHub statique (fichiers Markdown) répertoriant plus de 10 000 APIs publiques indexées par catégories.
- **Structure de Coût** : 0 € d'accès au catalogue. La quasi-totalité des APIs répertoriées dispose de tiers gratuits sans carte bancaire.
- **Rôle Architectural** : Sert exclusivement de bibliothèque de référence documentaire pour identifier des micro-APIs gratuites répondant à des besoins ciblés :
  - *Détection de CMS / Tech Stack* : Identification d'endpoints d'analyse d'en-têtes HTTP ou signatures HTML (alternatives gratuites et sans clé à Wappalyzer).
  - *Validation DNS / MX* : APIs ou requêtes directes pour vérifier l'existence de serveurs de messagerie actifs avant d'enregistrer un email.

---

## 4. Analyse des Chevauchements Fonctionnels

Le tableau croisé ci-dessous identifie les zones de redondance et tranche la répartition des responsabilités :

| Outil A | Outil B | Nature du Recouvrement | Analyse du Conflit | Décision Architecturale |
|---|---|---|---|---|
| **`invisible_playwright_mcp`** | **`google-maps-scraper`** | Sourcing initial d'agences | Les deux peuvent extraire des listes d'entreprises. Google Maps fournit une couverture géographique exhaustive des fiches d'établissements. `invisible_playwright_mcp` permet d'accéder à des annuaires spécialisés fermés (Malt, Sortlist) protégés par Cloudflare. | **Non-substituable, complémentaire**. `google-maps-scraper` reste le socle primaire du vivier brut géographique. `invisible_playwright_mcp` n'intervient qu'en amont secondaire pour ouvrir de nouvelles sources de qualification verticale (ex: vérifier le portfolio sur Sortlist). |
| **`theHarvester`** | **`agent-reach`** | Recherche d'informations sur le web public | Les deux interrogent des moteurs de recherche (Bing, DuckDuckGo). Cependant, `theHarvester` réalise une énumération passive d'infrastructure (DNS, hôtes, pattern d'emails `@domaine.fr`). `agent-reach` réalise une extraction sémantique de contenu (textes de posts, articles, actualités). | **Découplage strict des rôles**. `theHarvester` est cantonné à la découverte technique de coordonnées professionnelles. `agent-reach` est réservé à l'enrichissement sémantique de l'outreach et à la recherche d'actualités d'affaires (`commercial_signal`). |
| **`invisible_playwright_mcp`** | **`Firecrawl MCP`** | Scraping web profond | Les deux permettent d'extraire le contenu textuel d'un site web d'agence. Firecrawl utilise une infrastructure cloud gérée avec conversion Markdown propre. `invisible_playwright_mcp` utilise un navigateur local résistant aux challenges JavaScript complexes. | **Priorité à Firecrawl, repli sur Playwright Furtif**. Pour les sites web classiques des agences (95% des cas), Firecrawl est plus rapide et produit un markdown standardisé. `invisible_playwright_mcp` n'est activé qu'en cas de blocage strict (Cloudflare Turnstile bloquant Firecrawl). |
| **`API-mega-list` (APIs DNS)** | **Python `socket`/`urllib`** | Résolution DNS et audit SSL | Plusieurs APIs de la liste proposent de tester les enregistrements MX ou certificats SSL. Or, Python standard réalise déjà ces tests nativement via les modules `socket` et `ssl`. | **Primauté de la bibliothèque standard Python**. Tout appel externe vers une API tierce pour une tâche réalisable en stdlib est formellement rejeté. Les APIs d'API-mega-list ne sont retenues que si aucun moyen stdlib n'existe. |

---

## 5. Interfaces & Frontières Architecturales

### 5.1 Règle de Séparation des Responsabilités (La Frontière Étanche)
Une scission absolue doit être maintenue entre le cœur déterministe auditable et l'outillage de l'opérateur IA :

1. **Couche Déterministe Testée (Dans Git / Pip standard)** :
   - Tout script qui modifie, enrichit ou valide un champ du schéma de données officiel (`data/top30_leads_requalified.*`) **doit être un script Python déterministe versionné**.
   - Ce script doit être reproductible, pilotable en ligne de commande avec arguments `--offset` et `--limit`, et entièrement couvert par le banc de contrôles de `qa_check.py`.
   - **Interdiction formelle** de confier le renseignement d'un champ de données final à un appel de prompt conversationnel non reproductible.
2. **Couche d'Assistance & Investigation (Hors Git / Opérateur IA)** :
   - Les serveurs MCP (`invisible_playwright_mcp`, `Firecrawl MCP`, `Notion MCP`) et les skills (`agent-reach`, `google-maps-scraper`) sont des extensions d'outillage pour l'opérateur humain ou l'agent d'investigation.
   - Ils servent à explorer, contourner des blocages ponctuels ou structurer la matière brute, mais leurs résultats doivent être injectés dans le pipeline via des fichiers intermédiaires tracés et auditables.

### 5.2 Positionnement des Outils Retenus
- **`theHarvester`** : Exécuté comme un outil CLI local isolé (hors `requirements.txt`). Ses découvertes d'adresses emails publiques sont exportées dans un fichier de transit (`data/osint_emails_staging.json`). Un nouveau script déterministe léger (ex: `enrich_leads_osint.py`) vérifie la syntaxe, contrôle les MX via Python stdlib et injecte la donnée dans le pipeline avec preuve de traçabilité.
- **`invisible_playwright_mcp`** : Configuré comme serveur MCP local pour l'agent. Utilisé en investigation chirurgicale à la demande pour extraire les mentions légales ou répertoires protégés lorsque les requêtes HTTP standard échouent (code 403 / challenge Cloudflare).
- **`agent-reach`** : Maintien de son statut actuel "USE NOW" comme skill opérateur hors code.
- **`API-mega-list`** : Référentiel documentaire passif.

### 5.3 Diagramme du Pipeline Étendu

```text
[1. Sourcing Brut GMB]
  └── data/gmaps_agences_web_raw.csv (Nettoyé RGPD)
          │
          ▼
[2. Filtrage & Dédoublonnage]
  └── python3 dedupe_and_shortlist.py
          │
          ▼
      data/gmaps_agences_web_shortlist.csv
          │
          ▼
[3. Requalification Légale SIRENE & Audit Web HTTP]
  └── python3 requalify_leads.py --offset 0 --limit 30
          │    ├── API Recherche Entreprises (api.gouv.fr / INSEE)
          │    └── Audit SSL/HTTP natif (stdlib)
          │    [Option Repli : invisible_playwright_mcp si 403/Cloudflare]
          │
          ▼
      data/top30_leads_requalified.json & .csv (Intermédiaire)
          │
          ▼
[4. Enrichissement OSINT Déterministe & Traçabilité Emails] (NOUVEAU MODULE ÉVENTUEL)
  └── python3 enrich_leads_osint.py --offset 0 --limit 30
          │    ├── Consomme staging issu de theHarvester local (crt.sh, DDG)
          │    ├── Validation MX native (Python stdlib socket)
          │    └── Triplet de preuve structuré (source, extrait, timestamp)
          │
          ▼
      data/top30_leads_requalified.json & .csv (Finalisé)
          │
          ▼
[5. Restitution Client / Hub Notion]
  └── python3 build_notion_markdown.py
          │
          ▼
      data/lead_intelligence_room.md
          │
          ▼
[6. Contrôle Qualité Pré-Livraison (21+ Contrôles & 18+ Fixtures Négatives)]
  └── python3 qa_check.py
```

---

## 6. Contrats de Données & Correction des Lacunes

### 6.1 Correction de la Faille Historique sur `public_professional_email`
Dans la version actuelle de `docs/LEAD_DATA_SCHEMA.md` (ligne 38), l'attribut `public_professional_email` est spécifié de manière isolée :
```markdown
| `public_professional_email` | string | NON | Email professionnel public (ex: Non extrait (Option)) |
```
**Anomalie de rigueur** : Contrairement aux attributs `siren`, `company_size`, `main_offer`, `target_clients` et `decision_maker`, le champ email ne dispose d'aucun champ d'audit (`_source`, `_evidence`, `_checked_at`). Si un outil comme `theHarvester` alimente ce champ, une donnée non tracée et invérifiable pénètre dans un pipeline certifié 100% auditable.

### 6.2 Nouveaux Attributs de Données Requis

Pour intégrer proprement la découverte d'emails et la détection d'empreinte technique (CMS/stack), le schéma doit être complété par les attributs formels suivants :

| Attribut | Type | Requis | Format / Valeurs Autorisées | Description & Règles de Vérité |
|---|---|---|---|---|
| `public_professional_email` | string | NON | Adresse email RFC 5322 ou `"Non extrait"` | Email professionnel public collecté légalement. Interdiction d'adresses privées (`@gmail.com`, `@orange.fr`). |
| `email_source` | string (URL) | NON | URL valide ou libellé de source OSINT | Source exacte de découverte (ex: `https://agence.fr/contact/`, `crt.sh:SAN_DNS`, `Mentions Légales`). Obligatoire si email présent. |
| `email_evidence` | string | NON | Extrait textuel exact | Contexte d'apparition ou preuve d'enregistrement MX actif (`"Enregistrement MX vérifié : mail.agence.fr"`). |
| `email_checked_at` | string (ISO 8601) | NON | `YYYY-MM-DDTHH:MM:SSZ` | Horodatage dynamique UTC de la vérification de l'adresse et du MX. |
| `cms_detected` | string | NON | Libellé normalisé (ex: `WordPress`, `Webflow`, `Shopify`, `Custom/React`, `Inconnu`) | CMS ou framework détecté de manière observable sur le site. |
| `cms_source` | string (URL) | NON | URL de la page auditée | Page ayant fourni la signature HTML/headers. |
| `cms_evidence` | string | NON | Balise HTML ou header HTTP | Signature observable (ex: `meta[name='generator'] content='WordPress 6.4'`). |
| `cms_checked_at` | string (ISO 8601) | NON | `YYYY-MM-DDTHH:MM:SSZ` | Horodatage dynamique UTC de l'audit CMS. |

---

## 7. Stratégie de Résilience & Fallbacks Déterministes

Conformément à `docs/DATA_POLICY.md` §C, **aucune extrapolation ou estimation artificielle n'est admise pour combler une défaillance technique**. Le tableau ci-dessous formalise la gestion déterministe des pannes pour chaque outil candidat :

| Scénario d'Échec | Cause Technique | Valeur Assignée au Champ | Statut Attribué | Règle de Traçabilité dans `notes` & Scoring |
|---|---|---|---|---|
| **Blocage Cloudflare / DataDome sur `invisible_playwright_mcp`** | Challenge Turnstile non résolu, rate-limiting IP | `"Non vérifié"` | Maintien en `REQUIRES REVIEW` | Inscription de l'alerte : `"ÉCHEC TECHNIQUE INSPECTION WEB — BLOCAGE ANTI-BOT"`. Score confiance plafonné à 60. |
| **Panne ou Timeout d'une source `theHarvester` (ex: `crt.sh`)** | Indisponibilité du service tiers ou timeout réseau | `"Non extrait"` | Neutre pour le statut légal | L'absence d'email ne bloque pas le statut `VERIFIED` si le dirigeant légal et le téléphone professionnel sont confirmés. |
| **0 email détecté par `theHarvester`** | Domaine récent, masquage WHOIS, absence de contact public | `"Non extrait"` | Neutre | Inscription : `"Aucun email professionnel public détecté sur sources passives"`. Interdiction de deviner une syntaxe. |
| **Échec de détection CMS** | Code minifié, CMS propriétaire ou serveur masqué | `"Inconnu"` | Neutre | Inscription : `"Empreinte technique non observable"`. Aucun point de bonus technique attribué. |
| **Panne de l'API SIRENE (`recherche-entreprises.api.gouv.fr`)** | Code 500 / 502 / Timeout | `"Incertain"` | `REQUIRES REVIEW` | Traitement déjà codé : `"ÉCHEC TECHNIQUE API — À RE-VÉRIFIER"`. Score confiance forcé à 0. |

---

## 8. Hiérarchie de Vérité & Politique de Preuve

La validité de toute information collectée par les nouveaux outils est assujettie à la hiérarchie officielle définie dans `docs/RESEARCH_SOURCES.md` :

```text
┌────────────────────────────────────────────────────────────────────────┐
│ NIVEAU 1 : Sources Officielles Primaires de l'Entreprise               │
│ - Site web officiel (domaine vérifié https://)                         │
│ - Mentions Légales, CGV, Registre des traitements                      │
│ - Signatures CMS & Enregistrements MX directs (Serveurs de l'agence)   │
├────────────────────────────────────────────────────────────────────────┤
│ NIVEAU 2 : Registres Institutionnels & Données Publiques de l'État      │
│ - Base SIRENE / INSEE (Statut actif, Code NAF, Tranche d'effectif)     │
│ - Annuaire des Entreprises / API Recherche Entreprises                 │
│ - Mandataires sociaux & Dirigeants légaux inscrits au Greffe / RCS     │
├────────────────────────────────────────────────────────────────────────┤
│ NIVEAU 3 : Sources Professionnelles Secondaires Reconnues              │
│ - Fiches Pappers, Société.com, Verif.com (retranscription greffe)      │
│ - Registres professionnels spécialisés (BPI, French Tech)              │
├────────────────────────────────────────────────────────────────────────┤
│ NIVEAU 4 : Sources de Découverte & Signaux Faibles                     │
│ - Skill google-maps-scraper (Google Business Profile)                  │
│ - theHarvester (Énumération passive DNS, crt.sh, moteurs)              │
│ - invisible_playwright_mcp (Annuaires tiers, PagesJaunes, Malt)        │
│ - Skill agent-reach (Veille multi-plateformes, réseaux ouverts)        │
│ - Catalogues issus d'API-mega-list                                     │
└────────────────────────────────────────────────────────────────────────┘
```

> **RÈGLE D'OR INTANGIBLE** :  
> Une donnée issue d'une source de **Niveau 4** (`theHarvester`, `invisible_playwright_mcp`, annuaires tiers) ne peut **EN AUCUN CAS** se substituer, prévaloir ou déroger à une source de **Niveau 1 ou 2** :  
> - Un effectif mentionné sur un profil Sortlist ou LinkedIn ne prévaut JAMAIS sur la tranche officielle INSEE déclarée au registre SIRENE.  
> - Un "CEO" ou "Founder" autoproclamé sur le web ne peut être qualifié de décisionnaire `VERIFIED` s'il n'est pas corroboré par la qualité légale enregistrée au registre d'État (Contrôle 07).  
> - Un email extrait par `theHarvester` ne peut être qualifié sans vérification de concordance de domaine avec le site audité en Niveau 1.

---

## 9. Emplacement d'Installation & Projets d'ADR (Brouillons)

### 9.1 Matrice d'Implantation Technique & Isolation
Pour respecter la promesse de pureté du cœur de calcul (Budget 0 €, zéro maintenance complexe), l'implantation de chaque brique doit respecter les règles d'isolation suivantes :

| Outil Candidat | Mode d'Installation Recommandé | Impact sur `requirements.txt` | Justification d'Ingénierie |
|---|---|---|---|
| **`invisible_playwright_mcp`** | **Serveur MCP Opérateur Local** (`uvx` ou virtualenv dédié hors dépôt) | **AUCUN (Zéro ajout)** | Doit demeurer un outil d'assistance pour le runtime IA. Installer Playwright et des navigateurs lourds dans l'environnement du pipeline violerait la légèreté du projet. |
| **`theHarvester`** | **Conteneur Docker Local ou CLI isolé** (`uv tool install theHarvester`) | **AUCUN (Zéro ajout)** | `theHarvester` exige Python 3.12+ et une vingtaine de dépendances (aiohttp, netaddr, etc.). Polluer le `requirements.txt` principal du projet avec ces dépendances est un anti-pattern. |
| **`agent-reach`** | **Skill AI Agent autonome** (déjà implanté) | **AUCUN (Zéro ajout)** | Déjà installé dans `~/.gemini/config/skills/agent-reach/`. |
| **Micro-scripts d'enrichissement** | **Python Standard Library pur** (`socket`, `ssl`, `urllib`) | **AUCUN (Zéro ajout)** | La vérification MX et l'analyse des en-têtes CMS peuvent être écrites à 100% en bibliothèque standard Python. |

### 9.2 Préservation du `requirements.txt`
Le fichier `requirements.txt` actuel proclame formellement :
```text
# Le pipeline opérationnel repose exclusivement sur la bibliothèque standard Python (3.10+).
# Aucune dépendance externe payante ou nécessitant une carte bancaire.
```
**Conclusion technique** : Il est impératif de maintenir `requirements.txt` dans son état actuel (uniquement `flake8` et `pytest` pour les tests). Aucune dépendance tierce liée au scraping stealth ou à l'OSINT ne doit y être ajoutée.

---

### 9.3 Projets d'ADR en Attente de Validation (Brouillons)

Les deux projets d'ADR suivants sont rédigés au format officiel du projet. **Ils demeurent en statut DRAFT dans ce livrable et ne seront versés dans `docs/DECISIONS.md` qu'après validation explicite de Kreesten.**

---

#### [DRAFT ADR-008] Évolution de la Doctrine LinkedIn & Encadrement du Headless Stealth
- **Date** : 2026-09-27
- **Statut Proposé** : **NEXT** (En attente d'arbitrage Kreesten)
- **Contexte** : 
  L'ADR-003 et la section B de `docs/DATA_POLICY.md` interdisent formellement le scraping LinkedIn. Cependant, la vérification de l'activité réelle des dirigeants d'agences web et de leur appétence pour l'offre Founder Ghostwriting nécessite d'auditer l'existence et la tonalité de leurs publications publiques. L'outil `invisible_playwright_mcp` permet une navigation furtive locale sans détection anti-bot.
- **Décision Proposée** :
  1. **Levée Partielle et Chirurgicale de l'Interdiction** : Autoriser l'opérateur IA à utiliser `invisible_playwright_mcp` pour consulter en lecture seule les pages d'entreprises publiques et les profils publics de dirigeants préalablement identifiés au registre légal SIRENE.
  2. **Interdiction du Scraping de Masse & Comptes Connectés** : Interdiction absolue de connecter des comptes personnels LinkedIn ou de procéder à l'aspiration automatisée de listes de contacts. La consultation est limitée à unitairement 3 à 5 profils ciblés par jour.
  3. **Conformité RGPD** : Seuls l'existence d'une ligne éditoriale active et le lien public vers le profil sont consignés. Aucune donnée privée (relations, coordonnées privées, historique de navigation) n'est stockée.
  4. **Maintien du Démarchage Manuel** : L'interdiction du cold-emailing automatisé et des messages LinkedIn automatisés (bots de connexion) demeure absolue. L'approche reste 100% manuelle.

---

#### [DRAFT ADR-009] Enrichissement OSINT Déterministe & Traçabilité des Emails Professionnels
- **Date** : 2026-09-27
- **Statut Proposé** : **NEXT** (En attente d'arbitrage Kreesten)
- **Contexte** :
  Le schéma actuel comporte un attribut `public_professional_email` sans champ de preuve associé. L'utilisation de `theHarvester` permet d'identifier passivement des coordonnées publiques via des sources gratuites (`crt.sh`, moteurs de recherche).
- **Décision Proposée** :
  1. **Isolation de l'Outillage OSINT** : `theHarvester` est exécuté exclusivement en conteneur ou environnement CLI isolé, avec exclusion stricte de toute source payante (Shodan, Hunter).
  2. **Intégrité du Schéma de Données** : Amendement immédiat de `docs/LEAD_DATA_SCHEMA.md` pour adjoindre le triplet `email_source`, `email_evidence`, `email_checked_at`.
  3. **Vérification MX Déterministe en Stdlib** : Tout email collecté doit être validé techniquement au niveau de son serveur de messagerie (enregistrement DNS MX) via un script Python stdlib avant injection dans le dataset officiel.

---

## 10. Protocole d'Exécution & Barrière Étanche

Conformément à la directive de mission :
1. **Zéro Modification de Code** : Aucun fichier `.py` (`dedupe_and_shortlist.py`, `requalify_leads.py`, `build_notion_markdown.py`, `qa_check.py`) n'a été touché.
2. **Zéro Dépendance Installée** : `requirements.txt` reste inchangé. Aucun package n'a été installé sur l'environnement système.
3. **Zéro Altération Documentaire Silencieuse** : `docs/DATA_POLICY.md`, `docs/DECISIONS.md` et `docs/QA_PROTOCOL.md` demeurent strictement dans leur état de référence jusqu'à instruction explicite.

---

## 11. Décisions Requises

La mise en œuvre technique est conditionnée par l'arbitrage humain de Kreesten sur les **5 points bloquants** ci-dessous :

1. **Validation du Draft ADR-008 (Levée encadrée de l'interdiction LinkedIn)** :
   - *Question* : Validez-vous la levée partielle de l'interdiction de consultation LinkedIn via `invisible_playwright_mcp` selon les garde-fous stricts définis (lecture seule publique, débits chirurgicaux ≤ 5/jour, zéro connexion de compte personnel, zéro démarchage automatisé) ?
   - *Impact* : Nécessite l'amendement formel d'ADR-003 dans `docs/DECISIONS.md` et de la section B de `docs/DATA_POLICY.md`.

2. **Maintien du Principe "Stdlib Only" pour le Cœur Déterministe** :
   - *Question* : Confirmez-vous que les outils lourds (`theHarvester`, `invisible_playwright_mcp`) doivent rester strictement confinés dans des environnements isolés (Docker local / serveurs MCP) et ne JAMAIS figurer dans `requirements.txt` ?
   - *Impact* : Préserve l'intégrité de l'environnement de production et évite l'installation de dizaines de sous-dépendances instables.

3. **Adoption de l'Extension du Schéma de Données (Auditabilité Email & CMS)** :
   - *Question* : Approuvez-vous l'ajout formel dans `docs/LEAD_DATA_SCHEMA.md` du triplet de preuve sur les emails (`email_source`, `email_evidence`, `email_checked_at`) et de l'empreinte technique (`cms_detected`, `cms_source`, `cms_evidence`, `cms_checked_at`) ?
   - *Impact* : Condition préalable non-négociable avant d'autoriser tout script à peupler `public_professional_email`.

4. **Restriction des Sources de `theHarvester` aux Seules Sources 100% Gratuites** :
   - *Question* : Validez-vous la configuration stricte de `theHarvester` cantonnée aux seules sources ouvertes passives (`crt.sh`, `duckduckgo`, `bing`, `dnsdumpster`, `anubis`) à l'exclusion définitive des modules soumis à quotas ou carte bancaire (`shodan`, `hunter`, `censys`) ?
   - *Impact* : Garantie du respect absolu de la règle "Budget 0 €".

5. **Mise à Jour Officielle de la Documentation QA (21 Contrôles & 18 Fixtures)** :
   - *Question* : Autorisez-vous la mise à jour documentaire de `docs/QA_PROTOCOL.md`, `docs/TOOLING.md` et `README.md` pour corriger la désynchronisation et afficher officiellement les 21 contrôles métier et 18 tests négatifs déjà actifs dans le code ?
   - *Impact* : Rétablit la concordance absolue entre le code exécutable et la spécification qualité.
