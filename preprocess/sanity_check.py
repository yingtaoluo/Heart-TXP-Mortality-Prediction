import numpy as np
import pandas as pd
import pdb
from paths import DATA, DATASETS, RESULTS, CHECKPOINTS, IMAGES, MODELS, ensure_output_dirs


# Load data
offers = pd.read_csv("C:/Users/87128/PycharmProjects/Sequential_Decision_Making/data/donornet/offers.csv",     
                     parse_dates=['initial_response_dt', 'final_response_dt', 'match_submit_dt'], low_memory=False)

offers['initial_response_dt'] = pd.to_datetime(offers['initial_response_dt'], errors='coerce')
offers['final_response_dt'] = pd.to_datetime(offers['final_response_dt'], errors='coerce')
offers['match_submit_dt'] = pd.to_datetime(offers['match_submit_dt'], errors='coerce')

'''sanity check (manual, complete): Number of wl_id_code with at least one match_submit_dt before last final_response_dt is 0'''
# Check for each wl_id_code if any match_submit_dt is before the last offer's final_response_dt
# last_offers = offers[offers['ptr_sequence_num'] == -1][['wl_id_code', 'final_response_dt']].rename(columns={'final_response_dt': 'last_final_response_dt'})
# merged = offers.merge(last_offers, on='wl_id_code', how='left')
# problem_cases = merged[merged['match_submit_dt'] < merged['last_final_response_dt']]
# num_problem_wl_ids = problem_cases['wl_id_code'].nunique()
# print(f"Number of wl_id_code with at least one match_submit_dt before last final_response_dt: {num_problem_wl_ids}")


file_path = f'{DATA}/SAS Dataset/Thoracic/thoracic_data.csv'
df = pd.read_csv(file_path, low_memory=False, encoding='utf-8')
# donornet_donors = pd.read_parquet(f'{DATA}/donornet/donors.parquet', engine='pyarrow')
# donornet_offers = pd.read_parquet(f'{DATA}/donornet/offers.parquet', engine='pyarrow')


# Identify the rows with duplicated PT_CODE values
df = df[df['PT_CODE'].duplicated(keep=False)]

# make sure certain columns are datetime format
df['INIT_DATE'] = pd.to_datetime(df['INIT_DATE'])
df['END_DATE'] = pd.to_datetime(df['END_DATE'])
df['TX_DATE'] = pd.to_datetime(df['TX_DATE'])

# Apply the transformation selectively
for col in df.columns:
    if df[col].dtype == 'object' and df[col].str.contains("^b'.*'$").any():
        df[col] = df[col].str.replace("^b'(.*)'$", r'\1', regex=True)


'''SANITY CHECKS'''
for pt_code, group in df.groupby('PT_CODE'):
    condition_dead = (group['REM_CD'] == 8.0).any() or (group['PX_STAT'] == 'D').any()
    condition_transplanted = (group['TXED'].sum() > 0)

    '''sanity check: GSTATUS is mostly post-transplant and the date is unknown for those who had txp'''
    # # Convert the columns to datetime format
    # df['GRF_FAIL_DATE'] = pd.to_datetime(df['GRF_FAIL_DATE'], errors='coerce')
    # df['END_DATE'] = pd.to_datetime(df['END_DATE'], errors='coerce')
    #
    # # Check for rows where both GRF_FAIL_DATE and END_DATE are not missing
    # valid_rows = df.dropna(subset=['GRF_FAIL_DATE', 'END_DATE'])
    # count = (df['GRF_FAIL_DATE'] <= df['END_DATE']).sum()
    #
    # # If there are valid rows, calculate the number of days since transplant
    # if not valid_rows.empty:
    #     valid_rows['DAYS_SINCE_TRANSPLANT'] = (valid_rows['GRF_FAIL_DATE'] - valid_rows['END_DATE']).dt.days
    #     print(valid_rows[['GRF_FAIL_DATE', 'END_DATE', 'DAYS_SINCE_TRANSPLANT']])
    # else:
    #     print("There are no rows with both GRF_FAIL_DATE and END_DATE present.")

    '''sanity check (manual, complete): GSTATUS is more reliable than GRF_STAT as a binary variable'''

    '''sanity check: group['REM_CD'] is always a numerical value or NaN, but NaN implies nothing'''
    # for item in group['REM_CD']:
    #     if isinstance(item, str):
    #         pdb.set_trace()

    '''sanity check (manual, complete): REM_CD == 8 and PX_STAT == 'D' could be in different rows '''

    '''sanity check (manual, complete): STATUS_DATE (D) does not equal to END_DATE in the row of death'''
    # # (STAR file says only death before removal will equal)

    '''sanity check (complete): TX_DATE equal to END_DATE in the rows of transplant'''
    # # (star file END_DATE note already explains that)
    # # note: sometimes TX_DATE can be NaN even for TXED == 1
    # group = group.dropna(subset=['TX_DATE', 'END_DATE'])
    # TX_DATE = group[group['TXED'] == 1]['TX_DATE']
    # END_DATE = group[group['TXED'] == 1]['END_DATE']
    # if (TX_DATE.values != END_DATE.values).any():
    #     print('TXP_DATE does not equal to END_DATE!')

    '''sanity check (complete): transplanted and dead patient may not have a PTIME'''
    # if condition_dead and condition_transplanted and not (group['PTIME'].notna().any()):
    #     print('transplanted and dead patient may not have a PTIME!')

    '''sanity check (complete): some variable update times are earlier than time added to waitlist'''

