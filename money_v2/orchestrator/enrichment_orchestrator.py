from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.orchestrator.fallback_strategy import FallbackStrategy
from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.providers.cms_provider import CmsTechnologyProvider
from money_v2.providers.crawlee_provider import CrawleeProvider
from money_v2.providers.dns_mx_provider import DnsMxProvider
from money_v2.providers.firecrawl_provider import FirecrawlProvider
from money_v2.providers.http_provider import HttpProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider
from money_v2.providers.theharvester_provider import TheHarvesterProvider


class EnrichmentOrchestrator:
    """
    Orchestrateur central d'enrichissement Money V2.
    Pilote les providers par configuration, collecte les preuves avec traçabilité
    et applique le principe d'étanchéité absolue :
    AUCUNE donnée d'enrichissement ne peut écraser les données légales SIRENE.
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

    def __init__(
        self,
        observability_hub: Optional[ObservabilityHub] = None,
        enable_theharvester: bool = True,
        enable_playwright: bool = True,
        enable_crawlee: bool = False
    ):
        self.hub = observability_hub or ObservabilityHub()
        self.http_prov = HttpProvider()
        self.fc_prov = FirecrawlProvider()
        self.pw_prov = InvisiblePlaywrightProvider(enabled=enable_playwright)
        self.fallback = FallbackStrategy(self.http_prov, self.fc_prov, self.pw_prov)
        self.th_prov = TheHarvesterProvider(enabled=enable_theharvester)
        self.dns_prov = DnsMxProvider()
        self.cms_prov = CmsTechnologyProvider()
        self.crawlee_prov = CrawleeProvider(enabled=enable_crawlee)

    def enrich_lead(self, lead: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Evidence]]:
        """
        Enrichit un lead unique en respectant l'ordonnancement des dépendances,
        la chaîne de repli et l'étanchéité légale.
        """
        enriched = dict(lead)
        collected_evidences: List[Evidence] = []
        domain = str(lead.get("domain") or "").strip().lower()
        website = str(lead.get("website") or "").strip()
        lead_id = str(lead.get("brand_name") or domain or "unknown_lead")
        context = {"lead_id": lead_id, "domain": domain}

        # 1. Inspection du site vitrine via FallbackStrategy si main_offer est absente ou non vérifiée
        if not enriched.get("main_offer") or enriched.get("main_offer") == "Non vérifié":
            target_url = website or (f"https://{domain}" if domain else "")
            if target_url:
                result, _ = self.fallback.execute_inspection_chain(target_url, context)
                if result.telemetry:
                    self.hub.record(result.telemetry)
                for ev in result.evidences:
                    # Ne jamais écraser un champ protégé
                    if ev.field not in self.LEGAL_PROTECTED_FIELDS:
                        enriched[ev.field] = ev.value
                        enriched[f"{ev.field}_source"] = ev.source
                        enriched[f"{ev.field}_evidence"] = ev.evidence_text
                        enriched[f"{ev.field}_checked_at"] = ev.observed_at
                        collected_evidences.append(ev)

        # 2. Validation MX et délivrabilité DNS
        if domain:
            dns_res = self.dns_prov.execute(domain, context)
            if dns_res.telemetry:
                self.hub.record(dns_res.telemetry)
            for ev in dns_res.evidences:
                if ev.field not in self.LEGAL_PROTECTED_FIELDS:
                    enriched[ev.field] = ev.value
                    collected_evidences.append(ev)

        # 3. Détection d'empreinte CMS si non déjà détectée
        if website and (not enriched.get("cms_detected") or enriched.get("cms_detected") == "Non détecté"):
            cms_res = self.cms_prov.execute(website, context)
            if cms_res.telemetry:
                self.hub.record(cms_res.telemetry)
            for ev in cms_res.evidences:
                if ev.field not in self.LEGAL_PROTECTED_FIELDS:
                    enriched["cms_detected"] = ev.value
                    enriched["cms_source"] = ev.source
                    enriched["cms_evidence"] = ev.evidence_text
                    enriched["cms_checked_at"] = ev.observed_at
                    collected_evidences.append(ev)

        # 4. OSINT passif via theHarvester pour public_professional_email si absent
        if domain and not enriched.get("public_professional_email"):
            if self.th_prov.is_available():
                th_res = self.th_prov.execute(domain, context)
                if th_res.telemetry:
                    self.hub.record(th_res.telemetry)
                for ev in th_res.evidences:
                    if ev.field == "public_professional_email" and ev.field not in self.LEGAL_PROTECTED_FIELDS:
                        # Validation de concordance et résolution MX requise
                        enriched["public_professional_email"] = ev.value
                        enriched["email_source"] = ev.source
                        enriched["email_evidence"] = ev.evidence_text
                        enriched["email_checked_at"] = ev.observed_at
                        collected_evidences.append(ev)
                        break

        # 5. Consultation LinkedIn encadrée (ADR-008) si dirigeant MATCH_CONFIRMED et activée
        if (
            lead.get("matching_status") == "MATCH_CONFIRMED"
            and lead.get("decision_maker_is_person") is True
            and not enriched.get("decision_maker_linkedin_activity")
        ):
            # Simulation/vérification unitaire si profil URL fourni dans le lead
            profile_url = lead.get("linkedin_profile_url")
            if profile_url and self.pw_prov.is_available():
                ctx_li = dict(context)
                ctx_li["trigger_type"] = "linkedin_consultation"
                ctx_li["field_target"] = "decision_maker_linkedin_activity"
                ctx_li["matching_status"] = "MATCH_CONFIRMED"

                pw_res = self.pw_prov.execute(profile_url, ctx_li)
                if pw_res.telemetry:
                    self.hub.record(pw_res.telemetry)
                for ev in pw_res.evidences:
                    if ev.field not in self.LEGAL_PROTECTED_FIELDS:
                        enriched[ev.field] = ev.value
                        enriched["decision_maker_linkedin_source"] = ev.source
                        enriched["decision_maker_linkedin_checked_at"] = ev.observed_at
                        collected_evidences.append(ev)

        return enriched, collected_evidences
