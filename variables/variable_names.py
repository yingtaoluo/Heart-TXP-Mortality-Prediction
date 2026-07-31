base_descriptions = {'PSTATUS': 'Patient mortality',
                     'AGE': 'Patient age in years',
                     'GENDER': 'Patient gender',
                     'EDUCATION': 'Patient education',
                     'CITIZENSHIP': 'Patient citizenship',
                     'HGT_CM_CALC': 'Patient height (cm)',
                     'WGT_KG_CALC': 'Patient weight (kg)',
                     'BMI_CALC': 'Patient body mass index',
                     'ETHCAT': 'Patient race',
                     'TCR_DGN': 'Patient primary diagnosis',
                     'DAYSWAIT_CHRON': 'Patient total waitlist days',
                     'DAYS_STAT1A': 'Patient days in old UNOS status 1A',
                     'DAYS_STAT1B': 'Patient days in old UNOS status 1B',
                     'DAYS_STAT2': 'Patient days in old UNOS status 2',
                     'DAYS_STATA1': 'Patient days in new UNOS status 1',
                     'DAYS_STATA2': 'Patient days in new UNOS status 2',
                     'DAYS_STATA3': 'Patient days in new UNOS status 3',
                     'DAYS_STATA4': 'Patient days in new UNOS status 4',
                     'DAYS_STATA5': 'Patient days in new UNOS status 5',
                     'DAYS_STATA6': 'Patient days in new UNOS status 6',
                     # 'GSTATUS': 'Patient graft failure',
                     'Patient functional status at WL': 'Patient functional status at WL',
                     'Patient functional status at TXP': 'Patient functional status at TXP',
                     'DIAB': 'Patient diabetes mellitus',
                     'CEREB_VASC': 'Patient cerebrovascular disease',
                     'INFECT_IV_DRUG_TRR': 'Patient infection',
                     # 'HIV_NAT': 'Patient HIV NAT',
                     # 'HIV_SEROSTATUS': 'Patient HIV antibody serologic test',
                     'CMV_STATUS': 'Patient cytomegalovirus status at TXP',
                     'CMV_IGG': 'Patient cytomegalovirus status by IGG at TXP',
                     'CMV_IGM': 'Patient cytomegalovirus status by IGM at TXP',
                     'EBV_SEROSTATUS': 'Patient Epstein-Barr virus antibody test',
                     'HBV_CORE': 'Patient Hepatitis B antibody test',
                     'HBV_NAT': 'Patient Hepatitis B NAT',
                     # 'DIAL_PRIOR_TX': 'Patient dialysis prior to TXP',
                     'DIAL_AFTER_LIST': 'Patient dialysis between WL and TXP',
                     'TRANSFUSIONS': 'Patient transfusion between WL and TXP',
                     'NUM_PREV_TX': 'Patient number of previous TXPs',
                     'PRIOR_CARD_SURG_TCR': 'Patient prior cardiac surgery at WL',
                     'PRIOR_CARD_SURG_TRR': 'Patient cardiac surgery between WL and TXP',
                     # 'INTUBATED_72HOURS': 'Patient intubated at 72 hours',  # all U, meaningless
                     'MED_COND_TRR': 'Patient hospitalization status',
                     # (1 ICU, 2 Hospitalized not ICU, 3 Not hospitalized)
                     'ICU': 'Patient in ICU',  # only for baseline
                     'INOTROPES_TRR': 'Patient IV inotropes at TXP',
                     'INOTROPES_TCR': 'Patient IV inotropes at REG',
                     'VENTILATOR_TRR': 'Patient on ventilator at TXP',
                     'VENTILATOR_TCR': 'Patient on ventilator at REG',
                     'VENT_SUPPORT_TRR': 'Patient episode of vent support at TXP',
                     'ECMO_TCR': 'Patient On ECMO at REG',
                     'ECMO_TRR': 'Patient On ECMO at TXP',
                     'IABP_TCR': 'Patient On IABP at REG',
                     'IABP_TRR': 'Patient On IABP at TXP',
                     'PGE_TCR': 'Patient on prostaglandins at REG',
                     'PGE_TRR': 'Patient on prostaglandins at TXP',
                     'VAD_DEVICE_TY_TRR': 'Patient VAD device type at TXP',
                     'VAD_DEVICE_TY_TCR': 'Patient VAD device type at REG',
                     # 'VAD_TAH_TRR': 'Patient on life support - VAD/TAH at TXP',  # all U, meaningless
                     # 'VAD_TAH_TCR': 'Patient on VAD/TAH brand at REG',
                     'IMPL_DEFIBRIL': 'Patient implantable defibrillator at REG',
                     'TX_YEAR': 'Patient year of TXP',
                     # being filtered
                     'PRAMR_CL1': 'Patient PRA% class I at TXP',
                     'PRAMR_CL2': 'Patient PRA% class II at TXP',
                     'PRAMR': 'Patient PRA% at TXP (OLD SYSTEM)',
                     'PRAPK_CL1': 'Patient peak PRA% class I at TXP',
                     'PRAPK_CL2': 'Patient peak PRA% class II at TXP',
                     'PRAPK': 'Patient peak PRA% at TXP (OLD SYSTEM)',
                     # the below are treated as cat at the moment
                     # 'AMIS': 'Patient A locus mismatch level',
                     # 'BMIS': 'Patient B locus mismatch level',
                     # 'HLAMIS': 'Patient HLA locus mismatch level',
                     # 'DRMIS': 'Patient DR locus mismatch level',
                     'ABO': 'Patient blood group',
                     'CREAT_TRR': 'Patient serum creatinine at TXP',
                     # 'END_CREAT': 'Patient serum creatinine at TRR/Offer/Removal/Current Time',
                     #  (HL, LU only)
                     # 'INIT_CREAT': 'Patient serum creatinine at WL',  # a lot of missing
                     'MOST_RCNT_CREAT': 'Patient absolute creatinine at WL',  # some missing
                     'TBILI': 'Patient serum total bilirubin at TXP',

                     'AGE_DON': 'Donor age in years',
                     'GENDER_DON': 'Donor gender',
                     'CITIZENSHIP_DON': 'Donor citizenship',
                     # 'WGT_KG_DON_CALC': 'Donor weight (kg)',
                     # 'BMI_DON_CALC': 'Donor body mass index',
                     'ETHCAT_DON': 'Donor race',
                     # 'COD_CAD_DON': 'Donor cause of death',
                     'DISTANCE': 'Nautical miles from donor to TXP center',
                     'HGT_CM_DON_CALC': 'Donor height in centimeters',
                     # below being filtered
                     'ABO_MAT': 'Donor recipient ABO match level',
                     'ISCHTIME': 'Ischemic time in hours',
                     'LV_EJECT': 'Donor LV ejection fraction %',
                     # 'HIST_CIG_DON': 'Donor history of cigarettes >20 PACK YRS',
                     # 'CONTIN_CIG_DON': 'Donor recent cigarettes use + >20 PACK YRS',
                     # 'HIST_COCAINE_DON': 'Donor history of cocaine use',
                     # 'CONTIN_COCAINE_DON': 'Donor history of cocaine use + recent use',
                     # 'HIST_ALCOHOL_OLD_DON': 'Donor history of alcohol dependency',
                     # 'ALCOHOL_HEAVY_DON': 'Donor heavy alcohol use (>= 2 drinks/day)',
                     # 'HIST_HYPERTENS_DON': 'Donor history of hypertension',
                     # 'CLIN_INFECT_DON': 'Donor clinical infection',
                     # 'PULM_INF_DON': 'Donor infection pulmonary source',
                     # 'URINE_INF_DON': 'Donor infection urine source',
                     # 'BLOOD_INF_DON': 'Donor infection blood source',
                     # 'OTHER_INF_DON': 'Donor infection other sources',
                     # 'INOTROP_SUPPORT_DON': 'Donor inotropic medication',
                     'CMV_DON': 'Donor serology anti-CMV',
                     #  (FOR LIVING Donor, PRE UNET DATA ONLY)
                     'HEP_C_ANTI_DON': 'Donor antibody TO HEP C virus result',
                     'HIST_DIABETES_DON': 'Donor history/duration of diabetes',
                     # 'DIABDUR_DON': 'Donor diabetes duration',  # belongs to above, and too many unknown
                     # 'CREAT_DON': 'Donor terminal lab creatinine',
                     'SGOT_DON': 'Donor terminal SGOT/AST',
                     'SGPT_DON': 'Donor terminal SGPT/ALT',
                     'PCO2_DON': 'Donor pCO2',
                     'ABO_DON': 'Donor blood group'}

