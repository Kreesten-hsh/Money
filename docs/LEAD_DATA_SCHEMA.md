# Schéma de Données Officiel — Lead Intelligence Schema

## 1. Dictionnaire des Données

Chaque enregistrement du dataset de prospection doit respecter strictement les attributs suivants :

| Attribut | Type | Requis | Description & Règles de Valeur |
|---|---|---|---|
| `company_name` | string | OUI | Raison sociale officielle (issue du RCS/SIRENE) ou nom d'usage |
| `brand_name` | string | OUI | Nom commercial de marque tel qu'observé sur le marché |
| `siren` | string (9 chiffres) | OUI | Numéro SIREN issu du registre public (ou `Non trouvé`) |
| `website` | string (URL) | OUI | URL canonique du site web de l'agence (ex: `https://example.com/`) |
| `country` | string | OUI | Code pays ou libellé (défaut : `France`) |
| `city` | string | OUI | Ville d'établissement principal |
| `company_size` | string | OUI | Libellé officiel de la tranche d'effectif INSEE (ou `Incertain`) |
| `company_size_source` | string | OUI | Source de vérification de la taille (ex: `INSEE / Annuaire des Entreprises`, `Non vérifié`) |
| `main_offer` | string | OUI | Prestation principale observée sur le site (ou `Non vérifié`) |
| `target_clients` | string | OUI | Typologie de clientèle observée sur le site (ou `Non vérifié`) |
| `decision_maker` | string | OUI | Nom complet du dirigeant identifié au registre public (ou `Non identifié au registre`) |
| `decision_maker_role` | string | OUI | Rôle officiel extrait de l'attribut `qualite` SIRENE (ex: `Gérant`, `Président`, `Inconnu`) |
| `decision_maker_source` | string (URL) | NON | URL prouvant l'identité légale (ex: Annuaire des Entreprises) |
| `public_professional_email` | string | NON | Email professionnel public (ex: `Non extrait (Option)`) |
| `public_phone` | string | NON | Numéro de téléphone direct vérifié |
| `source_url` | string (URL) | OUI | Fiche de sourcing primaire (URL Google Maps) |
| `evidence_url` | string (URL) | OUI | URL de preuve légale (Annuaire des Entreprises ou site officiel) |
| `matching_status` | enum | OUI | Rapprochement SIRENE : `MATCH_CONFIRMED`, `MATCH_PLAUSIBLE`, `MATCH_UNCERTAIN`, `NO_MATCH` |
| `commercial_signal` | string | NON | Fait d'actualité ou opportunité externe réelle (vide si non vérifié) |
| `signal_source` | string (URL) | NON | URL prouvant la réalité du signal commercial |
| `signal_date` | string (YYYY-MM-DD) | NON | Date d'observation vérifiée du signal commercial |
| `lead_gen_score` | integer (0-100) | OUI | Score d'adéquation pour l'offre AI Lead Intelligence |
| `ghostwriting_score` | integer (0-100) | OUI | Score Founder Ghostwriting (neutralisé à 0 en phase actuelle) |
| `confidence_score` | integer (0-100) | OUI | Indice de solidité des preuves (Plafond 60 si statut != VERIFIED) |
| `verification_status` | enum | OUI | Statut : `CANDIDATE`, `REQUIRES REVIEW`, `PARTIALLY VERIFIED`, `VERIFIED`, `DISQUALIFIED` |
| `reasons` | list of string (JSON) / string délimité ';' (CSV) | OUI | Justifications factuelles traçables pour chaque composante des scores |
| `last_checked` | string (YYYY-MM-DD) | OUI | Date de la vérification (format ISO) |
| `notes` | string | NON | Rapprochement, alertes techniques (ex: `site inaccessible`), détails NAF |

## 2. Formats de Stockage
- **JSON Structuré** : `data/top30_leads_requalified.json` (avec `reasons` sous forme de liste native).
- **CSV Opérationnel** : `data/top30_leads_requalified.csv` (avec `reasons` aplati sous forme de chaîne délimitée par `; `).
