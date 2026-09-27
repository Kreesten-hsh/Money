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

### 3. Orchestration theHarvester & Enrichissement OSINT Déterministe
```bash
# Optionnel : génération du staging emails via theHarvester CLI (si installé via uv tool install theHarvester)
python3 harvest_osint.py --offset 0 --limit 30

# Ingestion et enrichissement déterministe (emails, MX, CMS, MCP staging)
python3 enrich_leads_osint.py
```
- **Rôle** :
  - Orchestration de theHarvester via subprocess stdlib pur (`harvest_osint.py`).
  - Consomme les stagings passifs (`data/osint_emails_staging.json` et `data/mcp_audit_staging.json`).
  - Valide les emails professionnels par résolution MX native en 3 paliers (DNS UDP brut RFC 1035, `getaddrinfo`, et DoH HTTPS `dns.google` pur stdlib) et contrôle de concordance stricte de domaine.
  - Détecte l'empreinte CMS de façon observable via signatures HTML et en-têtes HTTP.
  - Renseigne le triplet officiel de traçabilité (`source`, `evidence`, `checked_at`) et l'activité LinkedIn consultative (ADR-008) sans jamais altérer les registres légaux.
- **Sorties** : `data/top30_leads_requalified.json` et `data/top30_leads_requalified.csv` enrichis.

### 4. Restitution Client & Lead Intelligence Room
```bash
python3 build_notion_markdown.py
```
- **Rôle** : Génère la synthèse markdown consolidée avec tableau hiérarchisé par statut, fiches détaillées du Top 5 vérifié et templates de messages d'approche personnalisés (sans hallucination de prénom).
- **Sortie** : `data/lead_intelligence_room.md`.

### 5. Contrôle Qualité Automatisé (QA 24 Points & 21 Tests Négatifs)
```bash
python3 qa_check.py
```
- **Rôle** : Exécute automatiquement la vérification des 24 points de contrôle de vérité métier du protocole qualité (`docs/QA_PROTOCOL.md`) ainsi qu'une suite de 21 tests négatifs sur fixtures délibérément corrompues.
- **Points Clés** :
  - Hard gates pour le statut `VERIFIED` (`MATCH_CONFIRMED`, ICP strict 2-20, dirigeant officiel, HTTPS).
  - Plafond strict de confiance (max 60 si non-VERIFIED, max 40 si matching incertain).
  - Neutralisation du score Ghostwriting (0/100) en l'absence d'audit LinkedIn vérifié.
  - Zéro affirmation non prouvée dans l'outreach et aucun faux signal dérivé des avis Google.
  - Étanchéité absolue Niveau 4 vs Niveaux 1/2 : aucune donnée issue du staging MCP ne peut altérer l'identité du dirigeant ou la taille d'entreprise.

---

## 🛡️ Règles Non-Négociables

1. **Budget 0 €** : Aucune dépendance payante, aucun proxy payant, aucune API soumise à carte bancaire.
2. **Conformité RGPD** : Suppression des données privées (avis individuels, images, métadonnées personnelles de tracking).
3. **Vérité Légale** : La taille d'entreprise et l'identité des dirigeants proviennent exclusivement des registres publics de l'État (INSEE / SIRENE).
