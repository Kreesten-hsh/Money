# Spécification des Contrats d'Échange V2 — Providers & Évidences

## 1. Modèle Universel d'Évidence (`Evidence`)

Toute observation produite par un provider répond strictement aux 11 dimensions d'auditabilité :

```json
{
  "field": "public_professional_email",
  "value": "contact@agence-exemple.fr",
  "source": "theHarvester",
  "source_url": "osint://theharvester/agence-exemple.fr",
  "observed_at": "2026-09-27T16:45:00Z",
  "method": "OSINT_CLI",
  "provider": "theharvester_provider",
  "provider_status": "SUCCESS",
  "evidence_text": "Email public indexé via OSINT passif (crtsh,duckduckgo) : contact@agence-exemple.fr",
  "confidence": "HIGH",
  "lead_id": "agence-exemple.fr",
  "metadata": {
    "target_domain": "agence-exemple.fr",
    "email_domain": "agence-exemple.fr"
  }
}
```

### Niveaux de Confiance (`ConfidenceLevel`)
- `HIGH` : Preuve directe et vérifiée (balise HTML canonique, résolution DNS réussie, email extrait publiquement).
- `MEDIUM` : Preuve indirecte concordante (extraction markdown, métadonnées tierces).
- `LOW` : Preuve faible nécessitant confirmation humaine.
- `PATTERN` : Schéma déduit ou heuristique indicative (**jamais promu en valeur certifiée**).

---

## 2. Statuts Normalisés d'Exécution (`ProviderStatus`)

L'architecture V2 impose 11 statuts normalisés :

| Statut | Signification | Est une panne technique ? |
| :--- | :--- | :--- |
| `SUCCESS` | Exécution réussie avec évidences produites | Non |
| `NO_RESULT` | Exécution réussie mais aucune information trouvée | Non |
| `PARTIAL` | Exécution partiellement réussie (ex: crawl de lot) | Non |
| `RATE_LIMITED` | Quota de requêtes distant dépassé (HTTP 429) | **Oui** |
| `BLOCKED` | Blocage par pare-feu ou anti-bot (HTTP 403 / 401 / Turnstile) | **Oui** |
| `TIMEOUT` | Délai d'attente réseau ou processus dépassé | **Oui** |
| `NETWORK_ERROR`| Panne de connectivité (DNS, connexion refusée) | **Oui** |
| `AUTH_REQUIRED`| Clé d'API ou accréditation manquante | **Oui** |
| `TOOL_MISSING` | Binaire ou dépendance système introuvable | **Oui** |
| `INVALID_INPUT`| Paramètre d'entrée invalide (URL malformée, champ protégé) | Non |
| `UNKNOWN_ERROR`| Exception imprévue non typée | **Oui** |

> [!IMPORTANT]
> **Règle Fondamentale** : Une panne technique (`RATE_LIMITED`, `BLOCKED`, `TIMEOUT`, `NETWORK_ERROR`, `TOOL_MISSING`) ne doit **JAMAIS** être assimilée à `NO_RESULT`.

---

## 3. Télémétrie d'Observabilité (`ProviderTelemetry`)

Chaque invocation d'un provider génère une télémétrie persistée :

| Champ | Type | Description |
| :--- | :--- | :--- |
| `provider` | `string` | Nom unique du provider |
| `lead_id` | `string` | Identifiant du prospect audité |
| `started_at` | `string` | Horodatage ISO 8601 UTC de début |
| `finished_at`| `string` | Horodatage ISO 8601 UTC de fin |
| `duration_ms`| `float` | Durée exacte d'exécution en millisecondes |
| `status` | `string` | Valeur du `ProviderStatus` |
| `records_found` | `int` | Nombre d'enregistrements bruts trouvés |
| `evidence_count`| `int` | Nombre d'évidences structurées émises |
| `error_type` | `string?` | Nom de classe de l'erreur levée |
| `error_message_safe` | `string?` | Message tronqué et nettoyé pour les logs |
