# all should have 'U': 'Unknown'
# if you change description in variable_names.py, you have to change here
category_explanations = {
    # everything not listed should be mapped to 'U'
    'Patient gender': {'M': 'Male (Not Female)', 'F': 'Female'},
    'Donor gender': {'M': 'Male (Not Female)', 'F': 'Female'},
    'Patient race': {
        '1': 'White',
        '2': 'Black',
        **dict.fromkeys(['6', '7', '9'], 'Other'),
        '4': 'Hispanic',
        '5': 'Asian',
        # '6': 'Amer Ind/Alaska Native, Non-Hispanic',
        # '7': 'Native Hawaiian/other Pacific Islander, Non-Hispanic',
        # '9': 'Multiracial, Non-Hispanic'
    },
    'Patient primary diagnosis': {
        '999': ['Other'],
        '1000': ['Dilated cardiomyopathy', 'Idiopathic cardiomyopathy'],
        '1001': ['Dilated cardiomyopathy'],
        '1002': ['Dilated cardiomyopathy'],
        '1003': ['Dilated cardiomyopathy'],
        '1004': ['Dilated cardiomyopathy'],
        '1005': ['Dilated cardiomyopathy'],
        '1006': ['Dilated cardiomyopathy'],
        '1007': ['Dilated cardiomyopathy', 'Ischemic cardiomyopathy'],
        '1008': ['Dilated cardiomyopathy'],
        '1009': ['Dilated cardiomyopathy'],
        '1010': ['Dilated cardiomyopathy'],
        '1011': ['Dilated cardiomyopathy'],
        '1050': ['Restrictive cardiomyopathy', 'Idiopathic cardiomyopathy'],
        '1051': ['Restrictive cardiomyopathy'],
        '1052': ['Restrictive cardiomyopathy'],
        '1053': ['Restrictive cardiomyopathy'],
        '1054': ['Restrictive cardiomyopathy'],
        '1099': ['Restrictive cardiomyopathy'],
        '1100': ['Transplant graft failure/rejection'],
        '1101': ['Transplant graft failure/rejection'],
        '1102': ['Transplant graft failure/rejection', 'Ischemic cardiomyopathy'],
        '1103': ['Transplant graft failure/rejection'],
        '1104': ['Transplant graft failure/rejection', 'Restrictive cardiomyopathy'],
        '1105': ['Transplant graft failure/rejection'],
        '1106': ['Transplant graft failure/rejection'],
        '1199': ['Transplant graft failure/rejection'],
        '1200': ['Ischemic cardiomyopathy'],
        '1201': ['Hypertrophic cardiomyopathy'],
        '1202': ['Valvular cardiomyopathy'],
        '1203': ['Congenital heart disease'],
        '1204': ['Other'],
        '1205': ['Congenital heart disease'],
        '1206': ['Congenital heart disease'],
        '1207': ['Congenital heart disease'],
        '1208': ['Other'],
        '1209': ['Other'],
    },
    'Patient education': {
        # '1': 'NONE',
        # '2': 'GRADE SCHOOL (0-8)',
        # '3': 'HIGH SCHOOL (9-12) or GED',
        '1': 'None',
        '2': 'GRADE/HIGH SCHOOL',
        '3': 'GRADE/HIGH SCHOOL',
        '4': 'GRADE/HIGH SCHOOL',
        # '4': 'ATTENDED COLLEGE/TECHNICAL SCHOOL',
        '5': 'COLLEGE DEGREE',
        '6': 'GRADUATE DEGREE',
    },
    'Patient citizenship': {
        '1': 'US Citizen',
        **dict.fromkeys(['2', '3', '4', '5', '6'], 'Non-US Citizen'),
        # '2': 'RESIDENT ALIEN',
        # '3': 'NON-RESIDENT ALIEN',
        # '4': 'Non-US Citizen/US Resident ',
        # '5': 'Traveled to US for Reason Other Than Transplant',
        # '6': 'Traveled to US for Transplant',
    },
    'Donor citizenship': {
        '1': 'US Citizen',
        '2': 'US Resident Alien',
        '3': 'NON-US Resident',
        '4': 'US Resident Alien',
        '5': 'NON-US Resident',
    },
    'Donor race': {
        '1': 'White',
        '2': 'Black',
        '4': 'Hispanic',
        '5': 'Asian',
        **dict.fromkeys(['6', '7', '9'], 'Other'),
        # '6': 'Amer Ind/Alaska Native, Non-Hispanic',
        # '7': 'Native Hawaiian/other Pacific Islander, Non-Hispanic',
        # '9': 'Multiracial, Non-Hispanic'
    },
    'Patient graft failure': {'0': 'No', '1': 'Yes'},
    'Patient diabetes mellitus': {
        '1': 'No',
        '2': 'Type I',
        '3': 'Type II',
        '4': 'Other',
        # '5': 'Type Unknown',
    },
    'Patient hospitalization status': {
        '1': 'In ICU',
        '2': 'Hospitalized not in ICU',
        '3': 'Not hospitalized',
    },
    'Patient HLA locus mismatch level': {
        '1': '1',
        '2': '2',
        '3': '3',
        '4': '4',
        '5': '5',
        '6': '6',
    },
    # 'Donor chest X-ray' not found
    'Patient DR53 antigen from WL': {
        '95': 'Positive',
        '96': 'Negative',
        # '98': 'Confirmed Blank',
        # '99': 'Not Tested',
    },
    'Donor Inotropic Medication Type': {
        '1': 'Dopamine',
        '2': 'Dobutamine',
        '3': 'Epinephrine',
        '4': 'Levophed',
        '5': 'Neosynephrine',
        '6': 'Isoproterenol (Isuprel)',
        '999': 'Other',
    },
    'Patient VAD device type at TXP': {
        '1': 'NONE',
        '2': 'LVAD',
        '3': 'RVAD',
        '4': 'TAH',
        '5': 'LVAD+RVAD',
        # '6': 'LVAD/RVAD/TAH',
    },
    'Patient VAD device type at REG': {
        '1': 'NONE',
        '2': 'LVAD',
        '3': 'RVAD',
        '4': 'TAH',
        '5': 'LVAD+RVAD',
        # '6': 'LVAD/RVAD/TAH',
    },
    'Patient on VAD/TAH brand at REG': {
        '1': 'Cardio West',
        '2': 'Abiomed',
        '3': 'Novacor',
        '4': 'Heartmate',
        # '5': 'Unspecified',
        '7': 'Thoratec',
        '20': 'No',
        '999': 'Other',
    },
    'Patient Acute Rejection': {
        '1': 'Yes, treated',
        '2': 'Yes, untreated',
        '3': 'No',
    },
    'Patient blood group': {
        'A': 'A',
        'AB': 'AB',
        'B': 'B',
        'O': 'O',
        # 'Z': 'U',
    },
    'Patient initial waitlist status': {
        '2010': 'Old Status 1A',
        '2020': 'Old Status 1B',
        '2030': 'Old Status 2',
        '2090': 'Other',  # 'Old Status 1',
        '2110': 'New Status 1',
        '2120': 'New Status 2',
        '2130': 'New Status 3',
        '2140': 'New Status 4',
        '2150': 'New Status 5',
        '2160': 'New Status 6',
        '2999': 'Other'  # 'Temporarily inactive',
    },
    'Donor blood group': {
        'A': 'A',
        'A1': 'A1',
        'A1B': 'A1B',
        'A2': 'A2',
        'A2B': 'A2B',
        'AB': 'AB',
        'B': 'B',
        'O': 'O',
        'Z': 'Z (In Utero Only)',
    },
    'Donor cause of death': {
        '1': 'ANOXIA',
        '2': 'CEREBROVASCULAR/STROKE',
        '3': 'HEAD TRAUMA',
        '4': 'CNS TUMOR',
        '999': 'Other',
    },
    'Donor history/duration of diabetes': {
        '1': 'NO',
        '2': 'YES, 0-5 YEARS',
        '3': 'YES, 6-10 YEARS',
        '4': 'YES, >10 YEARS',
        '5': 'YES, DURATION UNKNOWN',
    },
    'Patient type of dialysis at REG': {
        '1': 'NO',
        '2': 'Hemodialysis',
        '3': 'Peritoneal Dialysis',
    },
    'Donor circumstance of death': {
        '1': 'MVA',
        '2': 'SUICIDE',
        '3': 'HOMICIDE',
        '4': 'CHILD-ABUSE',
        '5': 'Accident, Non-MVA',
        '6': 'DEATH FROM NATURAL CAUSES',
        '997': 'Other'
    },
    'Donor mechanism of death': {
        '1': 'DROWNING',
        '2': 'SEIZURE',
        '3': 'DRUG INTOXICATION',
        '4': 'ASPHYXIATION',
        '5': 'CARDIOVASCULAR',
        '6': 'ELECTRICAL',
        '7': 'VIOLENCE',
        '8': 'VIOLENCE',
        '9': 'BLUNT INJURY',
        '10': 'SIDS',
        '11': 'STROKE/ICH',
        '12': 'NATURAL CAUSES',
        '995': 'VIOLENCE',
        '997': 'Other'
    },
    'Donor cancer': {
        '1': 'NO',
        '2': 'SKIN CANCER', # - NON-MELANOMA',
        '3': 'SKIN CANCER', # - MELANOMA',
        '4': 'CNS TUMOR',
        '5': 'CNS TUMOR',
        '6': 'CNS TUMOR',
        '7': 'CNS TUMOR',
        '8': 'CNS TUMOR',
        '9': 'CNS TUMOR',
        '12': 'CNS TUMOR',
        '13': 'GENITOURINARY',
        '14': 'GENITOURINARY',
        '15': 'GENITOURINARY',
        '16': 'GENITOURINARY',
        '17': 'GENITOURINARY',
        '18': 'GENITOURINARY',
        '19': 'GENITOURINARY',
        '20': 'GENITOURINARY',
        '21': 'GENITOURINARY',
        '22': 'GENITOURINARY',
        '23': 'GASTROINTESTINAL',
        '24': 'GASTROINTESTINAL',
        '25': 'GASTROINTESTINAL',
        '26': 'GASTROINTESTINAL',
        '27': 'GASTROINTESTINAL',
        '28': 'GASTROINTESTINAL',
        '29': 'BREAST',
        '30': 'THYROID',
        '32': 'Other', # 'ENT',
        '33': 'Other', # 'ENT',
        '34': 'LUNG',
        '35': 'LEUKEMIA/LYMPHOMA',
        '999': 'Other'
    },
    'Donor chest X-ray': {
        '1': 'No',
        '2': 'Normal',
        '3': 'Abnormal-left',
        '4': 'Abnormal-right',
        '5': 'Abnormal-both'
    },
    'Donor Vent Mode': {
        '1': 'NC',
        '2': 'CPAP',
        '3': 'BiPAP',
        '4': 'SIMV',
        '5': 'A/C',
        '6': 'CMV',
        '7': 'Other'
    },
    'Donor microbiological culture type': {
        '0': 'Blood',
        '1': 'Urine',
        '2': 'Sputum Gram Stain',
        '3': 'Sputum Culture',
        '4': 'CSF',
        '5': 'Other'
    },
    'Donor Body Temperature Unit': {
        'F': 'Fahrenheit',
        'C': 'Celsius'
    },
    'Donor Agent Dosage Units': {
        '1': 'mcg/kg/min',
        '2': 'mcg/min',
        '3': 'mg/min',
        '4': 'units/hr',
        '5': 'mcg/hr'
    },
}