new_thoracic_description = {
    'BW4': 'Patient BW4 antigen from WL',
    'BW6': 'Patient BW6 antigen from WL',
    # 'C1': 'Patient C1 antigen from WL',
    # 'C2': 'Patient C2 antigen from WL',
    'CIG_USE': 'Patient history of cigarette use',
    'HEMO_CO_TCR': 'Patient hemodynamics CO L/MIN at REG',
    'HEMO_CO_TRR': 'Patient hemodynamics CO L/MIN at TXP',
    'HEMO_PA_DIA_TCR': 'Patient hemodynamics PA (DIA) MM/HG at REG',
    'HEMO_PA_DIA_TRR': 'Patient hemodynamics PA (DIA) MM/HG at TXP',
    'HEMO_PA_MN_TCR': 'Patient hemodynamics PA (MEAN) MM/HG at REG',
    'HEMO_PA_MN_TRR': 'Patient hemodynamics PA (MEAN) MM/HG at TXP',
    'HEMO_PCW_TCR': 'Patient hemodynamics PCW (MEAN) MM/HG at REG',
    'HEMO_PCW_TRR': 'Patient hemodynamics PCW (MEAN) MM/HG at TXP',
    'HEMO_SYS_TCR': 'Patient hemodynamics PA (SYS) MM/HG at REG',
    'HEMO_SYS_TRR': 'Patient hemodynamics PA (SYS) MM/HG at TXP',
    # 'RA1': 'Patient A1 antigen from WL',
    # 'RA2': 'Patient A2 antigen from WL',
    # 'RB1': 'Patient B1 antigen from WL',
    # 'RB2': 'Patient B2 antigen from WL',
    # 'RDR1': 'Patient DR1 antigen from WL',
    # 'RDR2': 'Patient DR2 antigen from WL',
    # 'TXKID': 'Simultaneous kidney TXP',
    # 'TXLIV': 'Simultaneous liver TXP',
    # 'TXLNG': 'Simultaneous lung TXP',
    # 'TXPAN': 'Simultaneous pancreas TXP',
    'MULTIORG': 'Patient multi-organ TXP',
    'DIAL_TY_TCR': 'Patient type of dialysis at REG',
    # 'DQ1': 'Patient DQB1 antigen from WL',
    # 'DQ2': 'Patient DQB2 antigen from WL',
    'DR51': 'Patient DR51 antigen from WL',
    'DR52': 'Patient DR52 antigen from WL',
    'DR53': 'Patient DR53 antigen from WL',
    # 'FEV1_TRR': 'Patient FEV1 % predicted at TXP',  # being filtered
    # 'FVC_TRR': 'Patient FVC % predicted at TXP',  # being filtered for HR
    'HBV_SUR_ANTIGEN': 'Patient HEP B surface antigen',  # being filtered
    'HCV_SEROSTATUS': 'Patient HEP C status',
    'CONTIN_CIG_OLD': 'Patient cigarette recent use + > 10 PACK YRS',
    'CRSMATCH_DONE': 'Patient crossmatch done',  # being filtered
    # 'STEROID': 'Patient chronic steroid use at TXP',
    'MALIG': 'Patient previous malignancy',
    'TOT_SERUM_ALBUM': 'Patient serum albumin at REG',
    'HIST_IV_DRUG_OLD_DON': 'Donor history of IV drug use in past',  # 1994-2004
    # 'ANTIHYPE_DON': 'Donor antihypertensives in 24 hrs pre-cross clamp',
    'ARGININE_DON': 'Donor arginine vasopressin in 24 hrs pre-cross clamp',
    'DDAVP_DON': 'Donor synthetic anti diuretic hormone (DDAVP)',
    'DEATH_CIRCUM_DON': 'Donor circumstance of death',
    'DEATH_MECH_DON': 'Donor mechanism of death',
    # 'HBSAB_DON': 'Donor HBSAB test', # the donornet hbsab has less unknown
    'HBV_CORE_DON': 'Donor HBV core antibody',
    'HBV_SUR_ANTIGEN_DON': 'Donor HEP B surface antigen',  # being filtered
    'HEMATOCRIT_DON': 'Donor hematocrit',
    # 'CANCER_SITE_DON': 'Donor cancer',
    # 'CDC_RISK_HIV_DON': 'Donor risk for blood-borne disease transmission',
    'DOBUT_DON_OLD': 'Donor dobutamine in 24 hrs pre-cross clamp',  # all U, meaningless
    'DOPAMINE_DON_OLD': 'Donor DOPAMINE in 24 hrs pre-cross clamp',  # all U, meaningless
    # 'DA1': 'Donor A1 antigen from WL',
    # 'DA2': 'Donor A2 antigen from WL',
    # 'DB1': 'Donor B1 antigen from WL',
    # 'DB2': 'Donor B2 antigen from WL',
    # 'DDR1': 'Donor DR1 antigen from WL',
    # 'DDR2': 'Donor DR2 antigen from WL',
    # 'HIST_CANCER_DON': 'Donor history of cancer',  # 'N' is always 1 in cancer site
    'HEPARIN_DON': 'Donor pre-recovery heparin',
    'CONTIN_OTH_DRUG_DON': 'Donor history of other drugs + recent use',
    'HIST_OTH_DRUG_DON': 'Donor history of other drug use',
    'HIST_MI': 'Donor history of myocardial infarction (MI)',
    'INSULIN_DON': 'Donor given insulin in 24 hrs pre-cross clamp',
    # 'INTRACRANIAL_CANCER_DON': 'Donor intracanial cancer at procurement',
    'HIST_INSULIN_DEP_DON': 'Donor insulin dependent diabetes',
    # 'VDRL_DON': 'Donor RPR-VDRL result',
    'VASODIL_DON': 'Donor vasodilators pre-cross clamp',
    'CPRA': 'Patient most recent CPRA',
    'CPRA_PEAK': 'Patient peak CPRA',
    'VAD_BRAND1_TRR': 'Patient on VAD brand at TXP',  # if combine 1 and 2: same as 1
}

