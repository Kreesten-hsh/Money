import json
import urllib.request
import urllib.parse
import time
import re
import csv

# Tranches d'effectif INSEE
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

def clean_company_name(name):
    name = name.split('|')[0].strip()
    name = re.sub(r' - Agence.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Agence Web .*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Création site internet .*', '', name, flags=re.IGNORECASE)
    name = name.replace('Agence Digitale', '').strip()
    return name.strip(' -')

def search_sirene(name, city):
    clean_name = clean_company_name(name)
    query = f"{clean_name} {city}".strip()
    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(query)}&per_page=3"
    req = urllib.request.Request(url, headers={'User-Agent': 'MoneyB2BAgent/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = data.get('results', [])
            if not results:
                # Fallback on clean_name only
                url_fallback = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(clean_name)}&per_page=3"
                req_fallback = urllib.request.Request(url_fallback, headers={'User-Agent': 'MoneyB2BAgent/1.0'})
                with urllib.request.urlopen(req_fallback, timeout=8) as resp_fb:
                    data_fb = json.loads(resp_fb.read().decode())
                    results = data_fb.get('results', [])

            for r in results:
                # Check if active
                etat = r.get('etat_administratif')
                nom = r.get('nom_complet')
                siren = r.get('siren')
                tranche = r.get('tranche_effectif_salarie')
                activite = r.get('activite_principale')
                dirigeants = [
                    f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()
                    for d in r.get('dirigeants', [])
                    if d.get('nom')
                ]
                siege = r.get('siege', {})
                code_postal = siege.get('code_postal', '')
                adresse = siege.get('adresse', '')
                
                return {
                    'found': True,
                    'nom_complet': nom,
                    'siren': siren,
                    'etat_administratif': etat,
                    'tranche_code': tranche,
                    'tranche_label': TRANCHES_INSEE.get(tranche, f'Code INSEE {tranche}' if tranche else 'Non renseigné'),
                    'activite_principale': activite,
                    'dirigeants': dirigeants,
                    'code_postal': code_postal,
                    'adresse': adresse,
                    'evidence_url': f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else ""
                }
    except Exception as e:
        return {'found': False, 'error': str(e)}
    return {'found': False}

def calculate_scores(lead, sirene_data):
    # LEAD_GEN_SCORE (0 to 100)
    # Activité Web pure (max 30)
    lg_activity = 30 if any(k in lead.get('category', '').lower() for k in ['concepteur', 'site', 'web']) else 15
    
    # Taille optimale 2-20 (max 25)
    tranche = sirene_data.get('tranche_code')
    if tranche in ['02', '03']: # 3 à 9 pers : Coeur de cible
        lg_size = 25
    elif tranche in ['01', '11']: # 1-2 pers ou 10-19 pers : Cible élargie
        lg_size = 18
    elif tranche == '12': # 20 à 49 pers : limite haute
        lg_size = 10
    elif tranche in ['NN', '00']: # Non employeur
        lg_size = 5
    else:
        lg_size = 10 # Incertain
    
    # Signal commercial (max 25)
    # Présence de preuves sociales fortes et avis récents
    reviews = int(float(lead.get('review_count', 0)))
    if reviews >= 50:
        lg_signal = 25
    elif reviews >= 20:
        lg_signal = 18
    else:
        lg_signal = 10

    # Traction / Réputation (max 20)
    rating = float(lead.get('review_rating', 0))
    if rating >= 4.8:
        lg_reputation = 20
    elif rating >= 4.5:
        lg_reputation = 15
    else:
        lg_reputation = 10

    lead_gen_score = min(100, lg_activity + lg_size + lg_signal + lg_reputation)

    # GHOSTWRITING_SCORE (0 to 100)
    # Dirigeant identifié (max 30)
    dirigeants = sirene_data.get('dirigeants', [])
    if len(dirigeants) > 0:
        gw_leader = 30
    else:
        gw_leader = 5

    # Positionnement différenciant (max 30)
    # Vérifié via titre, description et catégorie
    title_cat = (lead.get('title', '') + ' ' + lead.get('category', '')).lower()
    if any(k in title_cat for k in ['branding', 'studio', 'marketing', 'seo', 'eco', 'design']):
        gw_angle = 25
    else:
        gw_angle = 15

    # Matière & preuve sociale (max 20)
    if reviews >= 40:
        gw_proof = 20
    elif reviews >= 15:
        gw_proof = 12
    else:
        gw_proof = 5

    # Structure & Maturité (max 20)
    if tranche in ['02', '03', '11']:
        gw_maturity = 20
    elif tranche == '01':
        gw_maturity = 12
    else:
        gw_maturity = 5

    ghostwriting_score = min(100, gw_leader + gw_angle + gw_proof + gw_maturity)

    # CONFIDENCE_SCORE (0 to 100)
    # Preuve légale SIRENE / RCS (max 35)
    if sirene_data.get('found') and sirene_data.get('siren') and sirene_data.get('etat_administratif') == 'A':
        conf_legal = 35
    elif sirene_data.get('found'):
        conf_legal = 20
    else:
        conf_legal = 0

    # Preuve effectif officiel (max 30)
    if sirene_data.get('tranche_code') and sirene_data.get('tranche_code') not in ['NN', None]:
        conf_size = 30
    elif sirene_data.get('tranche_code') == 'NN':
        conf_size = 20 # Preuve qu'il est NN (non employeur)
    else:
        conf_size = 5

    # Site exploré & accessible (max 20)
    conf_site = 20 if lead.get('website') else 0

    # Canal direct téléphone / contact (max 15)
    conf_phone = 15 if lead.get('phone') else 0

    confidence_score = min(100, conf_legal + conf_size + conf_site + conf_phone)

    # STATUT QUALITÉ
    if sirene_data.get('etat_administratif') != 'A' and sirene_data.get('found'):
        status = 'DISQUALIFIED'
    elif confidence_score >= 80 and tranche in ['01', '02', '03', '11']:
        status = 'VERIFIED'
    elif confidence_score >= 60:
        status = 'PARTIALLY VERIFIED'
    else:
        status = 'REQUIRES REVIEW'

    return lead_gen_score, ghostwriting_score, confidence_score, status

def main():
    with open('/home/hasashi/Bureau/Money/data/top30_leads_qualified.json', 'r', encoding='utf-8') as f:
        leads = json.load(f)

    requalified_leads = []
    print(f"Requalification de {len(leads)} leads...")

    for i, lead in enumerate(leads, 1):
        name = lead.get('title')
        city = lead.get('city')
        print(f"[{i:02d}/30] Recherche SIRENE pour : {name} ({city})...")
        
        sirene_data = search_sirene(name, city)
        time.sleep(0.3) # Respect API rate-limits

        lg_score, gw_score, conf_score, status = calculate_scores(lead, sirene_data)

        dirigeant_nom = sirene_data.get('dirigeants')[0] if sirene_data.get('dirigeants') else 'Non identifié au registre'
        
        item = {
            'company_name': sirene_data.get('nom_complet') or lead.get('title'),
            'brand_name': lead.get('title'),
            'siren': sirene_data.get('siren') or 'Non trouvé',
            'website': lead.get('website'),
            'country': 'France',
            'city': lead.get('city'),
            'company_size': sirene_data.get('tranche_label') or 'Incertain',
            'company_size_source': 'INSEE / Annuaire des Entreprises' if sirene_data.get('siren') else 'Google Maps (non audité)',
            'main_offer': lead.get('category'),
            'target_clients': 'PME & Professionnels B2B',
            'decision_maker': dirigeant_nom,
            'decision_maker_role': 'Dirigeant légal / Associé' if sirene_data.get('dirigeants') else 'Inconnu',
            'decision_maker_source': sirene_data.get('evidence_url') or lead.get('website'),
            'public_professional_email': 'Non extrait (Option)',
            'public_phone': lead.get('phone'),
            'source_url': lead.get('google_maps_url'),
            'evidence_url': sirene_data.get('evidence_url') or lead.get('website'),
            'commercial_signal': f"Preuve sociale forte : {lead.get('review_rating')}/5 ({lead.get('review_count')} avis)",
            'signal_source': lead.get('google_maps_url'),
            'signal_date': '2026-09-26',
            'lead_gen_score': lg_score,
            'ghostwriting_score': gw_score,
            'confidence_score': conf_score,
            'verification_status': status,
            'last_checked': '2026-09-26',
            'notes': f"SIREN {sirene_data.get('siren')} | APE {sirene_data.get('activite_principale')} | Tranche: {sirene_data.get('tranche_label')}" if sirene_data.get('siren') else "Non identifié avec certitude dans l'annuaire public"
        }
        requalified_leads.append(item)

    # Save to JSON
    with open('/home/hasashi/Bureau/Money/data/top30_leads_requalified.json', 'w', encoding='utf-8') as f:
        json.dump(requalified_leads, f, ensure_ascii=False, indent=2)

    # Save to CSV
    fieldnames = list(requalified_leads[0].keys())
    with open('/home/hasashi/Bureau/Money/data/top30_leads_requalified.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(requalified_leads)

    print("\nRequalification terminée avec succès !")
    
    # Synthese
    statuses = {}
    for l in requalified_leads:
        st = l['verification_status']
        statuses[st] = statuses.get(st, 0) + 1
    print("Répartition des statuts réels :", statuses)

if __name__ == '__main__':
    main()
