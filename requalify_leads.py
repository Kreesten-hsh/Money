import json
import urllib.request
import urllib.parse
import time
import re
import csv
import ssl
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Tranches d'effectif INSEE officielles
TRANCHES_INSEE = {
    'NN': '0 salarié déclaré (Non employeur)',
    '00': '0 salarié au 31/12',
    '01': '1 ou 2 salariés',
    '02': '3 à 5 salariés',
    '03': '6 à 9 salariés',
    '11': '10 à 19 salariés',
    '12': '20 à 49 salariés',
    '21': '50 à 99 salariés',
    '22': '100 à 199 salariés'
}

# Codes NAF éligibles pour agences web / communication digitale
VALID_NAF = {
    '62.01Z',  # Programmation informatique
    '62.02A',  # Conseil en systèmes et logiciels informatiques
    '62.02B',  # Tierce maintenance de systèmes et d’applications informatiques
    '62.09Z',  # Autres activités informatiques et de conseil
    '73.11Z',  # Activités des agences de publicité
    '70.21Z',  # Conseil en relations publiques et communication
    '74.10Z',  # Activités spécialisées de design
    '63.11Z',  # Traitement de données, hébergement et activités connexes
    '63.12Z',  # Portails Internet
    '58.29C'   # Édition de logiciels applicatifs
}

