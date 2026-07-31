# create a discrete variable age
def revalue_age(x):
    if x >= 65:
        return 1
    else:
        return 2


def SOTA(df):
    df['AGE'] = df['AGE'].apply(revalue_age)

    # If the variable name changed over time, we merge them into one
    df['ALCOHOL_HEAVY_DON'] = df['HIST_ALCOHOL_OLD_DON'].combine_first(df['ALCOHOL_HEAVY_DON'])
    df = df.drop(columns=['HIST_ALCOHOL_OLD_DON'])

    return df

