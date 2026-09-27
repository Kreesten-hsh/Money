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
│  DnsMxProvider   │    │  CmsTechProvider │    │FirecrawlProvider │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         ▼
┌──────────────────┐
│ApiRegistryProv.  │
└──────────────────┘
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

## 3. Chaîne de Repli Déterministe pour l'Audit de Site (3 Paliers)

Lors de l'inspection de l'offre d'une agence (`main_offer`) ou de sa clientèle cible (`target_clients`), l'orchestrateur sollicite `FallbackStrategy` qui enchaîne séquentiellement 3 paliers déterministes :

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
[Palier 3 : Consignation Technique (BLOCKED / ERROR / TIMEOUT)]
  - Enregistrement du statut réel et de la cause safe dans la télémétrie.
  - Aucune invention de données ni masque de panne.
```

> [!NOTE]
> **Rôle d'InvisiblePlaywrightProvider et d'agent-reach** :  
> L'enrichissement via `InvisiblePlaywrightProvider` (serveur MCP officiel `uvx invisible-playwright-mcp` piloté via client stdio isolé `mcp_playwright_client.py`) reste **HORS** de cette chaîne HTTP synchrone de base. Il intervient sur les cas spécifiques (annuaires protégés, mentions légales bloquées, consultation éditoriale LinkedIn ADR-008) et alimente le dataset via le contrat d'audit staging (`data/mcp_audit_staging.json`).  
> De même, `agent-reach` est un outil d'investigation opérateur déclenché sur jugement et alimente le staging sous `trigger_type="agent_reach_research"`.

---

## 4. Isolation du Client MCP Stdio (`mcp_playwright_client.py`)

Afin de préserver l'étanchéité du cœur applicatif Python (zéro dépendance externe dans `requirements.txt`) :
1. **Sous-processus Isolé** : `InvisiblePlaywrightProvider` exécute `uv run --with mcp --python 3.11 python3 mcp_playwright_client.py <args>`.
2. **Protocole MCP Stdio** : Le script communique directement avec le serveur `uvx invisible-playwright-mcp` via les flux standard `stdio`.
3. **Moteur Furtif Spécifique** : Le serveur instancie le moteur Firefox patché stealth (`firefox-151.0-stealth`).
4. **Garde-fous Invariants** :
   - Quota strict ADR-008 (≤ 5 consultations/jour tracé).
   - Rejet immédiat de toute extraction de champs interdits (`FORBIDDEN_FIELDS` : `company_size`, `decision_maker_identity`).
   - Obligation d'un matching SIRENE confirmé (`MATCH_CONFIRMED`) pour la consultation LinkedIn.

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
