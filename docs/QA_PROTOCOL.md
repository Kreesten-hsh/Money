# Protocole de Contrôle Qualité (QA Protocol) — Money

## 1. Principe Fondamental : Preuves Structurées vs Présence de Mots
Le contrôle qualité ne valide plus la simple présence de chaînes de caractères (ex: mots « associé » ou « co-dirigeant » dans les notes). Il vérifie l'existence, la cohérence et l'auditabilité d'objets de preuves structurés et horodatés.

---

## 2. Checklist Obligatoire Pré-Livraison (20 Contrôles Métier)

1. **Contrôle 01 (Intégrité des URLs & HTTPS)** : Chaque site web déclaré possède une URL canonique commençant par `https://` (ou une note explicite d'inaccessibilité).
2. **Contrôle 02 (SIREN & Preuve Légale Structurée)** : Numéro SIREN officiel à 9 chiffres, présence de `siren_source` et URL greffe/INSEE officielle (`annuaire-entreprises.data.gouv.fr/entreprise/{siren}`).
3. **Contrôle 03 (Matching SIRENE Déterministe & Télémétrie)** : Statut reconnu (`MATCH_CONFIRMED`, `MATCH_PLAUSIBLE`, `MATCH_UNCERTAIN`, `NO_MATCH`) avec présence obligatoire des 5 champs télémétriques (`sirene_candidate_selected`, `sirene_candidate_score`, `sirene_second_candidate_score`, `sirene_score_delta`, `sirene_matching_decision_reason`).
4. **Contrôle 04 (Vraie Détection d'Ambiguïté SIRENE)** : Règle de delta concurrentiel : si un 2ème candidat concurrent obtient un score $\ge 55$ avec un delta $< 20$, le statut `MATCH_CONFIRMED` est formellement interdit (maintien obligatoire en `MATCH_UNCERTAIN`). Aucun lead `MATCH_UNCERTAIN` ou `NO_MATCH` ne peut recevoir le statut `VERIFIED`.
5. **Contrôle 05 (ICP Strict 2-20 & Exclusion Non-Employeurs)** : Codes INSEE `NN`, `00` et `>20` obligatoirement `DISQUALIFIED` avec score de confiance forcé à 0.
6. **Contrôle 06 (Preuve Structurée Effectif & Tranche 01)** : `company_size_source` renseigné. Pour tout lead `VERIFIED` en tranche `01`, `has_secondary_size_proof` doit être `True`, avec `secondary_size_proof_source` et `secondary_size_proof_details` certifiant au moins 2 co-dirigeants déclarés au greffe. En l'absence de preuve secondaire, maintien en `REQUIRES REVIEW`.
7. **Contrôle 07 (Preuve Structurée Dirigeant & Rôle Officiel)** : Pour tout `VERIFIED`, nom officiel du dirigeant non vide, rôle officiel exact extrait de `qualite` SIRENE (sans désignation générique), URL source officielle et horodatage ISO dynamique.
8. **Contrôle 08 (Preuves Indépendantes Main Offer)** : Si `main_offer != 'Non vérifié'`, présence obligatoire de `main_offer_source` (URL valide), de `main_offer_evidence` (extrait textuel vérifié) et d'un horodatage ISO.
9. **Contrôle 09 (Preuves Indépendantes Target Clients)** : Si `target_clients != 'Non vérifié'`, présence obligatoire d'une mention textuelle explicite dans `target_clients_evidence` et de son URL source. Si `target_clients == 'Non vérifié'`, la source doit être vide et la preuve doit justifier l'absence de mention explicite.
10. **Contrôle 10 (Temporalité Dynamique & Zéro Date Hardcodée)** : Tous les champs d'horodatage respectent le format ISO 8601 dynamique (`YYYY-MM-DDTHH:MM:SSZ`). Aucune date statique (ex: `"2026-09-27"` seul). Zéro confusion entre date de vérification et date de signal commercial.
11. **Contrôle 11 (Non-Redondance Domaine)** : Unicité stricte du nom de domaine canonique (netloc).
12. **Contrôle 12 (Non-Redondance Téléphone)** : Unicité stricte du numéro professionnel standardisé.
13. **Contrôle 13 (Non-Redondance SIREN)** : Aucun SIREN dupliqué entre entreprises distinctes.
14. **Contrôle 14 (Modèle Score Lead Gen /100 & Max 75)** : Score compris entre 0 et 100, calculé sur les 4 composantes. Faute de signal externe vérifié (`commercial_signal == ''`), la composante signal vaut 0 et le score effectif est plafonné à 75/100 en Phase 1.
15. **Contrôle 15 (Score Ghostwriting Neutralisé)** : Score = 0/100 pour tous les prospects (Option B).
16. **Contrôle 16 (Cohérence Score Confiance & Plafonds)** : Non-VERIFIED plafonné à 60/100, matching incertain/absent plafonné à 40/100, et DISQUALIFIED forcé à 0/100.
17. **Contrôle 17 (Hard Gates du Statut VERIFIED)** : Exige simultanément : `confidence_score >= 80`, `matching_status == 'MATCH_CONFIRMED'`, effectif 2-20 certifié, dirigeant officiel identifié, et site HTTPS en code retour 200.
18. **Contrôle 18 (Traçabilité Justifications Reasons)** : Décomposition chiffrée obligatoire pour Lead Gen, GW et Confidence avec renvoi aux sources.
19. **Contrôle 19 (Véracité Message d'Outreach Notion)** : Interdiction absolue d'affirmations d'urgence ("besoin urgent"), d'intentions d'achat supposées ("recherche actuellement des prestataires"), de compliments génériques non sourcés ("très solide") ou de placeholders corrompus ("Bonjour Non", "Bonjour ,").
20. **Contrôle 20 (Synchronisation Notion / Dataset & Pipeline Réel)** : Concordance exacte entre dataset et rapport Markdown, connexion directe de la shortlist dédupliquée et absence d'anciens artefacts obsolètes.

---

## 3. Banc de Tests Négatifs (17 Fixtures Corrompues)
Le protocole exige l'exécution d'un banc de 17 tests négatifs démontrant que toute altération unitaire des règles provoque immédiatement un échec du contrôle correspondant :
- **SIRENE (3 tests)** : delta ambigu < 20 forcé en `MATCH_CONFIRMED`, score insuffisant forcé en `MATCH_CONFIRMED`, lead `VERIFIED` avec matching incertain.
- **Preuves (5 tests)** : absence de source SIRENE, tranche 01 sans preuve secondaire, dirigeant manquant, offre sans source, cible sans source.
- **Temporalité (2 tests)** : date statique hardcodée, confusion date signal / date vérification.
- **Scoring (3 tests)** : attribution artificielle de points au signal commercial, score hors borne (>100), score GW non neutralisé.
- **Redondance (1 test)** : duplication artificielle de SIREN.
- **Outreach (3 tests)** : formulation de besoin urgent, affirmation d'entreprises recherchant des prestataires, placeholder corrompu ("Bonjour Non,").
