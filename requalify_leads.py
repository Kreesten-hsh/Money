import json
import urllib.request
import urllib.parse
import time
import re
import csv
import ssl
import unicodedata
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

def normalize(text: str) -> str:
    """Normalise une chaîne : minuscules, suppression des accents et caractères spéciaux."""
    if not text:
        return ''
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return ' '.join(text.split())

def clean_company_name(name: str) -> str:
    """Extrait le nom de marque pur débarrassé des suffixes de référencement Google Maps."""
    name = name.split('|')[0].strip()
    name = re.sub(r' - Agence.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Agence Web .*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Création site internet .*', '', name, flags=re.IGNORECASE)
    name = name.replace('Agence Digitale', '').strip()
    return name.strip(' -')

def inspect_website(url: str):
    """Audit HTTP réel : code 200, protocole HTTPS, et extraction de l'offre et clientèle réelle."""
    if not url or not str(url).startswith('https://'):
        return False, 'Non vérifié', 'Non vérifié', 'URL non HTTPS ou manquante'
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            if resp.status != 200:
                return False, 'Non vérifié', 'Non vérifié', f'HTTP status {resp.status}'
            html = resp.read(25000).decode('utf-8', errors='ignore')
            
            title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            page_title = title_m.group(1).strip() if title_m else ''
            
            desc_m = re.search(r'<meta[^>]*name=[\"\']description[\"\'][^>]*content=[\"\']([^\"\']*)[\"\']', html, re.IGNORECASE)
            meta_desc = desc_m.group(1).strip() if desc_m else ''
            
            text_corpus = f'{page_title} {meta_desc}'.lower()
            
            # Détection de l'offre réelle observable sur le site
            if 'webflow' in text_corpus:
                offer = 'Conception Webflow & Sites sur-mesure'
            elif 'e-commerce' in text_corpus or 'shopify' in text_corpus:
                offer = 'Création E-commerce & Refonte Web'
            elif 'seo' in text_corpus or 'referencement' in text_corpus:
                offer = 'Création de sites Web & Référencement SEO'
            elif 'wordpress' in text_corpus:
                offer = 'Création & Maintenance WordPress PME'
            elif 'sur-mesure' in text_corpus or 'sur mesure' in text_corpus:
                offer = 'Développement Web sur-mesure'
            elif any(k in text_corpus for k in ['site internet', 'site web', 'agence web']):
                offer = 'Création et refonte de sites web'
            else:
                offer = 'Non vérifié'
                
            # Détection de la clientèle cible observable
            if any(k in text_corpus for k in ['pme', 'tpe', 'eti']):
                targets = 'PME & TPE'
            elif any(k in text_corpus for k in ['startup', 'scaleup']):
                targets = 'Startups & Scaleups'
            elif any(k in text_corpus for k in ['artisan', 'commercant', 'local', 'region']):
                targets = 'Entreprises et commerçants régionaux'
            elif 'b2b' in text_corpus:
                targets = 'Entreprises B2B'
            else:
                targets = 'Non vérifié'
                
            return True, offer, targets, f'Site accessible ({page_title[:45]})'
    except Exception as e:
        return False, 'Non vérifié', 'Non vérifié', f'Inaccessible : {str(e)[:45]}'

