# Product Requirements Document (PRD) — Money B2B Engine

## 1. Problème Métier & Opportunité
Les agences web et studios digitaux de taille modeste (2 à 20 collaborateurs) subissent deux contraintes critiques dans leur développement commercial :
1. **Volatilité du flux d'affaires (Pipeline B2B)** : Dépendance excessive au bouche-à-oreille et à la recommandation passive, provoquant des périodes d'inactivité commerciale. Les prestataires traditionnels de leadgen fournissent des listes de contacts brutes, non qualifiées et non contextualisées, générant un faible taux de conversion et du spam.
2. **Déficit d'incarnation et d'autorité sur LinkedIn** : Les fondateurs et dirigeants d'agences détiennent une expertise technique et stratégique réelle mais manquent de temps pour structurer une présence éditoriale régulière, percutante et alignée sur leur voix authentique.

## 2. Utilisateurs Cibles & Bénéficiaires
- **Client Final Pilote** : Fondateur, Co-fondateur, Directeur Général ou Directeur Commercial d'une agence web / digitale française (2 à 20 personnes).
- **Opérateur Interne (Money Team)** : Analyste commercial assisté d'agents IA, garantissant la vérité des données et la pertinence du contexte avant transmission au client.

## 3. Offres Produits

### Offre A : AI Lead Intelligence (Offre Prioritaire)
Fourniture d'opportunités d'affaires hautement contextualisées, vérifiées par sources étatiques/officielles et enrichies de signaux faibles exploitables immédiatement.
- **Livrable** : Espace client dédié ("Lead Intelligence Room" Notion) répondant pour chaque compte à 6 questions : *Who? Why? Why Now? Who to Contact? What to Say? Proof?*.
- **Packs** :
  - *Pilote découverte* : 149 € HT (30 leads B2B vérifiés & contextualisés).
  - *Pilote Plus* : 249 € HT (50 leads B2B + signaux d'affaires + personnalisation d'accroches + restitution).
  - *Abonnement récurrent* : 390 € HT/mois (flux continu de 60 à 80 comptes qualifiés).

### Offre B : Founder LinkedIn Ghostwriting (Offre Secondaire)
Transformation de la matière brute du dirigeant (retours d'expérience, prises de position, réalisations clients) en publications LinkedIn à haute valeur d'autorité, sans inventer d'anecdotes ni faire de promesses métriques creuses.
- **Packs** :
  - *Pilote mensuel* : 249 € HT (4 posts prêts à publier, calibrés sur la voix du fondateur).
  - *Abonnement régulier* : 390 € HT/mois (8 posts / mois + calendrier éditorial).

## 4. Valeur Proposée & Différenciation
- **Zéro liste aveugle** : Aucune donnée non vérifiée ou purement déduite. Preuves sourcées obligatoires (INSEE, sites officiels, mentions légales).
- **Prêt à l'emploi** : Message d'approche sur-mesure pour chaque prospect, basé sur un fait vérifiable (recrutement, refonte, stack technique, engagement RSE).
- **Approche Synergique** : Utilisation de notre propre méthodologie de recherche pour acquérir nos propres clients agences.

## 5. Objectifs & Périmètre

### Objectifs Chiffrés
- **Financier** : Encaisser un minimum de 1 000 000 FCFA (soit environ 1 525 €) avant le 31 décembre 2026.
- **Opérationnel** : Vendre et exécuter 2 à 3 pilotes payants validant l'adéquation problème-solution.

### Dans le Périmètre (In Scope)
- Sourcing assisté par scraper local (Google Maps Scraper Docker).
- Requalification stricte via les registres publics français (INSEE, Annuaire des Entreprises, Pappers) et scraping profond légal (Firecrawl / Scrapling).
- Calcul déterministe de 3 scores distincts : `lead_gen_score`, `ghostwriting_score`, `confidence_score`.
- Espace de livraison client Notion standardisé et sobre.
- Prospection manuelle chirurgicale (5 contacts/jour max).

### Hors Périmètre (Out of Scope)
- Scraping de profils personnels LinkedIn (strictement interdit).
- Envoi d'emails en masse automatisé (Cold emailing spammy banni).
- Développement d'un logiciel SaaS complexe ou infrastructure Kubernetes.
- Achat de proxies résidentiels payants en phase MVP.
- Automatisation intégrale du closing commercial.

## 6. Critères de Succès & Portes de Validation
1. **Validation Données** : 100% des entreprises qualifiées disposent d'un statut légal vérifiable et d'une taille confirmée par une source institutionnelle ou déclarative officielle.
2. **Validation Commerciale Phase 1** : 1 premier pilote payé à 149 € HT ou 249 € HT encaissé.
3. **Validation Commerciale Phase 2** : 1 second pilote payé avec un taux de satisfaction permettant un renouvellement ou un passage en abonnement.

## 7. Risques & Mitigations
- **Risque de rejet de la prospection** : Atténué par le principe d'échantillon gracieux de démonstration (3 comptes cibles audités avant toute demande de paiement).
- **Risque d'hallucination / faux positifs de l'IA** : Éliminé par la règle d'or : Preuves > Hypothèses. Aucune donnée non sourcée n'est acceptée.
- **Risque de dispersion technique** : Verrouillage sur le canal Notion et tableurs structurés tant que 1M FCFA n'est pas sécurisé.
