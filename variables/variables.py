default_TXP_variables = ['PType', 'TXPSurv', 'WLType', 'PSTATUS', 'WL_ID_CODE']

default_WL_variables = ['WL_ID_CODE', 't',]  # , 'event', 'WLSurv', 'WLType', 'PType',

baseline_TXP_variable = ['AGE', 'GENDER', 'EDUCATION', 'CITIZENSHIP',
                     'WGT_KG_CALC', 'HGT_CM_CALC',  # need height temporarily to calculate hemodynamics
                     'BMI_CALC', 'ETHCAT',
                     'TCR_DGN',
                     # acuity
                     'DAYSWAIT_CHRON',
                     # 'DAYS_STAT1A', 'DAYS_STAT1B', 'DAYS_STAT2', 'DAYS_STATA1', 'DAYS_STATA2',
                     # 'DAYS_STATA3', 'DAYS_STATA4', 'DAYS_STATA5', 'DAYS_STATA6',  # 'DAYS_STAT1' too many 0s
                     #'GSTATUS',
                     'FUNC_STAT_TRR',
                     'DIAB', 'CEREB_VASC',
                     # CEREB_VASC has Y, N, U, NA. Probably need to treat U and NA the same?
                     'INFECT_IV_DRUG_TRR',  # is this the Infection that previous papers use?
                     # 'HIV_NAT', 'HIV_SEROSTATUS',  # both are about HIV, but how to use them synergistically?
                     'CMV_STATUS', 'CMV_IGG', 'CMV_IGM',
                     'EBV_SEROSTATUS', 'HBV_CORE', 'HBV_NAT',  # NAT has too many missing values
                     # 'DIAL_PRIOR_TX',
                     'DIAL_AFTER_LIST',  # DIAL_AFTER_LIST is more complete, may need to merge
                     'TRANSFUSIONS',
                     'NUM_PREV_TX',  # complete, but is numerical, need to convert to Y/N  # good num/cat fail example
                     'PRIOR_CARD_SURG_TRR',  # need to merge
                     # 'ICU',  # Could be replaced by 'MED_COND_TRR'
                     ## 'INTUBATED_72HOURS',  # many missing values
                     'MED_COND_TRR',  # 1 ICU, 2 Hospitalized not ICU, 3 Not hospitalized
                     # treatment & support
                     'INOTROPES_TRR',  # 'INOTROPIC' has too many missing values
                     'VENTILATOR_TRR',
                     'VENT_SUPPORT_TRR',
                     # 'ONVENT' has too many missing values
                     'ECMO_TRR',
                     'IABP_TRR',
                     'PGE_TRR',  # this is prostaglandins

                     'VAD_DEVICE_TY_TRR', # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     ## 'VAD_TAH_TRR',
                     # 'TAH' too many missing values
                     'IMPL_DEFIBRIL',  # this is ICD
                     'TX_YEAR',
                     # immunology
                     'PRAMR_CL1', 'PRAMR_CL2', 'PRAMR',  # 'PRAMR' is old, the other two are new, need to merge
                     'PRAPK_CL1', 'PRAPK_CL2', 'PRAPK',  # the peak pra, same as pramr
                     # 'AMIS', 'BMIS', 'HLAMIS', 'DRMIS',
                     'ABO',
                     'CREAT_TRR', 'MOST_RCNT_CREAT',  # 'INIT_CREAT',
                     'TBILI',

                     # start from here, all donor variables
                     'AGE_DON',
                     'GENDER_DON', 'CITIZENSHIP_DON',
                     # 'WGT_KG_DON_CALC',  # only used for normalizing other variables
                     # 'HGT_CM_DON_CALC',
                     # 'BMI_DON_CALC',
                     'ETHCAT_DON',
                     # 'COD_CAD_DON',
                     # need to calculate recipient-donor ratio/difference using the following:
                     'DISTANCE', 'ABO_MAT', 'ISCHTIME',
                     # acuity
                     'LV_EJECT',
                     # 'HIST_CIG_DON', 'CONTIN_CIG_DON',
                     # 'HIST_COCAINE_DON', 'CONTIN_COCAINE_DON',
                     # 'HIST_ALCOHOL_OLD_DON', 'ALCOHOL_HEAVY_DON',   # CONTIN_ALCOHOL_OLD_DON has many missing values
                     # 'HIST_HYPERTENS_DON',
                     # 'CLIN_INFECT_DON',
                     # for the above variable, depending on from what source is it confirmed:
                     # 'PULM_INF_DON', 'URINE_INF_DON', 'BLOOD_INF_DON', 'OTHER_INF_DON',
                     # 'INOTROP_SUPPORT_DON',
                     'CMV_DON',
                     # 'HIST_INSULIN_DEP_DON' has too many missing values
                     'HEP_C_ANTI_DON',
                     # 'HIST_DIABETES_DON',  # this includes length
                     ## 'DIABETES_DON',  # this is Y/N
                     # 'DIABDUR_DON',  # need to decide which to use
                     # 'CREAT_DON',
                     'SGPT_DON',
                     'PCO2_DON',
                     'ABO_DON',]

