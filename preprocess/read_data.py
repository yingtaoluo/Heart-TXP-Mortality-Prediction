from .helpers import (
    txp_datetime_format, remove_binary_indicators,
    os, pd, plt, pdb, TIME_NOW, tqdm
)
import datetime
import numpy as np
from lifelines import KaplanMeierFitter


# (waiting update) alive to the last status check or end of study [which is censoring]
# (waiting update) death
# (waiting update) removal -> death
# (waiting update) removal -> not sure
# (waiting update) transplant - (follow-up) > death
# (waiting update) transplant - (follow-up) > alive to the last status check or end of study
# also: horizon
def read_from_transplant_data():
    file_path = '../data/thoracic_data/thoracic_data.csv'
    # (217648, 553)
    # (93913, 553)
    # file_path = '../data/mybox-selected/STAR_SAS/SAS Dataset 202312/SAS Dataset 202312/Thoracic/2024.04.08_Akinwale_data_cleaning.csv'
    # (217648, 556)
    # (93913, 556)
    # file_path = '../data/mybox-selected/STAR_SAS/SAS Dataset 202312/SAS Dataset 202312/Thoracic/20240216_unos_commands.csv'
    # (127253, 553)
    # (80293, 553)
    df = pd.read_csv(file_path, low_memory=True, encoding='utf-8')
    cutoff = pd.Timestamp('2018-10-18')
    # cutoff = pd.Timestamp('1900-10-18')
    print(df.shape)

    # make sure certain columns are datetime format
    df = txp_datetime_format(df)
    # Apply the transformation selectively
    df = remove_binary_indicators(df)
    print(df.shape)
    # (217648, 549)
    df = df[df['WL_ORG'] == 'HR']  # only process those that are with heart
    # (139013, 553)
    # df = df[df['TXHRT'] == 'Y']  # only process those that get heart txp
    print(df.shape)
    # (93913, 549)
    # df = df[df['AGE'] >= 18]  # let us do this in specific data preprocessing steps
    df = df[df['INIT_DATE'] >= cutoff]
    print(df.shape)

    # timestamp
    df = df.assign(
        LAST_DATE=None,  # death / alive censored
        REMOVAL_DATE=None,  # txp / removal
        # patient survival time after txp
        TXPSurv=0,
        # patient survival time on the waitlist
        WLSurv=0,
        # patient final status
        WLType=None,  # 'txp', 'wl',
        PType=None,  # 'retxp' (not the last one), 'dead', 'alive', # no 'lost', 'removal'
    )

    # list_of_patients = []

    csv_file = '../datasets/transplant_data.csv'
    # csv_file = '../datasets/transplant_data_full.csv'
    if os.path.exists(csv_file):
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')  # Format: YYYYMMDD_HHMMSS
        backup_file = f"transplant_data_backup_{timestamp}.csv"
        os.rename(csv_file, backup_file)
        print(f"Existing file renamed to: {backup_file}")
    pd.DataFrame(columns=df.columns).to_csv(csv_file, index=False)

    PTIMES, EVENTS = [], []  # dead (have an event) for 1, alive for 0
    reason_to_continue = {'dead_on_unknown_date': 0, 'txp_on_unknown_date': 0, 'not_alive_not_dead': 0,
                          'non-last-re-transplant_record': 0}
    # {'dead_on_unknown_date': 0, 'txp_on_unknown_date': 0, 'not_alive_not_dead': 613, 'non-last-re-transplant_record': 0}

    # Group these rows by PT_CODE
    for pt_code, group in tqdm(df.groupby('PT_CODE'), desc="Processing PT_CODE groups"):
        # Now sort the DataFrame by the 'INIT_DATE' column
        group = group.sort_values(by='INIT_DATE')

        # 13: removal due to deterioration, 21: died during tx, 23: died during living donor tx
        condition_dead = (
            group['REM_CD'].isin([8.0, 21.0, 23.0]).any()
            or group['COMPOSITE_DEATH_DATE'].notna().any()
        )
        # only applies for those who get transplants!!
        condition_transplant_alive = (group['PX_STAT'] == 'A').any() or (group['PSTATUS'] == 0).any()
        # There are condition_dead == condition_alive, but dead has priority

        num_transplant_records = len(group[group['TXED'] == 1])
        # for patients without transplants
        if num_transplant_records == 0:

            recent_record = group.loc[group['INIT_DATE'].idxmax()].copy()
            init_date = recent_record['INIT_DATE']
            wait_days = recent_record['DAYSWAIT_CHRON']
            removal_date = recent_record['REMOVAL_DATE'] = recent_record['INIT_DATE'] + pd.to_timedelta(wait_days,
                                                                                                        unit='D')
            recent_record['WLType'] = 'wl'
            # PT_CODE 164849 has END_DATE < INIT_DATE
            # composite death date could < END_DATE (removal, or 'DAYSWAIT_CHRON')

            # TODO: [wl, dead, 'WLSurv']
            if condition_dead:
                if group['COMPOSITE_DEATH_DATE'].notna().any():
                    death_date = recent_record['LAST_DATE'] = group['COMPOSITE_DEATH_DATE'].max()
                else:
                    reason_to_continue['dead_on_unknown_date'] += 1  # 0 count
                    continue  # if dead and no date, cannot know survival time

                if removal_date > death_date:  # if removal report late, correct it
                    removal_date = recent_record['LAST_DATE'] = recent_record['REMOVAL_DATE'] = death_date

                recent_record['WLSurv'] = (removal_date - init_date).total_seconds() / (24 * 3600)
                recent_record['PType'] = 'dead'

            # TODO: [wl, alive, 'WLSurv']
            else:
                recent_record['PType'] = 'alive'
                recent_record['LAST_DATE'] = removal_date
                recent_record['WLSurv'] = (removal_date - init_date).total_seconds() / (24 * 3600)

            # list_of_patients.append(recent_record.to_frame().T)
            new_row = recent_record.to_frame().T
            new_row.to_csv(csv_file, index=False, mode='a', header=False)

            continue

        # for patients got transplants
        elif num_transplant_records > 1:  # re-transplantation
            re_txps = group[group['TXED'] == 1].sort_values(by='END_DATE')
            # only consider first transplant episode with second transplant as censoring
            this_record = re_txps.iloc[0].copy()
            i_record = 0
            this_init_date = re_txps['INIT_DATE'].iloc[i_record]
            this_txp_date = re_txps['END_DATE'].iloc[i_record]
            next_txp_date = re_txps['END_DATE'].iloc[i_record + 1] if len(re_txps) > i_record + 1 else None

            # TODO: [txp, retxp, 'WLSurv']
            # start clean, get a transplant, and another one in the future (final alive/death unobservable)
            if next_txp_date:
                this_record['LAST_DATE'] = next_txp_date
                this_record['REMOVAL_DATE'] = this_txp_date
                this_record['WLSurv'] = (this_txp_date - this_init_date).days
                this_record['TXPSurv'] = (next_txp_date - this_txp_date).days
                this_record['PType'] = 'retxp'  # useful for txp mortality
                this_record['WLType'] = 'txp'
                # list_of_patients.append(this_record.to_frame().T)
                new_row = this_record.to_frame().T
                new_row.to_csv(csv_file, index=False, mode='a', header=False)
                continue
                # surv analysis doesn't make sense for non-last re-txps

            else:
                reason_to_continue['non-last-re-transplant_record'] += 1  # none of this
                continue

        else:
            # exactly one transplant record (non re-transplant case)
            txp_rows = group.loc[group['TXED'] == 1]
            assert len(txp_rows) == 1
            txp_row = txp_rows.iloc[0].copy()

            wait_days = txp_row['WLSurv'] = txp_row['DAYSWAIT_CHRON']
            # do not use 'TX_DATE', some are missing values
            removal_date = txp_row['REMOVAL_DATE'] = txp_row['END_DATE']

            # TODO: [txp, dead]
            if condition_dead:
                # 'PTIME' has missing values
                if group['COMPOSITE_DEATH_DATE'].notna().any():
                    death_date = group['COMPOSITE_DEATH_DATE'].max()
                else:
                    reason_to_continue['dead_on_unknown_date'] += 1  # 0 count
                    continue

                txp_row['TXPSurv'] = (death_date - removal_date).total_seconds() / 24 / 3600
                # what about those group['TXED'] != 1 for wl?
                txp_row['WLSurv'] = wait_days
                txp_row['PType'] = 'dead'
                txp_row['WLType'] = 'txp'
                txp_row['LAST_DATE'] = death_date

            # TODO: [txp, alive], having PTIME
            elif condition_transplant_alive and pd.notna(txp_row['PTIME']):
                # same as txp_row['PX_STAT'] == 'A' and pd.notna(txp_row['PX_STAT_DATE'])
                txp_row['TXPSurv'] = txp_row['PTIME']
                txp_row['LAST_DATE'] = txp_row['COMPOSITE_DEATH_DATE']
                txp_row['WLSurv'] = wait_days
                txp_row['PType'] = 'alive'
                txp_row['WLType'] = 'txp'

            else:  # TODO: use the latest follow-up (removal) date as last date
                reason_to_continue['not_alive_not_dead'] += 1  # for patients got transplant
                txp_row['TXPSurv'] = 0
                txp_row['WLSurv'] = wait_days
                txp_row['PType'] = 'alive'
                txp_row['WLType'] = 'txp'
                txp_row['LAST_DATE'] = removal_date

            # list_of_patients.append(group[group['TXED'] == 1])
            new_row = txp_row.to_frame().T
            new_row.to_csv(csv_file, index=False, mode='a', header=False)

    print(reason_to_continue)

