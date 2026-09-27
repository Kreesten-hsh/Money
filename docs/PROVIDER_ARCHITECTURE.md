# Architecture des Providers & Chaîne de Repli — Money V2

## 1. Modèle Conceptuel des Providers

Chaque source d'information ou outil de collecte est encapsulé derrière l'interface unifiée `BaseProvider` (`money_v2/providers/base.py`). Le pipeline central ne dépend plus d'aucun appel système direct (`subprocess`, `urllib`, `socket`, `playwright`).

```
                    ┌─────────────────────────┐
                    │      BaseProvider       │
                    │─────────────────────────│
                    │ + name: str             │
                    │ + enabled: bool         │
                    │ + execute(target, ctx)  │
                    │ # _run(target, ctx)     │
                    │ + is_available() -> bool│
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         ▼                       ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   HttpProvider   │    │TheHarvesterProv. │    │InvisiblePlaywr.  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         ▼                       ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  DnsMxProvider   │    │  CmsTechProvider │    │ CrawleeProvider  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│FirecrawlProvider │    │ApiRegistryProv.  │
└──────────────────┘    └──────────────────┘
```

---

## 2. Cycle de Vie d'une Exécution

1. **Vérification d'activation (`enabled`)** : si le provider est désactivé, retour immédiat avec statut `AUTH_REQUIRED` sans appel réseau.
2. **Vérification de disponibilité (`is_available()`)** : contrôle de présence du binaire ou des dépendances dans l'environnement. Si absent : statut `TOOL_MISSING` explicite.
3. **Chronométrage télémétrique (`perf_counter`)** : calcul de la durée en millisecondes (`duration_ms`).
4. **Exécution protégée (`_run`)** :
   - Capture des `ProviderError` métier.
   - Capture des `TimeoutError` -> `TIMEOUT`.
   - Capture des exceptions génériques -> `UNKNOWN_ERROR`.
5. **Génération de la télémétrie (`ProviderTelemetry`)** : horodatages ISO 8601 UTC, volume d'évidences produites, statut d'exécution et message d'erreur sécurisé.

---

## 3. Chaîne de Repli Déterministe pour l'Audit de Site

Lors de l'inspection de l'offre d'une agence (`main_offer`) ou de sa clientèle cible (`target_clients`), l'orchestrateur sollicite `FallbackStrategy` qui enchaîne séquentiellement 4 paliers d'exécution :

```
[Palier 1 : HttpProvider]
  - Rapide, pur stdlib urllib.
  - Succès si HTTP 200 et balises observées.
  - Déclencheurs de repli : HTTP 403, 401, Cloudflare Turnstile, Timeout.
         │
         ▼ (si échec ou blocage)
[Palier 2 : FirecrawlProvider]
  - Extraction markdown haute fidélité via API/MCP.
  - Déclencheurs de repli : clé manquante, quota dépassé, échec API.
         │
         ▼ (si échec ou absent)
[Palier 3 : InvisiblePlaywrightProvider (`patchright_local`)]
  - Navigateur Chromium furtif piloté par patchright localement (zéro dépendance MCP distante).
  - Élimination des empreintes WebDriver et automatisation humaine des trajectoires.
  - Limité aux sites d'agences ou annuaires en lecture seule (ADR-008).
         │
         ▼ (si échec ou timeout)
[Palier 4 : CrawleeProvider]
  - Exploration multi-pages structurée avec file d'attente, retries et limitation de concurrence.
  - Moissonnage de secours sur les sous-pages de services.
         │
         ▼ (si épuisement des 4 paliers)
[Palier 5 : Consignation Technique (ERROR / BLOCKED / TIMEOUT)]
  - Enregistrement du statut réel et de la cause safe dans la télémétrie.
  - Aucune invention de données ni masque de panne.
```

---

## 4. Exploration Multi-Pages & CrawlPlanner

Le module `CrawlPlanner` (`money_v2/orchestrator/crawl_planner.py`) optimise la découverte d'informations manquantes :
1. **Planification Ciblée** : Détermine dynamiquement la liste d'URLs à explorer pour chaque lead :
   - `/` : Accueil (offre générique, footer, téléphone).
   - `/services`, `/offres`, `/expertises` : Prestations détaillées et mots-clés d'offres web.
   - `/contact` : Formulaire, adresses et emails de contact.
   - `/mentions-legales` : Rapprochement d'identité juridique et SIREN.
2. **Exécution Industrielle** : Déléguée à `CrawleeProvider.crawl_batch()` avec file d'attente FIFO, retries (2 max) et limitation de concurrence.
3. **Attribution Structurée des Évidences** : Chaque extrait d'offre, de cible ou d'email est tracé avec l'URL exacte de la sous-page où il a été observé (`source_url`).

---

## 5. Politique de Traitement des Emails (theHarvester)

Le provider `TheHarvesterProvider` applique une politique de confiance rigoureuse (`ConfidencePolicy`) :
- **Emails de domaine (`PUBLIC_DOMAIN_EMAIL`)** : collectés uniquement si le domaine correspond au domaine officiel du lead. Statut `HIGH`.
- **Adresses nominatives (`INDIVIDUAL_PROFESSIONAL_EMAIL`)** : séparées des adresses génériques (`contact@`, `info@`).
- **Emails rattachés au dirigeant (`DECISION_MAKER_MATCHED_EMAIL`)** : vérification de correspondance prénom/nom avec le dirigeant certifié SIRENE.
- **Interdiction Formelle de Promotion Arbitraire** : une adresse générique ne peut JAMAIS être déclarée comme email nominatif de dirigeant.
- **Adresses personnelles grand public (`BANNED_EMAIL_DOMAINS`)** : rejet formel (`gmail.com`, `orange.fr`, `yahoo.fr`, etc.).
- **Schémas d'adresses (`PATTERN`)** : si plusieurs formats apparaissent, l'information est catégorisée sous `email_pattern_indication` avec le niveau de confiance `PATTERN`. **Interdiction formelle de convertir un pattern en adresse email réelle.**
- **Résolution MX** : déléguée à `DnsMxProvider` et complétée par `ApiRegistryProvider (google_dns_doh)`.

---

## 6. Services Métier Dual-Product

1. **LeadIntelligenceService** (`money_v2/services/lead_intelligence_service.py`) :
   - Conformité ICP stricte (2 à 20 salariés, agence web, France).
   - Calcul mathématique du score d'opportunité d'affaires (`lead_gen_score`, max 75 en Phase 1).
   - Rédaction d'accroches personnalisées 100% vérifiables (salutation institutionnelle obligatoire sur dirigeant personne morale, ex: KWANTIC / WATTZ OFFICE).
2. **GhostwritingIntelligenceService** (`money_v2/services/ghostwriting_service.py`) :
   - Exigence stricte d'un dirigeant personne physique certifié SIRENE.
   - Neutralisation déterministe du score à 0/100 en l'absence de signal éditorial public observé.
   - Formulation d'angles éditoriaux B2B personnalisés basés sur le CMS détecté et l'offre observée.
