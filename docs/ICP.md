# Ideal Customer Profile (ICP) — Segment Test Initial (Money)

## 1. Description du Segment
Le segment test initial porte exclusivement sur les **agences web et digitales françaises indépendantes** de taille intermédiaire (TPE/PME de 2 à 20 collaborateurs).

## 2. Critères d'Éligibilité Obligatoires (Hard Filters)
Une entreprise ne peut obtenir le statut **VERIFIED** que si TOUS les critères suivants sont satisfaits avec des preuves traçables :

1. **Territoire & Juridiction** : Siège social ou établissement principal en France métropolitaine, immatriculé au RCS (SIREN actif et vérifié au registre public).
2. **Activité Principale Réelle** : Prestation de services web B2B (création de sites vitrines/e-commerce, développement sur-mesure, refonte, référencement naturel SEO, maintenance web, branding digital) avec code NAF concordant.
3. **Taille d'Équipe Vérifiable (STRICTEMENT 2 à 20 personnes)** :
   - **Tranches INSEE admises d'office** :
     - Code `02` : 3 à 5 salariés
     - Code `03` : 6 à 9 salariés
     - Code `11` : 10 à 19 salariés
   - **Tranche INSEE `01` (1 ou 2 salariés)** :
     - La tranche `01` ne prouve pas à elle seule la présence d'au moins 2 salariés.
     - Elle n'est admissible au statut `VERIFIED` **que si une preuve secondaire publique** établit clairement la présence d'au moins 2 personnes (ex: plusieurs co-dirigeants/associés enregistrés au RCS, organigramme nominatif public).
     - En l'absence de preuve secondaire formelle, le lead demeure obligatoirement au statut `REQUIRES REVIEW`.
   - **Interdiction formelle** : Ne jamais déduire la taille d'une agence à partir du nombre d'avis Google ou de la note moyenne.
4. **Site Web Opérationnel** : Nom de domaine propre actif, sécurisé (HTTPS avec code HTTP 200), présentant une offre vérifiable.
5. **Rapprochement Légal Non Ambigu** : Le matching SIRENE doit impérativement avoir le statut `MATCH_CONFIRMED`.

## 3. Critères d'Exclusion Stricts (Disqualification Immédiate)
Sont immédiatement classés au statut **DISQUALIFIED** (avec score de confiance forcé à 0) :
- Les structures non-employeurs / 0 salarié (codes INSEE `NN` ou `00`).
- Les structures dépassant 20 salariés (codes INSEE `12` [20-49], `21` [50-99], `22`, etc.).
- Les entités inactives, radiées ou en liquidation (`etat_administratif != 'A'`).
- Les entreprises dont le site web renvoie une erreur persistante ou un contenu parking.
- Les correspondances erronées ou homonymes d'autres secteurs (activités artistiques, restauration, BTP).

## 4. Signaux d'Affaires Porteurs (Triggers)
Pour qualifier un signal commercial réel (`commercial_signal`), un fait public et daté doit être observé (recrutement actif, expansion, nouvelle implantation, refonte récente avec cas client). En l'absence d'événement documenté, le signal reste neutre/vide.

## 5. Méthode de Validation sur le Terrain
L'ICP n'est pas un dogme figé. Il sera considéré comme validé uniquement lorsqu'au moins 2 agences de cette typologie auront accepté et payé un pilote.
