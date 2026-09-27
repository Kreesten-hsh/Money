from __future__ import annotations

import csv
import re
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def normalize_phone(phone: str) -> str:
    """Normalise un numéro de téléphone français pour comparaison stricte."""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("33") and len(digits) >= 11:
        digits = "0" + digits[2:]
    return digits


def extract_canonical_domain(url: str) -> str:
    """Extrait le nom de domaine canonique sans sous-domaine www."""
    if not url:
        return ""
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urllib.parse.urlsplit(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc.split(":")[0]
    except Exception:
        return ""


def is_web_agency_category(category: str, custom_keywords: Optional[List[str]] = None) -> bool:
    """Filtre les catégories relatives aux agences web et créateurs de sites."""
    if not category:
        return False
    cat_lower = category.lower()
    keywords = custom_keywords or [
        "concepteur de sites",
        "site web",
        "sites web",
        "agence web",
        "web",
        "internet",
        "digitale",
        "numérique",
        "création de site"
    ]
    return any(k in cat_lower for k in keywords)


class DiscoveryPipeline:
    """
    Pipeline de découverte et de constitution de shortlist dynamique.
    Supporte :
    - Fichiers d'entrée arbitraires (nouvelles villes, nouveaux crawls).
    - Exclusion des leads déjà traités pour les runs itératifs.
    - Pagination et découpage en batchs sans modifier le code source.
    - Ordonnancement objectif indépendant de listes fermées.
    """

    def __init__(self, custom_keywords: Optional[List[str]] = None):
        self.custom_keywords = custom_keywords

    def load_processed_identifiers(self, processed_file_path: Optional[Path]) -> Tuple[Set[str], Set[str]]:
        """Charge les domaines et téléphones déjà traités pour exclusion stricte."""
        seen_domains: Set[str] = set()
        seen_phones: Set[str] = set()

        if not processed_file_path or not processed_file_path.exists():
            return seen_domains, seen_phones

        try:
            with open(processed_file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dom = extract_canonical_domain(row.get("website") or row.get("domain") or "")
                    if dom:
                        seen_domains.add(dom)
                    ph = normalize_phone(row.get("phone") or "")
                    if ph:
                        seen_phones.add(ph)
        except Exception:
            pass

        return seen_domains, seen_phones

    def process_raw_dataset(
        self,
        raw_rows: List[Dict[str, Any]],
        exclude_domains: Optional[Set[str]] = None,
        exclude_phones: Optional[Set[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Dédoublonne et ordonne un flux brut de prospects Google Maps.
        """
        seen_domains = set(exclude_domains or set())
        seen_phones = set(exclude_phones or set())
        shortlisted: List[Dict[str, Any]] = []

        discarded_stats = {
            "no_website": 0,
            "non_web_category": 0,
            "duplicate_domain": 0,
            "duplicate_phone": 0,
            "already_processed": 0
        }

        for row in raw_rows:
            website = (row.get("website") or "").strip()
            phone = (row.get("phone") or "").strip()
            category = (row.get("category") or "").strip()

            if not website:
                discarded_stats["no_website"] += 1
                continue

            if not is_web_agency_category(category, self.custom_keywords):
                discarded_stats["non_web_category"] += 1
                continue

            domain = extract_canonical_domain(website)
            if not domain:
                discarded_stats["no_website"] += 1
                continue

            if domain in seen_domains:
                if exclude_domains and domain in exclude_domains:
                    discarded_stats["already_processed"] += 1
                else:
                    discarded_stats["duplicate_domain"] += 1
                continue
            seen_domains.add(domain)

            norm_ph = normalize_phone(phone)
            if norm_ph:
                if norm_ph in seen_phones:
                    if exclude_phones and norm_ph in exclude_phones:
                        discarded_stats["already_processed"] += 1
                    else:
                        discarded_stats["duplicate_phone"] += 1
                    continue
                seen_phones.add(norm_ph)

            shortlisted.append(row)

        # Ordonnancement objectif et déterministe
        shortlisted.sort(
            key=lambda x: (
                -int(float(x.get("review_count", 0) or 0)),
                -float(x.get("review_rating", 0) or 0),
                (x.get("title", "") or "").strip().lower()
            )
        )

        # Pagination dynamique
        total_shortlisted = len(shortlisted)
        start = max(0, offset)
        end = (start + limit) if limit is not None else total_shortlisted
        paginated_shortlist = shortlisted[start:end]

        return paginated_shortlist, discarded_stats
