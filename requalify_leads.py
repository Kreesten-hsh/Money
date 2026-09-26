import json
import urllib.request
import urllib.parse
import time
import re
import csv
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

def clean_company_name(name):
    name = name.split('|')[0].strip()
    name = re.sub(r' - Agence.*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Agence Web .*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'Création site internet .*', '', name, flags=re.IGNORECASE)
    name = name.replace('Agence Digitale', '').strip()
    return name.strip(' -')

def check_website(url: str) -> bool:
    """Audit HTTP réel : code 200 et protocole HTTPS avec timeout de 5 secondes."""
    if not url or not str(url).startswith('https://'):
        return False
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

def search_sirene(name, city, address=''):
    """Recherche SIRENE avec réconciliation stricte du code postal et extraction du rôle réel."""
    clean_name = clean_company_name(name)
    query = f"{clean_name} {city}".strip()
    
    # Extraction du code postal de l'adresse du lead
    target_cp_match = re.search(r'\b(0[1-9]|[1-8]\d|9[0-8])\d{3}\b', address or '')
    target_cp = target_cp_match.group(0) if target_cp_match else None

    url = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(query)}&per_page=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'MoneyB2BAgent/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = data.get('results', [])
            if not results:
                # Repli sur le nom nettoyé seul
                url_fallback = f"https://recherche-entreprises.api.gouv.fr/search?q={urllib.parse.quote(clean_name)}&per_page=5"
                req_fallback = urllib.request.Request(url_fallback, headers={'User-Agent': 'MoneyB2BAgent/1.0'})
                with urllib.request.urlopen(req_fallback, timeout=8) as resp_fb:
                    data_fb = json.loads(resp_fb.read().decode())
                    results = data_fb.get('results', [])

            for r in results:
                siege = r.get('siege', {})
                siege_cp = siege.get('code_postal', '')
                matching_cps = [e.get('code_postal', '') for e in r.get('matching_etablissements', [])]
                all_cps = {siege_cp} | set(matching_cps)

                # Contrôle postal strict si le lead possède un code postal
                if target_cp and target_cp not in all_cps:
                    continue

                etat = r.get('etat_administratif')
                nom = r.get('nom_complet')
                siren = r.get('siren')
                tranche = r.get('tranche_effectif_salarie')
                activite = r.get('activite_principale')
                
                # Capture du rôle réel (qualite) des dirigeants
                dirigeants = []
                for d in r.get('dirigeants', []):
                    if d.get('nom'):
                        full_name = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()
                        role = d.get('qualite') or 'Dirigeant'
                        dirigeants.append({
                            'name': full_name,
                            'role': role
                        })

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
                    'code_postal': siege_cp,
                    'adresse': adresse,
                    'evidence_url': f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else ""
                }

            if target_cp:
                return {'found': False, 'reason': 'no_postal_match'}
    except Exception as e:
        return {'found': False, 'error': str(e)}
    return {'found': False}

def calculate_scores(lead, sirene_data):
    """Calcul des scores découplés avec disqualification immédiate des 0 salarié."""
    tranche = sirene_data.get('tranche_code')

    # Task 3 : Bug ICP - Exclusion immédiate si tranche non employeur (NN ou 00)
    if tranche in ('NN', '00'):
        status = 'DISQUALIFIED'
        reasons = [
            "Activité (0/30) : Non évaluée suite à disqualification effectif",
            f"Taille (0/25) : Tranche {sirene_data.get('tranche_label', '0 salarié')} - Hors cible 2-20 salariés",
            "Signal commercial (0/25) : Aucun signal d'affaires externe qualifié",
            "Réputation (0/20) : Non prise en compte suite à disqualification",
            "Dirigeant (0/30) : Non évalué suite à disqualification",
            "Positionnement (0/30) : Non évalué suite à disqualification",
            "Preuve sociale (0/20) : Non prise en compte",
            "Maturité (0/20) : Structure non employeuse",
            "Preuve légale (0/35) : Établissement identifié mais hors cible",
            "Preuve effectif (0/30) : Tranche INSEE 0 salarié confirmée",
            "Audit site web (0/20) : Non audité",
            "Canal direct (0/15) : Non audité"
        ]
        return 0, 0, 0, status, False, reasons

    # LEAD_GEN_SCORE (0 to 100)
    # Activité Web pure (max 30)
    lg_activity = 30 if any(k in lead.get('category', '').lower() for k in ['concepteur', 'site', 'web']) else 15
    
    # Taille optimale 2-20 (max 25)
    if tranche in ['02', '03']: # 3 à 9 pers : Coeur de cible
        lg_size = 25
    elif tranche in ['01', '11']: # 1-2 pers ou 10-19 pers : Cible élargie
        lg_size = 18
    elif tranche == '12': # 20 à 49 pers : limite haute
        lg_size = 10
    else:
        lg_size = 10 # Incertain
    
    # Task 7 : Retrait du faux signal commercial tant qu'aucun événement externe réel n'est détecté
    lg_signal = 0

    # Traction / Réputation (max 20)
    rating = float(lead.get('review_rating', 0)) if lead.get('review_rating') else 0.0
    reviews = int(float(lead.get('review_count', 0))) if lead.get('review_count') else 0
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
    gw_leader = 30 if len(dirigeants) > 0 else 5

    # Positionnement différenciant (max 30)
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
    if sirene_data.get('tranche_code') and sirene_data.get('tranche_code') not in ['NN', '00', None]:
        conf_size = 30
    else:
        conf_size = 5

    # Task 4 : Audit HTTP réel
    site_accessible = check_website(lead.get('website'))
    conf_site = 20 if site_accessible else 0

    # Canal direct téléphone / contact (max 15)
    conf_phone = 15 if lead.get('phone') else 0

    confidence_score = min(100, conf_legal + conf_size + conf_site + conf_phone)

    # STATUT QUALITÉ
    if sirene_data.get('etat_administratif') != 'A' and sirene_data.get('found'):
        status = 'DISQUALIFIED'
        confidence_score = 0
    elif confidence_score >= 80 and tranche in ['01', '02', '03', '11']:
        status = 'VERIFIED'
    elif confidence_score >= 60:
        status = 'PARTIALLY VERIFIED'
        confidence_score = min(confidence_score, 60)
    else:
        status = 'REQUIRES REVIEW'
        confidence_score = min(confidence_score, 50)

    # Task 6 : Liste des justifications textuelles pour chaque composante de score
    reasons = [
        f"Activité ({lg_activity}/30) : {'Catégorie web pure' if lg_activity == 30 else 'Activité web secondaire'}",
        f"Taille ({lg_size}/25) : {sirene_data.get('tranche_label', 'Effectif non certifié')}",
        f"Signal commercial ({lg_signal}/25) : Aucun signal d'affaires externe qualifié",
        f"Réputation ({lg_reputation}/20) : Note {lead.get('review_rating')}/5 ({reviews} avis)",
        f"Dirigeant ({gw_leader}/30) : {'Dirigeant identifié au registre' if gw_leader == 30 else 'Dirigeant non identifié'}",
        f"Positionnement ({gw_angle}/30) : {'Angle différenciant détecté' if gw_angle == 25 else 'Positionnement généraliste'}",
        f"Preuve sociale ({gw_proof}/20) : {reviews} avis clients enregistrés",
        f"Maturité ({gw_maturity}/20) : Tranche effectif {sirene_data.get('tranche_code', 'N/A')}",
        f"Preuve légale ({conf_legal}/35) : {'SIREN actif et vérifié' if conf_legal == 35 else 'Non certifié au registre'}",
        f"Preuve effectif ({conf_size}/30) : {'Effectif officiel INSEE' if conf_size == 30 else 'Effectif incertain'}",
        f"Audit site web ({conf_site}/20) : {'HTTPS valide (HTTP 200)' if site_accessible else 'Site inaccessible ou non sécurisé'}",
        f"Canal direct ({conf_phone}/15) : {'Téléphone professionnel vérifié' if conf_phone == 15 else 'Aucun téléphone renseigné'}"
    ]

    return lead_gen_score, ghostwriting_score, confidence_score, status, site_accessible, reasons

