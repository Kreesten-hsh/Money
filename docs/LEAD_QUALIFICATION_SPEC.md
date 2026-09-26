# Spécification de Qualification & Système de Scoring — Money

## 1. Cycle de Vie d'un Lead (Statuts Unifiés)
Chaque prospect progresse à travers 5 statuts stricts :

1. **CANDIDATE** : Entité brute issue du sourcing Google Maps. Aucune vérification administrative ni technique effectuée.
2. **REQUIRES REVIEW** : Entité présentant une incertitude critique (ex: tranche `01` sans preuve secondaire d'une 2ème personne, matching incertain, dirigeant non identifié). `confidence_score` plafonné à **60/100** (et **40/100** si matching incertain).
3. **PARTIALLY VERIFIED** : Entité légalement identifiée (`MATCH_CONFIRMED` ou `MATCH_PLAUSIBLE`) avec site accessible, mais données incomplètes ou contact direct manquant. `confidence_score` plafonné à **60/100**.
4. **VERIFIED** : Entité dont l'immatriculation légale (`MATCH_CONFIRMED`), la taille (2 à 20 personnes strictement), le dirigeant officiel (`qualite` au RCS) et le site HTTPS 200 sont vérifiés avec preuves traçables. `confidence_score` $\ge$ **80/100**.
5. **DISQUALIFIED** : Entité hors ICP (0 salarié `NN`/`00`, effectif > 20, boîte fermée, fausse agence). `confidence_score` forcé à **0/100**.

---

## 2. Découplage des Scores & Formules de Calcul

### A. LEAD_GEN_SCORE (Sur 100 points)
Mesure l'adéquation opérationnelle pour l'offre *AI Lead Intelligence* :
- **Activité Web pure (max 30 pts)** : 30 pts si création/conception web cœur de métier, 15 pts si secondaire.
- **Taille optimale 2–20 personnes (max 25 pts)** :
  - 25 pts si 3 à 9 pers (tranches `02`, `03`)
  - 20 pts si 10 à 19 pers (tranche `11`)
  - 18 pts si 1-2 pers avec preuve secondaire de 2 personnes (tranche `01` + co-dirigeants)
  - 10 pts si 1-2 pers sans preuve secondaire
  - 0 pt si hors cible (`NN`, `00`, `>20`)
- **Signal d'affaires actif (max 25 pts)** : 25 pts si fait d'actualité/recrutement public prouvé avec URL source. 0 pt si non vérifié. (Interdiction de recycler les avis Google).
- **Visibilité commerciale & Traction (max 20 pts)** : 20 pts si note $\ge 4.8$ et $\ge 20$ avis Google, 15 pts si note $\ge 4.5$, 10 pts sinon.

### B. GHOSTWRITING_SCORE (Sur 100 points)
- **Statut en phase actuelle** : **Neutralisé à 0/100 (Option B)**.
- **Justification** : Conformément à la règle de vérité absolue, aucun score GW ne peut être attribué sans audit éditorial direct et vérifié des profils LinkedIn publics des dirigeants.
- La priorisation commerciale repose exclusivement sur `lead_gen_score` et `confidence_score`.

### C. CONFIDENCE_SCORE (Sur 100 points)
Mesure la solidité et l'auditabilité des preuves documentées :
- **Vérification légale & Matching SIRENE (max 35 pts)** :
  - `MATCH_CONFIRMED` + actif : 35 pts
  - `MATCH_PLAUSIBLE` : 20 pts
  - `MATCH_UNCERTAIN` : 5 pts
  - `NO_MATCH` : 0 pt
- **Preuve officielle de la taille 2-20 (max 30 pts)** :
  - Tranches `02`, `03`, `11` (3 à 19 salariés certifiés INSEE) : 30 pts
  - Tranche `01` avec preuve secondaire de 2 personnes : 25 pts
  - Tranche `01` sans preuve secondaire : 15 pts
  - Hors cible (`NN`, `00`, `>20`) : 0 pt
- **Audit technique du site web (max 20 pts)** : 20 pts si ping HTTP 200 avec SSL HTTPS valide et contenu exploitable. 0 pt si inaccessible ou non sécurisé.
- **Canal de contact direct vérifié (max 15 pts)** : 15 pts si téléphone professionnel français direct vérifié. 0 pt sinon.

---

## 3. Règles d'Attribution & Plafonds Non-Négociables
1. Tout lead ayant un matching `MATCH_UNCERTAIN` ou `NO_MATCH` ne peut JAMAIS recevoir le statut `VERIFIED`. Son score de confiance est plafonné à **40/100 maximum**.
2. Tout lead au statut `REQUIRES REVIEW` ou `PARTIALLY VERIFIED` a son `confidence_score` plafonné à **60/100 maximum**.
3. Le statut `VERIFIED` exige **strictement** :
   - `confidence_score >= 80`
   - `matching_status == 'MATCH_CONFIRMED'`
   - Tranche validée 2-20 salariés
   - Dirigeant légal identifié au registre
   - Site web HTTPS en code retour 200
