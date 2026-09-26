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
[4. Restitution Client / Hub]
  └── python3 build_notion_markdown.py
          │
          ▼
[5. Contrôle Qualité Pré-Livraison]
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

### 3. Restitution Client & Lead Intelligence Room
```bash
python3 build_notion_markdown.py
```
- **Rôle** : Génère la synthèse markdown consolidée avec tableau hiérarchisé par statut, fiches détaillées du Top 5 vérifié et templates de messages d'approche personnalisés (sans hallucination de prénom).
- **Sortie** : `data/lead_intelligence_room.md`.

### 4. Contrôle Qualité Automatisé (QA 20 Points & Tests Négatifs)
```bash
python3 qa_check.py
```
- **Rôle** : Exécute automatiquement la vérification des 20 points de contrôle de vérité métier du protocole qualité (`docs/QA_PROTOCOL.md`) ainsi qu'une suite de tests négatifs sur fixtures délibérément corrompues.
- **Points Clés** :
  - Hard gates pour le statut `VERIFIED` (`MATCH_CONFIRMED`, ICP strict 2-20, dirigeant officiel, HTTPS).
  - Plafond strict de confiance (max 60 si non-VERIFIED, max 40 si matching incertain).
  - Neutralisation du score Ghostwriting (0/100) en l'absence d'audit LinkedIn vérifié.
  - Zéro affirmation non prouvée dans l'outreach et aucun faux signal dérivé des avis Google.

---

## 🛡️ Règles Non-Négociables

1. **Budget 0 €** : Aucune dépendance payante, aucun proxy payant, aucune API soumise à carte bancaire.
2. **Conformité RGPD** : Suppression des données privées (avis individuels, images, métadonnées personnelles de tracking).
3. **Vérité Légale** : La taille d'entreprise et l'identité des dirigeants proviennent exclusivement des registres publics de l'État (INSEE / SIRENE).
