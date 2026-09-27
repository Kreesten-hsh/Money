#!/usr/bin/env python3
"""
tests/test_v2_1_negative_suite.py — Suite de Tests Négatifs Architecture V2.1

Valide les 10 exigences négatives absolues (Section 13) :
1. Tentative d'écraser SIREN avec des données MCP -> Rejeté par SealingViolationError
2. Tentative d'écraser le dirigeant légal avec des données MCP -> Rejeté par SealingViolationError
3. Email produit sans source_url -> Rejeté par EvidenceValidationError
4. Erreur réseau convertie en NO_RESULT -> Interdit (doit être NETWORK_ERROR)
5. Timeout converti en EMPTY / NO_RESULT -> Interdit (doit être TIMEOUT)
6. Réponse API malformée -> Interdit de prétendre au succès (doit être PARSE_ERROR / UNKNOWN_ERROR)
7. Provenance absente (source ou provider vide) -> Rejeté par EvidenceValidationError
8. Évidence de crawling injectée sans source URL -> Rejeté par EvidenceValidationError
9. Email générique promu en email personnel du dirigeant sans preuve -> Rejeté par ConfidencePolicyViolationError
10. Évidence produite sans horodatage ISO complet -> Rejeté par EvidenceValidationError
"""

import json
import unittest
from typing import Any, Dict

from money_v2.contracts.confidence_policy import (
    ConfidencePolicy,
    ConfidencePolicyViolationError,
    EmailClassification,
)
from money_v2.contracts.evidence import (
    ConfidenceLevel,
    Evidence,
    EvidenceValidationError,
    ObservationMethod,
    get_current_iso_timestamp,
)
from money_v2.contracts.provider_result import ProviderResult
from money_v2.contracts.provider_status import ProviderStatus
from money_v2.providers.api_registry_provider import ApiRegistryProvider
from money_v2.providers.base import BaseProvider
from money_v2.providers.http_provider import HttpProvider
from money_v2.providers.playwright_provider import InvisiblePlaywrightProvider
from money_v2.truth.reconciliation import LegalReconciliationLayer, SealingViolationError