new_thoracic_TXP_variables = [# 'BW4', 'BW6',
                              # 'C1', 'C2',
                     'CIG_GRT_10_OLD', 'CIG_USE',
                     'HEMO_CO_TRR', 'HEMO_PA_DIA_TRR',
                     'HEMO_PA_MN_TRR', 'HEMO_PCW_TRR',
                     'HEMO_SYS_TRR',  # 'RA1', 'RA2', 'RB1', 'RB2', 'RDR1', 'RDR2',
                     'MULTIORG',
                     # 'DQ1', 'DQ2',
                     # 'DR51', 'DR52', 'DR53',
                     # 'FEV1_TRR', 'FVC_TRR',
                     'HBV_SUR_ANTIGEN', 'HCV_SEROSTATUS', 'CONTIN_CIG_OLD',
                     # 'STEROID',
                     'MALIG', 'TOT_SERUM_ALBUM', 'HIST_IV_DRUG_OLD_DON',
                     # 'ANTIHYPE_DON',
                     'ARGININE_DON',
                     'DDAVP_DON',  # 'DEATH_CIRCUM_DON', 'DEATH_MECH_DON',
                     ## 'HBSAB_DON',
                     'HBV_CORE_DON', 'HBV_SUR_ANTIGEN_DON', 'HEMATOCRIT_DON',
                     # 'CANCER_SITE_DON',
                     # 'CDC_RISK_HIV_DON',
                     ## 'DOBUT_DON_OLD', 'DOPAMINE_DON_OLD',
                     # 'DA1', 'DA2', 'DB1', 'DB2', 'DDR1', 'DDR2',
                     ## 'HIST_CANCER_DON',
                     'HEPARIN_DON', 'CONTIN_OTH_DRUG_DON',
                     'HIST_OTH_DRUG_DON', 'HIST_MI', 'INSULIN_DON',
                     # 'INTRACRANIAL_CANCER_DON', 'VDRL_DON',
                     'VASODIL_DON', 'CPRA', 'CPRA_PEAK', 'VAD_BRAND1_TRR',
]

donor_TXP_variables = ['HIST_IV_DRUGUSE',  # 'HR_BACK_TBL_FLUSH', 'HR_FINAL_FLUSH', 'HR_INITIAL_FLUSH',
                       'INOTROP_AGENTS_DON', 'CORONARY_ANGIO_DON',
]