# ALOCUS
keys_to_assign = {
    'Patient A1 antigen from WL': 'HLA-A1',
    'Patient A2 antigen from WL': 'HLA-A2',
    'Donor A1 antigen from WL': 'HLA-A1',
    'Donor A2 antigen from WL': 'HLA-A2',
}
shared_values = {
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '9': '9',
    '10': '10',
    '11': '11',
    '19': '19',
    '23': '23',
    '24': '24',
    '25': '25',
    '26': '26',
    '28': '28',
    '29': '29',
    '30': '30',
    '31': '31',
    '32': '32',
    '33': '33',
    '34': '34',
    '36': '36',
    '43': '43',
    '66': '66',
    '68': '68',
    '69': '69',
    '74': '74',
    '80': '80',
    '98': 'No second antigen detected',
    # '99': 'Not Tested',
    '101': '{prefix}*01:01',
    '102': '{prefix}*01:02',
    '201': '{prefix}*02:01',
    '202': '{prefix}*02:02',
    '203': '{prefix}*02:03',
    '205': '{prefix}*02:05',
    '206': '{prefix}*02:06',
    '207': '{prefix}*02:07',
    '210': '{prefix}*02:10',
    '211': '{prefix}*02:11',
    '218': '{prefix}*02:18',
    '301': '{prefix}*03:01',
    '302': '{prefix}*03:02',
    '1101': '{prefix}*11:01',
    '1102': '{prefix}*11:02',
    '2402': '{prefix}*24:02',
    '2403': '{prefix}*24:03',
    '2601': '{prefix}*26:01',
    '2602': '{prefix}*26:02',
    '2603': '{prefix}*26:03',
    '2901': '{prefix}*29:01',
    '2902': '{prefix}*29:02',
    '3001': '{prefix}*30:01',
    '3002': '{prefix}*30:02',
    '3204': '{prefix}*32:04',
    '3301': '{prefix}*33:01',
    '3303': '{prefix}*33:03',
    '3401': '{prefix}*34:01',
    '3402': '{prefix}*34:02',
    '6601': '{prefix}*66:01',
    '6602': '{prefix}*66:02',
    '6801': '{prefix}*68:01',
    '6802': '{prefix}*68:02',
}
for key, prefix in keys_to_assign.items():
    # Replace the placeholder with the specific prefix for each key
    customized_values = {k: v.format(prefix=prefix) if '{prefix}' in v else v for k, v in shared_values.items()}
    category_explanations[key] = customized_values


