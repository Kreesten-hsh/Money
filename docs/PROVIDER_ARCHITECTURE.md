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

Lors de l'inspection de l'offre d'une agence (`main_offer`) ou de sa clientèle cible (`target_clients`), l'orchestrateur sollicite `FallbackStrategy` qui enchaîne séquentiellement :

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
[Palier 3 : InvisiblePlaywrightProvider]
  - Navigateur Chromium furtif piloté par patchright.
  - Contournement anti-bot, navigation réaliste sans compte connecté.
  - Limité aux sites d'agences ou annuaires en lecture seule.
         │
         ▼ (si échec)
[Palier 4 : Consignation Technique]
  - Enregistrement du statut réel (BLOCKED / TIMEOUT / NETWORK_ERROR).
  - Aucune invention de données.
```

---

## 4. Politique de Traitement des Emails (theHarvester)

Le provider `TheHarvesterProvider` applique une politique de confiance rigoureuse :
- **Emails de domaine (`PUBLIC_DOMAIN_EMAIL`)** : collectés uniquement si le domaine correspond au domaine officiel du lead. Statut `HIGH`.
- **Adresses personnelles grand public (`BANNED_EMAIL_DOMAINS`)** : rejet formel (`gmail.com`, `orange.fr`, `yahoo.fr`, etc.).
- **Schémas d'adresses (`PATTERN`)** : si plusieurs formats apparaissent, l'information est catégorisée sous `email_pattern_indication` avec le niveau de confiance `PATTERN`. **Interdiction formelle de convertir un pattern en adresse email réelle.**
- **Résolution MX** : déléguée à `DnsMxProvider` en preuve technique séparée.
