# Politique de Données, Confidentialité & Éthique — Money

## 1. Principes Directeurs
Le projet Money applique le principe de **minimisation absolue des données** et de **respect scrupuleux du RGPD** (Règlement Général sur la Protection des Données) et de la directive ePrivacy.

## 2. Règles Opérationnelles Strictes

### A. Données B2B Professionnelles et Publiques Uniquement
- Seules les données manifestement rendues publiques par les personnes morales ou par les professionnels dans le cadre de leur activité commerciale sont collectées (mentions légales, sites officiels, registres publics du commerce).
- Aucune donnée à caractère privé ou personnel non professionnel (adresses personnelles, téléphones personnels privés, données sensibles) n'est collectée, traitée ou stockée.

### B. Interdiction Formelle du Scraping LinkedIn
- Le scraping des profils personnels LinkedIn est banni de l'architecture.
- L'identification de profils LinkedIn se limite à la consultation humaine de profils publics librement accessibles ou via des moteurs de recherche publics lorsque le dirigeant mentionne son agence publiquement.

### C. Gestion des Incertitudes & Traçabilité des Preuves
- Aucune extrapolation n'est admise : une donnée manquante est déclarée "Incertain" ou "Non identifié".
- Chaque enregistrement conserve son horodatage (`last_checked`), sa source de découverte (`source_url`) et sa preuve de vérification (`evidence_url`).

### D. Droit d'Accès, de Rectification et d'Opposition
- Tout prospect contacté qui exprime son désintérêt ou son souhait de ne plus être sollicité est immédiatement retiré de la file de prospection et placé dans une liste de suppression définitive (Opt-out strict).

## 3. Sécurité & Stockage des Données
- Les données brutes et requalifiées sont hébergées sur le poste de travail local sous contrôle de version git.
- Aucun transfert de bases de données massives vers des tiers non autorisés.
