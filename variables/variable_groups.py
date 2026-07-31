variable_name_groups = {
    "Patient Demographics": [
        'Patient age in years', 'Patient gender', 'Patient race', 'Patient education',
        'Patient citizenship', 'Patient weight (kg)', 'Patient body mass index'
    ],
    "Patient Clinical Status": [
        'Patient total waitlist days', 'Patient days in old UNOS status 1A', 'Patient days in old UNOS status 1B',
        'Patient days in old UNOS status 2', 'Patient days in new UNOS status 1', 'Patient days in new UNOS status 2',
        'Patient days in new UNOS status 3', 'Patient days in new UNOS status 4',
        'Patient days in new UNOS status 5', 'Patient days in new UNOS status 6',
        'Patient functional status at WL', 'Patient functional status at TXP', 'Patient in ICU',
        'Patient hospitalization status',  'Patient history of cigarette use', 'Patient chronic steroid use at TXP',
        'Patient previous malignancy', 'Patient type of dialysis at REG',
        'Patient cigarette recent use + > 10 PACK YRS', 'Patient multi-organ TXP',
        'Patient primary diagnosis', 'Patient diabetes mellitus', 'Patient cerebrovascular disease', 'Patient infection',
        'Patient HIV NAT', 'Patient HIV antibody serologic test', 'Patient cytomegalovirus status at TXP',
        'Patient cytomegalovirus status by IGG at TXP', 'Patient cytomegalovirus status by IGM at TXP',
        'Patient Epstein-Barr virus antibody test', 'Patient Hepatitis B antibody test', 'Patient HEP C status',
        'Patient Hepatitis B NAT', 'Patient dialysis prior to TXP', 'Patient dialysis between WL and TXP',
        'Patient transfusion between WL and TXP', 'The number of previous TXPs',
        'Patient prior cardiac surgery at WL', 'Patient cardiac surgery between WL and TXP',
        'Patient history of cigarette use', 'Patient chronic steroid use at TXP',
        'Patient previous malignancy', 'Patient type of dialysis at REG',
        'Patient cigarette recent use + > 10 PACK YRS', 'Patient multi-organ TXP', 'Patient number of previous TXPs',

    ],
    "Patient Device Support": [
        'Patient on ventilator at TXP', 'Patient on ventilator at REG',
        'Patient On ECMO at TXP', 'Patient On ECMO at REG',
        'Patient On IABP at TXP', 'Patient On IABP at REG',
        'Patient on prostaglandins at TXP', 'Patient on prostaglandins at REG',
        'Patient IV inotropes at TXP', 'Patient IV inotropes at REG',
        'Patient VAD device type at TXP', 'Patient VAD device type at REG',
        'Patient on VAD/TAH brand at REG', 'Patient on VAD brand at TXP',
        'Patient implantable defibrillator at REG'
    ],
    "Patient Lab Values": [
        'Patient PRA% at TXP (OLD SYSTEM)', 'Patient peak PRA% at TXP (OLD SYSTEM)',
        'Patient PRA% class I at TXP', 'Patient PRA% class II at TXP',
        'Patient peak PRA% class I at TXP', 'Patient peak PRA% class II at TXP',
        'Patient A locus mismatch level', 'Patient B locus mismatch level',
        'Patient HLA locus mismatch level', 'Patient DR locus mismatch level',
        'Patient blood group', 'Patient serum creatinine at TXP', 'Patient absolute creatinine at WL',
        'Patient serum total bilirubin at TXP', 'Patient serum albumin at REG',
        'Patient most recent CPRA', 'Patient peak CPRA', 'Patient eGFR',
        'Patient creatinine clearance', 'Patient mean PAP at TXP',
    ],
    "Donor Demographics": [
        'Donor age in years', 'Donor gender', 'Donor citizenship',
        'Donor weight (kg)', 'Donor body mass index', 'Donor race'
    ],
    "Donor Clinical Factors": [
        'Donor cause of death', 'Donor circumstance of death', 'Donor mechanism of death',
        'Donor serology anti-CMV', 'Donor HBV core antibody', 'Donor HEP B surface antigen',
        'Donor HBsAg',  # DonorNet naming (same concept as HEP B surface antigen)
        'Donor antibody TO HEP C virus result', 'Donor history/duration of diabetes',
        'Donor history of coronary artery disease (CAD)',
        'Donor terminal lab creatinine', 'Donor terminal SGOT/AST', 'Donor terminal SGPT/ALT',
        'Donor pCO2', 'Donor hematocrit', 'Donor cancer'
    ],
    "Donor Infection Risk": [
        'Donor clinical infection', 'Donor infection pulmonary source', 'Donor infection urine source',
        'Donor infection blood source', 'Donor infection other sources',
        'Donor risk for blood-borne disease transmission'
    ],
    "Donor Substance Use & Comorbidities": [
        'Donor history of cigarettes >20 PACK YRS', 'Donor recent cigarettes use + >20 PACK YRS',
        'Donor history of cocaine use', 'Donor history of cocaine use + recent use',
        'Donor history of alcohol dependency', 'Donor heavy alcohol use (>= 2 drinks/day)',
        'Donor history of hypertension', 'Donor history of other drug use',
        'Donor history of other drugs + recent use', 'Donor insulin dependent diabetes'
    ],
    "Donor Procedural Factors": [
        'Donor inotropic medication', 'Donor antihypertensives in 24 hrs pre-cross clamp',
        'Donor arginine vasopressin in 24 hrs pre-cross clamp', 'Donor synthetic anti diuretic hormone (DDAVP)',
        'Donor vasodilators pre-cross clamp', 'Donor pre-recovery heparin'
    ],
    "Donor and Recipient Matching": [
        'Nautical miles from donor to TXP center', 'Donor recipient ABO match level',
        'Ischemic time in hours'
    ],
    "Organ Variables": [
        'Donor final flush solution', 'Donor heart back table flush solution', 'Donor coronary angiogram'
    ],
    "Transplant Era": ['Patient year of TXP'],
}