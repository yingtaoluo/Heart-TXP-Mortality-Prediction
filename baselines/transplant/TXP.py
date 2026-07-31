from ..CALCULATED import *
from utils import *


# def correct_units(df):
#     # df.loc[df['BODYTEMP_UNIT'] == 'F', 'BODYTEMP_RANGE_START'] = df.loc[
#     #     df['BODYTEMP_UNIT'] == 'F', 'BODYTEMP_RANGE_START'].apply(fahrenheit_to_celsius)
#     # df.loc[df['BODYTEMP_UNIT'] == 'F', 'BODYTEMP_RANGE_END'] = df.loc[
#     #     df['BODYTEMP_UNIT'] == 'F', 'BODYTEMP_RANGE_END'].apply(fahrenheit_to_celsius)
#     # df = df.drop(columns='BODYTEMP_UNIT')
#
#     df['DOSEUNITS'] = df['DOSEUNITS'].fillna('U')
#     df['DOSEUNITS'] = convert_to_string(df['DOSEUNITS'])
#     df['AGENT_VAL'] = df.apply(convert_to_mcg_kg_min, axis=1)
#     df = df.drop(columns='DOSEUNITS')
#
#     return df


def assign_variable_type(df, new_cols, old_cols, output_col):
    has_new = df[new_cols].notna().any(axis=1)
    has_old = df[old_cols].notna().any(axis=1)

    df[output_col] = np.select(
        [has_new, has_old],
        ['New', 'Old'],
        default='U'
    )
    return df


def integrate_variables(df):
    if {'HIST_IV_DRUGUSE', 'HIST_IV_DRUG_OLD_DON'}.issubset(df.columns):
        df['HIST_IV_DRUGUSE'] = df['HIST_IV_DRUGUSE'].combine_first(df['HIST_IV_DRUG_OLD_DON'])  # !!!
        df = df.drop(columns=['HIST_IV_DRUG_OLD_DON'])

    if {'CIG_USE', 'CIG_GRT_10_OLD'}.issubset(df.columns):
        # If the variable name changed over time, we merge them into one
        df['CIG_USE'] = df['CIG_USE'].combine_first(df['CIG_GRT_10_OLD'])
        df = df.drop(columns=['CIG_GRT_10_OLD'])

    if {'ALCOHOL_HEAVY_DON', 'HIST_ALCOHOL_OLD_DON'}.issubset(df.columns):
        # If the variable name changed over time, we merge them into one
        df['ALCOHOL_HEAVY_DON'] = df['HIST_ALCOHOL_OLD_DON'].combine_first(df['ALCOHOL_HEAVY_DON'])
        df = df.drop(columns=['HIST_ALCOHOL_OLD_DON'])

    if {'ABO', 'ABO_DON'}.issubset(df.columns):
        pdb.set_trace()
        # If the variable name changed over time, we merge them into one
        df['ALCOHOL_HEAVY_DON'] = df['HIST_ALCOHOL_OLD_DON'].combine_first(df['ALCOHOL_HEAVY_DON'])
        df = df.drop(columns=['HIST_ALCOHOL_OLD_DON'])

    return df


def complete_hemodynamics(df):
    df['Patient PVR at TXP'] = (df['HEMO_PA_MN_TRR'] - df['HEMO_PCW_TRR']) / df['HEMO_CO_TRR']
    df['Patient TPG at TXP'] = df['HEMO_PA_MN_TRR'] - df['HEMO_PCW_TRR']
    df['Patient mean PAP at TXP'] = (df['HEMO_SYS_TRR'] + 2 * df['HEMO_PA_DIA_TRR']) / 3
    df['Patient SPP at TXP'] = df['HEMO_SYS_TRR'] - df['Patient mean PAP at TXP']
    # # Dubios method to calculate BSA
    # BSA = 0.007184 * (df['HGT_CM_CALC'] ** 0.725) * (df['WGT_KG_CALC'] ** 0.425)
    # df['Patient cardiac index'] = df['HEMO_CO_TCR'] / BSA
    df['Patient eGFR'] = calculate_eGFR(df['CREAT_TRR'], df['AGE'], df['GENDER'], df['ETHCAT'])
    df['Patient creatinine clearance'] = creatinine_clearance(df['AGE'], df['WGT_KG_CALC'], df['CREAT_TRR'],
                                                              df['GENDER'])

    df = df.drop(columns=['HEMO_PA_MN_TRR', 'HEMO_PCW_TRR', 'HEMO_CO_TRR', 'HEMO_SYS_TRR',])
    df = df.drop(columns=['hgt_cm', 'HGT_CM_CALC'])

    return df

