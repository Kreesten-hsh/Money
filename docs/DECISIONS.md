# Registre des Décisions Stratégiques & Techniques (ADR) — Money

Toute orientation technique ou commerciale significative est consignée ici avec son statut : `NOW`, `NEXT`, `LATER`, `REJECTED`.

---

## [ADR-001] Découplage strict des scores et élimination du 100/100 par défaut
- **Date** : 2026-09-26
- **Statut** : **NOW**
- **Contexte** : L'ancien script attribuait `fit_score: 100` et `confidence_score: 100` à des entreprises pourtant marquées "À vérifier".
- **Décision** : Création de 3 scores indépendants (`lead_gen_score`, `ghostwriting_score`, `confidence_score`) calculés selon des formules mathématiques explicites documentées dans `/docs/LEAD_QUALIFICATION_SPEC.md`. Plafond de confiance à 60 si des données clés manquent.

---

## [ADR-002] Interdiction de déduire la taille d'une agence depuis les avis Google
- **Date** : 2026-09-26
- **Statut** : **NOW**
- **Contexte** : Une corrélation abusive existait entre nombre d'avis clients et effectif salarié.
- **Décision** : Seules les tranches d'effectifs déclarées aux registres d'État (INSEE / Annuaire Entreprises / Greffe) ou les organigrammes officiels font foi. Les avis Google ne mesurent que la satisfaction client et la présence commerciale.

---

## [ADR-003] Interdiction formelle du scraping LinkedIn et du spam d'emails
- **Date** : 2026-09-26
- **Statut** : **NOW**
- **Contexte** : Tentation fréquente d'automatiser massivement le démarchage avec des outils tiers.
- **Décision** : Respect strict du RGPD et des CGU des plateformes. Démarchage exclusivement manuel, personnalisé, apportant de la valeur démontrée avant toute demande commerciale (3 à 5 contacts ciblés par jour maximum).

---

## [ADR-004] Intégration de l'API publique Recherche d'Entreprises (Gouv.fr)
- **Date** : 2026-09-26
- **Statut** : **NOW**
- **Contexte** : Besoin d'une source gratuite et institutionnelle de vérification pour les entreprises françaises.
- **Décision** : Utiliser l'API publique ouverte de l'État français (`https://recherche-entreprises.api.gouv.fr/search`) pour valider le SIREN, le statut juridique actif, le code NAF et la tranche d'effectif officiel.

---

## [ADR-005] Développement d'un SaaS ou portail applicatif personnalisé
- **Date** : 2026-09-26
- **Statut** : **REJECTED** (pour le stade MVP)
- **Contexte** : Idée d'automatiser une plateforme web pour les clients.
- **Décision** : Rejeté tant que 1M FCFA n'a pas été encaissé. Notion et les formats CSV/JSON couvrent 100% des besoins sans coût d'infrastructure ni maintenance logicielle.

---

## [ADR-006] Offre combinée (Bundle Lead Intelligence + Ghostwriting)
- **Date** : 2026-09-26
- **Statut** : **LATER**
- **Contexte** : Vendre les deux prestations simultanément dès le premier contact.
- **Décision** : Reporté après la vente des deux premiers pilotes purs Lead Intelligence afin de ne pas brouiller le message commercial d'entrée.

---

## [ADR-007] Purge de l'historique Git des données brutes Google Maps (Conformité RGPD stricte)
- **Date** : 2026-09-27
- **Statut** : **NOW**
- **Contexte** : Le commit initial exposait dans l'historique public du dépôt des données personnelles non anonymisées issues de Google Maps (noms des commentateurs, photos, avis individuels sous `data/gmaps_agences_web_raw.csv`).
- **Décision** : Réécriture complète de l'historique git à l'aide de `git-filter-repo` pour exclure définitivement ce fichier et ses deltas passés. Réintroduction d'un fichier nettoyé contenant exclusivement des colonnes RGPD-safe (données d'entreprise publiques uniquement : titre, catégorie, adresse, ville, site, téléphone professionnel, volume et note globale d'avis, url Maps). Force-push sur `origin/main` et contrôle d'invalidation des anciens hashes.

