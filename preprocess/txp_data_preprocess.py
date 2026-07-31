from .helpers import *
from variables import *
import numpy as np
from sklearn.model_selection import train_test_split


def create_TXP_static_data():
    if analyze_full_data:
        df = pd.read_csv('../datasets/transplant_data_full.csv', low_memory=True, encoding='utf-8')
        save_path = '../datasets/df_txp_full.csv'
    else:
        df = pd.read_csv('../datasets/transplant_data.csv', low_memory=True, encoding='utf-8')
        save_path = '../datasets/df_txp.csv'

    df = txp_datetime_format(df)
    df = remove_binary_indicators(df)
    df = df[df['AGE'] >= 18]
    print(df.shape)
    print(df['INIT_DATE'].min())
    # (129616, 555)

    df_dd = pd.read_csv('../data/thoracic_data/deceased_donor_data.csv', low_memory=False, encoding='utf-8')
    # df_dd = txp_datetime_format(df_dd)
    df_dd = remove_binary_indicators(df_dd)[donor_TXP_variables+['DONOR_ID']]
    df = df.merge(df_dd, on='DONOR_ID', how='left')

    print(df.shape)
    # (129616, 558)

    # donor_df = pd.read_csv("../data/deceased_donor_data.csv", low_memory=False, encoding='utf-8')
    #
    # print(donor_df['DONOR_ID'].unique().shape)
    # # Find donor IDs in the patient data that are not present in the donor data
    # missing_donors = df[~df['DONOR_ID'].isin(donor_df['DONOR_ID'])]
    # # Check if any donor IDs are missing and display the missing donor IDs along with patient IDs
    # if missing_donors.empty:
    #     print("All donor IDs in the patient data have a corresponding record in the donor data.")
    # else:
    #     print("The following donor IDs are missing from the donor data along with their corresponding patient IDs:")
    #     # print(missing_donors[['WL_ID_CODE', 'DONOR_ID']])
    #     print(missing_donors.shape)

    df = read_donornet_and_merge(df, "../data/donornet/donors.csv", 'donor_record_datetime')
    df = read_donornet_and_merge(df, "../data/donornet/DonorNet_SAS/abgs.csv", 'ABG_DT')
    df = read_donornet_and_merge(df, "../data/donornet/DonorNet_SAS/cbc.csv", 'CBC_DT')
    df = read_donornet_and_merge(df, "../data/donornet/DonorNet_SAS/labpanels.csv", 'LABS_DT')
    df = read_donornet_and_merge(df, "../data/donornet/DonorNet_SAS/labvalues.csv", 'LABVALUES_DT')
    df = remove_binary_indicators(df)
    df = df.drop(columns=['DONOR_ID'])
    print(df)

    df = df[~df['TX_YEAR'].isin([2023])]  # some of these we cannot observe the outcome
    print(df.shape)
    # (125534, 783)
    df = df[df['WLType'] == 'txp']
    print(df.shape)
    # (87599, 783)
    df.to_csv(save_path, index=False)


