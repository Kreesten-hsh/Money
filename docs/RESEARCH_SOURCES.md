# Sources de Recherche & Hiérarchie de Vérité — Money

## 1. Hiérarchie Officielle des Preuves
Lorsqu'une information relative à une entreprise est consignée, sa validité est soumise à la hiérarchie stricte suivante :

### Niveau 1 : Sources Officielles Primaires de l'Entreprise
- Site web officiel sous nom de domaine vérifié (`https://...`).
- Page Mentions Légales, CGV, Politique de Confidentialité.
- Communiqués de presse officiels ou page équipe interne.

### Niveau 2 : Registres Institutionnels & Données Publiques de l'État
- **Base SIRENE / INSEE** : Identification du numéro SIREN, code NAF (ex: 6201Z, 6202A, 7311Z), date de création, statut administratif actif.
- **API Recherche d'Entreprises (recherche-entreprises.api.gouv.fr)** : Tranche d'effectif salarié déclarée, dirigeants statutaires enregistrés.
- **BODACC (Bulletin officiel des annonces civiles et commerciales)** : Annonces légales de nomination, modifications de capital.

### Niveau 3 : Sources Professionnelles Secondaires Reconnues
- Fiches Pappers, Société.com, Verif.com (retranscription certifiée des données du greffe).
- Annuaires spécialisés de la profession digitale (BPI France, annuaires régionaux French Tech).

### Niveau 4 : Sources de Découverte & Signaux Faibles
- **Skill `google-maps-scraper`** : Extraction géolocalisée locale (Docker) via Google Business Profile (Note client, volume d'avis, adresse, téléphone standard).
- **Skill `agent-reach`** : Router d'investigation multi-plateformes (Twitter, Reddit, YouTube, GitHub, web ouvert) à 0 € d'API pour capter les tendances du secteur, mentions publiques et actualités.
- Moteurs de recherche publics (Google, DuckDuckGo, Bing).
- Réseaux sociaux professionnels ouverts (pages d'entreprises publiques uniquement, hors scraping de profils privés).

*Règle d'or : Une source de niveau 4 ne peut en aucun cas se substituer ou prévaloir sur une source de niveau 1 ou 2 pour établir l'effectif ou le statut légal d'une entreprise.*