donornet_TXP_variables = ['age_in_months', 'wgt_kg', 'hgt_cm', 'donor_bmi',
                          'cardarrest_downtm_duration', 'cpr_admin_duration', 'hist_cad',
                          # 'prev_gastro_dis', 'chest_trauma', 'hba1c', 'other_blood',
                      # 'transfus_term',
                      # 'hbcore_stat',
                      'hbv_dna',
                      'hbsag', 'hbsab', 'hcv_nat',  #  'hiv', 'hiv_antigen', 'hiv_nat',
                      # 'hcv_stat',
                      'htlv',
                      # 'htlv_nat', too few
                      # 'cmv_stat',
                      'vdrl', 'ebv_igg', 'ebv_igm', 'ebna',  'toxo_igg', 'chagas_serology',
                      # 'chagas_nat', too few
                      'west_nile_serology', 'west_nile_nat', # 'bw4', 'bw6',
                      # 'c1', 'c2',
                      # 'dr51', 'dr52', 'dr53',
                      # 'dq1', 'dq2', 'dqa1', 'dqa2', 'dp1', 'dp2',
                      # 'cit_minutes', 'warm_ischemic_tm_min',
                      'shfrac', 'Septal_wall',
                      'Posterior_wall', 'Width_aortic_knob', 'Width_diaphragm',
                      # 'Chest_circ_landmark',
                      'Dist_rcpa_lcpa', # 'chest_xray',

                      # abgs
                      'ABG_PH', 'PAO2', 'PCO2', 'HCO3', 'SAO2',  # 'MODE',
                      'FIO2',  # 'RATE', 'TIDALVOLUME',
                      'PEEP',
                      # cbc
                      'WBC', 'RBC', 'HGB', 'HCT', 'PLT', 'BANDS',
                      ## culture
                      # 'RESULT', 'TYPE',

                      ## 'RECTYPE',
                      # 'AVG_BP_SYST', 'AVG_BP_DIAST', 'AVG_PULSE_RANGE_START', 'AVG_PULSE_RANGE_END',
                      # 'HIGH_BP_SYST', 'HIGH_BP_DIAST', 'LOW_BP_SYST',
                      # 'LOW_BP_DIAST', 'LOW_BP_DURATION', 'HIGH_BP_DURATION',  'CVP_INT_RANGE_START', 'CVP_INT_RANGE_END', 'CO_RANGE_START',
                      # 'CO_RANGE_END', 'CI_RANGE_START', 'CI_RANGE_END', 'BODYTEMP_RANGE_START', 'BODYTEMP_RANGE_END',
                      # 'BODYTEMP_UNIT', 'URINEOUTPUT_RANGE_START', 'URINEOUTPUT_RANGE_END', 'PA_SYST_RANGE_START',
                      # 'PA_SYST_RANGE_END', 'PA_DIAST_RANGE_START', 'PA_DIAST_RANGE_END', 'PAMP_RANGE_START',
                      # 'PAMP_RANGE_END', 'PCWP_RANGE_START', 'PCWP_RANGE_END',

                      # 'AGENT', 'AGENT_VAL', 'DOSEUNITS',

                      'SGOT', 'SGPT',  # 'AMYLASE', 'LIPASE',
                      'SODIUM170', 'CL', 'CO2', 'BUN', 'CREATININE', 'GLUCOSE',
                      'POTASSIUM', 'BILIRUBIN',  # 'BILIRUBIN_DIRECT', 'BILIRUBIN_INDIRECT', 'ALKPHOS', 'GLOBULIN',
                      'LDH', 'ALBUMIN', 'PROTEIN', 'PROTHROMBIN', 'INR',  # 'PTT', 'LIPASE_UPPER',

                      'CPK', 'CKMB', 'TROPONINI',  # 'TOXSCREEN',
                      'HBA1C', 'TROPONINT',
                      # check redundant variable names
                      ]

# 'CHEST_XRAY_DON' is for lung
# SYNTHETIC ANTI DIURETIC HORMONE (DDAVP_DON) seems to be similar to (ARGININE_DON)

# print([item for item in patient_variables if item not in baseline_variables])

DRI_TXP_variables = ['TCR_DGN',
                     # acuity

                     # start from here, all donor variables
                     'AGE_DON', 'GENDER_DON', 'ETHCAT_DON',
                     # need to calculate recipient-donor ratio/difference using the following:
                     'ISCHTIME',
                     # acuity
                     'LV_EJECT',
                     'HIST_CIG_DON', 'CONTIN_CIG_DON',
                     'HIST_HYPERTENS_DON',
                     'CLIN_INFECT_DON',
                     'CMV_DON',
                     'CREAT_DON']