# BLOCUS
keys_to_assign = {
    'Patient B1 antigen from WL': 'HLA-B1',
    'Patient B2 antigen from WL': 'HLA-B2',
    'Donor B1 antigen from WL': 'HLA-B1',
    'Donor B2 antigen from WL': 'HLA-B2',
}
shared_values = {
    '0': '0',
    '5': '5',
    '7': '7',
    '8': '8',
    '12': '12',
    '13': '13',
    '14': '14',
    '15': '15',
    '16': '16',
    '17': '17',
    '18': '18',
    '21': '21',
    '22': '22',
    '27': '27',
    '35': '35',
    '37': '37',
    '38': '38',
    '39': '39',
    '40': '40',
    '41': '41',
    '42': '42',
    '44': '44',
    '45': '45',
    '46': '46',
    '47': '47',
    '48': '48',
    '49': '49',
    '50': '50',
    '51': '51',
    '52': '52',
    '53': '53',
    '54': '54',
    '55': '55',
    '56': '56',
    '57': '57',
    '58': '58',
    '59': '59',
    '60': '60',
    '61': '61',
    '62': '62',
    '63': '63',
    '64': '64',
    '65': '65',
    '67': '67',
    '70': '70',
    '71': '71',
    '72': '72',
    '73': '73',
    '75': '75',
    '76': '76',
    '77': '77',
    '78': '78',
    '81': '81',
    '82': '82',
    '98': 'No second antigen detected',
    # '99': 'Not Tested',
    '702': '{prefix}*07:02',
    '703': '{prefix}*07:03',  # something seem wrong here for STAR File
    '704': '{prefix}*07:04',
    '714': '{prefix}*07:14',
    '801': '{prefix}*08:01',
    '802': '{prefix}*08:02',
    '803': '{prefix}*08:03',
    '804': '{prefix}*08:04',
    '1301': '{prefix}*13:01',
    '1302': '{prefix}*13:02',
    '1304': '{prefix}*13:04',
    '1401': '{prefix}*14:01',
    '1402': '{prefix}*14:02',
    '1501': '{prefix}*15:01',
    '1502': '{prefix}*15:02',
    '1503': '{prefix}*15:03',
    '1504': '{prefix}*15:04',
    '1506': '{prefix}*15:06',
    '1507': '{prefix}*15:07',
    '1510': '{prefix}*15:10',
    '1511': '{prefix}*15:11',
    '1512': '{prefix}*15:12',
    '1513': '{prefix}*15:13',
    '1516': '{prefix}*15:16',
    '1517': '{prefix}*15:17',
    '1518': '{prefix}*15:18',
    '1520': '{prefix}*15:20',
    '1521': '{prefix}*15:21',
    '1522': '{prefix}*15:22',
    '1524': '{prefix}*15:24',
    '1527': '{prefix}*15:27',
    '2703': '{prefix}*27:03',
    '2704': '{prefix}*27:04',
    '2705': '{prefix}*27:05',
    '2706': '{prefix}*27:06',
    '2708': '{prefix}*27:08',
    '3501': '{prefix}*35:01',
    '3502': '{prefix}*35:02',
    '3503': '{prefix}*35:03',
    '3508': '{prefix}*35:08',
    '3512': '{prefix}*35:12',
    '3801': '{prefix}*38:01',
    '3802': '{prefix}*38:02',
    '3901': '{prefix}*39:01',
    '3902': '{prefix}*39:02',
    '3904': '{prefix}*39:04',
    '3905': '{prefix}*39:05',
    '3906': '{prefix}*39:06',
    '3913': '{prefix}*39:13',
    '4001': '{prefix}*40:01',
    '4002': '{prefix}*40:02',
    '4003': '{prefix}*40:03',
    '4004': '{prefix}*40:04',
    '4005': '{prefix}*40:05',
    '4006': '{prefix}*40:06',
    '4101': '{prefix}*41:01',
    '4102': '{prefix}*41:02',
    '4201': '{prefix}*42:01',
    '4202': '{prefix}*42:02',
    '4402': '{prefix}*44:02',
    '4403': '{prefix}*44:03',
    '4415': '{prefix}*44:15',
    '4801': '{prefix}*48:01',
    '4802': '{prefix}*48:02',
    '5001': '{prefix}*50:01',
    '5002': '{prefix}*50:02',
    '5101': '{prefix}*51:01',
    '5102': '{prefix}*51:02',
    '5103': '{prefix}*51:03',
    '5501': '{prefix}*55:01',
    '5502': '{prefix}*55:02',
    '5504': '{prefix}*55:04',
    '5601': '{prefix}*56:01',
    '5603': '{prefix}*56:03',
    '5701': '{prefix}*57:01',
    '5703': '{prefix}*57:03',
    '7801': '{prefix}*78:01',
    '8201': '{prefix}*82:01',
    '8301': '{prefix}*83:01',
}
for key, prefix in keys_to_assign.items():
    # Replace the placeholder with the specific prefix for each key
    customized_values = {k: v.format(prefix=prefix) if '{prefix}' in v else v for k, v in shared_values.items()}
    category_explanations[key] = customized_values