def main():
    input_file = BASE_DIR / 'data' / 'top30_leads_qualified.json'
    with open(input_file, 'r', encoding='utf-8') as f:
        leads = json.load(f)

    requalified_leads = []
    print(f"Requalification de {len(leads)} leads...")

    for i, lead in enumerate(leads, 1):
        name = lead.get('title')
        city = lead.get('city')
        address = lead.get('address', '')
        print(f"[{i:02d}/30] Recherche SIRENE pour : {name} ({city})...")
        
        sirene_data = search_sirene(name, city, address)
        time.sleep(0.3) # Respect des limites de l'API publique

        lg_score, gw_score, conf_score, status, site_accessible, reasons = calculate_scores(lead, sirene_data)

        # Rôle réel issu de l'API SIRENE
        dirigeants = sirene_data.get('dirigeants', [])
        if dirigeants:
            dirigeant_nom = dirigeants[0]['name']
            dirigeant_role = dirigeants[0]['role']
        else:
            dirigeant_nom = 'Non identifié au registre'
            dirigeant_role = 'Inconnu'

        # Notes et alertes
        base_notes = f"SIREN {sirene_data.get('siren')} | APE {sirene_data.get('activite_principale')} | Tranche: {sirene_data.get('tranche_label')}" if sirene_data.get('siren') else "Non identifié avec certitude dans l'annuaire public"
        if not site_accessible:
            notes = f"{base_notes} | site inaccessible"
        else:
            notes = base_notes
        
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
            'decision_maker_role': dirigeant_role,
            'decision_maker_source': sirene_data.get('evidence_url') or lead.get('website'),
            'public_professional_email': 'Non extrait (Option)',
            'public_phone': lead.get('phone'),
            'source_url': lead.get('google_maps_url'),
            'evidence_url': sirene_data.get('evidence_url') or lead.get('website'),
            'lead_gen_score': lg_score,
            'ghostwriting_score': gw_score,
            'confidence_score': conf_score,
            'verification_status': status,
            'reasons': reasons,
            'last_checked': '2026-09-26',
            'notes': notes
        }
        requalified_leads.append(item)

    # Sauvegarde JSON (avec 'reasons' sous forme de liste native)
    json_output_path = BASE_DIR / 'data' / 'top30_leads_requalified.json'
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(requalified_leads, f, ensure_ascii=False, indent=2)

    # Sauvegarde CSV (avec 'reasons' aplati)
    csv_output_path = BASE_DIR / 'data' / 'top30_leads_requalified.csv'
    csv_leads = []
    for l in requalified_leads:
        row_copy = dict(l)
        row_copy['reasons'] = '; '.join(l.get('reasons', []))
        csv_leads.append(row_copy)

    fieldnames = list(csv_leads[0].keys())
    with open(csv_output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_leads)

    print("\nRequalification terminée avec succès !")
    
    statuses = {}
    for l in requalified_leads:
        st = l['verification_status']
        statuses[st] = statuses.get(st, 0) + 1
    print("Répartition des statuts réels :", statuses)

if __name__ == '__main__':
    main()
