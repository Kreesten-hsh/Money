# Spécification de Qualification & Système de Scoring — Money

## 1. Cycle de Vie d'un Lead (Statuts Unifiés)
Chaque prospect progresse à travers 5 statuts stricts :

1. **CANDIDATE** : Entité brute issue du sourcing Google Maps. Aucune vérification administrative ni technique effectuée.
2. **REQUIRES REVIEW** : Entité présentant une incertitude critique (ex: tranche `01` sans preuve secondaire de 2 personnes, matching SIRENE incertain ou ambigu avec delta < 20, dirigeant non identifié). `confidence_score` plafonné à **60/100** (et **40/100** si matching incertain ou absent).
3. **PARTIALLY VERIFIED** : Entité dont l'effectif ICP est certifié (tranches 02, 03, 11) et légalement identifiée (`MATCH_CONFIRMED` ou `MATCH_PLAUSIBLE`) avec site accessible, mais données incomplètes ou contact direct manquant. `confidence_score` plafonné à **60/100**.
4. **VERIFIED** : Entité dont l'immatriculation légale est confirmée sans ambiguïté (`MATCH_CONFIRMED`), la taille strictement de 2 à 20 personnes certifiée (avec co-gérance pour tranche 01), le dirigeant officiel extrait du registre (`qualite` au RCS) et le site HTTPS 200 sont vérifiés avec preuves indépendantes. `confidence_score` $\ge$ **80/100**.
5. **DISQUALIFIED** : Entité hors ICP (0 salarié `NN`/`00`, effectif > 20, boîte fermée, fausse agence). `confidence_score` forcé à **0/100**.

---

## 2. Rapprochement SIRENE Déterministe & Détection d'Ambiguïté

Le rapprochement entre l'entité commerciale observée et le registre national des entreprises s'appuie sur une évaluation multi-critères :
- **Nom et identité (max 40 pts)** : Concordance intégrale ou partielle des tokens de marque exclusifs avec la raison sociale, le sigle ou l'enseigne de l'établissement.
- **Localisation stricte (max 45 pts)** : Code postal strict (30 pts, éliminatoire si absent) + numéro et voie à l'adresse (15 pts).
- **Activité / Code NAF (max 15 pts)** : Concordance avec la nomenclature numérique et web (62.01Z, 62.02A, 73.11Z, etc.).

### Règle de Non-Ambiguïté (Delta Écart) :
Un score élevé ne suffit pas à certifier un rapprochement. L'algorithme mesure systématiquement l'écart entre le meilleur candidat et le deuxième candidat le plus proche :
- **`MATCH_CONFIRMED`** : Score $\ge$ 75, code postal strict validé, NAF éligible, ET absence de candidat concurrent proche ($\text{Delta} \ge 20$ ou score du 2ème candidat $< 50$).
- **`MATCH_PLAUSIBLE`** : Score entre 50 et 74, localisation concordante, mais absence de validation de voie ou nom commercial non déposé.
- **`MATCH_UNCERTAIN`** : Déclenché dès qu'un 2ème candidat concurrent obtient un score $\ge 55$ avec un $\text{Delta} < 20$, ou si le score global est $< 50$.
- **`NO_MATCH`** : Aucune concordance territoriale ou société inactive.

Tout lead en `MATCH_UNCERTAIN` ou `NO_MATCH` est strictement inéligible au statut `VERIFIED`.

---

## 3. Découplage des Scores & Formules de Calcul

### A. LEAD_GEN_SCORE (Sur 100 points — Plafond Effectif 75/100)
Mesure l'adéquation opérationnelle pour l'offre *AI Lead Intelligence* selon 4 piliers :
- **Activité Web pure (max 30 pts)** : 30 pts si création/conception web cœur de métier, 15 pts si secondaire.
- **Taille optimale 2–20 personnes (max 25 pts)** :
  - 25 pts si 3 à 9 pers (tranches `02`, `03`)
  - 20 pts si 10 à 19 pers (tranche `11`)
  - 18 pts si 1-2 pers avec preuve secondaire de 2 personnes (tranche `01` + co-dirigeants greffe)
  - 10 pts si 1-2 pers sans preuve secondaire
  - 0 pt si hors cible (`NN`, `00`, `>20`)
- **Signal d'affaires externe actif (max 25 pts)** : Fait d'actualité, recrutement ou expansion public prouvé avec URL source et date vérifiée. En Phase 1, aucun signal externe n'étant inventé ni recyclé depuis les avis Google, cette composante est à **0 pt** (pénalité de 25 points documentée, score max effectif = **75/100**).
- **Visibilité commerciale & Traction (max 20 pts)** : 20 pts si note $\ge 4.8$ et $\ge 20$ avis Google, 15 pts si note $\ge 4.5$, 10 pts sinon.

### B. GHOSTWRITING_SCORE (Sur 100 points)
- **Statut en phase actuelle** : **Neutralisé à 0/100 (Option B)**.
- **Justification** : Conformément à la règle de vérité absolue, aucun score GW ne peut être attribué sans audit éditorial direct et vérifié des profils LinkedIn publics des dirigeants.

### C. CONFIDENCE_SCORE (Sur 100 points)
Mesure la solidité et l'auditabilité des preuves documentées :
- **Vérification légale & Matching SIRENE (max 35 pts)** : `MATCH_CONFIRMED` actif (35), `MATCH_PLAUSIBLE` (20), `MATCH_UNCERTAIN` (5), `NO_MATCH` (0).
- **Preuve officielle de la taille 2-20 (max 30 pts)** : Tranches `02`, `03`, `11` (30), tranche `01` avec preuve secondaire (25), tranche `01` sans preuve secondaire (10), hors cible (0).
- **Audit technique du site web (max 20 pts)** : Ping HTTP 200 avec SSL HTTPS valide (20), HTTP seul (10), inaccessible (0).
- **Canal de contact direct vérifié (max 15 pts)** : Téléphone professionnel français direct vérifié (15), sinon (0).

---

## 4. Preuves Séparées & Indépendance Offre / Cible
Chaque prospect doit disposer de preuves documentées indépendantes :
- **Offre Principale (`main_offer`)** : Observée directement dans les balises meta/title ou h1 du site officiel avec URL source et extrait textuel vérifié.
- **Clientèle Cible (`target_clients`)** : Déclarée uniquement en présence d'une mention textuelle explicite sur le site (ex: "dédié aux PME"). En l'absence de mention formelle, le champ est obligatoirement positionné à **`Non vérifié`** avec source vide. Aucune inférence à partir du nom ou de l'offre n'est autorisée.

---

## 5. Règles d'Outreach & Vérité Métier
Tout message d'accroche recommandé doit respecter strictement 4 éléments factuels vérifiables :
1. **Ce qui a été observé** (activité réelle, ville).
2. **Où cela a été observé** (site officiel de l'agence).
3. **Pourquoi l'agence a été sélectionnée** (critères ICP d'ancrage local et taille 2-20 du projet Money).
4. **Ce qui est proposé** (échange exploratoire sur notre démarche de prospection ciblée).

Interdiction absolue de toute affirmation d'urgence ("besoin urgent"), d'intention d'achat supposée ("recherche actuellement des prestataires"), de compliment générique non sourcé ("très solide") ou de promesse d'échantillon préparé à l'avance.
