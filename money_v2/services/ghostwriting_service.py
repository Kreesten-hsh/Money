from __future__ import annotations

from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import Evidence


class GhostwritingIntelligenceService:
    """
    Service métier Founder LinkedIn Ghostwriting.
    Évalue l'éligibilité du dirigeant, analyse les signaux d'activité éditoriale publique,
    neutralise rigoureusement le score en l'absence de signal vérifié,
    et formule des angles éditoriaux à haute valeur ajoutée.
    """

    @classmethod
    def evaluate_eligibility(cls, lead: Dict[str, Any]) -> bool:
        """
        Détermine si le prospect est éligible à l'analyse Founder Ghostwriting.
        Exige impérativement un dirigeant personne physique certifié SIRENE.
        """
        if lead.get("matching_status") != "MATCH_CONFIRMED":
            return False
        if lead.get("decision_maker_is_person") is not True:
            return False
        dm = str(lead.get("decision_maker") or "").strip()
        if not dm or dm in ("Non trouvé", "Non renseigné"):
            return False
        return True

    @classmethod
    def compute_ghostwriting_score(cls, lead: Dict[str, Any]) -> int:
        """
        Calcule le score Ghostwriting (0-100).
        RÈGLE INFRANGIBLE (Contrôle QA 15) :
        En l'absence de signal éditorial public prouvé, le score DOIT être neutralisé à 0/100.
        """
        if not cls.evaluate_eligibility(lead):
            return 0

        has_activity = lead.get("decision_maker_linkedin_activity") is True
        source_url = str(
            lead.get("decision_maker_linkedin_source")
            or lead.get("decision_maker_linkedin_activity_source")
            or lead.get("linkedin_profile_url")
            or ""
        ).strip()

        # Neutralisation déterministe si aucune activité prouvée
        if not has_activity or not source_url:
            return 0

        score = 50  # Socle dirigeant éligible avec activité publique observée

        role = str(lead.get("decision_maker_role") or "").lower()
        if any(r in role for r in [
            "président", "présidente", "gérant", "gérante", 
            "fondateur", "fondatrice", "directeur", "directrice", 
            "ceo", "dg", "co-fondateur", "co-fondatrice"
        ]):
            score += 20

        # Prime d'agence établie (effectif 2-20)
        size_code = str(lead.get("company_size_code") or "")
        if size_code in ("02", "03", "11"):
            score += 15

        return min(score, 85)

    @classmethod
    def extract_editorial_angles(cls, lead: Dict[str, Any]) -> List[str]:
        """
        Formule des propositions d'angles éditoriaux B2B basées sur les signaux observés.
        """
        if not cls.evaluate_eligibility(lead):
            return ["Non éligible : dirigeant personne morale ou non confirmé."]

        brand = lead.get("brand_name") or "l'agence"
        offer = lead.get("main_offer") or "création de solutions digitales"
        cms = lead.get("cms_detected") or "technologies web"

        return [
            f"Retour d'expérience : Les coulisses de la refonte de projets sous {cms} pour les PME.",
            f"Positionnement marché : Pourquoi {brand} privilégie {offer} face à la standardisation du marché.",
            "Leadership & Croissance : Comment structurer une agence web de 2 à 20 experts sans compromettre la qualité technique."
        ]

    @classmethod
    def generate_ghostwriting_dossier(cls, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Génère le dossier d'intelligence Ghostwriting pour la restitution client."""
        eligible = cls.evaluate_eligibility(lead)
        score = cls.compute_ghostwriting_score(lead)
        angles = cls.extract_editorial_angles(lead)

        return {
            "lead_id": lead.get("brand_name") or lead.get("domain"),
            "decision_maker": lead.get("decision_maker"),
            "decision_maker_role": lead.get("decision_maker_role"),
            "decision_maker_is_person": lead.get("decision_maker_is_person"),
            "is_eligible": eligible,
            "ghostwriting_score": score,
            "is_neutralized": score == 0,
            "neutralization_reason": "Aucune activité éditoriale publique vérifiée" if (eligible and score == 0) else ("Non éligible" if not eligible else None),
            "linkedin_activity": lead.get("decision_maker_linkedin_activity", False),
            "linkedin_source": lead.get("decision_maker_linkedin_source", ""),
            "editorial_angles": angles
        }