RSS_TXP_variables = ['AGE', 'GENDER',
                     'TCR_DGN',
                     # acuity

                     'DIAB', 'CEREB_VASC',
                     'PRIOR_CARD_SURG_TRR',  # need to merge
                     'ICU',  # Could be replaced by 'MED_COND_TRR'
                     # 'INTUBATED_72HOURS',  # many missing values
                     'MED_COND_TRR',  # 1 ICU, 2 Hospitalized not ICU, 3 Not hospitalized
                     # treatment & support
                     'ECMO_TRR',
                     'VAD_DEVICE_TY_TRR',  # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     # 'VAD_TAH_TRR',  # missing values
                     # immunology
                     'TBILI',

                     # start from here, all donor variables
                     'AGE_DON', 'GENDER_DON', 'ISCHTIME',
                     # acuity
                     # 'HIST_INSULIN_DEP_DON' has too many missing values
                     'HEP_C_ANTI_DON']

IMPACT_TXP_variables = ['AGE', 'GENDER', 'ETHCAT', 'TCR_DGN',
                     # acuity
                     'INFECT_IV_DRUG_TRR',  # is this the Infection that previous papers use?
                     # 'DIAL_PRIOR_TX',
                     # treatment & support
                     'VENTILATOR_TRR', 'VENT_SUPPORT_TRR',
                     # 'ONVENT' has too many missing values
                     'ECMO_TRR',
                     'IABP_TRR',
                     # 'TAH' too many missing values
                     'TBILI']

IHTSA_TXP_variables = ['AGE', 'GENDER', 'HGT_CM_CALC', 'WGT_KG_CALC',
                     'TCR_DGN',
                     # acuity
                     'DAYS_STAT1A', 'DAYS_STAT1B', 'DAYS_STAT2',
                     # 'GSTATUS',
                     'DIAB',
                     # CEREB_VASC has Y, N, U, NA. Probably need to treat U and NA the same?
                     'INFECT_IV_DRUG_TRR',  # is this the Infection that previous papers use?
                     'DIAL_PRIOR_TX', 'DIAL_AFTER_LIST',  # DIAL_AFTER_LIST is more complete, may need to merge
                     'TRANSFUSIONS',
                     'NUM_PREV_TX',  # complete, but is numerical, need to convert to Y/N  # good num/cat fail example
                     'PRIOR_CARD_SURG_TRR',  # need to merge
                     'ICU',  # Could be replaced by 'MED_COND_TRR'
                     # treatment & support
                     'VENTILATOR_TRR', 'VENT_SUPPORT_TRR',
                     # 'ONVENT' has too many missing values
                     'ECMO_TRR',
                     'IABP_TRR',
                     'VAD_DEVICE_TY_TRR',  # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     # 'TAH' too many missing values
                     'TX_YEAR',
                     # immunology
                     'PRAMR_CL1', 'PRAMR_CL2', 'PRAMR',  # 'PRAMR' is old, the other two are new, need to merge
                     'DRMIS', 'HLAMIS',
                     'ABO',
                     'CREAT_TRR', 'INIT_CREAT', 'MOST_RCNT_CREAT',
                     'TBILI',

                     # start from here, all donor variables
                     'AGE_DON', 'GENDER_DON', 'WGT_KG_DON_CALC',
                     # need to calculate recipient-donor ratio/difference using the following:
                     'HGT_CM_DON_CALC', 'ISCHTIME',
                     'ABO_DON']