# DRLOCUS
keys_to_assign = {
    'Donor DR1 antigen from WL': 'HLA-DR1',
    'Donor DR2 antigen from WL': 'HLA-DR2',
    'Patient DR1 antigen from WL': 'HLA-DR1',
    'Patient DR2 antigen from WL': 'HLA-DR2',
}
shared_values = {
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    '10': '10',
    '11': '11',
    '12': '12',
    '13': '13',
    '14': '14',
    '15': '15',
    '16': '16',
    '17': '17',
    '18': '18',
    '98': 'No second antigen detected',
    # '99': 'Not Tested',
    '101': '{prefix}*01:01',
    '102': '{prefix}*01:02',
    '103': '{prefix}*01:03',
    '301': '{prefix}*03:01',
    '302': '{prefix}*03:02',
    '303': '{prefix}*03:03',
    '401': '{prefix}*04:01',
    '402': '{prefix}*04:02',
    '403': '{prefix}*04:03',
    '404': '{prefix}*04:04',
    '405': '{prefix}*04:05',
    '406': '{prefix}*04:06',
    '407': '{prefix}*04:07',
    '410': '{prefix}*04:10',
    '411': '{prefix}*04:11',
    '801': '{prefix}*08:01',
    '802': '{prefix}*08:02',
    '803': '{prefix}*08:03',
    '807': '{prefix}*08:07',
    '901': '{prefix}*09:01',
    '902': '{prefix}*09:02',
    '1101': '{prefix}*11:01',
    '1103': '{prefix}*11:03',
    '1104': '{prefix}*11:04',
    '1201': '{prefix}*12:01',
    '1202': '{prefix}*12:02',
    '1301': '{prefix}*13:01',
    '1302': '{prefix}*13:02',
    '1303': '{prefix}*13:03',
    '1305': '{prefix}*13:05',
    '1401': '{prefix}*14:01',
    '1402': '{prefix}*14:02',
    '1403': '{prefix}*14:03',
    '1404': '{prefix}*14:04',
    '1405': '{prefix}*14:05',
    '1406': '{prefix}*14:06',
    '1454': '{prefix}*14:54',
    '1501': '{prefix}*15:01',
    '1502': '{prefix}*15:02',
    '1503': '{prefix}*15:03',
    '1601': '{prefix}*16:01',
    '1602': '{prefix}*16:02',
    '10300': '{prefix}*103',
}
for key, prefix in keys_to_assign.items():
    # Replace the placeholder with the specific prefix for each key
    customized_values = {k: v.format(prefix=prefix) if '{prefix}' in v else v for k, v in shared_values.items()}
    category_explanations[key] = customized_values


