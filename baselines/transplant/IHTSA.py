# make discrete 'TX_YEAR'
def revalue_TX_YEAR(x):
    if x > 2005:
        return 1
    elif 2000 < x <= 2005:
        return 2
    elif 1996 <= x <= 2000:
        return 3
    else:
        return 4


def merge_columns_vad(row):
    if row['VAD_DEVICE_TY_TRR'] == 1 or row['VAD_DEVICE_TY_TCR'] == 1:
        return 1
    else:
        return 0


# create a variable VAD or not, nothing else
def revalue_vad(x):
    if x in [2, 3, 4, 5, 6]:
        return 1
    elif x == 1:
        return 0
    else:
        NotImplementedError()


def IHTSA(df):
    df['VAD_DEVICE_TY_TRR'] = df['VAD_DEVICE_TY_TRR'].apply(revalue_vad)
    df['VAD_DEVICE_TY_TCR'] = df['VAD_DEVICE_TY_TCR'].apply(revalue_vad)

    df['VAD'] = df.apply(merge_columns_vad, axis=1)
    df = df.drop(columns=['VAD_DEVICE_TY_TRR'])
    df = df.drop(columns=['VAD_DEVICE_TY_TCR'])

    df['TX_YEAR'] = df['TX_YEAR'].apply(revalue_TX_YEAR)

    # create total days variable
    df['total_days'] = df['DAYS_STAT1A'] + df['DAYS_STAT1B'] + df['DAYS_STAT2']
    df = df.drop(columns=['DAYS_STAT1A', 'DAYS_STAT1B', 'DAYS_STAT2'])

    # HLA-DR 'DRMIS', 'HLAMIS',
    df['HLA-DR'] = df['HLAMIS'] - df['DRMIS']
    df = df.drop(columns=['DRMIS', 'HLAMIS'])

    return df