Decreased_Donor_description = {
    'HIST_IV_DRUGUSE': 'Donor history of IV drug use',  # 2006 - now
    # 'HR_BACK_TBL_FLUSH': 'Donor heart back table flush solution',
    # 'HR_FINAL_FLUSH': 'Donor final flush solution',
    # 'HR_INITIAL_FLUSH': 'Donor initial flush solution',
    'INOTROP_AGENTS_DON': 'Donor 3+ inotropic agents at incision',
    'CORONARY_ANGIO_DON': 'Donor coronary angiogram',
}

Donornet_description = {
    'age_in_months': 'Donor age in months',
    'wgt_kg': 'Donor weight (kg)',
    'hgt_cm': 'Donor height (cm)',
    'donor_bmi': 'Donor body mass index',
    'cardarrest_downtm_duration': 'Donor cardiac arrest/downtime',
    'cpr_admin_duration': 'Donor CPR administered Duration',
    'hist_cad': 'Donor history of coronary artery disease (CAD)',  # ['NO', 'YES']
    # 'prev_gastro_dis': 'Donor previous gastrointestinal disease',  # ['NO', 'YES']
    'chest_trauma': 'Donor chest trauma',
    # 'toxscreen': 'Donor toxicology screen',  # sanity check: same as TOXSCREEN
    # 'hba1c': 'Donor HbA1c (%)',
    # 'transfus_term': 'Donor number of transfusions in hospitalization',
    # 'other_blood': 'Donor other blood products',
    # need checking
    'hbcore_stat': 'Donor anti-HBcAb status',
    'hbv_dna': 'Donor HBV NAT',
    'hbsag': 'Donor HBsAg',
    'hbsab': 'Donor HBsAb',
    'hcv_stat': 'Donor Anti-HCV status',
    'hcv_nat': 'Donor HCV NAT',
    # 'hiv': 'Donor anti-HIV I/II',
    # 'hiv_antigen': 'Donor HIV Ag/Ab combo assay',
    # 'hiv_nat': 'Donor HIV NAT',
    'htlv': 'Donor Anti-HTLV I/II',
    # 'htlv_nat': 'Donor HTLV NAT',
    # 'cmv_stat': 'Donor anti-CMV',  # sanity check: almost same as CMV_DON, more cats
    'vdrl': 'Donor Syphilis',
    'ebv_igg': 'Donor EBV (VCA) (IgG)',
    'ebv_igm': 'Donor EBV (VCA) (IgM)',
    'ebna': 'Donor EBNA',
    'toxo_igg': 'Donor Toxoplasma (IgG)',
    'chagas_serology': 'Donor Chagas serology',
    # 'chagas_nat': 'Donor Chagas NAT',
    'west_nile_serology': 'Donor West Nile serology',
    'west_nile_nat': 'Donor West Nile NAT',
    'bw4': 'Donor BW4 antigen',
    'bw6': 'Donor BW6 antigen',
    # 'c1': 'Donor C1 antigen',
    # 'c2': 'Donor C2 antigen',
    'dr51': 'Donor DR51 antigen',
    'dr52': 'Donor DR52 antigen',
    'dr53': 'Donor DR53 antigen',
    # 'dq1': 'Donor DQB1 antigen',
    # 'dq2': 'Donor DQB2 antigen',
    # 'dqa1': 'Donor DQA1 antigen',  # filtered
    # 'dqa2': 'Donor DQA2 antigen',  # filtered
    # 'dp1': 'Donor DPB1 antigen',
    # 'dp2': 'Donor DPB2 antigen',
    # 'cit_minutes': 'Cold ischemic time in minutes',  # something wrong
    # 'warm_ischemic_tm_min': 'Warm ischemic time in minutes',
    # 'lv_eject': 'LV ejection fraction',  # sanity check: same as LV_EJECT
    'shfrac': 'Donor shortening fraction (SF)',
    'Septal_wall': 'Donor septal wall thickness', #@
    'Posterior_wall': 'Donor LV posterior wall thickness', # @
    # 'intubated_dt': 'Donor date intubated',
    'Width_aortic_knob': 'Donor aortic knob width (cm)',
    'Width_diaphragm': 'Donor diaphragm width (cm)',
    # 'Chest_circ_landmark': 'Donor chest circ./landmark (cm)',
    'Dist_rcpa_lcpa': 'Donor dist. RCPA to LCPA (cm)',
    # 'chest_xray': 'Donor chest X-ray',

    # abgs
    'ABG_PH': 'Donor arterial blood gas pH',
    'PAO2': 'Donor PaO2 (mmHg)',
    'PCO2': 'Donor PaCO2 (mmGh)',
    'HCO3': 'Donor HCO3 (mEq/L)',
    'SAO2': 'Donor SaO2 %',
    # 'MODE': 'Donor Vent Mode',
    'FIO2': 'Donor FiO2 %',
    # 'RATE': 'Donor RR rate',
    # 'TIDALVOLUME': 'Donor Ventricular Tachyardia (cc)',
    'PEEP': 'Donor positive end-expiratory pressure (cmH20)',

    # cbc
    'WBC': 'Donor WBC (thous/mcL)',
    'RBC': 'Donor RBC (mill/mcL)',
    'HGB': 'Donor HgB (g/dL)',
    'HCT': 'Donor Hct (%)',
    'PLT': 'Donor Plt (thous/mcL)',
    'BANDS': 'Donor Bands (%)',

    # # cultures
    # 'RESULT': 'Donor microbiological culture result',
    # 'TYPE': 'Donor microbiological culture type',

    # indicators
    # 'RECTYPE': 'Donor Record Type',  # (R=Range/H=Hourly)  # need double-check  # do not use it at the moment
    # 'AVG_BP_SYST': 'Donor Average Blood Pressure - Systolic',
    # 'AVG_BP_DIAST': 'Donor Average Blood Pressure - Diastolic',
    # 'HIGH_BP_SYST': 'Donor High Blood Pressure - Systolic',  # filtered
    # 'HIGH_BP_DIAST': 'Donor High Blood Pressure - Diastolic',  # filtered
    # 'LOW_BP_SYST': 'Donor Low Blood Pressure - Systolic',  # filtered
    # 'LOW_BP_DIAST': 'Donor Low Blood Pressure - Diastolic',  # filtered
    # 'LOW_BP_DURATION': 'Donor Low Blood Pressure - Duration',  # filtered
    # 'HIGH_BP_DURATION': 'Donor High Blood Pressure - Duration',  # filtered
    # 'AVG_PULSE_RANGE_START': 'Donor Average Pulse Range - Start',
    # 'AVG_PULSE_RANGE_END': 'Donor Average Pulse Range - End',
    # 'CVP_INT_RANGE_START': 'Donor CVP Int Range - Start',  # filtered
    # 'CVP_INT_RANGE_END': 'Donor CVP Int Range - End',  # filtered
    # 'CO_RANGE_START': 'Donor CO Range - Start',  # filtered
    # 'CO_RANGE_END': 'Donor CO Range - End',  # filtered
    # 'CI_RANGE_START': 'Donor CI Range - Start',  # filtered
    # 'CI_RANGE_END': 'Donor CI Range - End',  # filtered
    # 'BODYTEMP_RANGE_START': 'Donor Body Temperature Range - Start',  # filtered
    # 'BODYTEMP_RANGE_END': 'Donor Body Temperature Range - End',  # filtered
    # 'BODYTEMP_UNIT': 'Donor Body Temperature Unit',  # filtered
    # 'URINEOUTPUT_RANGE_START': 'Donor Urine Output Range - Start',  # filtered
    # 'URINEOUTPUT_RANGE_END': 'Donor Urine Output Range - End',  # filtered
    # 'PA_SYST_RANGE_START': 'Donor PA Systolic Range - Start',  # filtered
    # 'PA_SYST_RANGE_END': 'Donor PA Systolic Range - End',  # filtered
    # 'PA_DIAST_RANGE_START': 'Donor PA Diastolic Range - Start',  # filtered
    # 'PA_DIAST_RANGE_END': 'Donor PA Diastolic Range - End',  # filtered
    # 'PAMP_RANGE_START': 'Donor PAMP Range - Start',  # filtered
    # 'PAMP_RANGE_END': 'Donor PAMP Range - End',  # filtered
    # 'PCWP_RANGE_START': 'Donor PCWP Range - Start',  # filtered
    # 'PCWP_RANGE_END': 'Donor PCWP Range - End',  # filtered

    # inomeds
    # 'AGENT': 'Donor Inotropic Medication Type',
    # 'AGENT_VAL': 'Donor Agent Value',
    # 'DOSEUNITS': 'Donor Agent Dosage Units',

    # labpanels
    'SGOT': 'Donor SGOT (AST) (u/L)',
    'SGPT': 'Donor SGPT (AST) (u/L)',
    # 'AMYLASE': 'Donor Serum Amylase (u/L)',
    # 'LIPASE': 'Donor Serum Lipase (u/L)',
    'SODIUM170': 'Donor Na (mmEq/L)',
    'CL': 'Donor Cl (mmol/L)',
    'CO2': 'Donor CO2 (mmol/L)',
    'BUN': 'Donor BUN (mg/dL)',
    'CREATININE': 'Donor Creatinine (mg/dL)',  # sanity check: not the same as CREAT_DON
    'GLUCOSE': 'Donor Glucose (mg/dL)',
    'POTASSIUM': 'Donor K+ (mmol/L)',
    'BILIRUBIN': 'Donor Total Bilirubin (mg/dL)',
    # 'BILIRUBIN_DIRECT': 'Donor Direct Bilirubin (mg/dL)',
    # 'BILIRUBIN_INDIRECT': 'Donor Indirect Bilirubin (mg/dL)',
    # 'ALKPHOS': 'Donor Alkaline Phosphatase (u/L)',
    # 'GLOBULIN': 'Donor GGT (u/L)',
    'LDH': 'Donor LDH (u/L)',
    'ALBUMIN': 'Donor Albumin (g/dL)',
    'PROTEIN': 'Donor Total Protein (g/dL)',
    'PROTHROMBIN': 'Donor Prothrombin (PT) (seconds)',
    'INR': 'Donor INR',
    # 'PTT': 'Donor PTT (seconds)',
    # 'LIPASE_UPPER': 'Donor Serum Lipase Normal Upper Limit (u/L)',

    # labvalues
    'CPK': 'Donor CPK (u/L)',
    'CKMB': 'Donor CK-MB (ng/mL)',
    'TROPONINT': 'Donor Troponin T (ng/mL)',
    'TROPONINI': 'Donor Troponin I (ng/mL)',
    # 'TOXSCREEN': 'Donor Toxicology Screen',
    'HBA1C': 'Donor HBA1C (%)',

    # pumpvalues
    # 'FLOW': 'Donor Flow (cc/min)',
    # 'PRESSURE_DIAST': 'Donor Pressure (Diastolic) (mmHg)',
    # 'PRESSURE_SYST': 'Donor Pressure (Systolic) (mmHg)',
    # 'RESISTANCE': 'Donor Resistance',  # filtered

    # check redundant variable names
    # urinalysis
    # 'PH': 'Donor urine pH',
    # 'SPECGRAV': 'Donor specific gravity',
    # 'PROTEIN_urinalysis': 'Donor urine Protein',
    # 'GLUCOSE_urinalysis': 'Donor urine Glucose',
    # 'BLOOD': 'Donor urine blood',
    # 'RBC_urinalysis': 'Donor urine RBC',
    # 'WBC_urinalysis': 'Donor urine WBC',
    # 'EPITH': 'Donor urine Epith',
    # 'CASTS': 'Donor urine casts',
    # 'BACTERIA': 'Donor urine Bacteria',
    # 'LEUKOCYTE_EST': 'Donor urine Leukocyte esterase',
}