class TestV21NegativeSuite(unittest.TestCase):
    """Banc d'épreuve négatif pour l'architecture Money V2.1."""

    def test_01_mcp_overwrite_siren_rejected(self):
        """1. Tentative d'écraser le SIREN légal avec des données MCP -> SealingViolationError."""
        lead = {
            "lead_id": "test_lead_01",
            "siren": "123456789",
            "company_name": "Agence Légitime SAS"
        }
        corrupted_evidence = Evidence(
            field="siren",
            value="987654321",
            source="mcp_injected_data",
            source_url="http://external-mcp-source",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.BROWSER_AUTOMATION.value,
            provider="invisible_playwright_mcp",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="SIREN halluciné par scraping tiers",
            confidence=ConfidenceLevel.LOW.value,
            lead_id="test_lead_01"
        )
        with self.assertRaises(SealingViolationError) as ctx:
            LegalReconciliationLayer.reconcile(lead, [corrupted_evidence])
        self.assertIn("VIOLATION D'ÉTANCHÉITÉ", str(ctx.exception))
        self.assertIn("siren", str(ctx.exception))

    def test_02_mcp_overwrite_legal_decision_maker_rejected(self):
        """2. Tentative d'écraser le dirigeant légal avec des données MCP -> SealingViolationError."""
        lead = {
            "lead_id": "test_lead_02",
            "decision_maker": "Jean Dupont",
            "decision_maker_role": "Président"
        }
        corrupted_evidence = Evidence(
            field="decision_maker",
            value="Commercial Trouvé Sur Linkedin",
            source="linkedin_scrape",
            source_url="https://linkedin.com/in/fake",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.BROWSER_AUTOMATION.value,
            provider="invisible_playwright_mcp",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Profil trouvé au hasard",
            confidence=ConfidenceLevel.LOW.value,
            lead_id="test_lead_02"
        )
        with self.assertRaises(SealingViolationError) as ctx:
            LegalReconciliationLayer.reconcile(lead, [corrupted_evidence])
        self.assertIn("decision_maker", str(ctx.exception))

    def test_03_email_without_source_url_rejected(self):
        """3. Email produit sans source_url -> Rejeté par EvidenceValidationError."""
        with self.assertRaises(EvidenceValidationError) as ctx:
            Evidence(
                field="public_professional_email",
                value="contact@agence-test.fr",
                source="theHarvester",
                source_url="",  # Source URL vide interdite
                observed_at=get_current_iso_timestamp(),
                method=ObservationMethod.OSINT_CLI.value,
                provider="theharvester_provider",
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="Email trouvé sans traçabilité",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="test_lead_03"
            )
        self.assertIn("source_url", str(ctx.exception))

    def test_04_network_error_converted_to_no_result_rejected(self):
        """4. Erreur réseau convertie en NO_RESULT -> Interdit, doit être NETWORK_ERROR."""
        prov = HttpProvider(timeout=0.5)
        # Port inaccessible garantissant une erreur réseau
        res = prov.execute("http://127.0.0.1:59997/unreachable")
        self.assertNotEqual(res.status, ProviderStatus.NO_RESULT)
        self.assertNotEqual(res.status, ProviderStatus.SUCCESS_EMPTY)
        self.assertEqual(res.status, ProviderStatus.NETWORK_ERROR)
        self.assertTrue(res.status.is_technical_failure)

    def test_05_timeout_converted_to_empty_rejected(self):
        """5. Timeout converti en EMPTY / NO_RESULT -> Interdit, doit être TIMEOUT."""
        class StrictTimeoutProvider(BaseProvider):
            def __init__(self):
                super().__init__("mock_timeout")
            def is_available(self) -> bool:
                return True
            def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
                raise TimeoutError("Socket timeout exceeded")

        prov = StrictTimeoutProvider()
        res = prov.execute("https://slow.test")
        self.assertEqual(res.status, ProviderStatus.TIMEOUT)
        self.assertNotEqual(res.status, ProviderStatus.NO_RESULT)
        self.assertNotEqual(res.status, ProviderStatus.SUCCESS_EMPTY)
        self.assertTrue(res.status.is_technical_failure)

    def test_06_malformed_api_response_rejected(self):
        """6. Réponse API malformée -> Interdit de prétendre au succès, doit être PARSE_ERROR."""
        prov = ApiRegistryProvider()
        # Simulation d'un payload corrompu reçu d'un endpoint
        class MalformedMockApi(ApiRegistryProvider):
            def _run(self, target: str, context: Dict[str, Any]) -> ProviderResult:
                bad_response = "<html><title>502 Bad Gateway</title><body>HTML instead of JSON</body></html>"
                try:
                    json.loads(bad_response)
                except Exception as e:
                    return ProviderResult(
                        provider=self.name,
                        status=ProviderStatus.PARSE_ERROR,
                        evidences=[],
                        raw_payload={"json_parse_error": str(e)}
                    )
                return ProviderResult(provider=self.name, status=ProviderStatus.SUCCESS)

        mock = MalformedMockApi()
        res = mock.execute("test.domain", {"api_name": "google_dns_doh"})
        self.assertEqual(res.status, ProviderStatus.PARSE_ERROR)
        self.assertFalse(res.has_evidences)
        self.assertTrue(res.status.is_technical_failure)

    def test_07_missing_provenance_rejected(self):
        """7. Provenance absente (source ou provider vide) -> Rejeté par EvidenceValidationError."""
        with self.assertRaises(EvidenceValidationError) as ctx_source:
            Evidence(
                field="main_offer",
                value="Création de sites web",
                source="",  # Source vide interdite
                source_url="https://agency.fr",
                observed_at=get_current_iso_timestamp(),
                method=ObservationMethod.DOM_INSPECTION.value,
                provider="http_provider",
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="Extrait sans source",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="lead_07"
            )
        self.assertIn("source", str(ctx_source.exception))

        with self.assertRaises(EvidenceValidationError) as ctx_prov:
            Evidence(
                field="main_offer",
                value="Création de sites web",
                source="homepage",
                source_url="https://agency.fr",
                observed_at=get_current_iso_timestamp(),
                method=ObservationMethod.DOM_INSPECTION.value,
                provider="",  # Provider vide interdit
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="Extrait sans provider",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="lead_07"
            )
        self.assertIn("provider", str(ctx_prov.exception))

    def test_08_crawled_result_injected_without_source_rejected(self):
        """8. Résultat de crawling injecté sans source URL -> Rejeté par EvidenceValidationError."""
        with self.assertRaises(EvidenceValidationError) as ctx:
            Evidence(
                field="crawled_content",
                value="Contenu crawlé",
                source="batch_crawler",
                source_url="",  # Absence de source_url
                observed_at=get_current_iso_timestamp(),
                method=ObservationMethod.DOM_INSPECTION.value,
                provider="external_crawler",
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="Page crawlée",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="lead_08"
            )
        self.assertIn("source_url", str(ctx.exception))

    def test_09_generic_email_promoted_to_decision_maker_rejected(self):
        """9. Email générique promu en email de dirigeant sans preuve -> Rejeté par ConfidencePolicy."""
        generic_ev = Evidence(
            field="public_professional_email",
            value="contact@agency-digitale.fr",
            source="homepage",
            source_url="https://agency-digitale.fr",
            observed_at=get_current_iso_timestamp(),
            method=ObservationMethod.DOM_INSPECTION.value,
            provider="http_provider",
            provider_status=ProviderStatus.SUCCESS.value,
            evidence_text="Email générique trouvé en footer",
            confidence=ConfidenceLevel.MEDIUM.value,
            lead_id="lead_09",
            email_classification=EmailClassification.GENERIC_EMAIL.value
        )
        # Tentative d'affecter cet email générique comme email nominatif du dirigeant
        with self.assertRaises(ConfidencePolicyViolationError) as ctx:
            ConfidencePolicy.assert_email_promotion_allowed(generic_ev, target_role="DECISION_MAKER")
        self.assertIn("VIOLATION CONFIDENCE POLICY", str(ctx.exception))
        self.assertIn("contact@agency-digitale.fr", str(ctx.exception))

    def test_10_output_without_iso_timestamp_rejected(self):
        """10. Sortie sans horodatage ISO complet -> Rejeté par EvidenceValidationError."""
        # Cas A : horodatage vide
        with self.assertRaises(EvidenceValidationError) as ctx_empty:
            Evidence(
                field="cms_fingerprint",
                value="WordPress",
                source="wp-content",
                source_url="https://agency.fr",
                observed_at="",
                method=ObservationMethod.DOM_INSPECTION.value,
                provider="cms_provider",
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="wp-content trouvé",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="lead_10"
            )
        self.assertIn("observed_at", str(ctx_empty.exception))

        # Cas B : date non-ISO sans composante horaire
        with self.assertRaises(EvidenceValidationError) as ctx_bad:
            Evidence(
                field="cms_fingerprint",
                value="WordPress",
                source="wp-content",
                source_url="https://agency.fr",
                observed_at="2026-09-27",  # Non-ISO strict (manque le T et l'heure)
                method=ObservationMethod.DOM_INSPECTION.value,
                provider="cms_provider",
                provider_status=ProviderStatus.SUCCESS.value,
                evidence_text="wp-content trouvé",
                confidence=ConfidenceLevel.HIGH.value,
                lead_id="lead_10"
            )
        self.assertIn("observed_at", str(ctx_bad.exception))


if __name__ == "__main__":
    unittest.main()
