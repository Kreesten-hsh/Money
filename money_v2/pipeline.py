from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from money_v2.contracts.evidence import Evidence
from money_v2.discovery.discovery_pipeline import DiscoveryPipeline
from money_v2.orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
from money_v2.orchestrator.observability import ObservabilityHub
from money_v2.services.ghostwriting_service import GhostwritingIntelligenceService
from money_v2.services.lead_intelligence_service import LeadIntelligenceService
from money_v2.truth.reconciliation import LegalReconciliationLayer
from money_v2.truth.truth_evaluator import TruthEvaluator


class MoneyPipelineV2:
    """
    Pipeline unifié Money V2.2 de bout en bout.
    Traite n'importe quel lot brut sans liste en dur ni cohorte figée,
    orchestre les 4 outils externes, garantit l'étanchéité légale
    et alimente les deux offres (AI Lead Intelligence + Founder Ghostwriting).
    """

    def __init__(
        self,
        observability_hub: Optional[ObservabilityHub] = None,
        orchestrator: Optional[EnrichmentOrchestrator] = None
    ):
        self.hub = observability_hub or ObservabilityHub()
        self.orchestrator = orchestrator or EnrichmentOrchestrator(observability_hub=self.hub)
        self.discovery = DiscoveryPipeline()

    def process_lead(
        self,
        lead: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Evidence]]:
        """
        Traite un lead à travers l'ensemble des couches de l'architecture.
        """
        # 1. Orchestration multi-providers (HTTP, Firecrawl, theHarvester, API Registry)
        enriched_lead, evidences = self.orchestrator.enrich_lead(lead)

        # 2. Réconciliation stricte et verrouillage d'étanchéité légale
        reconciled_lead = LegalReconciliationLayer.reconcile(enriched_lead, evidences)

        # 3. Évaluation dimensionnelle de vérité
        truth_summary = TruthEvaluator.evaluate_lead_summary(reconciled_lead)
        reconciled_lead["truth_summary"] = truth_summary

        # 4. Consolidation AI Lead Intelligence
        lead_dossier = LeadIntelligenceService.generate_intelligence_dossier(reconciled_lead)
        reconciled_lead["lead_gen_score"] = lead_dossier["lead_gen_score"]
        reconciled_lead["personalized_outreach"] = lead_dossier["outreach_draft"]

        # 5. Consolidation Founder LinkedIn Ghostwriting
        gw_dossier = GhostwritingIntelligenceService.generate_ghostwriting_dossier(reconciled_lead)
        reconciled_lead["ghostwriting_score"] = gw_dossier["ghostwriting_score"]
        reconciled_lead["ghostwriting_angles"] = gw_dossier["editorial_angles"]

        return reconciled_lead, evidences

    def process_batch(
        self,
        leads: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Evidence]]:
        """
        Exécute le pipeline complet sur un lot de leads.
        """
        processed_leads: List[Dict[str, Any]] = []
        all_evidences: List[Evidence] = []

        for lead in leads:
            p_lead, evs = self.process_lead(lead)
            processed_leads.append(p_lead)
            all_evidences.extend(evs)

        return processed_leads, all_evidences

    def run_from_raw_csv(
        self,
        raw_csv_path: Path,
        offset: int = 0,
        limit: int = 30
    ) -> Tuple[List[Dict[str, Any]], List[Evidence]]:
        """
        Point d'entrée dynamique traitant un fichier brut (ex: 340 leads Google Maps).
        """
        # 1. Découverte & Shortlisting
        shortlisted = self.discovery.process_raw_leads(raw_csv_path, max_candidates=offset + limit)
        batch = shortlisted[offset:offset + limit]

        # 2. Exécution du pipeline unifié
        return self.process_batch(batch)
