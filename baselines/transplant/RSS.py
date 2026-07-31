# create a discrete variable ischemic time
def revalue_ischtime(x):
    if x >= 6:
        return 1
    elif 4 <= x < 6:
        return 2
    else:
        return 3


# create a discrete variable age_don
def revalue_age_don(x):
    if 50 <= x < 60:
        return 1
    elif 40 <= x < 50:
        return 2
    elif 30 <= x < 40:
        return 3
    else:
        return 4


# TBILI
def revalue_TBILI(x):
    if x >= 2:
        return 1
    else:
        return 0


def revalue_hospitalized(x):
    if x == 1 or x == 2:
        return 1
    elif x == 3:
        return 0
    else:
        NotImplementedError()


# create a discrete variable age
def revalue_age(x):
    if x >= 70:
        return 1
    elif 55 <= x < 70:
        return 2
    else:
        return 3


def RSS(df):
    df['AGE'] = df['AGE'].apply(revalue_age)

    # MED_COND_TRR
    # only use hospitalized
    df['Hospitalized'] = df['MED_COND_TRR'].apply(revalue_hospitalized)
    df = df.drop(columns=['MED_COND_TRR'])
    df['TBILI'] = df['TBILI'].apply(revalue_TBILI)
    df['AGE_DON'] = df['AGE_DON'].apply(revalue_age_don)
    df['ISCHTIME'] = df['ISCHTIME'].apply(revalue_ischtime)

    return df