# Registre des Fournisseurs d'APIs — Money V2 (Index API-mega-list)

## 1. Rôle du Registre & Positionnement d'API-mega-list

L'index [API-mega-list](https://github.com/cporter202/API-mega-list) (11 860 APIs) est utilisé comme **catalogue de découverte et de sourcing**, et non comme un provider logiciel en soi.
Aucune API n'est considérée comme intégrée simplement parce qu'elle figure dans l'index : elle doit faire l'objet d'une sélection explicite, d'un adaptateur de code dédié et d'un test d'intégration.

---

## 2. Statuts des APIs dans le Registre

- `ACTIVE` : Adaptateur implémenté dans le code, tests d'intégration passants, utilisé en production sans clé payante.
- `DOCUMENTED` : Adaptateur préparé, sélection validée, activable sur demande opérationnelle.
- `INACTIVE` : Référencée pour étude future, désactivée par défaut pour respecter le budget 0€.

---

## 3. Fiches Détaillées des APIs Retenues

### A. API Recherche d'Entreprises (data.gouv.fr) — `recherche_entreprises_sirene`
- **Statut** : `ACTIVE`
- **Domaine** : `recherche-entreprises.api.gouv.fr`
- **Endpoint** : `https://recherche-entreprises.api.gouv.fr/search`
- **Usage Métier** : Vérification légale du SIREN, tranche d'effectifs INSEE, statut actif/fermé, nom officiel et dirigeants.
- **Entrées (Input)** : `q` (nom de marque), `code_postal` (code postal de l'établissement).
- **Sorties (Output)** : JSON officiel (SIREN, tranches effectifs, dirigeants personnes physiques / morales).
- **Coût** : **0 €** (Open Data sous Licence Ouverte v2.0).
- **Limites de Débit** : ~7 requêtes / seconde (respecté par sleep déterministe).
- **Authentification** : Aucune (libre d'accès).
- **Données Produites** : `siren`, `company_size_code`, `decision_maker`, `decision_maker_role`, `decision_maker_is_person`.
- **Preuve Associée** : URL officielle de consultation `https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}`.
- **Fallback** : Aucun (source légale exclusive Niveau 1/2).

### B. Google DNS-over-HTTPS — `google_dns_doh`
- **Statut** : `ACTIVE`
- **Domaine** : `dns.google`
- **Endpoint** : `https://dns.google/resolve`
- **Usage Métier** : Résolution déterministe des enregistrements MX sur réseaux bloquant le port UDP 53.
- **Entrées (Input)** : `name` (nom de domaine), `type` (`MX`).
- **Sorties (Output)** : JSON standard DNS RFC 8427.
- **Coût** : **0 €**.
- **Limites de Débit** : Plusieurs milliers de requêtes / minute.
- **Authentification** : Aucune.
- **Données Produites** : `mx_valid`, `mx_hosts`.
- **Preuve Associée** : Serveurs d'échange de mail observés et horodatés.
- **Fallback** : Précédé par UDP direct RFC 1035 et `socket.getaddrinfo`.

### C. OpenStreetMap Nominatim — `nominatim_osm`
- **Statut** : `DOCUMENTED`
- **Domaine** : `nominatim.openstreetmap.org`
- **Endpoint** : `https://nominatim.openstreetmap.org/search`
- **Usage Métier** : Géocodage et vérification de la cohérence géographique des agences web.
- **Entrées (Input)** : `q` (adresse textuelle), `format=json`.
- **Sorties (Output)** : Coordonnées GPS (latitude, longitude) et normalisation d'adresse.
- **Coût** : **0 €** (Données ODbL).
- **Limites de Débit** : Strictement max 1 requête / seconde (User-Agent requis).
- **Authentification** : User-Agent obligatoire.
- **Données Produites** : `normalized_address`, `latitude`, `longitude`.
- **Preuve Associée** : Place ID OSM officiel.
- **Fallback** : Coordonnées brutes Google Maps.

### D. Wappalyzer Core Tech Specs — `wappalyzer_core`
- **Statut** : `INACTIVE`
- **Domaine** : `api.wappalyzer.com`
- **Endpoint** : `https://api.wappalyzer.com/v2/lookup`
- **Usage Métier** : Audit approfondi de la stack Javascript / CMS.
- **Coût** : Payant au-delà du quota d'essai (rejeté par la politique Budget 0 €).
- **Authentification** : Clé API obligatoire.
- **Remplacement dans Money** : `CmsTechnologyProvider` natif stdlib (signatures HTML et headers HTTP observables).