def process_txp_data(file_path, selected_variables, model):
    df = pd.read_csv(file_path, low_memory=False, encoding='utf-8')
    # df = df[df['TX_YEAR'] >= 2018]
    print(df.shape)

    # df = df[df['NUM_PREV_TX'] == 0]
    # df = df[df['NUM_PREV_TX'] == 0]
    # df = df[df['MULTIORG'] != 'Y']

    # df = df[selected_variables+ours_WLHIST_variable]
    df = df[selected_variables]

    # from scipy.stats import chi2_contingency
    # contingency_table = pd.crosstab(df['PSTATUS'], df['EDUCATION'])
    # chi2, p, dof, expected = chi2_contingency(contingency_table)
    # print(f"Chi-Square Statistic: {chi2}")
    # print(f"p-value: {p}")
    # print(f"Degrees of Freedom: {dof}")
    # print("Expected Frequencies:")
    # print(expected)
    # contingency_percent = contingency_table.div(contingency_table.sum(axis=1), axis=0) * 100
    #
    # # Plot the heatmap
    # plt.figure(figsize=(10, 6))
    # sns.heatmap(contingency_percent, annot=True, fmt=".1f", cmap='coolwarm', cbar=True)
    # plt.title("Relative Frequency Heatmap: PSTATUS vs EDUCATION")
    # plt.xlabel("EDUCATION")
    # plt.ylabel("PSTATUS")
    # plt.show()
    #
    # pdb.set_trace()

    # Remove patient who do not get a transplant at the end
    df = df[df['WLType'] == 'txp']
    # Remove rows where 'PType' is 'retxp' or 'alive' and 'TXPSurv' < 365
    df = df[~(((df['PType'] == 'retxp') | (df['PType'] == 'alive')) & (df['TXPSurv'] < 365 * YEARS))]
    # If 'PType' is 'retxp' or 'alive' and 'TXPSurv' >= 365*YEARS, set 'PSTATUS' to 1 (survive)
    df.loc[((df['PType'] == 'retxp') | (df['PType'] == 'alive')) & (df['TXPSurv'] >= 365 * YEARS), 'PSTATUS'] = 1
    # If 'PType' is 'dead' and 'TXPSurv' >= 365*YEARS, set 'PSTATUS' to 1
    df.loc[(df['PType'] == 'dead') & (df['TXPSurv'] >= 365 * YEARS), 'PSTATUS'] = 1
    # If 'PType' is 'dead' and 'TXPSurv' < 365*YEARS, set 'PSTATUS' to 0
    df.loc[(df['PType'] == 'dead') & (df['TXPSurv'] < 365 * YEARS), 'PSTATUS'] = 0

    df = df.drop(['TXPSurv', 'PType', 'WLType'], axis=1).reset_index(drop=True)
    print(df.shape)

    if print_dist:
        print_year_dist(df)

    # adjust abo grouping
    df = df.drop(columns=['ABO', 'ABO_DON'])

    if 'TCR_DGN' in df.columns:
        diagnosis_map = category_explanations['Patient primary diagnosis']
        df, diagnosis_multi_hot = encode_multi_hot_column(df, 'TCR_DGN', diagnosis_map, "Patient primary diagnosis")
        df = pd.concat([df, diagnosis_multi_hot], axis=1)

    if model == 'DRI':
        df = DRI(df)
    elif model == 'RSS':
        df = RSS(df)
    elif model == 'IMPACT':
        df = IMPACT(df)
    elif model == 'IHTSA':
        df = IHTSA(df)
    elif model == 'SOTA':
        df = SOTA(df)

    elif model in ['ours']:
        df = integrate_variables(df)
        df = convert_functional_status(df)
        # # make sure the units are aligned
        # df = correct_units(df)
        # create desired hemodynamics variables
        df = complete_hemodynamics(df)
        df['MULTIORG'] = df['MULTIORG'].fillna('N')

    else:
        NotImplementedError('Please re-select the model.')

    # Merge in per-patient last waitlist dynamic covariates early so they go through
    # the same preprocessing + one-hot + imputation pipeline as other TXP features.
    if not analyze_full_data:
        wl_last_path = '../datasets/wl_dynamic_last_values.csv'
        if os.path.exists(wl_last_path):
            wl_last = pd.read_csv(wl_last_path, low_memory=False, encoding='utf-8')
            wl_last = wl_last.drop(columns=[c for c in ['stop', 'start', 'start_timestamp'] if c in wl_last.columns])
            # Avoid merge suffixes like INR_x/INR_y by renaming overlapping TXP-key columns
            # to their merged_descriptions names (e.g., INR -> Donor INR) before merging.
            overlap = (set(df.columns) & set(wl_last.columns)) - {'WL_ID_CODE'}
            if overlap:
                inv_merged_descriptions = {v: k for k, v in merged_descriptions.items()}
                wl_last = wl_last.rename(
                    columns={c: inv_merged_descriptions[c] for c in overlap if c in inv_merged_descriptions})
            n_before = len(df)
            df = df.merge(wl_last, on='WL_ID_CODE', how='inner')
            print(f"Merged WL last dynamic covariates into TXP df (inner join): {n_before} -> {len(df)} rows")
        else:
            print(f"Warning: {wl_last_path} not found. Skipping WL-last merge.")

    y_data = df['PSTATUS']  # can add WL_ID_CODE for ID
    df = df.drop('PSTATUS', axis=1)
    print('Original number of samples: {}'.format(len(df)))
    print('Original number of variables: {}'.format(df.shape[-1]))

    df, numerical_cols, categorical_cols = standard_preprocess(
        df, num_threshold, cat_threshold,
        rare_min_rate=rare_category_min_rate,
    )
    # Splitting dataset into features and target variable
    df = df.drop('WL_ID_CODE', axis=1)
    print(df.shape)  # 64

    # Split and get only indices
    train_idx, test_idx = train_test_split(
        df.index,
        test_size=0.2,
        random_state=0
    )

    y_train, y_test = y_data.loc[train_idx], y_data.loc[test_idx]
    print(y_train.shape, y_train.sum())
    print(y_test.shape, y_test.sum())

    # Now you have train_idx and test_idx
    # To get the actual data later:
    X_train = df.loc[train_idx]
    X_test = df.loc[test_idx]
    data_types = {'numerical': numerical_cols, 'categorical': categorical_cols}

    baseline_table = create_baseline_table_grouped(X_train, X_test, df, y_data,
                                                   data_types, variable_name_groups, lr_significant_vars)
    latex_string = baseline_table.to_latex(index=True, escape=True, multirow=True)
    latex_string = latex_string.replace(r'\textbackslash quad', r'\quad')
    print(latex_string)
    # pdb.set_trace()

    # statistical_tests_and_summaries(df, numerical_cols, categorical_cols)
    x_data = one_hot_encoding(df, categorical_cols, numerical_cols)
    x_data.columns = x_data.columns.map(replace_first_underscore)
    # !!! primary diagnosis not in summary

    # Run univariate linear regression for each variable in x_data
    univariate_results = []

    for col in x_data.columns:
        # Combine X and y to drop NaNs jointly for this specific column
        x_col = x_data[[col]].apply(pd.to_numeric, errors='coerce')  # keep as DataFrame
        y_col = pd.to_numeric(y_data, errors='coerce')
        data = pd.concat([x_col, y_col], axis=1).dropna()
        X = sm.add_constant(data[[col]])
        y = data[y_data.name]

        univariate_model = sm.OLS(y, X).fit()
        coefs = univariate_model.params
        ses = univariate_model.bse
        pvals = univariate_model.pvalues

        # Calculate HR and 95% CI
        hr = np.exp(coefs)
        ci_lower = np.exp(coefs - 1.96 * ses)
        ci_upper = np.exp(coefs + 1.96 * ses)
        variable_name = coefs.index.drop('const')[0]

        result = {
            'Variable': variable_name,
            'HR': hr[variable_name],
            'CI Lower 95%': ci_lower[variable_name],
            'CI Upper 95%': ci_upper[variable_name],
            'P-value': pvals[variable_name],
            'N': len(data)
        }

        univariate_results.append(result)

    univariate_df = pd.DataFrame(univariate_results).dropna().sort_values(by='P-value').reset_index()
    univariate_df, significant_uni_df = generate_model_summary(univariate_df)
    univariate_df.to_csv('../results/univariate_results.csv')
    significant_uni_df.to_csv('../results/significant_univariate_results.csv')
    print(x_data.shape, x_data.columns)

    y_data = y_data.loc[df.index].reset_index(drop=True)

    if analyze_full_data:
        x_data.to_csv('../datasets/{}YEAR/TXP_data_{}_full.csv'.format(YEARS, model), index=False)
        y_data.to_csv('../datasets/{}YEAR/TXP_label_{}_full.csv'.format(YEARS, model), index=False)

        x_data = impute_dataset_mcmc(x_data, numerical_cols, 0)
        # x_data = impute_dataset_knn(x_data, numerical_cols, 5)
        # x_data = impute_dataset_median(x_data, numerical_cols)
        x_data.to_csv('../datasets/{}YEAR/TXP_data_{}_imputed_full.csv'.format(YEARS, model), index=False)

    else:
        x_data.to_csv('../datasets/{}YEAR/TXP_data_{}.csv'.format(YEARS, model), index=False)
        y_data.to_csv('../datasets/{}YEAR/TXP_label_{}.csv'.format(YEARS, model), index=False)

        x_data = impute_dataset_mcmc(x_data, numerical_cols, 0)
        # x_data = impute_dataset_knn(x_data, numerical_cols, 5)
        # x_data = impute_dataset_median(x_data, numerical_cols)
        x_data.to_csv('../datasets/{}YEAR/TXP_data_{}_imputed.csv'.format(YEARS, model), index=False)


