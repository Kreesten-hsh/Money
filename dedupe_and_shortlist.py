import csv
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def normalize_phone(phone: str) -> str:
    """Normalise un numéro de téléphone français pour comparaison stricte."""
    if not phone:
        return ''
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('33') and len(digits) >= 11:
        digits = '0' + digits[2:]
    return digits

def extract_domain(url: str) -> str:
    """Extrait le nom de domaine canonique sans sous-domaine www."""
    if not url:
        return ''
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urllib.parse.urlsplit(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ''

def is_web_agency_category(category: str) -> bool:
    """Filtre les catégories relatives aux agences web et créateurs de sites."""
    if not category:
        return False
    cat_lower = category.lower()
    keywords = [
        'concepteur de sites',
        'site web',
        'sites web',
        'agence web',
        'web',
        'internet',
        'digitale',
        'numérique',
        'création de site'
    ]
    return any(k in cat_lower for k in keywords)

def dedupe_and_shortlist(
    raw_path_override: Path = None,
    output_path_override: Path = None,
    exclude_path_override: Path = None,
    offset: int = 0,
    limit: int = None
):
    raw_path = raw_path_override or (BASE_DIR / 'data' / 'gmaps_agences_web_raw.csv')
    output_path = output_path_override or (BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv')

    if not raw_path.exists():
        raise FileNotFoundError(f"Fichier brut introuvable : {raw_path}")

    from money_v2.discovery.discovery_pipeline import DiscoveryPipeline

    pipeline = DiscoveryPipeline()
    seen_domains, seen_phones = pipeline.load_processed_identifiers(exclude_path_override)

    with open(raw_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Volume d'entrée brut : {len(raw_rows)} prospects.")

    final_shortlist, discarded_stats = pipeline.process_raw_dataset(
        raw_rows=raw_rows,
        exclude_domains=seen_domains,
        exclude_phones=seen_phones,
        offset=offset,
        limit=limit
    )

    if final_shortlist:
        fieldnames = list(final_shortlist[0].keys())
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_shortlist)

    print(f"Shortlist générée avec succès : {len(final_shortlist)} agences qualifiées.")
    print(f"Statistiques de rejets : {discarded_stats}")
    return final_shortlist

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Dédoublonnage & Shortlist Dynamique Money")
    parser.add_argument("--raw-csv", type=str, default=None, help="Chemin du CSV brut source")
    parser.add_argument("--output-csv", type=str, default=None, help="Chemin du CSV shortlist généré")
    parser.add_argument("--exclude-processed", type=str, default=None, help="Chemin d'un CSV de leads déjà traités pour exclusion")
    parser.add_argument("--offset", type=int, default=0, help="Offset de départ")
    parser.add_argument("--limit", type=int, default=None, help="Nombre max de leads")
    args = parser.parse_args()

    dedupe_and_shortlist(
        raw_path_override=Path(args.raw_csv) if args.raw_csv else None,
        output_path_override=Path(args.output_csv) if args.output_csv else None,
        exclude_path_override=Path(args.exclude_processed) if args.exclude_processed else None,
        offset=args.offset,
        limit=args.limit
    )