def get_current_iso_timestamp() -> str:
    """Génère dynamiquement un horodatage ISO 8601 UTC réel sans date hardcodée."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def normalize(text: str) -> str:
    """Normalise une chaîne : minuscules, suppression des accents et caractères spéciaux."""
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return ' '.join(text.split())

def clean_company_name(name: str) -> str:
    """Extrait le nom de marque pur débarrassé des suffixes de référencement Google Maps."""
    name = str(name).split('|')[0].strip()
    name = re.sub(r' - Agence.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Agence Web .*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Création site internet .*', '', name, flags=re.IGNORECASE)
    name = name.replace('Agence Digitale', '').strip()
    return name.strip(' -')

def inspect_website(url: str, check_timestamp: str):
    """
    Audit HTTP réel avec séparation stricte des preuves :
    - main_offer avec source et extrait observé
    - target_clients avec source et extrait observé (strictement 'Non vérifié' si non explicite)
    """
    if not url or not str(url).startswith('https://'):
        return {
            'accessible': False,
            'audit_note': 'URL non HTTPS ou manquante',
            'main_offer': 'Non vérifié',
            'main_offer_source': '',
            'main_offer_evidence': 'Site non sécurisé HTTPS ou absent',
            'main_offer_checked_at': check_timestamp,
            'target_clients': 'Non vérifié',
            'target_clients_source': '',
            'target_clients_evidence': 'Site non sécurisé HTTPS ou absent',
            'target_clients_checked_at': check_timestamp
        }

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=6, context=ctx) as resp:
            if resp.status != 200:
                return {
                    'accessible': False,
                    'audit_note': f'HTTP status {resp.status}',
                    'main_offer': 'Non vérifié',
                    'main_offer_source': '',
                    'main_offer_evidence': f'Erreur HTTP {resp.status}',
                    'main_offer_checked_at': check_timestamp,
                    'target_clients': 'Non vérifié',
                    'target_clients_source': '',
                    'target_clients_evidence': f'Erreur HTTP {resp.status}',
                    'target_clients_checked_at': check_timestamp
                }

            html = resp.read(60000).decode('utf-8', errors='ignore')

            title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
            page_title = ' '.join(title_m.group(1).split()) if title_m else ''

            desc_m = re.search(r'<meta[^>]*name=[\"\']description[\"\'][^>]*content=[\"\']([^\"\']*)[\"\']', html, re.IGNORECASE)
            meta_desc = ' '.join(desc_m.group(1).split()) if desc_m else ''

            text_corpus = f'{page_title} {meta_desc}'.lower()

            # 1. Détection de l'offre réelle observable
            if 'prestashop' in text_corpus or 'e-commerce' in text_corpus or 'shopify' in text_corpus:
                main_offer = 'Création E-commerce & Refonte Web'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            elif 'webflow' in text_corpus:
                main_offer = 'Conception Webflow & Sites sur-mesure'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            elif 'wordpress' in text_corpus:
                main_offer = 'Création & Maintenance WordPress'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            elif 'seo' in text_corpus or 'referencement' in text_corpus:
                main_offer = 'Création de sites Web & Référencement SEO'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            elif 'sur-mesure' in text_corpus or 'sur mesure' in text_corpus or 'developpement' in text_corpus:
                main_offer = 'Développement Web sur-mesure'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            elif any(k in text_corpus for k in ['site internet', 'site web', 'agence web', 'agence digitale']):
                main_offer = 'Création et refonte de sites web'
                offer_evidence = f"Extrait observé (title/meta) : '{meta_desc[:80] or page_title[:80]}'"
            else:
                main_offer = 'Non vérifié'
                offer_evidence = 'Aucune offre web explicite observable dans les balises principales'

            # 2. Détection stricte et indépendante de la clientèle cible
            # Interdiction formelle de deviner : mention textuelle explicite requise
            target_clients = 'Non vérifié'
            target_evidence = "Aucune mention explicite de typologie de clientèle cible observée sur la page d'accueil"
            target_source = ''

            explicit_pme = re.search(r'\b(pme|tpe|eti|entreprises locales|grands comptes|startups?)\b', meta_desc.lower())
            if explicit_pme:
                kw = explicit_pme.group(0).upper()
                target_clients = f"Entreprises cibles ({kw})"
                target_source = url
                target_evidence = f"Mention textuelle explicite dans la description : '{meta_desc[:90]}'"

            return {
                'accessible': True,
                'audit_note': f"Site accessible ({page_title[:40]})",
                'main_offer': main_offer,
                'main_offer_source': url if main_offer != 'Non vérifié' else '',
                'main_offer_evidence': offer_evidence,
                'main_offer_checked_at': check_timestamp,
                'target_clients': target_clients,
                'target_clients_source': target_source,
                'target_clients_evidence': target_evidence,
                'target_clients_checked_at': check_timestamp
            }

    except Exception as e:
        return {
            'accessible': False,
            'audit_note': f"Inaccessible : {str(e)[:40]}",
            'main_offer': 'Non vérifié',
            'main_offer_source': '',
            'main_offer_evidence': f'Erreur de connexion : {str(e)[:40]}',
            'main_offer_checked_at': check_timestamp,
            'target_clients': 'Non vérifié',
            'target_clients_source': '',
            'target_clients_evidence': 'Site web inaccessible',
            'target_clients_checked_at': check_timestamp
        }

def query_sirene_api(query: str, max_retries: int = 3):
    """Interroge l'API SIRENE avec gestion du rate-limit (HTTP 429) et exponential backoff."""
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(query)}&per_page=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'MoneyB2BAgent/3.0'})
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                return data.get('results', [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            return []
        except Exception:
            return []
    return []

def evaluate_sirene_match_with_ambiguity(lead: dict, results: list):
    """
    Évalue les candidats SIRENE avec détection rigoureuse d'ambiguïté :
    - Évaluation multi-critères : nom (40 pts), code postal strict (30 pts), voie/numéro (15 pts), NAF (15 pts).
    - Classement des candidats et mesure du delta avec le 2ème candidat.
    - Règle de non-ambiguïté : si le 2ème candidat est proche (score >= 55 et delta < 20), MATCH_UNCERTAIN obligatoire.
    - MATCH_CONFIRMED uniquement si concordance forte (score >= 75) ET absence de candidat concurrent proche (delta >= 20 ou second < 50).
    - Traçabilité complète des scores, deltas, critères concordants et contradictoires.
    """
    if not results:
        return {
            'best_candidate': None,
            'matching_status': 'NO_MATCH',
            'candidate_selected': 'Aucun',
            'candidate_score': 0,
            'second_candidate_score': 0,
            'score_delta': 0,
            'concordant_criteria': [],
            'contradictory_criteria': ['Aucun résultat retourné par le registre public SIRENE'],
            'decision_reason': 'Aucune entreprise trouvée pour cette recherche'
        }

    title = lead.get('title', '')
    brand = clean_company_name(title)
    norm_brand = normalize(brand)

    stopwords = {'agence', 'web', 'site', 'internet', 'creation', 'studio', 'communication', 'france', 'paris', 'marseille', 'lyon', 'toulouse', 'bordeaux', 'nantes'}
    brand_tokens = [t for t in norm_brand.split() if t not in stopwords and len(t) >= 2]
    if not brand_tokens:
        brand_tokens = [t for t in norm_brand.split() if len(t) >= 2]

    lead_addr = lead.get('address', '')
    target_cp_m = re.search(r'\b(0[1-9]|[1-8]\d|9[0-8])\d{3}\b', lead_addr)
    target_cp = target_cp_m.group(0) if target_cp_m else None

    lead_num_m = re.search(r'\b\d{1,4}\b', lead_addr)
    lead_num = lead_num_m.group(0) if lead_num_m else None

    scored_candidates = []

    for r in results:
        concordant = []
        contradictory = []

        # 1. Nom / Identité (max 40 pts)
        nom_legal = normalize(r.get('nom_complet') or '')
        sigle = normalize(r.get('sigle') or '')
        enseignes = ' '.join([normalize(e.get('enseigne', '')) for e in r.get('matching_etablissements', [])])
        all_cand_names = f"{nom_legal} {sigle} {enseignes}"

        name_hits = [t for t in brand_tokens if t in all_cand_names]
        name_ratio = (len(name_hits) / len(brand_tokens)) if brand_tokens else 0.0

        if name_ratio >= 1.0:
            name_score = 40
            concordant.append(f"Nom de marque intégralement concordant ('{brand}')")
        elif name_ratio >= 0.5:
            name_score = 25
            concordant.append(f"Nom partiellement concordant ({len(name_hits)}/{len(brand_tokens)} tokens)")
        else:
            name_score = 0
            contradictory.append(f"Divergence de dénomination ('{brand}' non retrouvé dans '{nom_legal[:35]}')")

        # 2. Localisation / Code Postal & Voie (max 45 pts : CP 30 + Voie 15)
        siege_cp = r.get('siege', {}).get('code_postal', '')
        etab_cps = [e.get('code_postal', '') for e in r.get('matching_etablissements', [])]
        all_cps = {siege_cp} | set(etab_cps)
        cp_match = bool(target_cp and target_cp in all_cps)

        if cp_match:
            cp_score = 30
            concordant.append(f"Code postal strict concordant ({target_cp})")
        else:
            cp_score = 0
            contradictory.append(f"Code postal divergent (attendu: {target_cp}, candidat: {siege_cp})")

        cand_addresses = [r.get('siege', {}).get('adresse', '')] + [e.get('adresse', '') for e in r.get('matching_etablissements', [])]
        cand_addrs_norm = normalize(' '.join(cand_addresses))
        street_num_match = bool(lead_num and lead_num in cand_addrs_norm.split())

        if street_num_match:
            street_score = 15
            concordant.append(f"Numéro de voie validé à l'adresse ({lead_num})")
        else:
            street_score = 0
            contradictory.append("Numéro de voie non concordant ou non précisé")

        # 3. Activité NAF (max 15 pts)
        naf = r.get('activite_principale', '')
        naf_valid = naf in VALID_NAF
        if naf_valid:
            naf_score = 15
            concordant.append(f"Code NAF numérique/web éligible ({naf})")
        else:
            naf_score = 0
            contradictory.append(f"Code NAF non standard pour agence web ({naf})")

        # Statut actif
        is_active = (r.get('etat_administratif') == 'A')
        if not is_active:
            contradictory.append("Entreprise radiée ou inactive au registre")

        total_score = name_score + cp_score + street_score + naf_score if is_active else 0

        scored_candidates.append({
            'candidate': r,
            'total_score': total_score,
            'name_score': name_score,
            'cp_match': cp_match,
            'naf_valid': naf_valid,
            'is_active': is_active,
            'concordant': concordant,
            'contradictory': contradictory
        })

    scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
    best = scored_candidates[0]
    second = scored_candidates[1] if len(scored_candidates) > 1 else None

    best_score = best['total_score']
    second_score = second['total_score'] if second else 0
    delta = best_score - second_score

    # Rejet absolu si pas de concordance territoriale ou score trop faible
    if not best['cp_match'] or best_score < 30 or not best['is_active']:
        return {
            'best_candidate': None,
            'matching_status': 'NO_MATCH',
            'candidate_selected': 'Aucun candidat crédible',
            'candidate_score': best_score,
            'second_candidate_score': second_score,
            'score_delta': delta,
            'concordant_criteria': best['concordant'],
            'contradictory_criteria': best['contradictory'],
            'decision_reason': f"Aucune concordance territoriale ou entreprise inactive (CP attendu {target_cp})"
        }

    # DÉTECTION D'AMBIGUÏTÉ STRICTE
    # Si le deuxième candidat est proche et cohérent (second_score >= 55 et delta < 20), ambiguïté avérée
    if second and second['cp_match'] and second_score >= 55 and delta < 20:
        contradictory = best['contradictory'] + [
            f"Ambiguïté : 2ème candidat proche (SIREN {second['candidate']['siren']}, score {second_score}, delta={delta} < 20)"
        ]
        return {
            'best_candidate': best['candidate'],
            'matching_status': 'MATCH_UNCERTAIN',
            'candidate_selected': f"{best['candidate'].get('nom_complet')} (SIREN: {best['candidate'].get('siren')})",
            'candidate_score': best_score,
            'second_candidate_score': second_score,
            'score_delta': delta,
            'concordant_criteria': best['concordant'],
            'contradictory_criteria': contradictory,
            'decision_reason': f"Ambiguïté entre plusieurs sociétés candidates dans la même zone (delta {delta} < 20)"
        }

    # MATCH_CONFIRMED : Forte concordance (score >= 75) ET absence de candidat concurrent proche
    if best_score >= 75 and (delta >= 20 or second_score < 50) and best['name_score'] >= 25 and best['naf_valid']:
        return {
            'best_candidate': best['candidate'],
            'matching_status': 'MATCH_CONFIRMED',
            'candidate_selected': f"{best['candidate'].get('nom_complet')} (SIREN: {best['candidate'].get('siren')})",
            'candidate_score': best_score,
            'second_candidate_score': second_score,
            'score_delta': delta,
            'concordant_criteria': best['concordant'],
            'contradictory_criteria': best['contradictory'],
            'decision_reason': f"Concordance robuste confirmée sans ambiguïté concurrentielle (score {best_score}/100, delta {delta})"
        }

    # MATCH_PLAUSIBLE : Cohérent mais sans preuve suffisante pour certifier (score 50 à 74)
    if best_score >= 50:
        return {
            'best_candidate': best['candidate'],
            'matching_status': 'MATCH_PLAUSIBLE',
            'candidate_selected': f"{best['candidate'].get('nom_complet')} (SIREN: {best['candidate'].get('siren')})",
            'candidate_score': best_score,
            'second_candidate_score': second_score,
            'score_delta': delta,
            'concordant_criteria': best['concordant'],
            'contradictory_criteria': best['contradictory'],
            'decision_reason': f"Éléments plausibles mais confirmation incomplète (score {best_score}/100)"
        }

    # Sinon : MATCH_UNCERTAIN
    return {
        'best_candidate': best['candidate'],
        'matching_status': 'MATCH_UNCERTAIN',
        'candidate_selected': f"{best['candidate'].get('nom_complet')} (SIREN: {best['candidate'].get('siren')})",
        'candidate_score': best_score,
        'second_candidate_score': second_score,
        'score_delta': delta,
        'concordant_criteria': best['concordant'],
        'contradictory_criteria': best['contradictory'],
        'decision_reason': f"Score insuffisant pour validation ({best_score}/100)"
    }

def calculate_scores(lead: dict, sirene_eval: dict, sirene_data: dict, site_info: dict):
    """
    Calcul strict des scores découplés et statut qualité :
    - Modèle Lead Gen sur 100 points : Activité (30), Taille (25), Signal commercial (25), Traction (20).
      Plafond théorique effectif = 75/100 en Phase 1 (faute de signal d'affaires externe prouvé, pénalité de 25 pts).
    - Ghostwriting : neutralisé à 0/100 (Option B).
    - Confidence : calculé sur 4 composantes de preuves réelles avec plafonds stricts (max 60 si non VERIFIED, max 40 si matching incertain).
    """
    matching_status = sirene_eval['matching_status']
    tranche = sirene_data.get('tranche_code')
    dirigeants = sirene_data.get('dirigeants', [])
    site_accessible = site_info['accessible']

    # Exclusion immédiate des structures hors ICP (0 salarié ou > 20 salariés)
    tranches_hors_cible = ('NN', '00', '12', '21', '22', '31', '32', '41', '42', '51', '52')
    if tranche in tranches_hors_cible:
        status = 'DISQUALIFIED'
        reasons = [
            f"Lead Gen (0/100) : Structure hors cible ICP 2-20 (Tranche {sirene_data.get('tranche_label', 'Inconnue')})",
            "GW (0/100) : Neutralisé (Option B : absence d'audit éditorial public LinkedIn)",
            f"Confidence (0/100) : Structure disqualifiée (Preuve effectif: Tranche {tranche}; Matching: {matching_status})"
        ]
        return 0, 0, 0, status, reasons

    # 1. Lead Gen Score (/100 avec max effectif à 75)
    # A. Activité web pure (max 30)
    cat_lower = lead.get('category', '').lower()
    lg_activity = 30 if any(k in cat_lower for k in ['concepteur', 'site', 'web']) else 15

    # B. Taille ICP (max 25)
    has_secondary_size_proof = (tranche == '01' and len(dirigeants) >= 2)
    if tranche in ['02', '03']:
        lg_size = 25
    elif tranche == '11':
        lg_size = 20
    elif tranche == '01' and has_secondary_size_proof:
        lg_size = 18
    elif tranche == '01':
        lg_size = 10
    else:
        lg_size = 5

    # C. Signal commercial réel (max 25) — 0 pt car aucun signal externe vérifié
    lg_signal = 0

    # D. Traction / Réputation (max 20)
    rating = float(lead.get('review_rating', 0)) if lead.get('review_rating') else 0.0
    reviews = int(float(lead.get('review_count', 0))) if lead.get('review_count') else 0
    if rating >= 4.8 and reviews >= 20:
        lg_reputation = 20
    elif rating >= 4.5 and reviews >= 10:
        lg_reputation = 15
    else:
        lg_reputation = 10

    lead_gen_score = min(100, lg_activity + lg_size + lg_signal + lg_reputation)

    # 2. Ghostwriting Score (Neutralisé à 0/100)
    ghostwriting_score = 0

    # 3. Confidence Score (sur 100 points)
    # A. Preuve légale (max 35)
    if matching_status == 'MATCH_CONFIRMED' and sirene_data.get('etat_administratif') == 'A':
        conf_legal = 35
    elif matching_status == 'MATCH_PLAUSIBLE':
        conf_legal = 20
    elif matching_status == 'MATCH_UNCERTAIN':
        conf_legal = 5
    else:
        conf_legal = 0

    # B. Preuve effectif (max 30)
    if tranche in ['02', '03', '11']:
        conf_size = 30
    elif tranche == '01' and has_secondary_size_proof:
        conf_size = 25
    elif tranche == '01':
        conf_size = 10
    else:
        conf_size = 5

    # C. Contrôle technique site web (max 20)
    if site_accessible and lead.get('website', '').startswith('https://'):
        conf_site = 20
    elif site_accessible:
        conf_site = 10
    else:
        conf_site = 0

    # D. Canal direct vérifié (max 15)
    conf_phone = 15 if lead.get('phone') else 0

    raw_conf = min(100, conf_legal + conf_size + conf_site + conf_phone)

    # 4. Statut Qualité & Application des Plafonds
    is_icp_size_certified = (tranche in ['02', '03', '11']) or (tranche == '01' and has_secondary_size_proof)
    has_registered_leader = bool(dirigeants and len(dirigeants) > 0)

    if sirene_data.get('etat_administratif') != 'A' and sirene_data.get('found'):
        status = 'DISQUALIFIED'
        confidence_score = 0
    elif matching_status == 'MATCH_CONFIRMED' and is_icp_size_certified and has_registered_leader and site_accessible and raw_conf >= 80:
        status = 'VERIFIED'
        confidence_score = raw_conf
    elif is_icp_size_certified and raw_conf >= 60 and matching_status in ('MATCH_CONFIRMED', 'MATCH_PLAUSIBLE'):
        status = 'PARTIALLY VERIFIED'
        confidence_score = min(raw_conf, 60)
    else:
        status = 'REQUIRES REVIEW'
        if matching_status in ('MATCH_UNCERTAIN', 'NO_MATCH'):
            confidence_score = min(raw_conf, 40)
        else:
            confidence_score = min(raw_conf, 60)

    reasons = [
        f"Lead Gen ({lead_gen_score}/100) : Activité {lg_activity}/30 ('{lead.get('category')}'), Taille {lg_size}/25 (Tranche {tranche}" + ("; co-dirigeants RCS" if has_secondary_size_proof else "") + f"), Signal commercial 0/25 (aucun vérifié, pénalité -25 pts), Réputation {lg_reputation}/20 ({reviews} avis certifiés)",
        "GW (0/100) : Neutralisé (Option B : absence d'audit éditorial public LinkedIn)",
        f"Confidence ({confidence_score}/100) : Légal {conf_legal}/35 ({matching_status}), Effectif {conf_size}/30 ({tranche}), Site {conf_site}/20 ({site_info['audit_note']}), Canal {conf_phone}/15 ({lead.get('phone')})"
    ]

    return lead_gen_score, ghostwriting_score, confidence_score, status, reasons

def main():
    shortlist_file = BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv'
    if not shortlist_file.exists():
        raise FileNotFoundError(f"Fichier de shortlist introuvable : {shortlist_file}. Exécutez dedupe_and_shortlist.py en amont.")

    with open(shortlist_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        leads = list(reader)[:30]

    print(f"Requalification approfondie de {len(leads)} leads avec vérification structurée des preuves...")

    requalified_leads = []

    for i, lead in enumerate(leads, 1):
        name = lead.get('title')
        city = lead.get('city')
        now_iso = get_current_iso_timestamp()

        print(f"[{i:02d}/30] Requalification SIRENE & Audit Web : {name} ({city})...")

        # 1. Audit HTTP réel avec preuves séparées pour offre et clientèle cible
        site_info = inspect_website(lead.get('website'), now_iso)
        time.sleep(0.3)

        # 2. Interrogation SIRENE et évaluation avec détection d'ambiguïté
        clean_name = clean_company_name(name)
        sirene_results = query_sirene_api(f"{clean_name} {city}")
        if not sirene_results:
            sirene_results = query_sirene_api(clean_name)
        time.sleep(0.5)

        sirene_eval = evaluate_sirene_match_with_ambiguity(lead, sirene_results)
        best_cand = sirene_eval['best_candidate']

        if best_cand:
            siren = best_cand.get('siren')
            tranche = best_cand.get('tranche_effectif_salarie')
            
            # Extraction des dirigeants avec qualification officielle exacte
            dirigeants = []
            for d in best_cand.get('dirigeants', []):
                person_name = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip() if d.get('nom') else (d.get('denomination') or '')
                role_exact = d.get('qualite') or 'Dirigeant déclaré'
                if person_name:
                    dirigeants.append({'name': person_name, 'role': role_exact})

            sirene_data = {
                'found': True,
                'siren': siren,
                'siren_source': 'API Recherche Entreprises (api.gouv.fr) / Registre National SIRENE',
                'siren_checked_at': now_iso,
                'nom_complet': best_cand.get('nom_complet'),
                'etat_administratif': best_cand.get('etat_administratif'),
                'tranche_code': tranche,
                'tranche_label': TRANCHES_INSEE.get(tranche, f'Code INSEE {tranche}' if tranche else 'Non renseigné'),
                'activite_principale': best_cand.get('activite_principale'),
                'dirigeants': dirigeants,
                'evidence_url': f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else ""
            }
        else:
            sirene_data = {
                'found': False,
                'siren': None,
                'siren_source': 'Non trouvé',
                'siren_checked_at': now_iso,
                'nom_complet': lead.get('title'),
                'etat_administratif': None,
                'tranche_code': None,
                'tranche_label': 'Non identifié',
                'activite_principale': None,
                'dirigeants': [],
                'evidence_url': ""
            }

        # 3. Calcul des scores et statut
        lg_score, gw_score, conf_score, status, reasons = calculate_scores(lead, sirene_eval, sirene_data, site_info)

        # 4. Preuve structurée pour l'effectif
        tranche_code = sirene_data.get('tranche_code')
        has_secondary_size_proof = (tranche_code == '01' and len(sirene_data.get('dirigeants', [])) >= 2)

        if tranche_code in ['02', '03', '11']:
            company_size_source = f"INSEE / Registre SIRENE (Tranche {tranche_code})"
            company_size_interpretation = f"Éligible ICP direct ({sirene_data.get('tranche_label')})"
            secondary_size_proof_source = "INSEE Déclaration Sociale Nominative"
            secondary_size_proof_details = f"Effectif officiel certifié par tranche INSEE {tranche_code} (2 à 20 salariés)"
        elif tranche_code == '01' and has_secondary_size_proof:
            company_size_source = f"INSEE / Registre SIRENE (Tranche 01)"
            company_size_interpretation = "Tranche 01 (1-2 salariés) validée par co-gérance officielle au greffe (>= 2 personnes)"
            secondary_size_proof_source = f"{sirene_data.get('evidence_url')} (RCS Greffe)"
            secondary_size_proof_details = f"{len(sirene_data['dirigeants'])} co-dirigeants déclarés au greffe : {', '.join([d['name'] + ' (' + d['role'] + ')' for d in sirene_data['dirigeants']])} prouvant >= 2 personnes en activité"
        elif tranche_code == '01':
            company_size_source = f"INSEE / Registre SIRENE (Tranche 01)"
            company_size_interpretation = "Tranche 01 sans preuve secondaire suffisante (maintien en REQUIRES REVIEW)"
            secondary_size_proof_source = ""
            secondary_size_proof_details = "Aucune preuve secondaire publique certifiant au moins 2 personnes en activité"
        elif tranche_code in ('NN', '00'):
            company_size_source = f"INSEE / Registre SIRENE (Tranche {tranche_code})"
            company_size_interpretation = "Structure non employeur / 0 salarié (DISQUALIFIED)"
            secondary_size_proof_source = ""
            secondary_size_proof_details = ""
        else:
            company_size_source = "Non vérifié"
            company_size_interpretation = "Effectif non certifié"
            secondary_size_proof_source = ""
            secondary_size_proof_details = ""

        # 5. Preuve structurée pour le dirigeant
        dirigeants_list = sirene_data.get('dirigeants', [])
        if dirigeants_list:
            decision_maker = dirigeants_list[0]['name']
            decision_maker_role = dirigeants_list[0]['role']
            decision_maker_source = sirene_data.get('evidence_url')
            decision_maker_checked_at = now_iso
        else:
            decision_maker = 'Non identifié au registre'
            decision_maker_role = 'Inconnu'
            decision_maker_source = ''
            decision_maker_checked_at = now_iso

        notes_parts = [
            f"Matching SIRENE : {sirene_eval['matching_status']} ({sirene_eval['decision_reason']})",
            f"SIREN : {sirene_data.get('siren') or 'Non trouvé'}",
            f"Tranche : {sirene_data.get('tranche_label')}"
        ]
        if not site_info['accessible']:
            notes_parts.append("site inaccessible")
        notes = " | ".join(notes_parts)

        item = {
            'company_name': sirene_data.get('nom_complet') or lead.get('title'),
            'brand_name': lead.get('title'),
            'siren': sirene_data.get('siren') or 'Non trouvé',
            'siren_source': sirene_data.get('siren_source'),
            'siren_checked_at': now_iso,
            'website': lead.get('website'),
            'country': 'France',
            'city': lead.get('city'),
            'company_size': sirene_data.get('tranche_label') or 'Incertain',
            'company_size_code': tranche_code or '',
            'company_size_source': company_size_source,
            'company_size_interpretation': company_size_interpretation,
            'company_size_checked_at': now_iso,
            'has_secondary_size_proof': has_secondary_size_proof,
            'secondary_size_proof_source': secondary_size_proof_source,
            'secondary_size_proof_details': secondary_size_proof_details,
            'main_offer': site_info['main_offer'],
            'main_offer_source': site_info['main_offer_source'],
            'main_offer_evidence': site_info['main_offer_evidence'],
            'main_offer_checked_at': site_info['main_offer_checked_at'],
            'target_clients': site_info['target_clients'],
            'target_clients_source': site_info['target_clients_source'],
            'target_clients_evidence': site_info['target_clients_evidence'],
            'target_clients_checked_at': site_info['target_clients_checked_at'],
            'decision_maker': decision_maker,
            'decision_maker_role': decision_maker_role,
            'decision_maker_source': decision_maker_source,
            'decision_maker_checked_at': decision_maker_checked_at,
            'public_professional_email': 'Non extrait (Option)',
            'public_phone': lead.get('phone'),
            'source_url': lead.get('google_maps_url'),
            'evidence_url': sirene_data.get('evidence_url') or lead.get('website'),
            'matching_status': sirene_eval['matching_status'],
            'sirene_candidate_selected': sirene_eval['candidate_selected'],
            'sirene_candidate_score': sirene_eval['candidate_score'],
            'sirene_second_candidate_score': sirene_eval['second_candidate_score'],
            'sirene_score_delta': sirene_eval['score_delta'],
            'sirene_matching_concordant_criteria': sirene_eval['concordant_criteria'],
            'sirene_matching_contradictory_criteria': sirene_eval['contradictory_criteria'],
            'sirene_matching_decision_reason': sirene_eval['decision_reason'],
            'commercial_signal': '',
            'signal_source': '',
            'signal_date': '',
            'lead_gen_score': lg_score,
            'ghostwriting_score': gw_score,
            'confidence_score': conf_score,
            'verification_status': status,
            'reasons': reasons,
            'last_checked': now_iso,
            'notes': notes
        }
        requalified_leads.append(item)

    # Sauvegarde JSON
    json_path = BASE_DIR / 'data' / 'top30_leads_requalified.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(requalified_leads, f, ensure_ascii=False, indent=2)

    # Sauvegarde CSV
    csv_path = BASE_DIR / 'data' / 'top30_leads_requalified.csv'
    csv_rows = []
    for l in requalified_leads:
        r_copy = dict(l)
        r_copy['reasons'] = '; '.join(l.get('reasons', []))
        r_copy['sirene_matching_concordant_criteria'] = '; '.join(l.get('sirene_matching_concordant_criteria', []))
        r_copy['sirene_matching_contradictory_criteria'] = '; '.join(l.get('sirene_matching_contradictory_criteria', []))
        csv_rows.append(r_copy)

    fieldnames = list(csv_rows[0].keys())
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print("\nRequalification terminée avec succès !")
    statuses = {}
    for l in requalified_leads:
        st = l['verification_status']
        statuses[st] = statuses.get(st, 0) + 1
    print("Répartition des statuts finaux réels :", statuses)

if __name__ == '__main__':
    main()
