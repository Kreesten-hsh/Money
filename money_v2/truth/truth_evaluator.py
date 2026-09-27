from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from money_v2.contracts.provider_status import ProviderStatus


class TruthStatus(str, Enum):
    """Statuts de vérité métier pour chaque dimension d'un lead."""
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    NO_MATCH = "NO_MATCH"
    ERROR = "ERROR"


class TruthEvaluator:
    """
    Évalue le niveau de vérité pour les 8 dimensions critiques d'un prospect.
    Distingue rigoureusement une absence d'information d'une défaillance technique.
    """

    @staticmethod
    def evaluate_legal_identity(lead: Dict[str, Any]) -> TruthStatus:
        matching = lead.get("matching_status")
        siren = str(lead.get("siren") or "").strip()
        status = lead.get("verification_status")

        if matching == "NO_MATCH":
            return TruthStatus.NO_MATCH
        if matching == "MATCH_UNCERTAIN":
            return TruthStatus.REQUIRES_REVIEW
        if status == "VERIFIED" and len(siren) == 9:
            return TruthStatus.VERIFIED
        if status == "PARTIALLY VERIFIED":
            return TruthStatus.PARTIALLY_VERIFIED
        return TruthStatus.REQUIRES_REVIEW

    @staticmethod
    def evaluate_legal_employees(lead: Dict[str, Any]) -> TruthStatus:
        size_code = lead.get("company_size_code")
        if size_code in ("NN", "00"):
            return TruthStatus.REQUIRES_REVIEW
        if size_code == "01":
            # Nécessite preuve secondaire
            return TruthStatus.VERIFIED if lead.get("has_secondary_size_proof") else TruthStatus.PARTIALLY_VERIFIED
        if size_code in ("02", "03", "11"):
            return TruthStatus.VERIFIED
        return TruthStatus.UNVERIFIED

    @staticmethod
    def evaluate_legal_director(lead: Dict[str, Any]) -> TruthStatus:
        dm = lead.get("decision_maker")
        role = lead.get("decision_maker_role")
        is_person = lead.get("decision_maker_is_person")

        if not dm or dm == "Non trouvé":
            return TruthStatus.UNVERIFIED
        if is_person is False:
            # Personne morale
            return TruthStatus.PARTIALLY_VERIFIED
        if dm and role and role != "Non trouvé":
            return TruthStatus.VERIFIED
        return TruthStatus.REQUIRES_REVIEW

    @staticmethod
    def evaluate_main_offer(lead: Dict[str, Any], provider_status: Optional[ProviderStatus] = None) -> TruthStatus:
        if provider_status and provider_status.is_technical_failure:
            return TruthStatus.ERROR
        offer = lead.get("main_offer")
        source = lead.get("main_offer_source")
        if offer and offer != "Non vérifié" and source:
            return TruthStatus.VERIFIED
        return TruthStatus.UNVERIFIED

    @staticmethod
    def evaluate_email(lead: Dict[str, Any], provider_status: Optional[ProviderStatus] = None) -> TruthStatus:
        if provider_status and provider_status.is_technical_failure:
            return TruthStatus.ERROR
        email = lead.get("public_professional_email")
        source = lead.get("email_source")
        if email and source:
            return TruthStatus.VERIFIED
        return TruthStatus.UNVERIFIED

    @classmethod
    def evaluate_lead_summary(cls, lead: Dict[str, Any]) -> Dict[str, str]:
        """Génère un diagnostic de vérité dimensionnel complet."""
        return {
            "LEGAL_IDENTITY": cls.evaluate_legal_identity(lead).value,
            "LEGAL_EMPLOYEES": cls.evaluate_legal_employees(lead).value,
            "LEGAL_DIRECTOR": cls.evaluate_legal_director(lead).value,
            "MAIN_OFFER": cls.evaluate_main_offer(lead).value,
            "EMAIL": cls.evaluate_email(lead).value,
        }