baseline_new = {
    'VAD': 'Patient using VAD',
    'Hospitalized': 'Patient hospitalized',
    'total_days': 'Patient total days in UNOS statuses',
}

WL_static_descriptions = {
    # 'INIT_STAT': 'Patient initial waitlist status',
    'INIT_AGE': 'Patient age in years',
    'INIT_BMI_CALC': 'Patient body mass index',
    'INIT_WGT_KG_CALC': 'Patient weight at listing (kg)',
    'MALIG_TCR': 'Patient previous malignancy at REG',
    'INIT_HGT_CM_CALC': 'Patient height at listing (cm)',
    'LISTYR': 'Patients years on the waiting list',
}

WL_dynamic_descriptions = {
    "CANDHISTNUMHOSPADMN": "Number of Hospital Admissions in 12 Months",
    "CANDHISTNUMSTERNOTOMIES": "Total Number of Prior Sternotomies",
    "CANDHISTSTROKE": "History of Stroke",
    "CANDHISTTHROMB": "History of Peripheral Thromboembolic Events",
    "CPTESTMVO2": "Peak Oxygen Consumption (in ml/kg/min)",
    "CPTESTRER": "Respiratory Exchange Ratio (RER)",
    "CPTESTVEVCO2": "VE/VCO2",
    "CURRTHERANTIARRHYTHMICS": "On Anti-Arrhythmics",
    "CURRTHERBUMETANIDE": "Bumetanide Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHERBUMETANIDEDOSETYPE": "Bumetanide Cumulative 24 Hour Dosage Type",
    "CURRTHERCHLOROTHIAZIDE": "Chlorothiazide Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHERCHLOROTHIAZIDEDOSETYPE": "Chlorothiazide Cumulative 24 Hour Dosage Type",
    "CURRTHERDOBUTAMINE": "Dobutamine Cumulative 24 Hour Dosage Value (in mcg/kg/min)",
    "CURRTHERDOPAMINE": "Dopamine Cumulative 24 Hour Dosage Value (in mcg/kg/min)",
    "CURRTHEREPINEPHRINE": "Epinephrine Cumulative 24 Hour Dosage Value (in mcg/kg/min)",
    "CURRTHERFUROSEMIDE": "Furosemide Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHERFUROSEMIDEDOSETYPE": "Furosemide Cumulative 24 Hour Dosage Type",
    "CURRTHERMECHVENT": "On Continuous Invasive Mechanical Ventilation",
    "CURRTHERMETOLAZONE": "Metolazone Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHERMETOLAZONEDOSETYPE": "Metolazone Cumulative 24 Hour Dosage Type",
    "CURRTHERMILRINONE": "Milrinone Cumulative 24 Hour Dosage Value (in mcg/kg/min)",
    "CURRTHERNOREPHINEPHRINE": "Epinephrine Cumulative 24 Hour Dosage Type (in mcg/kg/min)",
    "CURRTHERONDIALYSIS": "On Dialysis",
    "CURRTHERONLOOPDIURETIC": "On a Diuretic",
    "CURRTHEROTHERDIURETICDOSE": "Other Diuretic Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHEROTHERDIURETICDOSETYPE": "Other Diuretic Cumulative 24 Hour Dosage Type",
    "CURRTHERPULVAS": "On Pulmonary Vasodilators",
    "CURRTHERPULVASTYPE": "Type of Pulmonary Vasodilators",
    "CURRTHERTORSEMIDE": "Torsemide Cumulative 24 Hour Dosage Value (in mg)",
    "CURRTHERTORSEMIDEDOSETYPE": "Torsemide Cumulative 24 Hour Dosage Type",
    "CURRTHERVASOACTIVESUPPORT": "On Vasoactive Support",
    "CURRTHERVASOPRESSIN": "Vasopressin Cumulative 24 Hour Dosage Value (in units/min)",
    "HEMOCARDIACINDEX": "Cardiac Index (in L/min/m²)",
    # "HEMOCARDIACOUTPUT": "Cardiac Output (in L/min)",
    "HEMOCVP": "Central Venous Pressure (in mmHg)",
    # "HEMODATAOBTAINED": "Most Recent Hemodynamic Data - Hemo Data Obtained Using",
    "HEMODBP": "Diastolic Blood Pressure (in mmHg)",
    "HEMOHEMOGLOBIN": "Hemoglobin at Time of SvO2 (in g/dL)",
    "HEMOLVEDP": "LVEDP (in mmHg)",
    "HEMOMEANPRESSURE": "Mean Pulmonary Artery Pressure (in mmHg)",
    "HEMOOBTAINEDONSUPPORT": "Support (Device/Inotrope)",
    "HEMOPADP": "Pulmonary Artery Diastolic Pressure (in mmHg)",
    "HEMOPASP": "Pulmonary Artery Systolic Pressure (in mmHg)",
    "HEMOPCWP": "PCWP (in mmHg)",
    # "HEMOPCWPLVEDPPERF": "Most Recent Hemodynamic Data - Value Obtained for PCWP or LVEDP",
    # "HEMOPCWPORLVEDP": "Most Recent Hemodynamic Data - PCWP or LVEDP",
    "HEMORESTINGHEARTRATE": "Resting Heart Rate (in bpm)",
    "HEMOSBP": "Systolic Blood Pressure (in mmHg)",
    "HEMOSVO2": "Mixed Venous Oxygen Saturation (SvO2) (in %)",
    "HRSEVFAILALBUMIN": "Serum Albumin (g/dL)",
    "HRSEVFAILARTERIALLACT": "Arterial Lactate (mmol/L)",
    "HRSEVFAILASPARTRANS": "AST (U/L)",
    "HRSEVFAILBILIRUBIN": "Serum Bilirubin (mg/dL)",
    "HRSEVFAILBNP": "BNP (pg/mL)",
    "HRSEVFAILBUN": "BUN (mg/dL)",
    "HRSEVFAILCREATININE": "Serum Creatinine (mg/dL)",
    "HRSEVFAILINR": "INR",
    "HRSEVFAILINRANTICOAG": "On Oral Anticoagulant when INR was Obtained",
    # "HRSEVFAILNTBNPTYPE": "BNP Test Type",
    "HRSEVFAILSODIUM": "Serum Sodium (mEq/L)",
    "SENDATACPRA": "CPRA (%)",
    "SENDATAMFITHRESHOLD": "Sensitization - MFI Threshold (MFI)",
    #"SENDATAPRAMETHOD": "Most Recent Sensitization Data - PRA Typing Method",
    "VADHEMOGLOBINURIA": "Has the Candidate Experienced Hemoglobinuria",
    "VADLDHLEVELS": "LDH (U/L)",
    "VADPLASMAFREEHEMO": "Plasma Free Hemoglobin (mg/dL)",
}

