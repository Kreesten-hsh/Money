# Schéma de Données Officiel — Lead Intelligence Schema

## 1. Dictionnaire des Données

Chaque enregistrement du dataset de prospection doit respecter strictement les attributs suivants :

| Attribut | Type | Requis | Description & Règles de Valeur |
|---|---|---|---|
| `company_name` | string | OUI | Raison sociale officielle (issue du RCS/SIRENE) ou nom d'usage |
| `brand_name` | string | OUI | Nom commercial de marque tel qu'observé sur le marché |
| `siren` | string (9 chiffres) | OUI | Numéro SIREN issu du registre public (ou `Non trouvé`) |
| `siren_source` | string | OUI | Source officielle d'immatriculation (ex: `API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE`) |
| `siren_checked_at` | string (ISO 8601) | OUI | Horodatage dynamique UTC de l'interrogation du registre |
| `website` | string (URL) | OUI | URL canonique du site web de l'agence (ex: `https://example.com/`) |
| `country` | string | OUI | Code pays ou libellé (défaut : `France`) |
| `city` | string | OUI | Ville d'établissement principal |
| `company_size` | string | OUI | Libellé officiel de la tranche d'effectif INSEE (ou `Incertain`) |
| `company_size_code` | string | OUI | Code officiel INSEE de la tranche (ex: `01`, `02`, `03`, `11`, `NN`) |
| `company_size_source` | string | OUI | Source de vérification de l'effectif (ex: `INSEE / Registre SIRENE (Tranche 03)`) |
| `company_size_interpretation` | string | OUI | Analyse métier de la tranche d'effectif et éligibilité ICP |
| `company_size_checked_at` | string (ISO 8601) | OUI | Horodatage dynamique UTC de l'observation d'effectif |
| `has_secondary_size_proof` | boolean | OUI | `True` si une preuve secondaire atteste d'au moins 2 personnes (co-dirigeants greffe pour tranche 01), sinon `False` |
| `secondary_size_proof_source` | string (URL) | NON | Source de la preuve secondaire d'effectif (ex: RCS Greffe via Annuaire des Entreprises) |
| `secondary_size_proof_details` | string | NON | Détails des co-dirigeants certifiés prouvant >= 2 personnes en activité |
| `main_offer` | string | OUI | Prestation principale observée sur le site (ou `Non vérifié`) |
| `main_offer_source` | string (URL) | NON | URL de la page ayant permis d'observer l'offre principale |
| `main_offer_evidence` | string | OUI | Extrait textuel exact ou balise HTML prouvant l'offre observée |
| `main_offer_checked_at` | string (ISO 8601) | OUI | Horodatage dynamique UTC de l'audit de l'offre |
| `target_clients` | string | OUI | Typologie de clientèle explicitement déclarée sur le site (ou `Non vérifié`) |
| `target_clients_source` | string (URL) | NON | URL de la page où la cible est expressément mentionnée (vide si non vérifié) |
| `target_clients_evidence` | string | OUI | Extrait textuel exact prouvant la cible observée (interdiction d'inférence) |
| `target_clients_checked_at` | string (ISO 8601) | OUI | Horodatage dynamique UTC de l'audit de la cible |
| `decision_maker` | string | OUI | Nom complet du dirigeant officiel ou dénomination de la personne morale présidente |
| `decision_maker_role` | string | OUI | Rôle officiel exact extrait de l'attribut `qualite` SIRENE (ex: `Gérant`, `Président de SAS`, `Directeur Général`) |
| `decision_maker_is_person` | boolean | OUI | `True` si le décisionnaire retenu est une personne physique, `False` si personne morale ou non identifié |
| `decision_maker_source` | string (URL) | NON | URL officielle prouvant l'identité légale (Annuaire des Entreprises) |
| `decision_maker_checked_at` | string (ISO 8601) | OUI | Horodatage dynamique UTC de l'extraction du dirigeant |
| `public_professional_email` | string | NON | Email professionnel public (ex: `Non extrait (Option)`) |
| `public_phone` | string | NON | Numéro de téléphone direct vérifié |
| `source_url` | string (URL) | OUI | Fiche de sourcing primaire (URL Google Maps) |
| `evidence_url` | string (URL) | OUI | URL de preuve légale officielle (Annuaire des Entreprises) |
| `matching_status` | enum | OUI | Rapprochement SIRENE : `MATCH_CONFIRMED`, `MATCH_PLAUSIBLE`, `MATCH_UNCERTAIN`, `NO_MATCH` |
| `sirene_candidate_selected` | string | OUI | Raison sociale et SIREN du candidat retenu |
| `sirene_candidate_score` | integer (0-100) | OUI | Score calculé pour le candidat retenu |
| `sirene_second_candidate_score` | integer (0-100) | OUI | Score du 2ème candidat concurrent le plus proche |
| `sirene_score_delta` | integer | OUI | Écart de score entre le 1er et le 2ème candidat (seuil de non-ambiguïté >= 20) |
| `sirene_matching_concordant_criteria` | list / string | OUI | Liste des critères concordants (Nom, CP strict, Voie, NAF) |
| `sirene_matching_contradictory_criteria` | list / string | OUI | Liste des critères divergents ou alertes de concurrence |
| `sirene_matching_decision_reason` | string | OUI | Motivation explicite et déterministe de la décision de matching |
| `commercial_signal` | string | NON | Fait d'actualité ou opportunité externe réelle (vide si non vérifié) |
| `signal_source` | string (URL) | NON | URL prouvant la réalité du signal commercial |
| `signal_date` | string (YYYY-MM-DD) | NON | Date d'observation vérifiée du signal commercial |
| `lead_gen_score` | integer (0-100) | OUI | Score Lead Gen (modèle 4 piliers, plafond effectif à 75/100 en Phase 1) |
| `ghostwriting_score` | integer (0-100) | OUI | Score Founder Ghostwriting (neutralisé à 0/100 en Phase 1) |
| `confidence_score` | integer (0-100) | OUI | Indice de solidité des preuves (Plafond 60 si non-VERIFIED, 40 si matching incertain) |
| `verification_status` | enum | OUI | Statut : `CANDIDATE`, `REQUIRES REVIEW`, `PARTIALLY VERIFIED`, `VERIFIED`, `DISQUALIFIED` |
| `reasons` | list / string | OUI | Justifications factuelles traçables pour chaque composante des scores |
| `last_checked` | string (ISO 8601) | OUI | Date et heure réelles de la vérification dynamique (ex: `2026-09-27T01:10:00Z`) |
| `notes` | string | NON | Synthèse du rapprochement et alertes techniques |

## 2. Formats de Stockage
- **JSON Structuré** : `data/top30_leads_requalified.json` (avec types natifs listes et booléens).
- **CSV Opérationnel** : `data/top30_leads_requalified.csv` (avec listes aplaties par `; `).
