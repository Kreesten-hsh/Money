# Spécification de Qualification & Système de Scoring — Money

## 1. Cycle de Vie d'un Lead (Statuts Unifiés)
Chaque prospect progresse à travers 4 statuts immuables :

1. **CANDIDATE** : Entité brute détectée lors d'un crawl (ex: fiche Google Maps brute). Aucune vérification administrative ni éditoriale effectuée.
2. **REQUIRES REVIEW** : Entité ayant franchi un premier filtre d'éligibilité sommaire, mais présentant des lacunes critiques de données (ex: effectif incertain, dirigeant non identifié, site nécessitant un examen manuel).
3. **PARTIALLY VERIFIED** : Entité existante, immatriculée au RCS et activité web validée, mais pour laquelle le signal d'affaires ou le contact nominatif précis reste à consolider.
4. **VERIFIED** : Entité dont l'immatriculation légale, la tranche d'effectif (2-20), le site web, l'offre B2B et le dirigeant/associé public sont documentés avec preuves et URLs sources.
5. **DISQUALIFIED** : Entité ne respectant pas l'ICP (freelance seul, effectif > 20, boîte fermée, fausse agence, etc.).

## 2. Découplage des Scores & Formules de Calcul

Pour éliminer l'anti-pattern des scores uniques artificiels à 100/100, le système calcule obligatoirement trois dimensions distinctes :

### A. LEAD_GEN_SCORE (Sur 100 points)
Mesure l'appétence et le potentiel du compte pour acheter l'offre *AI Lead Intelligence* :
- **Activité Web pure (30 pts)** : Conception de sites vitrines/e-commerce, refonte, Webflow/WordPress (30 pts si cœur de métier, 15 pts si secondaire).
- **Taille optimale 2–15 pers (25 pts)** : Structure idéale avec besoin urgent de pipeline (25 pts si 2-10 pers, 15 pts si 11-20 pers, 0 sinon).
- **Signal d'affaires actif (25 pts)** : Recrutement en cours, expansion géographique, actualité récente (25 pts si vérifié avec URL, 10 pts si signal modéré, 0 si aucun).
- **Visibilité commerciale & Traction (20 pts)** : Preuve sociale existante et clientèle active (15 avis Google = 10 pts, >30 avis = 20 pts).

### B. GHOSTWRITING_SCORE (Sur 100 points)
Mesure l'appétence du fondateur pour l'offre *Founder LinkedIn Ghostwriting* :
- **Présence & Identité publique du dirigeant (30 pts)** : Fondateur / Associé clairement nommé sur le site (mentions légales, page équipe) avec profil LinkedIn public existant (30 pts si profil identifiable, 10 pts si nom seul sans URL).
- **Positionnement éditorialisant fort (30 pts)** : Thématique d'expertise différenciante (Éco-conception, IA, UX complexe, NoCode) offrant de la matière riche (30 pts si angle saillant, 15 pts si agence généraliste).
- **Déficit d'activité / Friction observable (20 pts)** : Manque de régularité manifeste dans les prises de parole ou absence de contenu récent malgré des cas clients de premier plan (20 pts).
- **Matière disponible (20 pts)** : Portfolio riche, études de cas détaillées sur le site exploitables pour la rédaction (20 pts si études de cas publiques chiffrées, 10 pts si réalisations basiques).

### C. CONFIDENCE_SCORE (Sur 100 points)
Mesure la solidité et l'auditabilité des preuves documentées :
- **Vérification légale d'identité & statut RCS (35 pts)** : SIREN / SIRET identifié et actif dans les registres officiels (INSEE / Annuaire Entreprises / Pappers).
- **Preuve institutionnelle ou officielle de la taille (30 pts)** : Tranche d'effectif issue de l'INSEE ou organigramme officiel documenté (30 pts si INSEE/RCS, 15 pts si organigramme site seul, 0 pt si simple déduction).
- **Audit technique du site & offre (20 pts)** : Site exploré et analysé via Firecrawl ou extraction DOM avec métadonnées valides.
- **Canal de contact direct vérifié (15 pts)** : Numéro de téléphone direct ou email professionnel nominatif vérifié fonctionnel.

## 3. Règles d'Attribution
- Aucun lead ne peut recevoir un score sans justification explicite dans ses champs `reasons` et `evidence_url`.
- Si un champ critique (ex: effectif réel) est absent ou purement présumé, le `confidence_score` est plafonné à **60/100 maximum**.
- Le statut `VERIFIED` exige un `confidence_score` $\ge 75/100$.