ToRsR_TXP_variables = ['AGE', 'GENDER', 'BMI_CALC',
                     # acuity
                     'DAYS_STAT1A', 'DAYS_STAT1B', 'DAYS_STAT2',
                     'DIAB',
                     'INFECT_IV_DRUG_TRR',  # is this the Infection that previous papers use?
                     'TRANSFUSIONS',
                     # treatment & support
                     'INOTROPES_TRR',  # 'INOTROPIC' has too many missing values
                     'VENTILATOR_TRR', 'VENT_SUPPORT_TRR',
                     # 'ONVENT' has too many missing values
                     'ECMO_TRR',
                     'IABP_TRR',
                     'VAD_DEVICE_TY_TRR',  # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     # 'TAH' too many missing values
                     'TX_YEAR',
                     # immunology
                     'PRAMR_CL1', 'PRAMR_CL2', 'PRAMR',  # 'PRAMR' is old, the other two are new, need to merge
                     'AMIS', 'BMIS', 'HLAMIS', 'DRMIS',
                     'ABO',
                     'CREAT_TRR', 'INIT_CREAT', 'MOST_RCNT_CREAT',
                     'TBILI',

                     # start from here, all donor variables
                     'AGE_DON', 'GENDER_DON', 'BMI_DON_CALC',
                     # need to calculate recipient-donor ratio/difference using the following:
                     'DISTANCE', 'ABO_MAT', 'ISCHTIME',
                     # acuity
                     'HEP_C_ANTI_DON',
                     'HIST_DIABETES_DON',  # need to decide which to use
                     # 'DIABETES_DON',  # need to decide which to use
                     # 'DIABDUR_DON',  # need to decide which to use
                     'ABO_DON']

SOTA_TXP_variables = ['AGE', 'GENDER', 'EDUCATION', 'HGT_CM_CALC', 'BMI_CALC', 'ETHCAT',
                     'TCR_DGN',
                     # acuity
                     'DAYSWAIT_CHRON',
                     'DAYS_STAT1A',
                     'DIAB',
                     'HIV_NAT', 'HIV_SEROSTATUS',  # both are about HIV, but how to use them synergistically?
                     'CMV_STATUS', 'CMV_IGG', 'CMV_IGM',
                     'EBV_SEROSTATUS', 'HBV_CORE', 'HBV_NAT',  # NAT has too many missing values
                     'NUM_PREV_TX',  # complete, but is numerical, need to convert to Y/N  # good num/cat fail example
                     'PRIOR_CARD_SURG_TRR',  # need to merge

                     # treatment & support
                     'INOTROPES_TRR',  # 'INOTROPIC' has too many missing values
                     'VENTILATOR_TRR', 'VENT_SUPPORT_TRR',
                     # 'ONVENT' has too many missing values
                     'VAD_DEVICE_TY_TRR',  # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     'IMPL_DEFIBRIL',  # this is ICD
                     'TX_YEAR',

                     'CREAT_TRR', 'INIT_CREAT', 'MOST_RCNT_CREAT',

                     # start from here, all donor variables
                     'AGE_DON', 'GENDER_DON', 'BMI_DON_CALC', 'ETHCAT_DON',  # 'COD_CAD_DON',
                     # need to calculate recipient-donor ratio/difference using the following:
                     'DISTANCE', 'ABO_MAT', 'ISCHTIME',
                     # acuity
                     'HIST_COCAINE_DON', 'CONTIN_COCAINE_DON',
                     'HIST_ALCOHOL_OLD_DON', 'ALCOHOL_HEAVY_DON',   # CONTIN_ALCOHOL_OLD_DON has many missing values
                     'HIST_HYPERTENS_DON',
                     'INOTROP_SUPPORT_DON',
                     # 'HIST_INSULIN_DEP_DON' has too many missing values
                     'CREAT_DON',
                     'SGPT_DON',
                     'PCO2_DON']

