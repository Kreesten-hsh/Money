from __future__ import annotations

from typing import Any, Dict, List, Set
from money_v2.contracts.evidence import Evidence


class SealingViolationError(Exception):
    """Exception critique levée si une donnée OSINT tente d'écraser un champ légal SIRENE."""
    pass


class LegalReconciliationLayer:
    """
    Couche de réconciliation stricte garantissant le principe d'étanchéité :
    Niveau 4 (OSINT, MCP, Scrapers) ne prévaut JAMAIS sur Niveau 1/2 (SIRENE, Registre d'État).
    """

    LEGAL_PROTECTED_FIELDS: Set[str] = {
        "siren",
        "company_name",
        "legal_status",
        "company_size",
        "company_size_code",
        "decision_maker",
        "decision_maker_role",
        "decision_maker_is_person",
        "has_secondary_size_proof",
        "siren_source",
        "evidence_url",
        "sirene_candidate_selected",
        "sirene_candidate_score",
        "sirene_second_candidate_score",
        "sirene_score_delta",
        "sirene_matching_decision_reason"
    }

    @classmethod
    def assert_sealing(cls, evidences: List[Evidence]) -> None:
        """Vérifie programmatiquement qu'aucune évidence ne cible un champ protégé."""
        for ev in evidences:
            if ev.field in cls.LEGAL_PROTECTED_FIELDS:
                raise SealingViolationError(
                    f"VIOLATION D'ÉTANCHÉITÉ : Le provider '{ev.provider}' a produit "
                    f"une preuve ciblant le champ légal réservé '{ev.field}' avec la valeur '{ev.value}'."
                )

    @classmethod
    def reconcile(cls, lead: Dict[str, Any], evidences: List[Evidence]) -> Dict[str, Any]:
        """
        Fusionne les évidences autorisées dans le dictionnaire du lead.
        Rejette toute tentative d'écrasement de données légales.
        """
        cls.assert_sealing(evidences)
        reconciled = dict(lead)

        for ev in evidences:
            reconciled[ev.field] = ev.value
            if ev.source:
                reconciled[f"{ev.field}_source"] = ev.source
            if ev.evidence_text:
                reconciled[f"{ev.field}_evidence"] = ev.evidence_text
            if ev.observed_at:
                reconciled[f"{ev.field}_checked_at"] = ev.observed_at

        return reconciled
