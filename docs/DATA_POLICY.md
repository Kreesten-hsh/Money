# Politique de Données, Confidentialité & Éthique — Money

## 1. Principes Directeurs
Le projet Money applique le principe de **minimisation absolue des données** et de **respect scrupuleux du RGPD** (Règlement Général sur la Protection des Données) et de la directive ePrivacy.

## 2. Règles Opérationnelles Strictes

### A. Données B2B Professionnelles et Publiques Uniquement
- Seules les données manifestement rendues publiques par les personnes morales ou par les professionnels dans le cadre de leur activité commerciale sont collectées (mentions légales, sites officiels, registres publics du commerce).
- Aucune donnée à caractère privé ou personnel non professionnel (adresses personnelles, téléphones personnels privés, données sensibles) n'est collectée, traitée ou stockée.

### B. Encadrement Strict de la Consultation LinkedIn (Conformité ADR-008 & RGPD)
- Le scraping de masse et l'aspiration automatisée de listes de contacts LinkedIn sont formellement bannis de l'architecture.
- L'utilisation d'outils d'assistance furtifs (`invisible_playwright_mcp`) est strictement restreinte à la consultation passive en lecture seule des pages d'entreprises et des profils publics de dirigeants préalablement identifiés au registre légal SIRENE.
- Aucune connexion de compte personnel LinkedIn n'est autorisée (session publique déconnectée ou environnement isolé).
- Le débit est strictement plafonné à 5 profils uniques audités par jour.
- Zéro stockage de données privées (relations, historique, coordonnées personnelles privées) : seuls l'existence d'une activité éditoriale publique et le lien du profil sont vérifiés.
- L'interdiction du cold-emailing massif et de l'envoi de messages automatisés (bots de connexion/inmail) demeure absolue et intégrale. L'approche reste 100% manuelle.

### C. Gestion des Incertitudes & Traçabilité des Preuves
- Aucune extrapolation n'est admise : une donnée manquante est déclarée "Incertain" ou "Non identifié".
- Chaque enregistrement conserve son horodatage (`last_checked`), sa source de découverte (`source_url`) et sa preuve de vérification (`evidence_url`).

### D. Droit d'Accès, de Rectification et d'Opposition
- Tout prospect contacté qui exprime son désintérêt ou son souhait de ne plus être sollicité est immédiatement retiré de la file de prospection et placé dans une liste de suppression définitive (Opt-out strict).

## 3. Sécurité & Stockage des Données
- Les données brutes et requalifiées sont hébergées sur le poste de travail local sous contrôle de version git.
- Aucun transfert de bases de données massives vers des tiers non autorisés.