ours_WL_variable = ['INIT_AGE', 'GENDER', 'EDUCATION',
                    'CITIZENSHIP',  # not significant
                     'INIT_WGT_KG_CALC', 'INIT_HGT_CM_CALC',  # need height temporarily to calculate hemodynamics
                     'INIT_BMI_CALC', 'ETHCAT',
                     'TCR_DGN',
                     # acuity
                     'INIT_STAT',
                     'FUNC_STAT_TCR',
                     'DIAB', 'CEREB_VASC',
                     'DIAL_TY_TCR',  # 'DIAL_AFTER_LIST',  # between
                     # 'TRANSFUSIONS',  # between
                     'MALIG_TCR',
                     'TOT_SERUM_ALBUM',
                     'NUM_PREV_TX',  # complete, but is numerical, need to convert to Y/N  # good num/cat fail example
                     'PRIOR_CARD_SURG_TCR',
                     'ICU',
                     'PGE_TCR',
                     'INOTROPES_TCR',  # 'INOTROPIC' has too many missing values
                     'VENTILATOR_TCR',
                     'ECMO_TCR',
                     'IABP_TCR',
                     'VAD_DEVICE_TY_TCR',  # NONE LVAD RVAD TAH LVAD+RVAD LVAD/RVAD/TAH Unspecified
                     # 'VAD_TAH_TCR',  # 20 for no, others are different brands
                     'IMPL_DEFIBRIL',  # this is ICD, IMPLANTABLE DEFIBRILLATOR
                     # 'LISTYR',  # VIF too high
                     # immunology
                     'ABO',  # not significant
                     'MOST_RCNT_CREAT',  # most recent at listing

                    # 'BW4', 'BW6', 'C1', 'C2', 'DQ1', 'DQ2', 'DR51', 'DR52', 'DR53',  # between
                    # 'RA1', 'RA2', 'RB1', 'RB2', 'RDR1', 'RDR2',  # unsure
                    'CIG_GRT_10_OLD', 'CIG_USE',  # need to merge
                    'HEMO_CO_TCR', 'HEMO_PA_DIA_TCR', 'HEMO_PA_MN_TCR', 'HEMO_PCW_TCR', 'HEMO_SYS_TCR',
                    'CONTIN_CIG_OLD',
                    ]

ours_WLHIST_variable = [
    "CANDHISTNUMHOSPADMN", "CANDHISTNUMSTERNOTOMIES", "CANDHISTSTROKE", "CANDHISTTHROMB",
    "CPTESTMVO2", "CPTESTRER", "CPTESTVEVCO2", "CURRTHERANTIARRHYTHMICS", "CURRTHERBUMETANIDE",
    "CURRTHERBUMETANIDEDOSETYPE", "CURRTHERCHLOROTHIAZIDE", "CURRTHERCHLOROTHIAZIDEDOSETYPE",
    "CURRTHERDOBUTAMINE", "CURRTHERDOPAMINE", "CURRTHEREPINEPHRINE", "CURRTHERFUROSEMIDE",
    "CURRTHERFUROSEMIDEDOSETYPE", "CURRTHERMECHVENT", "CURRTHERMETOLAZONE",
    "CURRTHERMETOLAZONEDOSETYPE", "CURRTHERMILRINONE", "CURRTHERNOREPHINEPHRINE",
    "CURRTHERONDIALYSIS", "CURRTHERONLOOPDIURETIC", "CURRTHEROTHERDIURETICDOSE",
    "CURRTHEROTHERDIURETICDOSETYPE", "CURRTHERPULVAS", "CURRTHERPULVASTYPE",
    "CURRTHERTORSEMIDE", "CURRTHERTORSEMIDEDOSETYPE", "CURRTHERVASOACTIVESUPPORT",
    "CURRTHERVASOPRESSIN",
    # "DONCRIT_ACPT_ABO_INCOMP", "DONCRIT_ACPT_DCD",
    # "DONCRIT_ACPT_DCD_IMPORT", "DONCRIT_ACPT_HBCOREPOS", "DONCRIT_ACPT_HBV_NAT_POS",
    # "DONCRIT_ACPT_HCV_NAT_POS", "DONCRIT_ACPT_HCVPOS", "DONCRIT_ACPT_HIST_CAD",
    # "DONCRIT_ACPT_HIST_CIG", "DONCRIT_ACPT_HTLV_POS", "DONCRIT_GENDER_REQ",
    # "DONCRIT_MAX_AGE", "DONCRIT_MAX_AGE_IMPORT", "DONCRIT_MAX_HGT", "DONCRIT_MAX_HGT_IMPORT",
    # "DONCRIT_MAX_MILE", "DONCRIT_MAX_WGT", "DONCRIT_MAX_WGT_IMPORT", "DONCRIT_MIN_AGE",
    # "DONCRIT_MIN_AGE_IMPORT", "DONCRIT_MIN_HGT", "DONCRIT_MIN_HGT_IMPORT", "DONCRIT_MIN_WGT",
    # "DONCRIT_MIN_WGT_IMPORT",
    "HEMOCARDIACINDEX",  # "HEMOCARDIACOUTPUT",
    "HEMOCVP",
    # "HEMODATAOBTAINED",
    "HEMODBP",
    "HEMOHEMOGLOBIN", "HEMOLVEDP", "HEMOMEANPRESSURE", "HEMOOBTAINEDONSUPPORT",
    "HEMOPADP", "HEMOPASP", "HEMOPCWP", "HEMORESTINGHEARTRATE", "HEMOSBP", "HEMOSVO2", "HRSEVFAILALBUMIN",
    "HRSEVFAILARTERIALLACT", "HRSEVFAILASPARTRANS", "HRSEVFAILBILIRUBIN", "HRSEVFAILBNP",
    "HRSEVFAILBUN", "HRSEVFAILCREATININE", "HRSEVFAILINR", "HRSEVFAILINRANTICOAG",
    "HRSEVFAILSODIUM", "SENDATACPRA", "SENDATAMFITHRESHOLD",  # "HRSEVFAILNTBNPTYPE",
    # "SENDATAPRAMETHOD",  # we do not know what each category means
    "VADHEMOGLOBINURIA", "VADLDHLEVELS", "VADPLASMAFREEHEMO",
]