def read_donornet(file_path):
    df = pd.read_csv(file_path)

    # Count the number of offers per 'wl_id_code'
    offers_per_record = df.groupby('wl_id_code').size().reset_index(name='offer_count')['offer_count']
    print(offers_per_record.mean(), offers_per_record.std())
    # 57.44072128964354 126.59750089116575

    # Visualize the distribution of offer counts
    plt.figure(figsize=(10, 6))
    sns.histplot(offers_per_record, bins=100, kde=False, edgecolor='black', alpha=0.7)
    plt.title('Number of Donor Offers per Waitlist Record', fontsize=14)
    plt.xlabel('Number of Offers', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('../images/number_offers.png')
    plt.close()

    df['final_response_dt'] = pd.to_datetime(df['final_response_dt'])

    # Sort by 'wl_id_code' and 'final_response_dt'
    df = df.sort_values(by=['wl_id_code', 'final_response_dt'])

    # Calculate the time difference between consecutive rows for each 'wl_id_code'
    df['wait_time'] = df.groupby('wl_id_code')['final_response_dt'].diff().dt.total_seconds() / 60 / 60

    # Drop rows with NaN (first donor offer per 'wl_id_code' has no wait time)
    df_donor_wait_time = df.dropna(subset=['wait_time'])['wait_time']

    print(df_donor_wait_time.mean(), df_donor_wait_time.std())
    # hours: 100.335121619571 454.26331161434484
    print(df_donor_wait_time.mean() / 24, df_donor_wait_time.std() / 24)
    # days: 4.180630067482125 18.927637983931035

    df_donor_wait_time = df_donor_wait_time.apply(lambda x: 1000 if x > 1000 else x)

    # Visualize the wait time distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df_donor_wait_time, bins=100, edgecolor='black', alpha=0.7)
    plt.title('Wait Time Distribution for Donor Offers (Capped at 1000 Hours)', fontsize=14)
    plt.xlabel('Wait Time (hours)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig('../images/offer_time.png')
    plt.close()


def run_txp_data(model_choice):
    if analyze_full_data:
        data_path = '../datasets/df_txp_full.csv'
    else:
        data_path = '../datasets/df_txp.csv'

    if model_choice == 'DRI':
        process_txp_data(data_path, DRI_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'RSS':
        process_txp_data(data_path, RSS_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'IMPACT':
        process_txp_data(data_path, IMPACT_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'IHTSA':
        process_txp_data(data_path, IHTSA_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'ToRsR':
        process_txp_data(data_path, ToRsR_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'SOTA':
        process_txp_data(data_path, SOTA_TXP_variables + default_TXP_variables, model_choice)
    elif model_choice == 'ours':
        process_txp_data(data_path, baseline_TXP_variable + new_thoracic_TXP_variables + donornet_TXP_variables +
                         donor_TXP_variables + default_TXP_variables, model_choice)


# read_from_transplant_data
if __name__ == '__main__':
    # offer_data_path = '../data/donornet/offers.csv'
    # read_donornet(offer_data_path)
    # pdb.set_trace()

    # read_from_transplant_data()
    # create_TXP_static_data(txp_data_path)

    if run_all:
        for model in txp_model_choices:
            run_txp_data(model)
    else:
        run_txp_data(model)


