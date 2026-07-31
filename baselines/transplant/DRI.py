def revalue_eth(x):
    if x == 1 or x == 998:
        return x
    elif x in [2, 3, 4, 5, 6, 7, 9]:
        return 2
    else:
        NotImplementedError()


# create a variable VAD or not, nothing else
def revalue_vad(x):
    if x in [2, 3, 4, 5, 6]:
        return 1
    elif x == 1:
        return 0
    else:
        NotImplementedError()


def merge_columns_vad(row):
    if row['VAD_DEVICE_TY_TRR'] == 1 or row['VAD_DEVICE_TY_TCR'] == 1:
        return 1
    else:
        return 0


# create a discrete variable age_don
def revalue_age_don(x):
    if x >= 50:
        return 1
    elif 40 <= x < 50:
        return 2
    else:
        return 3


# create a discrete variable ischemic time
def revalue_ischtime(x):
    if x >= 8:
        return 1
    elif 6 <= x < 8:
        return 2
    elif 4 <= x < 6:
        return 3
    elif 2 <= x < 4:
        return 4
    else:
        return 5


def DRI(df):
    # change race to White or not
    df['ETHCAT_DON'] = df['ETHCAT_DON'].apply(revalue_eth)
    df['AGE_DON'] = df['AGE_DON'].apply(revalue_age_don)
    df['ISCHTIME'] = df['ISCHTIME'].apply(revalue_ischtime)

    return df