# CWHLA
keys_to_assign = {
    'Patient C1 antigen from WL': 'HLA-C1',
    'Patient C2 antigen from WL': 'HLA-C2',
    'Donor C1 antigen': 'HLA-C1',
    'Donor C2 antigen': 'HLA-C2',
}
shared_values = {
    '0': '0',
    '1': '01',
    '2': '02',
    '3': '03',
    '4': '04',
    '5': '05',
    '6': '06',
    '7': '07',
    '8': '08',
    '9': '09',
    '10': '10',
    '11': '11',
    '12': '12',
    '13': '13',
    '14': '14',
    '15': '15',
    '16': '16',
    '17': '17',
    '18': '18',
    '98': 'No second antigen detected',
    # '99': 'Not Tested',
    '100': 'No antigen detected',
    '102': '{prefix}*01:02',
    '103': '{prefix}*01:03',
    '202': '{prefix}*02:02',
    '210': '{prefix}*02:10',
    '302': '{prefix}*03:02',
    '303': '{prefix}*03:03',
    '304': '{prefix}*03:04',
    '305': '{prefix}*03:05',
    '306': '{prefix}*03:06',
    '401': '{prefix}*04:01',
    '403': '{prefix}*04:03',
    '404': '{prefix}*04:04',
    '407': '{prefix}*04:07',
    '501': '{prefix}*05:01',
    '602': '{prefix}*06:02',
    '701': '{prefix}*07:01',
    '702': '{prefix}*07:02',
    '704': '{prefix}*07:04',
    '706': '{prefix}*07:06',
    '718': '{prefix}*07:18',
    '801': '{prefix}*08:01',
    '802': '{prefix}*08:02',
    '803': '{prefix}*08:03',
    '804': '{prefix}*08:04',
    '1202': '{prefix}*12:02',
    '1203': '{prefix}*12:03',
    '1204': '{prefix}*12:04',
    '1402': '{prefix}*14:02',
    '1403': '{prefix}*14:03',
    '1502': '{prefix}*15:02',
    '1504': '{prefix}*15:04',
    '1505': '{prefix}*15:05',
    '1506': '{prefix}*15:06',
    '1509': '{prefix}*15:09',
    '1601': '{prefix}*16:01',
    '1602': '{prefix}*16:02',
    '1604': '{prefix}*16:04',
    '1701': '{prefix}*17:01',
    '1703': '{prefix}*17:03',
    '1801': '{prefix}*18:01',
    '1802': '{prefix}*18:02',
}
for key, prefix in keys_to_assign.items():
    # Replace the placeholder with the specific prefix for each key
    customized_values = {k: v.format(prefix=prefix) if '{prefix}' in v else v for k, v in shared_values.items()}
    category_explanations[key] = customized_values


