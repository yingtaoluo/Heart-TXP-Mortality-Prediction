# TBILI
def revalue_TBILI(x):
    if x >= 4:
        return 1
    elif 2 <= x < 4:
        return 2
    elif 1 <= x < 2:
        return 3
    else:
        return 4


# change race to Black or not
def revalue_eth(x):
    if x == 2 or x == 998:
        return x
    elif x in [1, 3, 4, 5, 6, 7, 9]:
        return 2
    else:
        NotImplementedError()


# create a discrete variable age
def revalue_age(x):
    if x >= 60:
        return 1
    else:
        return 2


def IMPACT(df):

    df['AGE'] = df['AGE'].apply(revalue_age)
    df['ETHCAT'] = df['ETHCAT'].apply(revalue_eth)
    df['TBILI'] = df['TBILI'].apply(revalue_TBILI)

    return df

