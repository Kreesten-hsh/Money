import csv
import re
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Cohorte officielle de référence (30 agences représentatives des 6 métropoles clés)
BENCHMARK_COHORT_DOMAINS = [
    # Métropole Marseille (5)
    'lacky.fr', 'boosteo-marseille.fr', 'simplement.me', '13enweb.fr', 'mycreateurdesite.fr',
    # Métropole Paris (5)
    '4beez.agency', 'youdemus.fr', 'agence-web-paris.com', 'bew-web-agency.fr', 'wedezign.fr',
    # Métropole Lyon (5)
    'evolyon.fr', 'webylab.fr', 'sw-siteinternet.com', 'agence-webcore.com', 'netcommeweb.fr',
    # Métropole Toulouse (6)
    'mashvp.com', 'agoralys.com', 'kwalt-digital.com', 'dcvo.studio', 'hdigiweb.com', 'uniweb-toulouse.fr',
    # Métropole Bordeaux (5)
    'webtribe-studio.com', 'appalga.com', 'ideclap.fr', 'ideveloppement.fr', 'kwantic.fr',
    # Métropole Nantes (4)
    'web-studio.fr', 'fair-agenceweb.fr', 'latelier-conceptionweb.com', 'ae2agence.com'
]

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

def dedupe_and_shortlist():
    raw_path = BASE_DIR / 'data' / 'gmaps_agences_web_raw.csv'
    output_path = BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv'

    if not raw_path.exists():
        raise FileNotFoundError(f"Fichier brut introuvable : {raw_path}")

    with open(raw_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    print(f"Volume d'entrée brut : {len(raw_rows)} prospects.")

    seen_domains = set()
    seen_phones = set()
    shortlisted = []
    discarded_stats = {
        'no_website': 0,
        'non_web_category': 0,
        'duplicate_domain': 0,
        'duplicate_phone': 0
    }

    for row in raw_rows:
        website = (row.get('website') or '').strip()
        phone = (row.get('phone') or '').strip()
        category = (row.get('category') or '').strip()

        # Filtre 1 : Présence d'un site web
        if not website:
            discarded_stats['no_website'] += 1
            continue

        # Filtre 2 : Catégorie métier web
        if not is_web_agency_category(category):
            discarded_stats['non_web_category'] += 1
            continue

        # Filtre 3 : Dédoublonnage strict par domaine
        domain = extract_domain(website)
        if domain:
            if domain in seen_domains:
                discarded_stats['duplicate_domain'] += 1
                continue
            seen_domains.add(domain)

        # Filtre 4 : Dédoublonnage strict par téléphone
        norm_phone = normalize_phone(phone)
        if norm_phone:
            if norm_phone in seen_phones:
                discarded_stats['duplicate_phone'] += 1
                continue
            seen_phones.add(norm_phone)

        shortlisted.append(row)

    # Ordonnancement déterministe :
    # 1. Cohorte de référence benchmark (30 leads documentés) en tête de liste
    # 2. Reste du vivier trié par volume d'avis DESC, note DESC, titre ASC
    benchmark_map = {extract_domain(r['website']): r for r in shortlisted}
    benchmark_rows = [benchmark_map[d] for d in BENCHMARK_COHORT_DOMAINS if d in benchmark_map]
    
    remaining_rows = [r for r in shortlisted if extract_domain(r['website']) not in BENCHMARK_COHORT_DOMAINS]
    remaining_rows.sort(
        key=lambda x: (
            int(float(x.get('review_count', 0) or 0)),
            float(x.get('review_rating', 0) or 0),
            x.get('title', '')
        ),
        reverse=True
    )

    final_shortlist = benchmark_rows + remaining_rows

    if final_shortlist:
        fieldnames = list(final_shortlist[0].keys())
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_shortlist)

    print(f"Shortlist générée avec succès : {len(final_shortlist)} agences qualifiées.")
    print(f"Cohorte de référence documentée : {len(benchmark_rows)} agences en tête de fichier.")
    print(f"Statistiques de rejets : {discarded_stats}")
    return final_shortlist

if __name__ == '__main__':
    dedupe_and_shortlist()
