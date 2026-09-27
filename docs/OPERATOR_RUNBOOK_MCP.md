# Runbook Opérateur MCP — Navigation Furtive & Enrichissement Sécurisé

> **Statut** : Document opérationnel de référence (ADR-008 & ADR-009)  
> **Outil** : `invisible_playwright_mcp` (Contournement anti-bot & browser stealth en lecture seule)  
> **Cible** : Agent IA Opérateur & Développeur Senior  
> **Règle Fondamentale** : Les extractions MCP (Niveau 4) ne prévalent **JAMAIS** sur les registres légaux officiels (Niveau 1/2 SIRENE).

---

## 1. Contexte & Principes Directeurs

L'outil `invisible_playwright_mcp` fournit un navigateur Chromium piloté via `patchright` (ou Playwright) configuré pour minimiser la détection automatisée (masquage de `navigator.webdriver`, courbes de souris réalistes, gestion des en-têtes et CDP patché).

### Capacités Réelles vs Non-Garanties (Section 5 Spécification)
> [!IMPORTANT]
> - **Capacités Réelles** : Permet de franchir des challenges anti-bots basiques ou d'accéder à des pages d'accueil et annuaires publics rejetant les requêtes HTTP brutes (ex: 403 Forbidden sur `urllib`).
> - **NON-GARANTIE ABSOLUE** : Ne garantit en aucun cas un contournement à 100% de Cloudflare Turnstile, DataDome, Akamai ou de tout système de détection comportementale avancée.
> - **Murs d'authentification** : Ne permet aucun contournement des pages nécessitant un compte connecté ou une authentification obligatoire (login wall).
> - **Interdiction du Scraping de Masse** : L'outil est strictement un moteur de repli unitaire, et non un outil de moissonnage industriel.

Conformément à **ADR-008** et à la politique de conformité RGPD (`docs/DATA_POLICY.md` §B), son utilisation par l'opérateur IA est **strictement encadrée** :
1. **Lecture Seule Exclusive** : Aucune interaction d'écriture, aucun envoi de message, aucune soumission de formulaire automatisé.
2. **Zéro Compte Connecté** : Interdiction absolue de connecter des comptes personnels (notamment LinkedIn). Les consultations se font exclusivement sur des pages et profils publics accessibles sans authentification.
3. **Plafond de Fréquence** : 3 à 5 consultations unitaires ciblées par jour maximum.
4. **Zéro Stockage Privé** : Seules des métadonnées professionnelles publiques observables et vérifiables sont consignées.
5. **Justification Obligatoire (`browser_usage_reason`)** : Chaque évidence produite par le navigateur doit obligatoirement porter la mention explicite du motif d'appel (`annuaire_fallback`, `unitaire_linkedin_adr008`, `waf_fallback`).

---

## 2. Déclencheurs Opérationnels (Triggers)

L'opérateur IA invoque `invisible_playwright_mcp` **exclusivement** sous l'un des deux déclencheurs ci-dessous.

```
                           [Événement Pipeline]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
[Trigger A : Repli Site / Annuaire]           [Trigger B : Consultation LinkedIn]
- Échec HTTP / 403 / Challenge WAF           - Lead déjà MATCH_CONFIRMED SIRENE
- Site agence ou annuaire pro                 - Profil public dirigeant physique
- Extraction : Offre, Mentions, Équipe        - Extraction : Activité éditoriale (Oui/Non)
           │                                                   │
           └─────────────────────────┬─────────────────────────┘
                                     ▼
                      [data/mcp_audit_staging.json]
                 (INTERDICTION : Champs légaux / effectifs)
```

---

### Trigger A : Repli Annuaires & Mentions Légales (`annuaire_fallback`)

#### Condition d'activation
- L'audit HTTP direct de `requalify_leads.py` (`inspect_website()`) ou un fetch Firecrawl échoue avec un code HTTP 403 (Cloudflare/WAF), un timeout de chargement, ou un challenge anti-bot.
- Le lead possède un SIREN validé (`MATCH_CONFIRMED` ou `MATCH_PLAUSIBLE`).

#### Cibles autorisées
1. **Le site officiel de l'agence directement** en navigation furtive.
2. **En cas d'inaccessibilité persistante du site propre**, les fiches d'annuaires professionnels publics suivants :
   - PagesJaunes (`pagesjaunes.fr`)
   - Malt (`malt.fr`)
   - Sortlist (`sortlist.fr`)
   - Annuaires régionaux d'entreprises

