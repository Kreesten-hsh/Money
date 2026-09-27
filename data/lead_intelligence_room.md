# 🎯 Lead Intelligence Room — Agences Web France

> **Campagne** : AI Lead Intelligence & Founder Ghostwriting (MVP)  
> **Dernière mise à jour** : 2026-09-27T22:58:37Z (Audit Déterminisme SIRENE & Preuves Séparées)  
> **Statut** : Registres Publics (INSEE / SIRENE) + Matching Multi-Critères + Contrôle HTTP  
> **Données consolidées** : 6 vérifiées | 1 partiellement vérifiées | 15 à auditer | 8 disqualifiées

---

## 01 — Campaign Overview

Cette Lead Intelligence Room documente le lot audité d'agences web françaises de 2 à 20 collaborateurs, conformément aux standards de vérité stricts du projet Money (zéro hallucination, preuves traçables, détection d'incohérences).

### Métriques Clés Consolidées
- **Volume total analysé** : 30 entreprises issues de la shortlist dédupliquée.
- **Entités confirmées dans l'ICP (VERIFIED)** : **6 agences** (SIREN actif, effectif vérifié 2 à 20 personnes avec double preuve pour tranche 01, dirigeant légal officiel vérifié, matching confirmé sans ambiguïté, site HTTPS accessible).
- **Entités partiellement vérifiées (PARTIALLY VERIFIED)** : **1 agence** (immatriculation active mais données d'effectif partielles ou discordantes).
- **Entités en révision (REQUIRES REVIEW)** : **15 agences** (homonymie, ambiguïté concurrentielle SIRENE avec delta < 20, ou site web sous-domaine/inaccessible).
- **Entités disqualifiées (DISQUALIFIED)** : **8 agences** (non employeur tranche NN/00, cessation d'activité ou effectif hors cible >20).
- **Objectif financier** : 1 000 000 FCFA encaissés avant le 31 décembre 2026 via 2 à 3 pilotes payants.

---

## 02 — ICP & Criteria

### Critères d'Éligibilité Appliqués
1. **Statut Légal & Immatriculation** : Établissement actif au registre national SIRENE / INSEE.
2. **Matching SIRENE Déterministe & Détection d'Ambiguïté** :
   - `MATCH_CONFIRMED` : Concordance nom, code postal strict, voie et NAF (score >= 75) avec delta >= 20 vis-à-vis du 2ème candidat.
   - `MATCH_UNCERTAIN` : Dès qu'un 2ème candidat concurrent est proche (score >= 55 et delta < 20) ou informations insuffisantes.
3. **Tranche d'Effectif Réelle (2 à 20 personnes)** :
   - Tranches INSEE `02` (3-5), `03` (6-9), `11` (10-19) admises.
   - Tranche INSEE `01` (1 ou 2 salariés) : Admise uniquement avec preuve secondaire publique (co-gérance / multiples dirigeants au greffe prouvant >= 2 personnes). Sans cette preuve, maintien en `REQUIRES REVIEW`.
   - Tranches `NN` et `00` (non employeur / 0 salarié) : Disqualifiées d'office.
4. **Scores Découplés & Justifiés** :
   - `Lead Gen Score` (0–100) : Activité (30), Taille (25), Signal commercial (25), Traction (20). En Phase 1, faute de signal d'affaires externe vérifié, le signal commercial est à 0 (pénalité de 25 points documentée, score max effectif = 75/100).
   - `Ghostwriting Score` (0–100) : Neutralisé à 0/100 en Phase 1 (aucun audit LinkedIn public conduit, refus des heuristiques artificielles).
   - `Confidence Score` (0–100) : Solidité des preuves (plafonné à 60 si non VERIFIED, 40 si matching incertain).

---

## 03 — Qualified Leads (Lot Requalifié des 30)

| # | Entreprise | Ville | SIREN | Effectif Officiel | Dirigeant Légal (Rôle Officiel) | Matching | Scores (LG / GW / Conf) | Statut |
|---|---|---|---|---|---|---|---|---|
| 01 | **Simplement** | Marseille | `881530265` | 1 ou 2 salariés | JONATHAN COLNAT (Gérant) | `MATCH_CONFIRMED` | `68` / `0` / `95` | ✅ VERIFIED |
| 02 | **Akisiweb** | Paris | `492119599` | 6 à 9 salariés | FRANCOIS ADRASTE (Gérant) | `MATCH_CONFIRMED` | `65` / `0` / `100` | ✅ VERIFIED |
| 03 | **Pilot'in - Agence WordPress** | Lyon | `794214619` | 10 à 19 salariés | CARGO (Directeur Général) | `MATCH_CONFIRMED` | `65` / `0` / `100` | ✅ VERIFIED |
| 04 | **Keole & Gazoline** | Saint-Jean-de-Védas | `433978616` | 10 à 19 salariés | ALEXANDRE JEAN BERNARD ALZOUNIES (Gérant) | `MATCH_CONFIRMED` | `65` / `0` / `100` | ✅ VERIFIED |
| 05 | **4Beez** | Paris | `837559301` | 3 à 5 salariés | KARIM BELHADJ LARBI (Directeur Général) | `MATCH_CONFIRMED` | `65` / `0` / `100` | ✅ VERIFIED |
| 06 | **Evolyon** | Lyon | `823956289` | 1 ou 2 salariés | FRÉDÉRIC JULIEN FRANCE (Directeur Général) | `MATCH_CONFIRMED` | `65` / `0` / `95` | ✅ VERIFIED |
| 07 | **Agence THRIVE** | Bordeaux | `835080409` | 10 à 19 salariés | PIERRE PATRICK MARSANNE (Président de SAS) | `MATCH_PLAUSIBLE` | `70` / `0` / `60` | 🟡 PARTIALLY |
| 08 | **Linkeo** | Lyon | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `20` | 🔍 REVIEW |
| 09 | **M COM** | Marseille | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 10 | **Starboost** | Paris | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `40` / `0` / `40` | 🔍 REVIEW |
| 11 | **Linkeo** | Montpellier | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `50` / `0` / `20` | 🔍 REVIEW |
| 12 | **Agence Info Conception - SEO Nantes** | Vertou | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `40` / `0` / `40` | 🔍 REVIEW |
| 13 | **eMaginance** | Nice | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 14 | **ImagesCréations** | Nantes | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 15 | **Aixpressweb - Création de site internet Marseille** | Marseille | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 16 | **Referencemoi - Agence Web Lille - Agence SEO Lillle - Ads - Intervenant Digital** | Lille | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `35` / `0` / `40` | 🔍 REVIEW |
| 17 | **JALIS Toulouse** | Toulouse | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 18 | **NRV** | Toulouse | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `40` / `0` / `20` | 🔍 REVIEW |
| 19 | **Weby Lab** | Lyon | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `20` | 🔍 REVIEW |
| 20 | **Rankit - Agence SEO Lyon** | Lyon | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `40` / `0` / `40` | 🔍 REVIEW |
| 21 | **Webmaster freelance Paris - DIGIWEBLINE** | Saint-Denis | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `55` / `0` / `40` | 🔍 REVIEW |
| 22 | **Promoovoir** | Paris | `Non trouvé` | Non identifié | Non identifié au registre | `NO_MATCH` | `40` / `0` / `5` | 🔍 REVIEW |
| 23 | **Jalis** | Marseille | `440941888` | 100 à 199 salariés | SERGE ZAREH ALAGY (Directeur Général) | `MATCH_UNCERTAIN` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 24 | **Horizon** | Toulouse | `788502466` | 20 à 49 salariés | EQUINOXE (Président de SAS) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 25 | **Vistalid** | Marseille | `792365421` | 100 à 199 salariés | JULIEN MARCHAND (Directeur Général) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 26 | **Gentleview** | Lyon | `807522719` | 0 salarié déclaré (Non employeur) | THEODORE LAFOND (Président de SAS) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 27 | **Webdevo** | Bordeaux | `901389767` | 0 salarié déclaré (Non employeur) | ARTHUR MAXIME JEAN LONGERON (Dirigeant déclaré) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 28 | **Ethiko** | Bordeaux | `841563711` | 0 salarié au 31/12 | RAPHAEL AYMAR RAOUL DUMOND (Gérant) | `MATCH_UNCERTAIN` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 29 | **Cédric Chevillard** | Seyssinet-Pariset | `830623138` | 0 salarié déclaré (Non employeur) | CEDRIC CHEVILLARD (Dirigeant déclaré) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |
| 30 | **Yohann Deprez** | Lyon | `902407170` | 0 salarié déclaré (Non employeur) | YOHANN DEPREZ (Dirigeant déclaré) | `MATCH_CONFIRMED` | `0` / `0` / `0` | ❌ DISQUALIFIED |

---

## 04 — Priority Leads (Top 5 Réellement Vérifiés & Sans Ambiguïté)

### 01 — Simplement (Marseille)
- **Raison Sociale / SIREN** : SIMPLEMENT | SIREN `881530265` (Source : [API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE](https://annuaire-entreprises.data.gouv.fr/entreprise/881530265))
- **Site Web** : [https://simplement.me/](https://simplement.me/) | **Téléphone Direct** : `+33 7 61 94 15 67`
- **Taille Officielle (INSEE)** : **1 ou 2 salariés** (Tranche 01 (1-2 salariés) validée par co-gérance officielle au greffe (>= 2 personnes))
  - *Preuve d'effectif vérifiée* : 2 co-dirigeants déclarés au greffe : JONATHAN COLNAT (Gérant), EDWIN PARMENTIER (Gérant) prouvant >= 2 personnes en activité
- **Dirigeant Identifié** : **JONATHAN COLNAT** (Gérant) (Source : [https://annuaire-entreprises.data.gouv.fr/entreprise/881530265](https://annuaire-entreprises.data.gouv.fr/entreprise/881530265))
- **Matching SIRENE Déterministe** : `MATCH_CONFIRMED` (Score candidat: 100/100 | Delta 2ème candidat: 60 | Concordance robuste confirmée sans ambiguïté concurrentielle (score 100/100, delta 60))
- **Preuve de l'Offre Principale (`main_offer`)** :
  - Offre : **Création de sites Web & Référencement SEO**
  - Preuve : Extrait observé (title/meta) : 'Agence web à Marseille : Design UX/UI sur mesure, SEO optimisé et leviers d’acqu'
  - Source : [https://simplement.me/](https://simplement.me/) (vérifié le `2026-09-27T22:56:06Z`)
- **Preuve de la Clientèle Cible (`target_clients`)** :
  - Cible : **Non vérifié**
  - Preuve : Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil
  - Source : Aucune source externe (non inféré) (vérifié le `2026-09-27T22:56:06Z`)
- **Évaluation des Scores** :
  - `Lead Gen Score` : **68/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)
  - `Ghostwriting Score` : **0/100** (Neutralisé — en attente d'audit éditorial direct)
  - `Confidence Score` : **95/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)
- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :
> "Bonjour Jonathan, J'ai pris connaissance de vos réalisations sur votre site (https://simplement.me/), qui met en avant votre activité en création de sites web & référencement seo à Marseille. Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires. Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

### 02 — Akisiweb (Paris)
- **Raison Sociale / SIREN** : AKISIWEB | SIREN `492119599` (Source : [API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE](https://annuaire-entreprises.data.gouv.fr/entreprise/492119599))
- **Site Web** : [https://www.akisiweb.com/](https://www.akisiweb.com/) | **Téléphone Direct** : `+33 1 84 80 99 98`
- **Taille Officielle (INSEE)** : **6 à 9 salariés** (Éligible ICP direct (6 à 9 salariés))
- **Dirigeant Identifié** : **FRANCOIS ADRASTE** (Gérant) (Source : [https://annuaire-entreprises.data.gouv.fr/entreprise/492119599](https://annuaire-entreprises.data.gouv.fr/entreprise/492119599))
- **Matching SIRENE Déterministe** : `MATCH_CONFIRMED` (Score candidat: 100/100 | Delta 2ème candidat: 100 | Concordance robuste confirmée sans ambiguïté concurrentielle (score 100/100, delta 100))
- **Preuve de l'Offre Principale (`main_offer`)** :
  - Offre : **Création de sites Web & Référencement SEO**
  - Preuve : Extrait observé (title/meta) : 'Akisiweb vous accompagne pour la mise en place de votre stratégie digitale depui'
  - Source : [https://www.akisiweb.com/](https://www.akisiweb.com/) (vérifié le `2026-09-27T22:54:43Z`)
- **Preuve de la Clientèle Cible (`target_clients`)** :
  - Cible : **Non vérifié**
  - Preuve : Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil
  - Source : Aucune source externe (non inféré) (vérifié le `2026-09-27T22:54:43Z`)
- **Évaluation des Scores** :
  - `Lead Gen Score` : **65/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)
  - `Ghostwriting Score` : **0/100** (Neutralisé — en attente d'audit éditorial direct)
  - `Confidence Score` : **100/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)
- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :
> "Bonjour Francois, J'ai pris connaissance de vos réalisations sur votre site (https://www.akisiweb.com/), qui met en avant votre activité en création de sites web & référencement seo à Paris. Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires. Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

### 03 — Pilot'in - Agence WordPress (Lyon)
- **Raison Sociale / SIREN** : PILOT'IN (PILOT'IN) | SIREN `794214619` (Source : [API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE](https://annuaire-entreprises.data.gouv.fr/entreprise/794214619))
- **Site Web** : [https://www.pilot-in.com/](https://www.pilot-in.com/) | **Téléphone Direct** : `+33 4 82 53 74 30`
- **Taille Officielle (INSEE)** : **10 à 19 salariés** (Éligible ICP direct (10 à 19 salariés))
- **Dirigeant Identifié** : **CARGO** (Directeur Général) (Source : [https://annuaire-entreprises.data.gouv.fr/entreprise/794214619](https://annuaire-entreprises.data.gouv.fr/entreprise/794214619))
- **Matching SIRENE Déterministe** : `MATCH_CONFIRMED` (Score candidat: 100/100 | Delta 2ème candidat: 100 | Concordance robuste confirmée sans ambiguïté concurrentielle (score 100/100, delta 100))
- **Preuve de l'Offre Principale (`main_offer`)** :
  - Offre : **Création et refonte de sites web**
  - Preuve : Extrait observé (title/meta) : 'Hissez-haut vos projets digitaux ! Nous donnons du sens à vos ambitions digitale'
  - Source : [https://www.pilot-in.com/](https://www.pilot-in.com/) (vérifié le `2026-09-27T22:54:52Z`)
- **Preuve de la Clientèle Cible (`target_clients`)** :
  - Cible : **Non vérifié**
  - Preuve : Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil
  - Source : Aucune source externe (non inféré) (vérifié le `2026-09-27T22:54:52Z`)
- **Évaluation des Scores** :
  - `Lead Gen Score` : **65/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)
  - `Ghostwriting Score` : **0/100** (Neutralisé — en attente d'audit éditorial direct)
  - `Confidence Score` : **100/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)
- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :
> "Bonjour l'équipe Pilot'in - Agence WordPress, J'ai pris connaissance de vos réalisations sur votre site (https://www.pilot-in.com/), qui met en avant votre activité en création et refonte de sites web à Lyon. Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires. Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

### 04 — Keole & Gazoline (Saint-Jean-de-Védas)
- **Raison Sociale / SIREN** : KEOLE & GAZOLINE | SIREN `433978616` (Source : [API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE](https://annuaire-entreprises.data.gouv.fr/entreprise/433978616))
- **Site Web** : [https://www.studiokg.fr/](https://www.studiokg.fr/) | **Téléphone Direct** : `+33 7 44 99 52 52`
- **Taille Officielle (INSEE)** : **10 à 19 salariés** (Éligible ICP direct (10 à 19 salariés))
- **Dirigeant Identifié** : **ALEXANDRE JEAN BERNARD ALZOUNIES** (Gérant) (Source : [https://annuaire-entreprises.data.gouv.fr/entreprise/433978616](https://annuaire-entreprises.data.gouv.fr/entreprise/433978616))
- **Matching SIRENE Déterministe** : `MATCH_CONFIRMED` (Score candidat: 100/100 | Delta 2ème candidat: 100 | Concordance robuste confirmée sans ambiguïté concurrentielle (score 100/100, delta 100))
- **Preuve de l'Offre Principale (`main_offer`)** :
  - Offre : **Extrait Firecrawl : Agence communication Montpellier : Transformez vos idées**
  - Preuve : Firecrawl scrape validé : 'Transformez vos idées en succès avec Studio KG, l'agence créative de Montpellier. Sans bla'
  - Source : [https://www.studiokg.fr/](https://www.studiokg.fr/) (vérifié le `2026-09-27T22:56:18Z`)
- **Preuve de la Clientèle Cible (`target_clients`)** :
  - Cible : **Non vérifié**
  - Preuve : Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil
  - Source : Aucune source externe (non inféré) (vérifié le `2026-09-27T22:55:38Z`)
- **Évaluation des Scores** :
  - `Lead Gen Score` : **65/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)
  - `Ghostwriting Score` : **0/100** (Neutralisé — en attente d'audit éditorial direct)
  - `Confidence Score` : **100/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)
- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :
> "Bonjour Alexandre, J'ai pris connaissance de vos réalisations sur votre site (https://www.studiokg.fr/), qui met en avant votre activité en extrait firecrawl : agence communication montpellier : transformez vos idées à Saint-Jean-de-Védas. Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires. Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

### 05 — 4Beez (Paris)
- **Raison Sociale / SIREN** : 4BEEZ | SIREN `837559301` (Source : [API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE](https://annuaire-entreprises.data.gouv.fr/entreprise/837559301))
- **Site Web** : [https://4beez.agency/](https://4beez.agency/) | **Téléphone Direct** : `+33 1 76 54 30 97`
- **Taille Officielle (INSEE)** : **3 à 5 salariés** (Éligible ICP direct (3 à 5 salariés))
- **Dirigeant Identifié** : **KARIM BELHADJ LARBI** (Directeur Général) (Source : [https://annuaire-entreprises.data.gouv.fr/entreprise/837559301](https://annuaire-entreprises.data.gouv.fr/entreprise/837559301))
- **Matching SIRENE Déterministe** : `MATCH_CONFIRMED` (Score candidat: 100/100 | Delta 2ème candidat: 100 | Concordance robuste confirmée sans ambiguïté concurrentielle (score 100/100, delta 100))
- **Preuve de l'Offre Principale (`main_offer`)** :
  - Offre : **Développement Web sur-mesure**
  - Preuve : Extrait observé (title/meta) : '4Beez est une agence digitale à Paris qui conçoit des identités fortes, des site'
  - Source : [https://4beez.agency/](https://4beez.agency/) (vérifié le `2026-09-27T22:55:43Z`)
- **Preuve de la Clientèle Cible (`target_clients`)** :
  - Cible : **Non vérifié**
  - Preuve : Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil
  - Source : Aucune source externe (non inféré) (vérifié le `2026-09-27T22:55:43Z`)
- **Évaluation des Scores** :
  - `Lead Gen Score` : **65/100** (Plafond effectif 75/100 en Phase 1 : pénalité de 25 pts en l'absence de signal commercial externe vérifié)
  - `Ghostwriting Score` : **0/100** (Neutralisé — en attente d'audit éditorial direct)
  - `Confidence Score` : **100/100** (Preuves légales, effectif, site HTTPS et canal direct vérifiés)
- **Message d'Outreach Recommandé (Manuel & 100% Vérifiable)** :
> "Bonjour Karim, J'ai pris connaissance de vos réalisations sur votre site (https://4beez.agency/), qui met en avant votre activité en développement web sur-mesure à Paris. Dans le cadre de l'initiative Money, nous sélectionnons des agences web régionales indépendantes de 2 à 20 collaborateurs afin de tester un protocole de qualification ciblée d'opportunités d'affaires. Seriez-vous ouvert à un court échange afin de découvrir notre démarche et évaluer si ce format présente une pertinence pour votre développement ?"

---

## 05 — Outreach Queue & Cadencement Manuel

1. **Approche 100% Manuelle** : Aucun outil d'automatisation, aucun cold emailing massif, aucun scraping sauvage.
2. **Cibles Immédiates** : Uniquement les agences disposant du statut `VERIFIED` avec rapprochement `MATCH_CONFIRMED`.
3. **Cadencement** : 2 à 3 prises de contact personnalisées par jour après audit approfondi de chaque projet.
4. **Règle de Clarté Commerciale** : Aucune promesse non prouvée, aucune affirmation d'urgence infondée.

---

## 06 — Market Signals & Analyse Terrain

- **Divergence Enseigne Commerciale / Dénomination Juridique** : Plusieurs agences utilisent un nom commercial non déposé au RCS. La recherche SIRENE exige une validation croisée du code postal et du numéro de voie pour éviter les faux homonymes.
- **Détection des Ambiguïtés SIRENE** : L'algorithme pénalise les résultats concurrents proches (delta score < 20), empêchant tout faux rapprochement arbitraire.
- **Effectifs Déclarés vs Effectifs Réels** : La tranche INSEE 01 (« 1 ou 2 salariés ») n'est acceptée en `VERIFIED` qu'en présence avérée d'au moins deux personnes (co-dirigeants déclarés au greffe).

---

## 07 — Sources & Evidence (Traçabilité)

- **Données Légales & Effectifs** : Registre national SIRENE via l'API publique `recherche-entreprises.api.gouv.fr`.
- **Données Commerciales** : Google Maps Scraper (Docker local) dédupliqué et filtré par pôle urbain.
- **Audit des Offres & Sites** : Contrôle HTTP/HTTPS direct et inspection de contenu.
- **Datasets du Projet** :
  - `data/gmaps_agences_web_shortlist.csv`
  - `data/top30_leads_requalified.csv`
  - `data/top30_leads_requalified.json`

---

## 08 — Delivery History

- **26/09/2026 (Audit Initial)** : Premier crawl et détection des failles méthodologiques.
- **26/09/2026 (Correction Commit db02a84)** : Ajout SIRENE initial et découplage.
- **2026-09-27 (Refonte Preuves Métier & Ambiguïté SIRENE)** : Matching SIRENE avec détection d'ambiguïté (delta), séparation stricte offre/cible, preuves structurées, outreach vérifié et dates 100% dynamiques.