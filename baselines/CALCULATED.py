import math


def abo_grouping(df, compatible=True):
    # adjust abo grouping
    abo_mapping = {
        'A': 'A', 'A1': 'A', 'A2': 'A',  # Group A and subtypes
        'B': 'B',  # Group B
        'AB': 'AB', 'A1B': 'AB', 'A2B': 'AB',  # Group AB and subtypes
        'O': 'O'  # Group O
    }
    if 'ABO' in df.columns:
        df['ABO'] = df['ABO'].map(abo_mapping)
    if 'ABO_DON' in df.columns:
        df['ABO_DON'] = df['ABO_DON'].map(abo_mapping)

    if compatible:
        df["ABO Compatible"] = df.apply(
            lambda row: abo_compatible(row["ABO_DON"], row["ABO"]), axis=1
        )
        df = df.drop(columns=['ABO', 'ABO_DON'])

    return df


# function to check compatibility
def abo_compatible(donor, recipient):
    compatibility = {
        "O": {"O", "A", "B", "AB"},
        "A": {"A", "AB"},
        "B": {"B", "AB"},
        "AB": {"AB"}
    }

    # handle None or NaN values → return NaN
    if donor is None or recipient is None:
        return float("nan")
    if isinstance(donor, float) and math.isnan(donor):
        return float("nan")
    if isinstance(recipient, float) and math.isnan(recipient):
        return float("nan")

    try:
        return "Y" if recipient in compatibility[donor] else "N"
    except KeyError:
        return float("nan")  # unexpected values


# Apply conversion where BODYTEMP_UNIT is 'F'
def fahrenheit_to_celsius(temp_f):
    return (temp_f - 32) * 5.0 / 9.0


def convert_functional_status(df):
    # Map the functional status from string to int
    def map_funcstat(code):
        if code in [1, 2, 3]:
            return {1: 100, 2: 60, 3: 20}[code]
        elif 2010 <= code <= 2100 or 4010 <= code <= 4100:
            return code % 1000  # e.g., 2040 → 40
        elif code in [996, 998]:
            return None
        else:
            return None

    if 'FUNC_STAT_TCR' in df.columns:
        df['Patient functional status at WL'] = df['FUNC_STAT_TCR'].apply(map_funcstat)
        df = df.drop(columns=['FUNC_STAT_TCR'])
    if 'FUNC_STAT_TRR' in df.columns:
        df['Patient functional status at TXP'] = df['FUNC_STAT_TRR'].apply(map_funcstat)
        df = df.drop(columns=['FUNC_STAT_TRR'])

    return df


# Conversion Inotropic Medication dosage unit to mcg/kg/min
def get_conversion_factor(dose_unit, weight):
    conversion_factors = {
        '1': 1,  # mcg/kg/min (no conversion needed)
        '2': 1 / weight,  # mcg/min to mcg/kg/min
        '3': 1000 / weight,  # mg/min to mcg/kg/min
        '4': 1000 / (weight * 60),  # units/hr to mcg/kg/min
        '5': 1 / (weight * 60)  # mcg/hr to mcg/kg/min
    }
    return conversion_factors.get(dose_unit, 1)


def convert_to_mcg_kg_min(row):
    weight = row['WGT_KG_DON_CALC']
    dose_unit = row['DOSEUNITS']
    agent_val = row['AGENT_VAL']
    factor = get_conversion_factor(dose_unit, weight)
    return agent_val * factor


def creatinine_clearance(age, weight_kg, serum_creatinine, sex):
    sex_factor = sex.apply(lambda x: 0.85 if x == 'F' else 1.0)
    # Cockcroft-Gault equation
    return ((140 - age) * weight_kg * sex_factor) / (72 * serum_creatinine)


# CKD-EPI equation
def calculate_eGFR(creatinine, age, sex, race):
    """
    Calculate eGFR using the CKD-EPI equation.

    Parameters: (pd.Series)
    - creatinine (float): Serum creatinine in mg/dL.
    - age (int): Age in years.
    - sex (str): "M" or "F".
    - race (float): "2.0" (black) or others (non-black).

    Returns:
    - eGFR (float): Estimated glomerular filtration rate in mL/min/1.73m².
    """
    k = sex.map({'M': 0.9, 'F': 0.7})  # Assign k based on sex
    alpha = sex.map({'M': -0.411, 'F': -0.329})  # Assign alpha based on sex

    # Calculate the creatinine ratio
    scr_ratio = creatinine / k

    # Apply min/max conditions
    min_scr = scr_ratio.where(scr_ratio < 1, 1) ** alpha
    max_scr = scr_ratio.where(scr_ratio >= 1, 1) ** -1.209

    # Race adjustment
    race_factor = race.apply(lambda x: 1.159 if x == 2.0 else 1)

    # Calculate eGFR
    egfr = 141 * min_scr * max_scr * (0.993 ** age) * race_factor

    return round(egfr, 2)


# unused
def combine_immunology(serology, NAT):
    if NAT == 'Positive':
        return 'Active Infection'
    elif NAT == 'Negative':
        if serology == 'Positive':
            return 'Past Infection/Immunity'
        elif serology == 'Negative':
            return 'No Infection'
    else:
        return 'Inconclusive'
