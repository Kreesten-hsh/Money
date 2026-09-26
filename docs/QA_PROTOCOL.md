# Protocole de Contrôle Qualité (QA Protocol) — Money

## 1. Principe de Zéro Tolérance
Aucun livrable client et aucune mise à jour de dataset ne peuvent être validés si les contrôles ci-dessous ne sont pas exécutés et documentés.

## 2. Checklist Obligatoire Pré-Livraison (10 Points de Contrôle)

- [ ] **Contrôle 1 (Intégrité des URLs)** : Chaque site web déclaré a été pingé et répond en code HTTP 200 avec certificat SSL valide.
- [ ] **Contrôle 2 (Preuve Légale)** : L'entreprise est immatriculée au registre du commerce français (SIREN identifié et actif).
- [ ] **Contrôle 3 (Contrôle d'Effectif)** : L'effectif déclaré ne provient JAMAIS d'une déduction basée sur les avis Google, mais d'une tranche INSEE ou d'une preuve nominative.
- [ ] **Contrôle 4 (Non-Redondance)** : Aucun doublon de nom de domaine, de numéro de téléphone ou de SIREN dans le lot.
- [ ] **Contrôle 5 (Séparation des Scores)** : Les colonnes `lead_gen_score`, `ghostwriting_score` et `confidence_score` sont calculées avec leurs formules respectives. Aucun score arbitraire à 100/100 par défaut.
- [ ] **Contrôle 6 (Cohérence Statut vs Confiance)** : Si un prospect a le statut `REQUIRES REVIEW` ou `PARTIALLY VERIFIED`, son `confidence_score` est strictement inférieur à 75/100.
- [ ] **Contrôle 7 (Véracité du Décideur)** : Le nom du dirigeant provient des mentions légales, du greffe ou du site officiel. S'il n'est pas certain, le champ est explicitement marqué `Non identifié`.
- [ ] **Contrôle 8 (Personnalisation du Message)** : Le message proposé cite un fait ou une étude de cas réel et vérifié de l'agence.
- [ ] **Contrôle 9 (Conformité RGPD)** : Aucune donnée privée personnelle n'est présente dans les exports.
- [ ] **Contrôle 10 (Synchronisation Notion / Dataset)** : Le tableau et les fiches affichés dans Notion correspondent exactement aux données des fichiers CSV/JSON sous git.