WL_test_values_mapping = {
    "CHG_DATETIME": ["CURRTHERANTIARRHYTHMICS", "CURRTHERBUMETANIDE", "CURRTHERBUMETANIDEDOSETYPE",
                     "CURRTHERCHLOROTHIAZIDE", "CURRTHERCHLOROTHIAZIDEDOSETYPE", "CURRTHERDOBUTAMINE",
                     "CURRTHERDOPAMINE", "CURRTHEREPINEPHRINE", "CURRTHERFUROSEMIDE", "CURRTHERFUROSEMIDEDOSETYPE",
                     "CURRTHERMECHVENT", "CURRTHERMETOLAZONE", "CURRTHERMETOLAZONEDOSETYPE", "CURRTHERMILRINONE",
                     "CURRTHERNOREPHINEPHRINE", "CURRTHERONDIALYSIS", "CURRTHERONLOOPDIURETIC",
                     "CURRTHEROTHERDIURETICDOSE", "CURRTHEROTHERDIURETICDOSETYPE", "CURRTHERPULVAS",
                     "CURRTHERPULVASTYPE", "CURRTHERTORSEMIDE", "CURRTHERTORSEMIDEDOSETYPE",
                     "CURRTHERVASOACTIVESUPPORT", "CURRTHERVASOPRESSIN",
                     "CANDHISTNUMHOSPADMN",
                     "CANDHISTNUMSTERNOTOMIES",
                     "CANDHISTSTROKE",
                     "CANDHISTTHROMB",
                     ],
    "CPTESTDT": ["CPTESTMVO2", "CPTESTRER", "CPTESTVEVCO2"],
    "HEMODT": ["HEMOCARDIACINDEX", # HEMOCARDIACOUTPUT",
               "HEMOCVP",
               # "HEMODATAOBTAINED",
               "HEMODBP",
               "HEMOHEMOGLOBIN", "HEMOLVEDP", "HEMOMEANPRESSURE", "HEMOOBTAINEDONSUPPORT",
               "HEMOPADP", "HEMOPASP", "HEMOPCWP", "HEMORESTINGHEARTRATE", "HEMOSBP", "HEMOSVO2"],
    "HRSEVFAILALBUMINDT": ["HRSEVFAILALBUMIN"],
    "HRSEVFAILARTERIALLACTDT": ["HRSEVFAILARTERIALLACT"],
    "HRSEVFAILASPARTRANSDT": ["HRSEVFAILASPARTRANS"],
    "HRSEVFAILBILIRUBINDT": ["HRSEVFAILBILIRUBIN"],
    "HRSEVFAILBNPDT": ["HRSEVFAILBNP", "HRSEVFAILNTBNPTYPE"],
    "HRSEVFAILBUNDT": ["HRSEVFAILBUN"],
    "HRSEVFAILCREATININEDT": ["HRSEVFAILCREATININE"],
    "HRSEVFAILINRDT": ["HRSEVFAILINR", "HRSEVFAILINRANTICOAG"],
    "HRSEVFAILSODIUMDT": ["HRSEVFAILSODIUM"],
    "SENDATADT": ["SENDATACPRA", "SENDATAMFITHRESHOLD"],  # "SENDATAPRAMETHOD" # we do not know what each category means
    "VADLDHLEVELSDT": ["VADHEMOGLOBINURIA", "VADLDHLEVELS"],
    "VADPLASMAFREEHEMODT": ["VADPLASMAFREEHEMO"]
}