Alshawabkeh_WL_variable = ['INIT_AGE', 'GENDER', 'ECMO_TCR', 'VENTILATOR_TCR', 'DIAL_TY_TCR',
                           # 'INIT_STAT',  # only status 1A
                           'CITIZENSHIP', 'DIAB', 'PRIOR_CARD_SURG_TCR', 'INOTROPES_TCR', 'IMPL_DEFIBRIL',
                           'VAD_DEVICE_TY_TCR', 'ABO', 'INIT_STAT'
                           ]

Jasseron_WL_variable = [  # long-term mcs and short-term mcs
    'DIAB',
    'ETHCAT', 'GENDER', 'INIT_AGE', 'MOST_RCNT_CREAT'  # Ln (eGFR),
    # Ln (bilirubin)
    #'HRSEVFAILBNP',  # Natriuretic peptide (decile)
]

Hsich_WL_variable = [  # cardiac index
    'LISTYR', 'IABP_TCR', 'ECMO_TCR', 'VAD_DEVICE_TY_TCR',  # only LVAD
    'INOTROPES_TCR', 'VENTILATOR_TCR',
    'TOT_SERUM_ALBUM',
    # 'CANDHISTSTROKE',
    'CEREB_VASC', 'MALIG_TCR',
    'CIG_GRT_10_OLD', 'CIG_USE',
    'DIAL_TY_TCR', 'DIAB', 'IMPL_DEFIBRIL', 'TCR_DGN',  # only a few
    'ABO', 'INIT_BMI_CALC', 'INIT_AGE', 'GENDER', 'ETHCAT',
    'MOST_RCNT_CREAT'  # for eGFR
]

Bakhtiyar_WL_variable = [
    # 'LISTYR',  # every five years from 1996 to 2017
    'DIAB',
    'INIT_AGE', 'INIT_BMI_CALC', 'GENDER', 'TCR_DGN',  # only a few
    'IABP_TCR', 'ECMO_TCR', 'INOTROPES_TCR', 'VENTILATOR_TCR',
    'VAD_DEVICE_TY_TCR',  # only vad
    'FUNC_STAT_TCR',  # 50% as threshold
    'INIT_STAT',  # 1, 1a, 1b
]

ours_NextOffer_variable = [
    'LISTING_CTR_CODE', 'REGION',
]

followup_variable = [
    'CREAT',
    'FUNC_STAT',
    'DIAB',
    'CHRONIC_DIAL',
    # 'BMI',
    'HOSP',
    # 'WGT_KG',  # 90% missing
    # 'HGT_CM',
    # These are new
    'ACUTE_REJ_EPI',
    'GRF_STAT',
    'EJFRAC',
    'RENAL_TX',
    'CORART',
    'HOSP_INF',
    'HOSP_REJ',
    'IMMUNO_MAINT_MED',
    'PACE',
    'WORK_INCOME',
]

# mismatch_rows = offers[offers['recipient_region'] == offers['donor_region']]

