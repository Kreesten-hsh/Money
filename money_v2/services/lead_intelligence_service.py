from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from money_v2.contracts.evidence import Evidence


class LeadIntelligenceService:
    """
    Service métier AI Lead Intelligence.
    Consolide la qualification ICP, synthétise l'offre et les cibles observables,
    calcule le score Lead Gen et génère l'outreach vérifié sans hallucination.
    """

    ALLOWED_SIZE_CODES = {"02", "03", "11"}

    @classmethod
    def evaluate_icp_compliance(cls, lead: Dict[str, Any]) -> bool:
        """Vérifie la conformité absolue à l'ICP (agence web française 2-20 salariés)."""
        if lead.get("company_closed") is True:
            return False

        size_code = str(lead.get("company_size_code") or "")
        if size_code in cls.ALLOWED_SIZE_CODES:
            return True
        if size_code == "01" and lead.get("has_secondary_size_proof") is True:
            return True
        return False

    @classmethod
    def compute_lead_gen_score(cls, lead: Dict[str, Any]) -> int:
        """
        Calcule le score d'opportunité Lead Gen (0-100).
        Plafonné à 75/100 en l'absence de signal commercial exceptionnel observable.
        """
        if not cls.evaluate_icp_compliance(lead):
            return 0

        score = 30  # Socle entreprise active ICP validée

        # Signal d'offre observable
        offer = str(lead.get("main_offer") or "")
        if offer and offer not in ("Non vérifié", "Non renseigné", "Inconnu"):
            score += 15

        # Signal de cible observable
        target = str(lead.get("target_clients") or "")
        if target and target not in ("Non vérifié", "Non renseigné", "Inconnu"):
            score += 10

        # Délivrabilité et email professionnel
        if lead.get("mx_valid") is True:
            score += 10
        if lead.get("public_professional_email"):
            score += 10

        # Plafond strict à 75 points sauf si traction démontrée
        return min(score, 75)

    @classmethod
    def generate_personalized_outreach(cls, lead: Dict[str, Any]) -> str:
        """
        Génère une ébauche de message de prise de contact 100% vérifiée.
        Zéro hallucination : respect strict de la salutation (personne morale vs physique)
        et ancrage exclusif sur les signaux observés.
        """
        brand = str(lead.get("brand_name") or lead.get("title") or "l'agence").strip()
        dm = str(lead.get("decision_maker") or "").strip()
        is_person = lead.get("decision_maker_is_person")
        offer = str(lead.get("main_offer") or "").strip()
        cms = str(lead.get("cms_detected") or "").strip()

        # Règle de salutation (Contrôle QA 21)
        if is_person is False or not dm or dm in ("Non trouvé", "Non renseigné"):
            greeting = f"Bonjour l'équipe {brand},"
        else:
            first_name = dm.split()[0].title() if " " in dm else dm.title()
            greeting = f"Bonjour {first_name},"

        lines = [greeting, ""]

        # Accroche contextuelle basée sur l'offre ou la stack observée
        if offer and offer != "Non vérifié":
            lines.append(f"J'ai remarqué vos réalisations autour de votre offre : {offer}.")
        elif cms and cms != "Non détecté":
            lines.append(f"J'ai analysé votre expertise digitale et vos déploiements sur {cms}.")
        else:
            lines.append(f"J'ai découvert les projets digitaux développés par {brand}.")

        lines.append(
            "Dans le cadre de nos collaborations avec des agences web à taille humaine, "
            "nous accompagnons les dirigeants dans la structuration de leur acquisition B2B."
        )
        lines.append("")
        lines.append("Seriez-vous ouvert à un échange de 10 minutes cette semaine ?")
        lines.append("")
        lines.append("Bien cordialement,")
        lines.append("Kreesten Agboton")

        return "\n".join(lines)

    @classmethod
    def generate_intelligence_dossier(cls, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Consolide le dossier commercial complet pour la Lead Intelligence Room."""
        icp_ok = cls.evaluate_icp_compliance(lead)
        score = cls.compute_lead_gen_score(lead)
        outreach = cls.generate_personalized_outreach(lead)

        return {
            "lead_id": lead.get("brand_name") or lead.get("domain"),
            "brand_name": lead.get("brand_name"),
            "domain": lead.get("domain"),
            "siren": lead.get("siren"),
            "company_size": lead.get("company_size"),
            "decision_maker": lead.get("decision_maker"),
            "decision_maker_role": lead.get("decision_maker_role"),
            "is_icp_compliant": icp_ok,
            "lead_gen_score": score,
            "main_offer": lead.get("main_offer", "Non vérifié"),
            "main_offer_source": lead.get("main_offer_source", ""),
            "target_clients": lead.get("target_clients", "Non vérifié"),
            "cms_detected": lead.get("cms_detected", "Non détecté"),
            "public_professional_email": lead.get("public_professional_email", ""),
            "mx_valid": lead.get("mx_valid", False),
            "outreach_draft": outreach,
            "verification_status": lead.get("verification_status", "REQUIRES REVIEW")
        }
