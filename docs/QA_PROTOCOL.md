# Protocole de Contrôle Qualité (QA Protocol) — Money

## 1. Principe de Zéro Tolérance (Vérité Métier vs Existence Technique)
Aucun livrable client et aucune mise à jour de dataset ne peuvent être validés si les 20 contrôles métier ci-dessous ne sont pas exécutés et validés par le script automatisé `qa_check.py`.

---

## 2. Checklist Obligatoire Pré-Livraison (20 Points de Contrôle)

1. **Contrôle 1 (Intégrité des URLs)** : Chaque site web déclaré possède une URL canonique valide commençant par `https://`.
2. **Contrôle 2 (Preuve Légale)** : L'entreprise possède un SIREN officiel à 9 chiffres pour tout statut vérifié et une URL source greffe/INSEE.
3. **Contrôle 3 (Matching SIRENE Non Ambigu)** : Le statut de rapprochement est tracé (`MATCH_CONFIRMED`, `MATCH_PLAUSIBLE`, `MATCH_UNCERTAIN`, `NO_MATCH`). Aucun `MATCH_UNCERTAIN` ou `NO_MATCH` ne peut recevoir le statut `VERIFIED`.
4. **Contrôle 4 (ICP Strict 2-20)** :
   - Tranches INSEE `02` (3-5), `03` (6-9), `11` (10-19) admises.
   - Tranche `01` (1-2) admise en `VERIFIED` UNIQUEMENT si une preuve secondaire nominative prouve au moins 2 personnes. Sans preuve, statut `REQUIRES REVIEW`.
   - Tranches `NN`, `00` (0 salarié) et `>20` obligatoirement `DISQUALIFIED` avec score de confiance à 0.
5. **Contrôle 5 (Non-Redondance Domaine)** : Aucun doublon de nom de domaine dans le lot qualifié.
6. **Contrôle 6 (Non-Redondance Téléphone)** : Aucun doublon de numéro de téléphone professionnel.
7. **Contrôle 7 (Non-Redondance SIREN)** : Aucun SIREN réutilisé pour deux fiches distinctes.
8. **Contrôle 8 (Cohérence Score Lead Gen)** : Le score est borné [0, 100], sans attribution arbitraire à 100 par défaut.
9. **Contrôle 9 (Cohérence Score Ghostwriting)** : Score neutralisé à 0/100 (Option B) tant qu'aucun audit éditorial LinkedIn public vérifié n'a été réalisé.
10. **Contrôle 10 (Cohérence Score Confiance)** : Score borné [0, 100], calculé fidèlement selon les 4 composantes de preuves.
11. **Contrôle 11 (Application des Plafonds de Confiance)** :
    - Si statut $\neq$ `VERIFIED`, le score de confiance est strictement plafonné à 60/100.
    - Si `matching_status` est `MATCH_UNCERTAIN` ou `NO_MATCH`, le score de confiance est strictement plafonné à 40/100.
12. **Contrôle 12 (Hard Gates du Statut VERIFIED)** : Un lead `VERIFIED` possède impérativement : `confidence_score >= 80`, `MATCH_CONFIRMED`, tranche d'effectif 2-20 certifiée, dirigeant identifié au registre, et site HTTPS accessible.
13. **Contrôle 13 (Présence et Traçabilité des Reasons)** : Le champ `reasons` contient une liste non vide de justifications factuelles reliant chaque note à sa source.
14. **Contrôle 14 (Zéro Faux Signal Google Reviews)** : Le champ `commercial_signal` ne recycle jamais la note ou le volume d'avis Google Maps.
15. **Contrôle 15 (Intégrité des Signaux Commerciaux)** : `signal_date` est obligatoirement vide si aucun `commercial_signal` et aucune `signal_source` ne sont vérifiés.
16. **Contrôle 16 (Spécificité Offre & Cible)** : `main_offer` et `target_clients` ne sont pas remplis par une formule générique dupliquée sans observation réelle (si non observé, explicitement marqué `Non vérifié`).
17. **Contrôle 17 (Véracité du Message d'Outreach)** : Les messages d'approche ne contiennent aucune affirmation non prouvée ("besoin urgent", "positionnement très solide", "échantillon préparé") et aucun placeholder corrompu ("Bonjour Non", "Bonjour ,").
18. **Contrôle 18 (Synchronisation Dataset / Markdown)** : Les effectifs, scores, statuts et dirigeants de `data/lead_intelligence_room.md` correspondent exactement aux enregistrements CSV et JSON.
19. **Contrôle 19 (Connexion Réelle du Pipeline)** : `requalify_leads.py` consomme directement la sortie de `dedupe_and_shortlist.py` (`data/gmaps_agences_web_shortlist.csv`).
20. **Contrôle 20 (Zéro Dépendance Obsolète)** : Aucune référence silencieuse à d'anciens fichiers temporaires (`top30_leads_qualified.json`).