#### Données extractibles (Strictement délimitées)
- **Offre principale observable** (`main_offer`) : description concrète des prestations (ex: *Création de sites WordPress, e-commerce Prestashop, refonte UX*).
- **Mentions légales publiques** : extrait textuel prouvant l'exploitation du site.
- **Présence d'une page équipe / collaborateurs** : constat d'activité collective.

#### Format d'écriture dans `data/mcp_audit_staging.json`
```json
{
  "domain": "agence-exemple.fr",
  "trigger_type": "annuaire_fallback",
  "field_target": "main_offer",
  "extracted_value": "Développement web sur-mesure & applications mobiles",
  "source_url": "https://www.pagesjaunes.fr/pros/agence-exemple",
  "evidence_text": "Extrait observable : 'Spécialiste de la refonte e-commerce et applications métiers.'",
  "collected_at": "2026-09-27T14:30:00Z"
}
```

---

### Trigger B : Consultation LinkedIn Passif (`linkedin_consultation`)

#### Condition d'activation
- Réservé **exclusivement** aux leads certifiés avec un dirigeant personne physique confirmé (`decision_maker_is_person == True`) et un matching SIRENE `MATCH_CONFIRMED`.
- But unique : qualifier l'opportunité pour l'offre *Founder LinkedIn Ghostwriting* en vérifiant si le dirigeant prend la parole publiquement.

#### Contraintes d'exécution strictes (ADR-008)
- **Débit maximal** : 5 consultations de profils par jour ouvrable.
- **Mode déconnecté** : session de navigation vierge, aucun cookie de session privée.
- **Périmètre d'observation** : uniquement les 3 dernières publications publiques visibles.
- **Interdiction formelle** : Ne jamais scraper ni consigner la liste des relations, les recommandations privées, les coordonnées personnelles (téléphone/email personnel) ou le parcours scolaire non pertinent.

#### Données extractibles
- **Activité éditoriale publique récente** (`decision_maker_linkedin_activity`) : booléen (`True` si au moins un post public date de moins de 60 jours, `False` sinon).
- **URL du profil public** (`decision_maker_linkedin_source`).
- **Extrait textuel de preuve** (`evidence_text`) : thématique générale observable (ex: *Dernier post public du 12/09/2026 traitant de l'éco-conception web*).

#### Format d'écriture dans `data/mcp_audit_staging.json`
```json
{
  "profile_url": "https://www.linkedin.com/in/jean-dupont-agence",
  "trigger_type": "linkedin_consultation",
  "field_target": "decision_maker_linkedin_activity",
  "extracted_value": "True",
  "source_url": "https://www.linkedin.com/in/jean-dupont-agence",
  "evidence_text": "Post public observé daté du 12/09/2026 traitant des tendances CMS 2026.",
  "collected_at": "2026-09-27T14:32:00Z"
}
```

---

## 3. L'Interdit Absolu : Étanchéité Staging vs Registre Légal

> [!CAUTION]
> **RÈGLE TECHNIQUE INFRANGIBLE (CONTRÔLE QA 24)** :  
> Il est **strictement interdit** d'écrire dans `data/mcp_audit_staging.json` ou d'injecter via le MCP une valeur ciblant :
> - `decision_maker`
> - `decision_maker_role`
> - `decision_maker_is_person`
> - `company_size`
> - `company_size_code`
>
> Ces cinq attributs sont du **Niveau 1 et 2 (Registres officiels INSEE / Greffe / SIRENE)**. Aucune observation sur un annuaire, une page web ou LinkedIn ne peut surclasser ou altérer la vérité légale d'immatriculation.
>
> Le **Contrôle QA 24** de `qa_check.py` vérifie programmatiquement cette étanchéité et bloque immédiatement la livraison en cas de fuite.

---

## 4. Procédure d'Exécution Pas-à-Pas pour l'Opérateur IA

1. **Identification du besoin** : Lors de la phase de requalification, repérer les leads où l'audit HTTP direct a échoué (`main_offer` manquant) ou les leads `VERIFIED` éligibles à l'évaluation LinkedIn Ghostwriting.
2. **Ouverture de session furtive** : Invoquer `invisible_playwright_mcp` en mode headless stealth.
3. **Navigation & Capture** : Charger la page cible, attendre la stabilisation du DOM, extraire l'élément factuel textuel observable.
4. **Validation du Triplet de Preuve** : Vérifier que l'extrait contient une citation textuelle exacte et l'URL source précise.
5. **Écriture dans le Staging** : Insérer l'objet dans `data/mcp_audit_staging.json`.
6. **Ingestion & Validation QA** : Exécuter `python3 enrich_leads_osint.py` puis `python3 qa_check.py` pour valider l'absence de régression.