WL_test_names = {
    "CPTESTDT": "Cardiac Pulmonary Stress Test",
    "HEMODT": "Hemodynamic Data",
    "HRSEVFAILALBUMINDT": "Serum Albumin Test",
    "HRSEVFAILARTERIALLACTDT": "Arterial Lactate Test",
    "HRSEVFAILASPARTRANSDT": "AST Test",
    "HRSEVFAILBILIRUBINDT": "Serum Bilirubin Test",
    "HRSEVFAILBNPDT": "BNP Test",
    "HRSEVFAILBUNDT": "BUN Test",
    "HRSEVFAILCREATININEDT": "Serum Creatinine Test",
    "HRSEVFAILINRDT": "INR Test",
    "HRSEVFAILSODIUMDT": "Serum Sodium Test",
    "SENDATADT": "Sensitization Assessment",
    "VADLDHLEVELSDT": "LDH Test",
    "VADPLASMAFREEHEMODT": "Plasma Free Hemoglobin Test"
}

others_description = {
    'ptr_sequence_num': 'Rank on Donor Match Run',
    # 'offer_time_days': 'Patient Waiting Time (Days)',
    'donor_patient_distance_km': 'Distance (km) between donor and recipient',
}

followup_description = {
    # These are aligned with waitlist longitudinal
    'CREAT': 'Serum Creatinine (mg/dL)',
    'FUNC_STAT': 'Patient functional status',
    'DIAB': 'Patient diabetes mellitus',
    'CHRONIC_DIAL': 'On Dialysis',
    # 'BMI': 'Patient body mass index',
    'HOSP': 'Number of Hospital Admissions in 12 Months',
    # 'WGT_KG': 'Patient Weight (kg)',
    # 'HGT_CM': 'Patient Height (cm)',
    # These are new
    'ACUTE_REJ_EPI': 'Patient Acute Rejection',
    'GRF_STAT': 'Patient Graft Functioning',
    'EJFRAC': 'Patient Ejection Fraction (%)',
    'RENAL_TX': 'Renal Transplant Post-Thoracic TX',
    'CORART': 'Coronary Artery Disease',
    'HOSP_INF': 'Hospitalized for Infection',
    'HOSP_REJ': 'Hospitalized for Rejection',
    'IMMUNO_MAINT_MED': 'On Maintenance Immunosuppression',
    'PACE': 'Permanent Pacemaker Inserted',
    'WORK_INCOME': 'Working for Income',
}


merged_descriptions = {**base_descriptions, **new_thoracic_description, **Donornet_description, **baseline_new,
                       **Decreased_Donor_description, **WL_static_descriptions, **WL_dynamic_descriptions,
                       **others_description, **followup_description}

