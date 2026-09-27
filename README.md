# 🎯 Money — AI Lead Intelligence & Founder Ghostwriting

Outil de prospection chirurgicale et de qualification de leads B2B (agences web françaises de 2 à 20 collaborateurs), conçu selon un standard strict de vérité des données, budget 0€ et zéro dépendance payante.

---

## 📋 Ordre d'Exécution du Pipeline

Le pipeline opérationnel doit être exécuté dans l'ordre séquentiel suivant :

```text
[1. Sourcing Brut]
  └── data/gmaps_agences_web_raw.csv (Nettoyé RGPD)
          │
          ▼
[2. Filtrage & Dédoublonnage]
  └── python3 dedupe_and_shortlist.py
          │
          ▼
[3. Requalification Légale & Scoring Découplé]
  └── python3 requalify_leads.py
          │
          ▼
[4. Enrichissement OSINT Déterministe & Traçabilité]
  └── python3 enrich_leads_osint.py
          │
          ▼
[5. Restitution Client / Hub]
  └── python3 build_notion_markdown.py
          │
          ▼
[6. Contrôle Qualité Pré-Livraison]
  └── python3 qa_check.py
```

### 1. Filtrage et Dédoublonnage
```bash
python3 dedupe_and_shortlist.py
```
- **Rôle** : Nettoie le vivier brut issu de Google Maps, élimine les non-web, et dédoublonne strictement sur le nom de domaine et le numéro de téléphone.
- **Sortie** : `data/gmaps_agences_web_shortlist.csv`.

### 2. Requalification Légale (SIRENE) & Scoring
```bash
python3 requalify_leads.py
```
- **Rôle** :
  - Interroge l'API publique de l'État (`recherche-entreprises.api.gouv.fr`).
  - Réconcilie l'établissement avec le code postal strict de l'adresse.
  - Vérifie la tranche d'effectif officielle INSEE (exclusion immédiate des structures non-employeurs `NN`/`00`).
  - Extrait l'identité et le rôle officiel du dirigeant (`qualite` au registre).
  - Réalise un audit HTTP réel (code HTTP 200 + SSL HTTPS avec timeout 5s).
  - Calcule les scores découplés (`lead_gen_score`, `ghostwriting_score`, `confidence_score`) et génère les justifications textuelles (`reasons`).
- **Sorties** : `data/top30_leads_requalified.json` et `data/top30_leads_requalified.csv`.

### 3. Orchestration Multi-Providers & Enrichissement V2
```bash
# Architecture V2 : Orchestration centralisée avec chaîne de repli et observabilité
python3 enrichment_orchestrator.py --offset 0 --limit 30

# Diagnostic d'un prospect (Pourquoi non enrichi ?)
python3 enrichment_orchestrator.py --explain "Nom ou domaine du prospect"

# Optionnel (Pipeline V1) : Moissonnage CLI theHarvester et ingestion
python3 harvest_osint.py --offset 0 --limit 30
python3 enrich_leads_osint.py
```
- **Rôle** :
  - Orchestration modulaire via `money_v2` pilotant `HttpProvider`, `FirecrawlProvider`, `InvisiblePlaywrightProvider` (serveur MCP officiel `uvx invisible-playwright-mcp` en sous-processus isolé), `TheHarvesterProvider`, `DnsMxProvider`, `CmsTechnologyProvider` et `ApiRegistryProvider`.
  - Chaîne de repli déterministe pour l'audit web : `HttpProvider (1) -> FirecrawlProvider (2) -> Consignation Technique (3)`. Invisible Playwright intervient hors chaîne synchrone pour les cas spécifiques et staging d'audit.
  - Détection CMS observable et résolution MX en 3 paliers (DNS UDP RFC 1035, `getaddrinfo`, et DoH HTTPS `dns.google` pur stdlib).
  - Enregistrement universel d'évidences à 11 dimensions et persistance télémétrique (`data/telemetry_events.json`).
  - Barrière d'étanchéité inviolable (`LegalReconciliationLayer`) interdisant toute modification des champs SIRENE Niveau 1/2.
- **Sorties** : `data/top30_leads_requalified.json` et `data/top30_leads_requalified.csv` enrichis.

### 4. Restitution Client & Lead Intelligence Room
```bash
python3 build_notion_markdown.py
```
- **Rôle** : Génère la synthèse markdown consolidée avec tableau hiérarchisé par statut, fiches détaillées du Top 5 vérifié et templates de messages d'approche personnalisés (sans hallucination de prénom).
- **Sortie** : `data/lead_intelligence_room.md`.

### 5. Contrôle Qualité Métier & Tests Comportementaux V2
```bash
# 1. Contrôle Qualité Métier (24 points & 21 tests négatifs)
python3 qa_check.py

# 2. Suite de Tests Comportementaux V2 (24 tests unitaires)
python3 -m unittest tests/test_v2_architecture.py
```
- **Rôle** :
  - `qa_check.py` : Exécute automatiquement la vérification des 24 points de contrôle de vérité métier (`docs/QA_PROTOCOL.md`) et 21 tests négatifs sur fixtures délibérément corrompues.
  - `tests/test_v2_architecture.py` : Valide 24 scénarios comportementaux d'infrastructure (pannes réseau, timeouts, blocages WAF, détection d'outils manquants, étanchéité SIRENE, pagination de découverte, rejet de CAC et personnes morales).


---

## 🛡️ Règles Non-Négociables

1. **Budget 0 €** : Aucune dépendance payante, aucun proxy payant, aucune API soumise à carte bancaire.
2. **Conformité RGPD** : Suppression des données privées (avis individuels, images, métadonnées personnelles de tracking).
3. **Vérité Légale** : La taille d'entreprise et l'identité des dirigeants proviennent exclusivement des registres publics de l'État (INSEE / SIRENE).
