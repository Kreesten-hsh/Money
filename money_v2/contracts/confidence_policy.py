from __future__ import annotations

import re
import unicodedata
from enum import Enum
from typing import Optional, Set
from money_v2.contracts.evidence import Evidence


class EmailClassification(str, Enum):
    """Classification déterministe de la nature d'une adresse email collectée."""
    GENERIC_EMAIL = "GENERIC_EMAIL"
    INDIVIDUAL_PROFESSIONAL_EMAIL = "INDIVIDUAL_PROFESSIONAL_EMAIL"
    DECISION_MAKER_MATCHED_EMAIL = "DECISION_MAKER_MATCHED_EMAIL"
    UNVERIFIED_PUBLIC_EMAIL = "UNVERIFIED_PUBLIC_EMAIL"


class ConfidencePolicyViolationError(Exception):
    """Exception levée en cas de violation des règles d'attribution de confiance."""
    pass


class ConfidencePolicy:
    """
    Règles strictes d'attribution des niveaux de confiance et de classification.
    Interdit formellement la promotion d'emails génériques en emails de dirigeants
    sans corrélation nominative prouvée.
    """

    GENERIC_PREFIXES: Set[str] = {
        "contact", "info", "bonjour", "hello", "agence", "support",
        "commercial", "devis", "admin", "contactez-nous", "accueil",
        "bureau", "mail", "postmaster", "direction", "webmaster",
        "team", "aide", "billing", "facturation", "jobs", "rh", "recrutement"
    }

    @staticmethod
    def _normalize_string(val: str) -> str:
        """Supprime accents et minusculise pour matching robuste."""
        nfkd = unicodedata.normalize('NFKD', val)
        return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()

    @classmethod
    def classify_email(
        cls,
        email: str,
        decision_maker_name: Optional[str] = None
    ) -> EmailClassification:
        """
        Classe une adresse email selon son préfixe et sa concordance avec le dirigeant légal.
        """
        clean_email = email.strip().lower()
        if "@" not in clean_email:
            return EmailClassification.UNVERIFIED_PUBLIC_EMAIL

        local_part, _ = clean_email.split("@", 1)
        local_clean = re.sub(r'[^a-z0-9]', '', local_part)

        # 1. Vérification des préfixes génériques
        if local_part in cls.GENERIC_PREFIXES or any(local_part.startswith(p + ".") or local_part.startswith(p + "-") for p in cls.GENERIC_PREFIXES):
            return EmailClassification.GENERIC_EMAIL

        # 2. Vérification de concordance avec le dirigeant légal
        if decision_maker_name and decision_maker_name not in ("Non trouvé", "Non renseigné", ""):
            norm_dm = cls._normalize_string(decision_maker_name)
            parts = [p for p in re.split(r'[\s\-_]+', norm_dm) if len(p) >= 2]
            
            # Si le nom et prénom (ou nom complet) apparaissent dans la partie locale
            matched_parts = [p for p in parts if p in local_clean]
            if len(matched_parts) >= 2 or (len(parts) == 1 and len(matched_parts) == 1):
                return EmailClassification.DECISION_MAKER_MATCHED_EMAIL
            if len(parts) >= 2 and any(p == local_part for p in parts):
                return EmailClassification.DECISION_MAKER_MATCHED_EMAIL

        # 3. Détection de format nominatif standard (prenom.nom ou p.nom)
        if "." in local_part or "_" in local_part or "-" in local_part:
            return EmailClassification.INDIVIDUAL_PROFESSIONAL_EMAIL

        return EmailClassification.UNVERIFIED_PUBLIC_EMAIL

    @classmethod
    def assert_email_promotion_allowed(
        cls,
        evidence: Evidence,
        target_role: str = "DECISION_MAKER"
    ) -> None:
        """
        Vérifie qu'un email n'est pas indûment promu en adresse personnelle de dirigeant.
        """
        classification = evidence.email_classification
        if not classification:
            classification = cls.classify_email(str(evidence.value or "")).value

        if classification == EmailClassification.GENERIC_EMAIL.value and target_role == "DECISION_MAKER":
            raise ConfidencePolicyViolationError(
                f"VIOLATION CONFIDENCE POLICY : L'adresse générique '{evidence.value}' "
                f"ne peut pas être affectée comme email personnel du dirigeant sans preuve d'attribution explicite."
            )