# DQHLA
keys_to_assign = {
    'Patient DQB1 antigen from WL': 'HLA-DQB1',
    'Patient DQB2 antigen from WL': 'HLA-DQB2',
    'Donor DQB1 antigen': 'HLA-DQB1',
    'Donor DQB2 antigen': 'HLA-DQB2',
}
shared_values = {
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
    # '97': 'Unknown',
    '98': 'No second antigen detected',
    # '99': 'Not Tested',
    '201': '{prefix}*02:01',
    '202': '{prefix}*02:02',
    '301': '{prefix}*03:01',
    '302': '{prefix}*03:02',
    '303': '{prefix}*03:03',
    '319': '{prefix}*03:19',
    '401': '{prefix}*04:01',
    '402': '{prefix}*04:02',
    '501': '{prefix}*05:01',
    '502': '{prefix}*05:02',
    '503': '{prefix}*05:03',
    '601': '{prefix}*06:01',
    '602': '{prefix}*06:02',
    '603': '{prefix}*06:03',
    '604': '{prefix}*06:04',
    '609': '{prefix}*06:09',
}
for key, prefix in keys_to_assign.items():
    # Replace the placeholder with the specific prefix for each key
    customized_values = {k: v.format(prefix=prefix) if '{prefix}' in v else v for k, v in shared_values.items()}
    category_explanations[key] = customized_values


