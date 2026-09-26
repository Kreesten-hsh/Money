# Schéma de Données Officiel — Lead Intelligence Schema

## 1. Définition des Attributs
Chaque enregistrement de prospect qualifié doit respecter strictement le dictionnaire de données suivant :

| Colonne | Type | Requis | Description & Règles de Valeur |
|---|---|---|---|
| `company_name` | string | OUI | Raison sociale officielle ou nom commercial d'usage |
| `siren` | string (9 digits) | NON | Numéro SIREN issu du registre du commerce et des sociétés |
| `website` | string (URL) | OUI | URL canonique du site web de l'agence (ex: `https://example.com/`) |
| `country` | string | OUI | Code pays ISO ou libellé (défaut : `France`) |
| `city` | string | OUI | Ville principale de rattachement de l'établissement |
| `company_size` | string | OUI | Intervalle d'effectif documenté (ex: `1 à 2 salariés`, `3 à 5 salariés`, `6 à 9 salariés`, `10 à 19 salariés`, `Incertain`) |
| `company_size_source` | string | OUI | Source prouvant la taille (ex: `INSEE / Annuaire Entreprises`, `Mentions Légales`, `Organigramme Site Web`) |
| `main_offer` | string | OUI | Prestation centrale (ex: `Conception Webflow & SEO`, `Refonte WordPress PME`, `Branding & Acquisition`) |
| `target_clients` | string | OUI | Clientèle cible prioritaire déclarée (ex: `PME locales`, `Startups B2B`, `Grands Comptes RSE`) |
| `decision_maker` | string | NON | Nom complet du dirigeant / associé public (ou `Non identifié`) |
| `decision_maker_role` | string | NON | Fonction officielle (ex: `Fondateur & CEO`, `Gérant Associé`, `Directeur Général`) |
| `decision_maker_source` | string (URL) | NON | URL prouvant l'identité (ex: mentions légales, page équipe, registre société) |
| `public_professional_email` | string | NON | Email professionnel de contact public (ex: `contact@agence.fr`) |
| `public_phone` | string | NON | Numéro de téléphone professionnel au format international |
| `source_url` | string (URL) | OUI | Source de découverte primaire (ex: URL fiche Google Maps ou requête d'indexation) |
| `evidence_url` | string (URL) | OUI | URL de vérification principale (ex: mentions légales du site, fiche Pappers/INSEE) |
| `commercial_signal` | string | NON | Fait d'actualité ou opportunité commerciale exploitable pour l'approche |
| `signal_source` | string (URL) | NON | URL prouvant la réalité du signal commercial |
| `signal_date` | string (YYYY-MM-DD) | NON | Date d'observation du signal commercial |
| `lead_gen_score` | integer (0-100) | OUI | Score d'adéquation pour l'offre AI Lead Intelligence |
| `ghostwriting_score` | integer (0-100) | OUI | Score d'adéquation pour l'offre Founder Ghostwriting |
| `confidence_score` | integer (0-100) | OUI | Indice de solidité des preuves recueillies (Plafond 60 si données partielles) |
| `verification_status` | enum | OUI | `CANDIDATE`, `REQUIRES REVIEW`, `PARTIALLY VERIFIED`, `VERIFIED`, `DISQUALIFIED` |
| `last_checked` | string (YYYY-MM-DD) | OUI | Date de la dernière vérification humaine ou agentique |
| `notes` | string | NON | Commentaires d'analyse ou points de vigilance particuliers |

## 2. Formats de Stockage
- **CSV Opérationnel** : Format tabulaire plat encodé en UTF-8 avec séparateur virgule (fichier `data/top30_leads_requalified.csv`).
- **JSON Structuré** : Format hiérarchique avec conservation des métadonnées (fichier `data/top30_leads_requalified.json`).
