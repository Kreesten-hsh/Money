from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from money_v2.contracts.confidence_policy import ConfidencePolicy, EmailClassification
from money_v2.contracts.evidence import ConfidenceLevel, Evidence, get_current_iso_timestamp
from money_v2.contracts.provider_result import ProviderResult, ProviderTelemetry
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.orchestrator.crawl_planner import CrawlPlanner
from money_v2.orchestrator.fallback_strategy import FallbackStrategy
from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.providers.api_registry_provider import ApiRegistryProvider
from money_v2.providers.cms_provider import CmsTechnologyProvider
from money_v2.providers.crawlee_provider import CrawleeProvider
from money_v2.providers.dns_mx_provider import DnsMxProvider
from money_v2.providers.firecrawl_provider import FirecrawlProvider
from money_v2.providers.http_provider import HttpProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider
from money_v2.providers.theharvester_provider import TheHarvesterProvider


class EnrichmentOrchestrator:
    """
    Orchestrateur central d'enrichissement Money V2.2.
    Pilote les 4 providers externes et les providers internes avec chaîne de repli,
    Crawl Planner multi-pages, observabilité et étanchéité absolue :
    AUCUNE donnée d'enrichissement ne peut altérer ou écraser les données légales SIRENE.
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
        enable_crawlee: bool = True,
        enable_api_registry: bool = True
    ):
        self.hub = observability_hub or ObservabilityHub()
        self.http_prov = HttpProvider()
        self.fc_prov = FirecrawlProvider()
        self.pw_prov = InvisiblePlaywrightProvider(enabled=enable_playwright)
        self.crawlee_prov = CrawleeProvider(enabled=enable_crawlee)
        self.crawl_planner = CrawlPlanner(self.crawlee_prov)
        self.fallback = FallbackStrategy(
            self.http_prov,
            self.fc_prov,
            self.pw_prov,
            self.crawlee_prov
        )
        self.th_prov = TheHarvesterProvider(enabled=enable_theharvester)
        self.dns_prov = DnsMxProvider()
        self.cms_prov = CmsTechnologyProvider()
        self.api_registry_prov = ApiRegistryProvider(enabled=enable_api_registry)

    def _apply_evidences(
        self,
        lead: Dict[str, Any],
        evidences: List[Evidence],
        collected_list: List[Evidence]
    ) -> None:
        """Applique les évidences non protégées dans le dictionnaire du lead."""
        for ev in evidences:
            if ev.field in self.LEGAL_PROTECTED_FIELDS:
                continue
            lead[ev.field] = ev.value
            if ev.source:
                lead[f"{ev.field}_source"] = ev.source
            if ev.evidence_text:
                lead[f"{ev.field}_evidence"] = ev.evidence_text
            if ev.observed_at:
                lead[f"{ev.field}_checked_at"] = ev.observed_at
            collected_list.append(ev)

    def enrich_lead(self, lead: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Evidence]]:
        """
        Enrichit un lead unique en respectant l'ordonnancement des dépendances,
        la chaîne de repli, le crawl approfondi et l'étanchéité légale.
        """
        enriched = dict(lead)
        collected_evidences: List[Evidence] = []
        domain = str(lead.get("domain") or "").strip().lower()
        website = str(lead.get("website") or "").strip()
        lead_id = str(lead.get("brand_name") or domain or "unknown_lead")
        context = {
            "lead_id": lead_id,
            "domain": domain,
            "decision_maker": lead.get("decision_maker")
        }

        # 1. Inspection du site vitrine via FallbackStrategy (4 Paliers : HTTP -> FC -> PW -> Crawlee)
        target_url = website or (f"https://{domain}" if domain else "")
        if target_url and (not enriched.get("main_offer") or enriched.get("main_offer") == "Non vérifié"):
            res_inspection, audit_trail = self.fallback.execute_inspection_chain(target_url, context)
            if res_inspection.telemetry:
                self.hub.record(res_inspection.telemetry)
            self._apply_evidences(enriched, res_inspection.evidences, collected_evidences)

        # 2. Crawl approfondi multi-pages via CrawlPlanner / Crawlee si informations critiques manquantes
        need_deep_crawl = (
            not enriched.get("main_offer")
            or enriched.get("main_offer") == "Non vérifié"
            or not enriched.get("target_clients")
            or enriched.get("target_clients") == "Non vérifié"
        )
        if target_url and need_deep_crawl and self.crawlee_prov.is_available():
            deep_evidences, crawl_summary = self.crawl_planner.execute_lead_crawl(enriched, max_urls=3)
            self._apply_evidences(enriched, deep_evidences, collected_evidences)

        # 3. Résolution DNS/MX & Délivrabilité via API-mega-list (DoH) et fallback DnsMxProvider
        if domain:
            # A. Interrogation de l'adaptateur API Registry google_dns_doh
            if self.api_registry_prov.is_available():
                doh_res = self.api_registry_prov.execute(domain, {"api_name": "google_dns_doh", "lead_id": lead_id})
                if doh_res.telemetry:
                    self.hub.record(doh_res.telemetry)
                self._apply_evidences(enriched, doh_res.evidences, collected_evidences)

            # B. Validation globale DNS/MX
            dns_res = self.dns_prov.execute(domain, context)
            if dns_res.telemetry:
                self.hub.record(dns_res.telemetry)
            self._apply_evidences(enriched, dns_res.evidences, collected_evidences)

        # 4. Détection d'empreinte CMS si non déjà détectée
        if target_url and (not enriched.get("cms_detected") or enriched.get("cms_detected") == "Non détecté"):
            cms_res = self.cms_prov.execute(target_url, context)
            if cms_res.telemetry:
                self.hub.record(cms_res.telemetry)
            self._apply_evidences(enriched, cms_res.evidences, collected_evidences)

        # 5. OSINT passif via theHarvester pour public_professional_email si absent
        if domain and not enriched.get("public_professional_email"):
            th_res = self.th_prov.execute(domain, context)
            if th_res.telemetry:
                self.hub.record(th_res.telemetry)

            if th_res.is_success and th_res.has_evidences:
                # Filtrer le meilleur email (nominatif prioritaire sur générique)
                sorted_emails = sorted(
                    th_res.evidences,
                    key=lambda e: 2 if e.email_classification == EmailClassification.DECISION_MAKER_MATCHED_EMAIL.value
                    else (1 if e.email_classification == EmailClassification.INDIVIDUAL_PROFESSIONAL_EMAIL.value else 0),
                    reverse=True
                )
                self._apply_evidences(enriched, [sorted_emails[0]], collected_evidences)

        # 6. Consultation LinkedIn encadrée (ADR-008) pour dirigeant confirmé
        if (
            lead.get("matching_status") == "MATCH_CONFIRMED"
            and lead.get("decision_maker_is_person") is True
            and not enriched.get("decision_maker_linkedin_activity")
        ):
            profile_url = lead.get("linkedin_profile_url") or lead.get("decision_maker_linkedin_source")
            if profile_url and self.pw_prov.is_available():
                ctx_li = dict(context)
                ctx_li["trigger_type"] = "linkedin_consultation"
                ctx_li["field_target"] = "decision_maker_linkedin_activity"
                ctx_li["matching_status"] = "MATCH_CONFIRMED"

                pw_res = self.pw_prov.execute(profile_url, ctx_li)
                if pw_res.telemetry:
                    self.hub.record(pw_res.telemetry)
                self._apply_evidences(enriched, pw_res.evidences, collected_evidences)

        return enriched, collected_evidences

    def enrich_batch(
        self,
        leads: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Evidence]]:
        """
        Enrichit un lot de leads avec traçabilité globale et persistance d'observabilité.
        """
        enriched_leads: List[Dict[str, Any]] = []
        all_evidences: List[Evidence] = []

        for lead in leads:
            enriched, evs = self.enrich_lead(lead)
            enriched_leads.append(enriched)
            all_evidences.extend(evs)

        return enriched_leads, all_evidences