# WKGRPHLA
keys_to_assign = [
    'Patient BW4 antigen from WL',
    'Patient BW6 antigen from WL',
    'Patient DR51 antigen from WL',
    'Patient DR52 antigen from WL',
    'Patient DR53 antigen from WL',
    'Donor BW4 antigen',
    'Donor BW6 antigen',
    'Donor DR51 antigen',  # there are also 1, 2, 3, 4, 5 as categories, just ignored here
    'Donor DR52 antigen',
    'Donor DR53 antigen',
]
shared_values = {
    '0': 'Negative',  # No specific antigen was detected
    '95': 'Positive',
    '96': 'Negative',
    # '98': 'Confirmed Blank',
    # '99': 'Not Tested',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# Antigen Mismatch Level
keys_to_assign = [
    'Patient A locus mismatch level',
    'Patient B locus mismatch level',
    'Patient HLA locus mismatch level',
    'Patient DR locus mismatch level',
]
shared_values = {
    '0': 'Fully Matched',
    '1': 'Partial Mismatch',
    '2': 'Full Mismatch',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# DONORNET-POSNEG
keys_to_assign = [
    'Donor urine Bacteria',
    'Donor urine blood',
    'Donor urine casts',
    'Donor urine Epith',
    'Donor urine Glucose',
    'Donor urine Leukocyte esterase',
    'Donor urine Protein',
    'Donor urine RBC',
    'Donor urine WBC'
]
shared_values = {
    '1': 'Positive',
    '2': 'Negative',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# a lot of 0-1 facts, but may need double-check
keys_to_assign = [
    'Patient IV inotropes at TXP',
    'Patient IV inotropes at REG',
    'Patient on ventilator at TXP',
    'Patient on ventilator at REG',
    'Patient on prostaglandins at TXP',
    'Patient on prostaglandins at REG',
    'Patient On ECMO at REG',
    'Patient On ECMO at TXP',
    'Patient On IABP at REG',
    'Patient On IABP at TXP',
    'Donor infection pulmonary source',
    'Donor infection urine source',
    'Donor infection blood source',
    'Donor infection other sources',
    'Donor and recipient in same UNOS region'
]
shared_values = {
    '0': 'No', '1': 'Yes',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# a lot of N-Y facts, but may need double-check
keys_to_assign = [
    'ABO Compatible',
    'Patient episode of vent support at REG',
    'Patient implantable defibrillator at REG',
    'Patient previous malignancy',
    'Patient previous malignancy at REG',
    'Patient chronic steroid use at TXP',
    'Patient history of cigarette use',
    'Patient dialysis prior to TXP',
    'Patient dialysis between WL and TXP',
    'Patient multi-organ TXP',
    'Patient cigarette recent use + > 10 PACK YRS',
    'Patient transfusion between WL and TXP',
    'Patient infection',
    'Donor history of cigarettes >20 PACK YRS',
    'Donor recent cigarettes use + >20 PACK YRS',
    'Donor history of cocaine use',
    'Donor history of cocaine use + recent use',
    'Donor heavy alcohol use (>= 2 drinks/day)',
    'Donor history of hypertension',
    'Donor clinical infection',
    'Donor inotropic medication',
    'Donor pre-recovery heparin',
    'Donor history of other drugs + recent use',
    'Donor antihypertensives in 24 hrs pre-cross clamp',
    'Donor arginine vasopressin in 24 hrs pre-cross clamp',
    'Donor synthetic anti diuretic hormone (DDAVP)',
    'Donor risk for blood-borne disease transmission',
    # 'Donor history of cancer',
    'Donor Toxicology Screen',
    'Donor history of IV drug use',
    'Donor history of other drug use',
    'Donor history of myocardial infarction (MI)',
    'Donor 3+ inotropic agents at the time of incision',
    'Donor given insulin in 24 hrs pre-cross clamp',
    'Donor intracanial cancer at procurement',
    'Donor insulin dependent diabetes',
    'Donor vasodilators pre-cross clamp',
    'Donor coronary angiogram',
    'Donor other blood products',
    # waitlist
    'On Continuous Invasive Mechanical Ventilation',
    'On Anti-Arrhythmics',
    'On Dialysis',
    'On a Diuretic',
    'On Pulmonary Vasodilators',
    'On Vasoactive Support',
    'History of Stroke',
    'History of Peripheral Thromboembolic Events',
    'On Oral Anticoagulant when INR was Obtained',
    'Patient Graft Functioning',
    'Renal Transplant Post-Thoracic TX',
    'Coronary Artery Disease',
    'Hospitalized for Infection',
    'Hospitalized for Rejection',
    'On Maintenance Immunosuppression',
    'Permanent Pacemaker Inserted',
    'Working for Income',
    'Has the Candidate Experienced Hemoglobinuria',
]
shared_values = {
    'N': 'No', 'Y': 'Yes',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# a lot of stat results
keys_to_assign = [
    'Patient HIV NAT',
    'Patient HIV antibody serologic test',
    'Patient cerebrovascular disease',
    'Patient cytomegalovirus status at TXP',
    'Patient cytomegalovirus status by IGG at TXP',
    'Patient cytomegalovirus status by IGM at TXP',
    'Patient Epstein-Barr virus antibody test',
    'Patient Hepatitis B antibody test',
    'Patient Hepatitis B NAT',
    'Patient prior cardiac surgery at WL',
    'Patient cardiac surgery between WL and TXP',
    'Patient HEP C status',
    'Patient HEP B surface antigen',
    'Donor HIV NAT',
    'Donor West Nile NAT',
    'Donor Toxoplasma (IgG)',
    'Donor anti-HIV I/II',
    'Donor Anti-HCV status',
    'Donor anti-HBcAb status',
    'Donor HBV NAT',
    'Donor HCV NAT',
    'Donor Syphilis',
    # the following has 'I' ...
    'Donor serology anti-CMV',
    'Donor antibody TO HEP C virus result',
    'Donor HIV Ag/Ab combo assay',
    'Donor HBV core antibody',
    'Donor HEP B surface antigen',
    'Donor microbiological culture result',
    'Donor Anti-HTLV I/II',
    'Donor HBsAg',
    'Donor HBsAb',
    'Donor EBNA',
    'Donor EBV (VCA) (IgM)',
    'Donor EBV (VCA) (IgG)',
    'Donor RPR-VDRL result',
    'Donor Chagas serology',
]
shared_values = {
    # 'C': 'Cannot Disclose',  # 4
    # 'I': 'Indeterminate',  # 6
    'N': 'Negative',  # 2
    '2': 'Negative',
    # 'ND': 'Not Done',  # 5
    'P': 'Positive',  # 1
    '1': 'Positive',
    # 'PD': 'Pending'  # 7
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# multi-organ txo
keys_to_assign = [
    'Simultaneous liver TXP',
    # 'Simultaneous pancreas TXP',  # only 20 samples in raw data
]
shared_values = {
    'W': 'Yes', 'S': 'Yes',  # only 1 Segment
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# multi-organ txo
keys_to_assign = [
    'Simultaneous kidney TXP',
]
shared_values = {
    'R': 'Yes', 'L': 'Yes', 'E': 'Yes',  # 'E': 'En-Bloc', only 2
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# # multi-organ txo
# keys_to_assign = [
#     'Simultaneous lung TXP',
# ]
# shared_values = {
#     'R': 'Right', 'L': 'Left', 'D': 'Double',
# }
# for key in keys_to_assign:
#     category_explanations[key] = shared_values


# # functional statuses
# keys_to_assign = [
#     'Patient functional status > 70% at WL',
#     'Patient functional status > 70% at TXP',
# ]
# shared_values = {
#     '2010': 'No',
#     '2020': 'No',
#     '2030': 'No',
#     '2040': 'No',
#     '2050': 'No',
#     '2060': 'No',
#     '2070': 'Yes',
#     '2080': 'Yes',
#     '2090': 'Yes',
#     '2100': 'Yes',
#     '4010': 'No',
#     '4020': 'No',
#     '4030': 'No',
#     '4040': 'No',
#     '4050': 'No',
#     '4060': 'No',
#     '4070': 'Yes',
#     '4080': 'Yes',
#     '4090': 'Yes',
#     '4100': 'Yes',
#     '1': 'Yes',
#     '2': 'No',
#     '3': 'No'
# }
# for key in keys_to_assign:
#     category_explanations[key] = shared_values


# flush solution
keys_to_assign = [
    'Donor heart back table flush solution',
    'Donor final flush solution',
    'Donor initial flush solution',
]
shared_values = {
    '200': 'NO',
    '300': 'VIASPAN (UW/BELZER)',
    '301': 'EUROCOLLINS',
    '302': 'MODIFIED COLLINS',
    '303': 'CARDIOPLEGE',
    '304': 'PULMOPLEGE',
    '305': 'SALINE',
    '306': 'RINGERS',
    '307': 'CELSIOR',
    '308': 'CUSTODIOL',
    '309': 'PERFADEX',
    '310': 'NO',
    '311': 'BELZER MPS/KPS - 1',
    '312': 'HTK/CUSTODIOL',
    '313': 'UW/BELZER COLD STORAGE/VIASPAN/SPS-1',
    '999': 'Other'
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


# VAD Brand
keys_to_assign = [
    'Patient on VAD brand at REG',
    'Patient on VAD brand at TXP'
]
shared_values = {
    '201': 'Abiomed BVS 5000',
    '202': 'Arrow Lionheart',
    '203': 'Berlin Heart',
    '204': 'Biomedicus',
    '205': 'HeartMate II',
    '206': 'HeartMate IP',
    '207': 'HeartMate VE',
    '208': 'HeartMate XVE',
    '209': 'Heartsaver VAD',
    '210': 'Jarvik 2000',
    '211': 'Medos',
    '212': 'MicroMed DeBakey',
    '213': 'Novacor PC',
    '214': 'Novacor PCq',
    '215': 'Cardiac Assist Tandem Heart',
    '216': 'Thoratec',
    '217': 'Thoratec IVAD',
    '218': 'Toyobo',
    '219': 'Unspecified',
    '221': 'Abiomed AB5000',
    '222': 'Berlin Heart EXCOR',
    '223': 'Evaheart',
    '224': 'HeartWare HVAD',
    '225': 'Impella Recover 2.5',
    '226': 'Impella Recover 5.0',
    '227': 'CentriMag (Thoratec/Levitronix)',
    '228': 'Maquet Jostra Rotaflow',
    '229': 'MicroMed DeBakey',
    '230': 'Terumo DuraHeart',
    '231': 'Thoratec PVAD',
    '232': 'Ventracor VentrAssist',
    '233': 'Worldheart Levacor',
    '234': 'PediMag (Thoratec/Levitronix)',
    '235': 'Cardiac Assist Protek Duo',
    '236': 'HeartMate III',
    '237': 'Impella CP',
    '238': 'Impella RP',
    '239': 'ReliantHeartAssist 5',
    '240': 'ReliantHeart aVAD',
    '301': 'Abiomed BVS 5000',
    '302': 'Berlin Heart',
    '303': 'Biomedicus',
    '304': 'Medos',
    '305': 'Thoratec',
    '306': 'Thoratec IVAD',
    '307': 'Toyobo',
    '309': 'Abiomed AB5000',
    '310': 'Berlin Heart EXCOR',
    '311': 'Cardiac Assist Tandem Heart',
    '312': 'Evaheart',
    '313': 'HeartMate II',
    '314': 'HeartMate XVE',
    '315': 'Heartsaver VAD',
    '316': 'HeartWare HVAD',
    '317': 'Impella Recover 2.5',
    '318': 'Impella Recover 5.0',
    '319': 'Jarvik 2000',
    '320': 'CentriMag (Thoratec/Levitronix)',
    '321': 'Maquet Jostra Rotaflow',
    '322': 'MicroMed DeBakey',
    '323': 'MicroMed DeBakey',
    '324': 'Terumo DuraHeart',
    '325': 'Thoratec PVAD',
    '326': 'Ventracor VentrAssist',
    '327': 'WorldHeart Levacor',
    '328': 'PediMag (Thoratec/Levitronix)',
    '329': 'Cardiac Assist Protek Duo',
    '330': 'HeartMate III',
    '331': 'Impella CP',
    '332': 'Impella RP',
    '333': 'ReliantHeartAssist 5',
    '334': 'ReliantHeart aVAD',
    '401': 'AbioCor',
    '402': 'SynCardia CardioWest',
}
for key in keys_to_assign:
    category_explanations[key] = shared_values


keys_to_assign = [
    'Patient year of TXP',
    'Patients years on the waiting list',
]
shared_values = {
    # 1988-1993 group
    '1988': '1988-1993',
    '1989': '1988-1993',
    '1990': '1988-1993',
    '1991': '1988-1993',
    '1992': '1988-1993',
    '1993': '1988-1993',

    # 1994-1998 group
    '1994': '1994-1998',
    '1995': '1994-1998',
    '1996': '1994-1998',
    '1997': '1994-1998',
    '1998': '1994-1998',

    # 1999-2003 group
    '1999': '1999-2003',
    '2000': '1999-2003',
    '2001': '1999-2003',
    '2002': '1999-2003',
    '2003': '1999-2003',

    # 2004-2008 group
    '2004': '2004-2008',
    '2005': '2004-2008',
    '2006': '2004-2008',
    '2007': '2004-2008',
    '2008': '2004-2008',

    # 2009-2013 group
    '2009': '2009-2013',
    '2010': '2009-2013',
    '2011': '2009-2013',
    '2012': '2009-2013',
    '2013': '2009-2013',

    # 2014-2018 group
    '2014': '2014-2018',
    '2015': '2014-2018',
    '2016': '2014-2018',
    '2017': '2014-2018',
    '2018': '2014-2018',

    # 2019-2023 group
    '2019': '2019-2023',
    '2020': '2019-2023',
    '2021': '2019-2023',
    '2022': '2019-2023',
    '2023': '2019-2023'
}
for key in keys_to_assign:
    category_explanations[key] = shared_values