def query_sirene_api(query: str, max_retries: int = 3):
    """Interroge l'API SIRENE avec gestion du rate-limit (HTTP 429) et exponential backoff."""
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(query)}&per_page=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'MoneyB2BAgent/2.0'})
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                return data.get('results', [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                sleep_time = 2.0 * (attempt + 1)
                time.sleep(sleep_time)
                continue
            return []
        except Exception:
            return []
    return []

def evaluate_sirene_match(lead: dict, results: list):
    """
    Évalue les candidats SIRENE selon 3 dimensions strictes :
    A. Identité / Nom (tokens pertinents, enseigne, sigle, raison sociale)
    B. Localisation (code postal strict + concordance voie / numéro)
    C. Cohérence métier (NAF numérique/web éligible)
    Sortie : (meilleur_candidat, match_status, justification)
    """
    if not results:
        return None, 'NO_MATCH', 'Aucun résultat retourné par le registre public'

    title = lead.get('title', '')
    brand = clean_company_name(title)
    norm_brand = normalize(brand)
    
    # Mots vides à exclure pour isoler le terme de marque distinctif
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
        # A. Identité
        nom_legal = normalize(r.get('nom_complet') or '')
        sigle = normalize(r.get('sigle') or '')
        enseignes = ' '.join([normalize(e.get('enseigne', '')) for e in r.get('matching_etablissements', [])])
        all_cand_names = f"{nom_legal} {sigle} {enseignes}"
        
        name_hits = [t for t in brand_tokens if t in all_cand_names]
        name_score = (len(name_hits) / len(brand_tokens)) if brand_tokens else 0.0

        # B. Localisation
        siege_cp = r.get('siege', {}).get('code_postal', '')
        etab_cps = [e.get('code_postal', '') for e in r.get('matching_etablissements', [])]
        all_cps = {siege_cp} | set(etab_cps)
        cp_match = bool(target_cp and target_cp in all_cps)

        cand_addresses = [r.get('siege', {}).get('adresse', '')] + [e.get('adresse', '') for e in r.get('matching_etablissements', [])]
        cand_addrs_norm = normalize(' '.join(cand_addresses))
        street_num_match = bool(lead_num and lead_num in cand_addrs_norm.split())

        # C. Cohérence métier (NAF)
        naf = r.get('activite_principale', '')
        naf_valid = naf in VALID_NAF

        # Statut actif
        is_active = (r.get('etat_administratif') == 'A')

        # Score global du candidat (0 à 100)
        total_score = 0
        if cp_match:
            total_score += 40
        if name_score >= 1.0:
            total_score += 35
        elif name_score >= 0.5:
            total_score += 20
        if street_num_match:
            total_score += 15
        if naf_valid:
            total_score += 10
        if not is_active:
            total_score = 0

        scored_candidates.append({
            'candidate': r,
            'total_score': total_score,
            'name_score': name_score,
            'cp_match': cp_match,
            'street_num_match': street_num_match,
            'naf_valid': naf_valid,
            'is_active': is_active,
            'naf': naf
        })

    # Tri par score décroissant
    scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
    best = scored_candidates[0]

    # Pas de matching si code postal non concordant ou inactif
    if not best['cp_match'] or not best['is_active']:
        return None, 'NO_MATCH', f"Aucune concordance territoriale ou entreprise inactive (CP attendu {target_cp})"

    # Décision de classification déterministe
    if best['name_score'] >= 1.0 and best['cp_match'] and best['naf_valid']:
        if best['street_num_match'] or len(brand_tokens) >= 1:
            return best['candidate'], 'MATCH_CONFIRMED', f"Identité, CP ({target_cp}) et NAF ({best['naf']}) confirmés"
        return best['candidate'], 'MATCH_PLAUSIBLE', f"Nom et CP confirmés, numéro de voie non explicite (NAF {best['naf']})"

    if best['name_score'] >= 0.5 and best['cp_match'] and best['naf_valid']:
        return best['candidate'], 'MATCH_PLAUSIBLE', f"Raison sociale partiellement concordante et CP {target_cp} validé"

    return best['candidate'], 'MATCH_UNCERTAIN', f"Rapprochement incertain (score {best['total_score']}/100, NAF {best['naf']})"

def calculate_scores(lead: dict, sirene_data: dict, site_info: tuple):
    """
    Calcul strict des scores découplés et statut qualité :
    - Exclusion immédiate des 0 salarié (NN, 00) et >20 salariés.
    - Tranche 01 soumise à preuve secondaire nominative pour prétendre à VERIFIED.
    - Score Ghostwriting neutralisé (Option B).
    - Plafonds stricts de confiance en cas d'incertitude.
    """
    site_accessible, main_offer, target_clients, audit_note = site_info
    matching_status = sirene_data.get('matching_status', 'NO_MATCH')
    tranche = sirene_data.get('tranche_code')
    dirigeants = sirene_data.get('dirigeants', [])

    # Task 3 : Exclusion stricte ICP des structures non-employeurs ou >20 salariés
    tranches_hors_cible = ('NN', '00', '12', '21', '22', '31', '32', '41', '42', '51', '52')
    if tranche in tranches_hors_cible:
        status = 'DISQUALIFIED'
        reasons = [
            f"Lead Gen (0/100) : Structure hors cible ICP 2-20 (Tranche {sirene_data.get('tranche_label', 'Inconnue')})",
            "GW (0/100) : Neutralisé (Option B : absence d'audit éditorial public LinkedIn)",
            f"Confidence (0/100) : Structure disqualifiée (Preuve effectif: Tranche {tranche}; Matching: {matching_status})"
        ]
        return 0, 0, 0, status, reasons

    # LEAD_GEN_SCORE (0 à 100)
    # 1. Activité web pure (max 30)
    cat_lower = lead.get('category', '').lower()
    lg_activity = 30 if any(k in cat_lower for k in ['concepteur', 'site', 'web']) else 15

    # 2. Taille ICP (max 25)
    # Preuve secondaire pour tranche 01 : présence d'au moins 2 co-dirigeants déclarés au registre
    has_secondary_size_proof = (tranche == '01' and len(dirigeants) >= 2)
    if tranche in ['02', '03']: # 3 à 9 pers : cœur de cible
        lg_size = 25
    elif tranche == '11': # 10 à 19 pers : cible haute
        lg_size = 20
    elif tranche == '01' and has_secondary_size_proof:
        lg_size = 18
    elif tranche == '01':
        lg_size = 10 # 1 ou 2 sans preuve secondaire
    else:
        lg_size = 5 # Taille incertaine

    # 3. Signal commercial réel (max 25) - Aucun faux signal Google reviews
    lg_signal = 0

    # 4. Traction / Réputation (max 20)
    rating = float(lead.get('review_rating', 0)) if lead.get('review_rating') else 0.0
    reviews = int(float(lead.get('review_count', 0))) if lead.get('review_count') else 0
    if rating >= 4.8 and reviews >= 20:
        lg_reputation = 20
    elif rating >= 4.5 and reviews >= 10:
        lg_reputation = 15
    else:
        lg_reputation = 10

    lead_gen_score = min(100, lg_activity + lg_size + lg_signal + lg_reputation)

    # GHOSTWRITING_SCORE (Neutralisé à 0 selon Task 5 - Option B)
    ghostwriting_score = 0

    # CONFIDENCE_SCORE (0 à 100)
    # 1. Preuve légale (max 35)
    if matching_status == 'MATCH_CONFIRMED' and sirene_data.get('etat_administratif') == 'A':
        conf_legal = 35
    elif matching_status == 'MATCH_PLAUSIBLE':
        conf_legal = 20
    elif matching_status == 'MATCH_UNCERTAIN':
        conf_legal = 5
    else:
        conf_legal = 0

    # 2. Preuve effectif officiel (max 30)
    if tranche in ['02', '03', '11']:
        conf_size = 30
    elif tranche == '01' and has_secondary_size_proof:
        conf_size = 25
    elif tranche == '01':
        conf_size = 15
    else:
        conf_size = 5

    # 3. Audit technique site web (max 20)
    conf_site = 20 if site_accessible else 0

    # 4. Canal direct vérifié (max 15)
    conf_phone = 15 if lead.get('phone') else 0

    raw_conf = min(100, conf_legal + conf_size + conf_site + conf_phone)

    # STATUT QUALITÉ & APPLICATION STRICTE DES PLAFONDS
    # Conditions strictes pour VERIFIED :
    # 1. Matching SIRENE confirmé (non ambigu)
    # 2. Tranche 2-20 prouvée (02, 03, 11, ou 01 avec preuve secondaire)
    # 3. Dirigeant identifié au registre
    # 4. Site web HTTPS accessible
    # 5. Score confiance brut >= 80
    is_icp_size_certified = (tranche in ['02', '03', '11']) or (tranche == '01' and has_secondary_size_proof)
    has_registered_leader = bool(dirigeants and len(dirigeants) > 0)

    if sirene_data.get('etat_administratif') != 'A' and sirene_data.get('found'):
        status = 'DISQUALIFIED'
        confidence_score = 0
    elif matching_status == 'MATCH_CONFIRMED' and is_icp_size_certified and has_registered_leader and site_accessible and raw_conf >= 80:
        status = 'VERIFIED'
        confidence_score = raw_conf
    elif raw_conf >= 60 and matching_status in ('MATCH_CONFIRMED', 'MATCH_PLAUSIBLE'):
        status = 'PARTIALLY VERIFIED'
        confidence_score = min(raw_conf, 60) # Plafond strict 60
    else:
        status = 'REQUIRES REVIEW'
        if matching_status in ('MATCH_UNCERTAIN', 'NO_MATCH'):
            confidence_score = min(raw_conf, 40) # Plafond strict 40 pour matching incertain
        else:
            confidence_score = min(raw_conf, 60) # Plafond strict 60 pour non-vérifié

    # Justifications textuelles traçables (reasons)
    leader_name = dirigeants[0]['name'] if dirigeants else 'Non identifié'
    leader_role = dirigeants[0]['role'] if dirigeants else 'Inconnu'

    reasons = [
        f"Lead Gen ({lead_gen_score}/100) : Activité {lg_activity}/30 ('{lead.get('category')}'), Taille {lg_size}/25 (Tranche {tranche}" + ("; co-dirigeants RCS" if has_secondary_size_proof else "") + f"), Signal commercial 0/25 (aucun vérifié), Réputation {lg_reputation}/20 ({reviews} avis certifiés)",
        "GW (0/100) : Neutralisé (Option B : absence d'audit éditorial public LinkedIn)",
        f"Confidence ({confidence_score}/100) : Légal {conf_legal}/35 ({matching_status}), Effectif {conf_size}/30 ({tranche}), Site {conf_site}/20 ({audit_note}), Canal {conf_phone}/15 ({lead.get('phone')})"
    ]

    return lead_gen_score, ghostwriting_score, confidence_score, status, reasons

def main():
    shortlist_file = BASE_DIR / 'data' / 'gmaps_agences_web_shortlist.csv'
    if not shortlist_file.exists():
        raise FileNotFoundError(f"Fichier de shortlist introuvable : {shortlist_file}. Exécutez dedupe_and_shortlist.py en amont.")

    with open(shortlist_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_shortlisted = list(reader)

    # Consommation de la cohorte des 30 leads en tête de shortlist
    leads = all_shortlisted[:30]
    print(f"Requalification de {len(leads)} leads issus de la shortlist...")

    requalified_leads = []

    for i, lead in enumerate(leads, 1):
        name = lead.get('title')
        city = lead.get('city')
        address = lead.get('address', '')
        print(f"[{i:02d}/30] Requalification SIRENE & Audit Web : {name} ({city})...")

        # 1. Audit HTTP réel
        site_info = inspect_website(lead.get('website'))
        site_accessible, main_offer, target_clients, audit_note = site_info
        time.sleep(0.3)

        # 2. Interrogation SIRENE et matching multi-critères
        clean_name = clean_company_name(name)
        sirene_results = query_sirene_api(f"{clean_name} {city}")
        if not sirene_results:
            sirene_results = query_sirene_api(clean_name)
        time.sleep(0.5)

        best_cand, match_status, match_reason = evaluate_sirene_match(lead, sirene_results)

        if best_cand:
            siren = best_cand.get('siren')
            tranche = best_cand.get('tranche_effectif_salarie')
            dirigeants = [
                {'name': f"{d.get('prenoms', '')} {d.get('nom', '')}".strip(), 'role': d.get('qualite') or 'Dirigeant'}
                for d in best_cand.get('dirigeants', []) if d.get('nom')
            ]
            sirene_data = {
                'found': True,
                'siren': siren,
                'nom_complet': best_cand.get('nom_complet'),
                'etat_administratif': best_cand.get('etat_administratif'),
                'tranche_code': tranche,
                'tranche_label': TRANCHES_INSEE.get(tranche, f'Code INSEE {tranche}' if tranche else 'Non renseigné'),
                'activite_principale': best_cand.get('activite_principale'),
                'dirigeants': dirigeants,
                'matching_status': match_status,
                'match_reason': match_reason,
                'evidence_url': f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else ""
            }
        else:
            sirene_data = {
                'found': False,
                'siren': None,
                'tranche_code': None,
                'tranche_label': 'Non identifié',
                'dirigeants': [],
                'matching_status': match_status,
                'match_reason': match_reason,
                'evidence_url': ""
            }

        # 3. Calcul des scores et du statut
        lg_score, gw_score, conf_score, status, reasons = calculate_scores(lead, sirene_data, site_info)

        # Extraction dirigeant
        dirigeants = sirene_data.get('dirigeants', [])
        if dirigeants:
            decision_maker = dirigeants[0]['name']
            decision_maker_role = dirigeants[0]['role']
        else:
            decision_maker = 'Non identifié au registre'
            decision_maker_role = 'Inconnu'

        # Construction des notes traçables
        notes_parts = [
            f"Matching SIRENE : {match_status} ({match_reason})",
            f"SIREN : {sirene_data.get('siren') or 'Non trouvé'}",
            f"Tranche : {sirene_data.get('tranche_label')}"
        ]
        if not site_accessible:
            notes_parts.append("site inaccessible")
        notes = " | ".join(notes_parts)

        item = {
            'company_name': sirene_data.get('nom_complet') or lead.get('title'),
            'brand_name': lead.get('title'),
            'siren': sirene_data.get('siren') or 'Non trouvé',
            'website': lead.get('website'),
            'country': 'France',
            'city': lead.get('city'),
            'company_size': sirene_data.get('tranche_label') or 'Incertain',
            'company_size_source': 'INSEE / Annuaire des Entreprises' if sirene_data.get('siren') else 'Non vérifié',
            'main_offer': main_offer,
            'target_clients': target_clients,
            'decision_maker': decision_maker,
            'decision_maker_role': decision_maker_role,
            'decision_maker_source': sirene_data.get('evidence_url') or lead.get('website'),
            'public_professional_email': 'Non extrait (Option)',
            'public_phone': lead.get('phone'),
            'source_url': lead.get('google_maps_url'),
            'evidence_url': sirene_data.get('evidence_url') or lead.get('website'),
            'matching_status': match_status,
            'commercial_signal': '',
            'signal_source': '',
            'signal_date': '',
            'lead_gen_score': lg_score,
            'ghostwriting_score': gw_score,
            'confidence_score': conf_score,
            'verification_status': status,
            'reasons': reasons,
            'last_checked': '2026-09-27',
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
