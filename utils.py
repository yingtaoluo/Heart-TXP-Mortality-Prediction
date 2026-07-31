from variables import *
import os
import pandas as pd
import numpy as np
import pdb
import matplotlib.pyplot as plt
import statsmodels.api as sm
from lifelines import KaplanMeierFitter, CoxTimeVaryingFitter
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from scipy.stats import kstest, norm
from scipy.stats import ttest_ind
from scipy.stats import chi2_contingency
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import BayesianRidge
from sklearn.impute import SimpleImputer, KNNImputer
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    balanced_accuracy_score, roc_auc_score, roc_curve, auc,
    confusion_matrix, ConfusionMatrixDisplay, brier_score_loss,
    average_precision_score
)
from sklearn.calibration import calibration_curve
from scipy import stats
import re
import copy
import seaborn as sns
from tqdm import tqdm
import pickle
import pgeocode
from functools import lru_cache


special_columns_to_consider = []
# special_columns_to_consider = ['Patient functional status at TXP',
#                                'Donor LV ejection fraction %',
#                                'Donor shortening fraction (SF)', 'Donor septal wall thickness',
#                                'Donor LV posterior wall thickness', 'Donor aortic knob width (cm)',
#                                'Donor diaphragm width (cm)', 'Donor dist. RCPA to LCPA (cm)', ]

pd.set_option('display.max_rows', 120)
pd.set_option('display.max_columns', 100)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

plt.rcParams.update({
    'font.size': 18,            # Global font size
    'axes.titlesize': 20,       # Title font
    'axes.labelsize': 18,       # Axis labels
    'xtick.labelsize': 16,      # X tick labels
    'ytick.labelsize': 16,      # Y tick labels
    'legend.fontsize': 18,      # Legend text
})

reference_dict = {}
con_keywords = ['age', 'days', 'hours', 'minutes', 'number', 'Number', 'functional', ]
cat_keywords = ['antigen', 'primary diagnosis', 'cancer', 'year', 'brand', 'region']
ID_keywords = ['Offer Accept', 'offer_accept', 'WL_ID_CODE', 'DONOR_ID', 't', 'event', 'start_timestamp',
               'start', 'stop', 'initial_response_dt', 'waitlist_start_date',]


def standard_preprocess(
    df,
    num_threshold,
    cat_threshold,
    load_rows=False,
    task_type=None,
    rare_min_rate=0.01,
):
    df = df.rename(columns=merged_descriptions)

    numerical_cols, categorical_cols = detect_data_types(df)
    print("Numerical columns: {}".format(numerical_cols))
    print("Categorical columns: {}".format(categorical_cols))

    if not load_rows:
        df = handle_missing_values(df, categorical_cols, task_type, num_threshold, cat_threshold)
    else:
        df = load_cols_and_rows(df, task_type)

    numerical_cols, categorical_cols = detect_data_types(df)
    print(numerical_cols)
    print(len(numerical_cols))
    print(categorical_cols)
    print(len(categorical_cols))

    df = collapse_rare_categories(df, categorical_cols, min_rate=rare_min_rate)
    df, categorical_cols = drop_rare_binary_categoricals(
        df, categorical_cols, min_rate=rare_min_rate,
    )

    return df, numerical_cols, categorical_cols


def load_cols_and_rows(df, task_type='TXP'):
    if task_type == 'TXP':
        wl_codes = pd.read_csv('../checkpoints/TXP_row_codes.csv')['WL_ID_CODE'].tolist()
        columns_to_drop = pd.read_csv('../checkpoints/TXP_columns_to_drop.csv')['drop'].tolist()
    else:
        wl_codes = pd.read_csv('../checkpoints/WL_row_codes.csv')['WL_ID_CODE'].tolist()
        columns_to_drop = pd.read_csv('../checkpoints/WL_columns_to_drop.csv')['drop'].tolist()

    # Filter the new DataFrame to include only rows with matching WL_ID_CODE
    df = df.drop(columns=columns_to_drop)
    df = df[df['WL_ID_CODE'].isin(wl_codes)]

    return df


def clean_suffix(suffix):
    if suffix.endswith('.0'):
        return suffix[:-2]  # Remove the last two characters '.0'
    return suffix


def get_clean_variable_name(column_name):
    suffixes = set()
    for key in merged_descriptions.keys():
        parts = key.split('_')
        if len(parts) > 1:
            # We assume the last part of a split name could be a suffix
            suffixes.add(parts[-1])

    parts = column_name.split('_')

    if parts[-1] in suffixes or len(parts) == 1:
        base_name = column_name
        suffix = None
    else:
        base_name = ':'.join(parts[:-1])
        suffix = parts[-1]

    return base_name, suffix


def encode_multi_hot_column(df, col, label_map, prefix):
    # Convert to string and safely map to label list
    col_str = f"{col}_str"
    df[col_str] = df[col].fillna(-1).astype(int).astype(str)
    df['__multi_labels__'] = df[col_str].map(lambda x: label_map.get(x, []))

    # Multi-hot encode
    mlb = MultiLabelBinarizer()
    multi_hot = pd.DataFrame(
        mlb.fit_transform(df['__multi_labels__']),
        columns=[f"{prefix}_{cls}" for cls in mlb.classes_],
        index=df.index
    )

    df.drop(columns=['__multi_labels__', col_str, col], inplace=True)

    return df, multi_hot


def get_variable_description(column_name):
    base_name, suffix = get_clean_variable_name(column_name)

    if base_name in merged_descriptions:
        description = merged_descriptions[base_name]
        if suffix:
            return f"{description}: {[suffix]}."
        else:
            return description
    else:
        return column_name


# Function to map values based on category explanations, defaulting to 'U' if not found
def map_to_description(column, value):  # the columns are variable_names, not variables
    # If the value is in the explanations for the column, return the mapped value
    if column in category_explanations and value in category_explanations[column]:
        return category_explanations[column][value]
    elif column in category_explanations and value not in category_explanations[column] and value not in category_explanations[column].values():
        return 'U'
    else:
        return value


# Function to transform a single description
def transform_description(description):
    for key in category_explanations.keys():
        if key in description:
            # Extract the value inside the brackets
            start_idx = description.find("['") + 2
            end_idx = description.find("']", start_idx)
            value = description[start_idx:end_idx]
            # Get the explanation for the value using map_to_description
            explanation = map_to_description(key, value)
            # Replace the entire pattern including brackets with the explanation
            description = description.replace(f"['{value}']", explanation)
    # Remove any remaining brackets if transformation did not occur
    description = description.replace("['", "").replace("']", "")
    return description


def collapse_rare_categories(df, cat_cols, min_rate=0.01):
    """
    Collapse infrequent category levels to 'Other'.

    A level is infrequent if its count is < min_rate * N (default 1% of the cohort).
    No absolute-count threshold.
    """
    n = len(df)
    if n == 0:
        return df
    min_count = n * float(min_rate)

    for col in cat_cols:
        if col not in df.columns:
            continue
        value_counts = df[col].value_counts(dropna=True)
        rare_values = value_counts[value_counts < min_count].index.tolist()
        if not rare_values:
            continue
        print(
            f"  collapse '{col}': {len(rare_values)} level(s) < {min_rate:.0%} "
            f"(n<{min_count:.0f}) -> Other",
            flush=True,
        )
        df[col] = df[col].apply(lambda x, rare=set(rare_values): 'Other' if x in rare else x)

    return df


_BINARY_IGNORE_LEVELS = {
    "u", "unknown", "none", "nan", "nat", "", "not reported", "not asked",
}


def drop_rare_binary_categoricals(df, cat_cols, min_rate=0.01):
    """
    Drop binary categorical columns whose minority class is < min_rate of the cohort.

    A column counts as binary if, after dropping NA and ignore-levels (U/Unknown/…),
    exactly two levels remain (e.g. Yes/No, Positive/Negative).
    """
    cat_cols = list(cat_cols)
    n = len(df)
    if n == 0:
        return df, cat_cols

    drop_cols = []
    for col in cat_cols:
        if col not in df.columns:
            continue
        vals = df[col].dropna().astype(str).str.strip()
        informative = vals[~vals.str.lower().isin(_BINARY_IGNORE_LEVELS)]
        vc = informative.value_counts()
        if len(vc) != 2:
            continue

        minority_n = int(vc.min())
        minority_rate = minority_n / n
        if minority_rate < min_rate:
            drop_cols.append(col)
            print(
                f"  drop binary '{col}': levels={dict(vc)}; "
                f"minority n={minority_n} ({minority_rate:.4%}) < {min_rate:.0%}",
                flush=True,
            )

    if drop_cols:
        print(
            f"Dropped {len(drop_cols)} rare binary categorical(s) "
            f"(min_rate={min_rate:.0%}): {drop_cols}",
            flush=True,
        )
        df = df.drop(columns=drop_cols)
        cat_cols = [c for c in cat_cols if c not in drop_cols]
    else:
        print(
            f"No rare binary categoricals dropped (min_rate={min_rate:.0%}).",
            flush=True,
        )

    return df, cat_cols


def one_hot_encoding(df, cat_cols, num_cols):
    # Skip variables that already have ":" in their names (already processed)
    cat_cols_unprocessed = [col for col in cat_cols if ":" not in col]
    
    # Identify diagnosis cols
    diagnosis_cols = [col for col in cat_cols_unprocessed if "Patient primary diagnosis" in col]

    # Remove diagnosis cols from cat_cols (to exclude from encoding)
    cat_cols_to_encode = [col for col in cat_cols_unprocessed if col not in diagnosis_cols]

    # Fit encoder only on filtered categorical columns
    encoder = OneHotEncoder(drop=None, sparse_output=False, handle_unknown='ignore')
    encoder.fit(df[cat_cols_to_encode])

    # Create preprocessor with explicit passthrough for diagnosis and already processed columns
    # already_processed_cols = [col for col in cat_cols if ":" in col]
    processed_cols = [col for col in df.columns if col not in num_cols + cat_cols_to_encode + diagnosis_cols]
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', num_cols),
            ('cat', encoder, cat_cols_to_encode),
            ('diag', 'passthrough', diagnosis_cols),
            ('processed', 'passthrough', processed_cols),
        ],
        remainder='drop'  # now safe to drop others, all needed cols are handled
    )

    # Transform data
    df_transformed_array = preprocessor.fit_transform(df)
    feature_names = preprocessor.get_feature_names_out()
    feature_names = [name.split("__")[-1] for name in feature_names]
    # feature_names = num_cols + diagnosis_cols + encoder.get_feature_names_out(cat_cols).tolist()
    df_transformed = pd.DataFrame(df_transformed_array, columns=feature_names, index=df.index)

    # Define default reference keywords
    prioritized_labels = ['n', 'no', 'none', 'not hospitalized', 'Unspecified', 'other', 'Fully Matched']
    prioritized_labels = [kw.strip().lower() for kw in prioritized_labels]

    # Drop reference category from each categorical variable that was actually encoded
    for col in cat_cols_to_encode:
        related_cols = [c for c in df_transformed.columns if c.startswith(f"{col}_")]

        # Drop 'U' if present
        u_col = next((c for c in related_cols if c.endswith('_U')), None)
        if u_col:
            df_transformed.drop(u_col, axis=1, inplace=True)
            related_cols.remove(u_col)

        # Step 1: Use user-defined reference category
        if col in reference_dict:
            ref_cat = reference_dict[col]
            ref_col = f"{col}_{ref_cat}"
        else:
            # Step 2: Use prioritized keywords for label-based reference selection
            ref_col = None
            if col in category_explanations:
                for keyword in prioritized_labels:
                    for code, label in category_explanations[col].items():
                        if label.strip().lower() == keyword:
                            ref_col_candidate = f"{col}_{label}"
                            if ref_col_candidate in related_cols:
                                ref_col = ref_col_candidate
                                break
                    if ref_col:
                        break

            # Step 3: If still none, fallback to first sorted column
            if not ref_col and related_cols:
                ref_col = sorted(related_cols)[0]

        # Drop the chosen reference column
        if ref_col and ref_col in df_transformed.columns:
            df_transformed.drop(ref_col, axis=1, inplace=True)

    # print(df_transformed.columns)
    return df_transformed


def statistical_tests_and_summaries(df, num_cols, cat_cols):
    def calculate_vif(X):
        # Adding a constant column for intercept
        X = sm.add_constant(X)
        vif = pd.DataFrame()
        vif["Variables"] = X.columns
        vif["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
        return vif

    vif = calculate_vif(df[num_cols])
    print(vif)

    # Calculate statistical summaries
    summaries_mean_var = {}
    for col in num_cols:
        try:
            df[col] = df[col].astype(float)
            # statistic, p_value = kstest(df[col], 'norm', args=(df[col].mean(), df[col].std()))
            summaries_mean_var[col] = {'Mean': df[col].mean(), 'Standard Deviation': df[col].std(),
                                       'Median': df[col].median(), 'Q1': df[col].quantile(0.25),
                                       'Q3': df[col].quantile(0.75)
                                       }
        except:
            pdb.set_trace()

    categorical_summaries = {}
    # Categorical Columns: Ratios
    for col in cat_cols:
        categorical_summaries[col] = df[col].value_counts(normalize=True).to_dict()

    # Create DataFrames from the summaries dictionaries
    mean_var_df = pd.DataFrame(summaries_mean_var).T.round(3)


# Function to impute a dataset
def impute_dataset_mcmc(data_df, cols_to_impute, random_state):
    # Prepare data for imputation
    cols_to_impute = [c for c in cols_to_impute if c in data_df.columns]
    numeric_df = data_df[cols_to_impute].copy()

    # Create MCMC imputer
    imputer = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=5,
        random_state=random_state,
        sample_posterior=True  # MCMC-like behavior
    )

    imputed_data = imputer.fit_transform(numeric_df)
    imputed_df = pd.DataFrame(imputed_data, columns=cols_to_impute)

    # Merge imputed values with original data
    result_df = data_df.copy()
    for col in cols_to_impute:
        result_df[col] = imputed_df[col]

    return result_df


# Function to impute a dataset using KNN
def impute_dataset_knn(data_df, cols_to_impute, n_neighbors=5):
    # Prepare data for imputation
    numeric_df = data_df[cols_to_impute].copy()

    # Create KNN imputer
    imputer = KNNImputer(n_neighbors=n_neighbors)

    # Fit and transform
    imputed_data = imputer.fit_transform(numeric_df)
    imputed_df = pd.DataFrame(imputed_data, columns=cols_to_impute)

    # Merge imputed values with original data
    result_df = data_df.copy()
    for col in cols_to_impute:
        result_df[col] = imputed_df[col]

    return result_df


# Function to impute a dataset
def impute_dataset_median(data_df, cols_to_impute):
    # Prepare data for imputation
    numeric_df = data_df[cols_to_impute].copy()

    # Create median imputer
    imputer = SimpleImputer(strategy='median')
    imputed_data = imputer.fit_transform(numeric_df)
    imputed_df = pd.DataFrame(imputed_data, columns=cols_to_impute)

    # Merge imputed values with original data
    result_df = data_df.copy()
    for col in cols_to_impute:
        result_df[col] = imputed_df[col]

    return result_df


def calculate_vif(df, features):
    # Create a dataframe for VIF values
    vif_data = pd.DataFrame()
    vif_data["Feature"] = features

    # Calculate VIF for each feature
    vif_data["VIF"] = [variance_inflation_factor(df[features].values, i)
                       for i in range(len(features))]

    # Sort by VIF values
    vif_data = vif_data.sort_values("VIF", ascending=False)

    return vif_data


# Add a small value to duration for rows where entry >= duration
def prepare_time_data(df):
    # Find problematic rows
    problematic_rows = df['start'] >= df['stop']
    print(f"Found {problematic_rows.sum()} rows where start >= stop")

    # Add a small epsilon to stop time for these rows
    if problematic_rows.sum() > 0:
        epsilon = 1e-4  # Small value (e.g., 0.0001 day)
        df.loc[problematic_rows, 'stop'] = df.loc[problematic_rows, 'start'] + epsilon
        print(f"Added {epsilon} to stop time for problematic rows")

    return df


# Function to replace unknown values with 'U' and convert to string
def replace_unknowns_and_convert_to_str(df, col):
    # Replace known unknowns and fill NaN
    df[col] = df[col].replace(['ND', 'PD', None, 'UNK', 998], 'U').fillna('U')
    df[col] = convert_to_string(df[col])

    return df


def handle_missing_values(df, cat_cols, data_type, num_threshold, cat_threshold):
    # replace unknown values with 'U' and convert to string
    for col in cat_cols:
        df = replace_unknowns_and_convert_to_str(df, col)

    # ratio 0.3 means >0.3 missing values is not acceptable
    threshold = len(df) * num_threshold
    missing_values_count = df.isna().sum().sort_values(ascending=False)

    # Identify columns to drop
    columns_to_drop = missing_values_count[missing_values_count > threshold].index
    print(f"Columns with >{int(num_threshold * 100)}% missingness:", columns_to_drop)
    columns_to_drop = [col for col in columns_to_drop if col not in special_columns_to_consider]

    # Remove these columns from the DataFrame
    df = df.drop(columns=columns_to_drop)
    print('{} numerical columns are removed: {}.'.format(len(columns_to_drop), columns_to_drop))

    # Apply the mapping function to each categorical column
    for col in df.columns:
        if col in category_explanations:  # Only process columns that have explanations
            df[col] = df[col].apply(lambda x: map_to_description(col, x))

    u_ratio = (df == 'U').mean()  # computes the proportion of 'U' in each column
    cols_with_many_U = u_ratio[u_ratio > cat_threshold].index.tolist()
    print(f"Columns with >{int(cat_threshold * 100)}% 'U':", cols_with_many_U)
    cols_with_many_U = [col for col in cols_with_many_U if col not in special_columns_to_consider]
    df = df.drop(columns=cols_with_many_U)
    print('{} categorical columns are removed: {}.'.format(len(cols_with_many_U), cols_with_many_U))

    columns_to_drop = columns_to_drop + cols_with_many_U
    remaining_columns = set(df.columns)
    print('remaining columns: {}'.format(remaining_columns))

    # # Define which tokens count as "string-missing"
    # missing_tokens = {'U', 'Unknown', 'None'}
    # # Count total cells
    # total_cells = df.shape[0] * df.shape[1]
    # # Count NaNs
    # nan_missing = df.isna().sum().sum()
    # # Count token-based missing values
    # token_missing = df.map(
    #     lambda x: str(x).strip() in missing_tokens if pd.notna(x) else False
    # ).to_numpy().sum()
    # # Compute totals
    # total_missing = nan_missing + token_missing
    #
    # # Percent breakdown
    # nan_pct = nan_missing / total_cells * 100
    # token_pct = token_missing / total_cells * 100
    # total_pct = total_missing / total_cells * 100
    # print(f"Total missing: {total_missing} ({total_pct:.2f}%)")
    # print(f"  • NaN: {nan_missing} ({nan_pct:.2f}%)")
    # print(f"  • 'U'/Unknown/None: {token_missing} ({token_pct:.2f}%)")

    # df.dropna(inplace=True)  # Example: Removing rows with missing values
    if data_type == 'TXP':
        pd.DataFrame(columns_to_drop, columns=['drop']).to_csv('../checkpoints/TXP_columns_to_drop.csv', index=False)
        df['WL_ID_CODE'].to_csv('../checkpoints/TXP_row_codes.csv', index=False)
    elif data_type == 'WL':
        pd.DataFrame(columns_to_drop, columns=['drop']).to_csv('../checkpoints/WL_columns_to_drop.csv', index=False)
        df['WL_ID_CODE'].to_csv('../checkpoints/WL_row_codes.csv', index=False)

    return df


def print_year_dist(df):
    y = df['PSTATUS']
    y = y.map({1: 0, 0: 1})  # for mortality rate prediction
    X = df.drop('PSTATUS', axis=1)

    # Assuming 'TX_YEAR' contains the actual transplant year values
    tx_years = X['TX_YEAR'].unique()
    tx_years = tx_years[~np.isnan(tx_years)]

    Mortality_rates = []
    patient_counts = []

    for year in sorted(tx_years):
        # Calculate Mortality rate and patient count for the current year
        Mortality_rate = y[X['TX_YEAR'] == year].mean()
        patient_count = (X['TX_YEAR'] == year).sum()

        Mortality_rates.append((year, Mortality_rate))
        patient_counts.append((year, patient_count))

    # Convert to DataFrame for plotting
    Mortality_df = pd.DataFrame(Mortality_rates, columns=['Year', 'Mortality Rate'])
    patient_count_df = pd.DataFrame(patient_counts, columns=['Year', 'Patient Count'])

    # Plot the Mortality rate and patient count
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Mortality rate (line plot)
    ax1.plot(Mortality_df['Year'], Mortality_df['Mortality Rate'], marker='o', color='blue', linestyle='-',
             label='Actual Mortality Rate')

    ax1.set_xlabel('Year of TXP')
    ax1.set_ylabel('Mortality Rate', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Set x-ticks to be integers
    ax1.set_xticks(Mortality_df['Year'])
    ax1.set_xticklabels(Mortality_df['Year'].astype(int), rotation=45)

    # Update legend
    ax1.legend(loc='upper center')

    # Create a second y-axis for the patient count
    ax2 = ax1.twinx()
    ax2.bar(patient_count_df['Year'], patient_count_df['Patient Count'], alpha=0.6, color='gray',
            label='Patient Count')
    ax2.set_ylabel('Patient Count', color='gray')
    ax2.tick_params(axis='y', labelcolor='gray')

    # Title and layout
    plt.title('Mortality Rate and Patient Count by Year of Transplant (TXP) in Adult Patients')
    fig.tight_layout()

    plt.savefig("../images/year_mortality.png", dpi=300)

    # Show the plot
    plt.show()


def detect_data_types(df, unique_threshold=20, is_description=True):
    numerical_columns = []
    categorical_columns = []

    for column in df.columns:
        if column.strip().lower() in {k.lower() for k in ID_keywords}:
            continue

        if not is_description:
            description = merged_descriptions.get(column, "")
        else:
            description = column

        # checks if any keyword appears as a whole word (case-insensitive) in the string description
        if any(re.search(rf'\b{re.escape(keyword)}\b', description, flags=re.IGNORECASE) for keyword in con_keywords):
            numerical_columns.append(column)
            continue
        if any(re.search(rf'\b{re.escape(keyword)}\b', description, flags=re.IGNORECASE) for keyword in cat_keywords):
            categorical_columns.append(column)
            continue

        # Check if the column contains any alphabetic characters
        if df[column].apply(lambda x: isinstance(x, str) and x.isalpha()).any():
            categorical_columns.append(column)
            continue

        unique_values = df[column].nunique()
        try:
            if unique_values >= unique_threshold:
                numerical_columns.append(column)
            else:
                categorical_columns.append(column)
        except ValueError:  # this means that you have multiple columns with the same name
            print('Value Error!')
            pdb.set_trace()

    return numerical_columns, categorical_columns


def remove_binary_indicators(df):
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if the column contains binary strings
            try:
                if df[col].str.contains("^b'.*'$").any():
                    df[col] = df[col].str.replace("^b'(.*)'$", r'\1', regex=True)
            except AttributeError:
                # print(col)
                pass
    return df


# Convert everything to clean strings
def convert_to_string(df_col):
    df_col = df_col.apply(lambda x: str(int(x)).strip() if isinstance(x, (int, float)) else str(x).strip())
    return df_col


def txp_datetime_format(df):
    # make sure certain columns are datetime format
    df['INIT_DATE'] = pd.to_datetime(df['INIT_DATE'], errors='coerce')
    df['END_DATE'] = pd.to_datetime(df['END_DATE'], errors='coerce')
    df['TX_DATE'] = pd.to_datetime(df['TX_DATE'], errors='coerce')
    df['PX_STAT_DATE'] = pd.to_datetime(df['PX_STAT_DATE'], errors='coerce')
    df['COMPOSITE_DEATH_DATE'] = pd.to_datetime(df['COMPOSITE_DEATH_DATE'], errors='coerce')

    return df


# ------------------------------------------------------------------
# Shared ZIP/region/distance utilities for donor-feature pipelines
# ------------------------------------------------------------------

STATE_TO_UNOS_REGION = {
    'CT': 1, 'MA': 1, 'ME': 1, 'NH': 1, 'RI': 1, 'VT': 1,
    'DC': 2, 'DE': 2, 'MD': 2, 'NJ': 2, 'PA': 2, 'WV': 2,
    'FL': 3, 'GA': 3, 'PR': 3,
    'OK': 4, 'TX': 4,
    'AZ': 5, 'CA': 5, 'NV': 5, 'NM': 5, 'UT': 5,
    'AK': 6, 'HI': 6, 'ID': 6, 'MT': 6, 'OR': 6, 'WA': 6,
    'IL': 7, 'MN': 7, 'ND': 7, 'SD': 7, 'WI': 7,
    'CO': 8, 'IA': 8, 'KS': 8, 'MO': 8, 'NE': 8, 'WY': 8,
    'NY': 9,
    'IN': 10, 'MI': 10, 'OH': 10,
    'AL': 11, 'AR': 11, 'KY': 11, 'LA': 11, 'MS': 11, 'NC': 11, 'SC': 11, 'TN': 11, 'VA': 11,
}

_NOMI_US = pgeocode.Nominatim("us")


def normalize_us_zip(zip_code):
    """Normalize ZIP to 5-digit string; return np.nan for invalid/missing."""
    if pd.isna(zip_code):
        return np.nan
    z = str(zip_code).strip()
    if z == "" or z.lower() == "nan":
        return np.nan
    z = z.split("-")[0]
    digits = "".join(ch for ch in z if ch.isdigit())
    if digits == "":
        return np.nan
    return digits[:5].zfill(5)


@lru_cache(maxsize=None)
def zip_to_unos_region(zip_code):
    """Convert ZIP to UNOS region (1-11). Returns np.nan if unknown."""
    z = normalize_us_zip(zip_code)
    if pd.isna(z):
        return np.nan
    rec = _NOMI_US.query_postal_code(z)
    state = rec.state_code if rec is not None else None
    return STATE_TO_UNOS_REGION.get(state, np.nan)


@lru_cache(maxsize=None)
def zip_to_latlon(zip_code):
    """Convert ZIP to (lat, lon) tuple; returns (np.nan, np.nan) when missing."""
    z = normalize_us_zip(zip_code)
    if pd.isna(z):
        return (np.nan, np.nan)
    rec = _NOMI_US.query_postal_code(z)
    if rec is None:
        return (np.nan, np.nan)
    lat = getattr(rec, "latitude", np.nan)
    lon = getattr(rec, "longitude", np.nan)
    return (lat, lon)


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance in kilometers."""
    r = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(a))


def compute_distance_from_zip_series(source_zip, target_zip):
    """
    Compute row-wise source-target distance (km) from two ZIP Series.
    Returns a float Series aligned to source_zip index.
    """
    src = source_zip.apply(normalize_us_zip)
    tgt = target_zip.apply(normalize_us_zip)
    pairs = pd.DataFrame({"src_zip": src, "tgt_zip": tgt}, index=source_zip.index)
    pairs["src_latlon"] = pairs["src_zip"].map(zip_to_latlon)
    pairs["tgt_latlon"] = pairs["tgt_zip"].map(zip_to_latlon)
    pairs["src_lat"] = pairs["src_latlon"].str[0]
    pairs["src_lon"] = pairs["src_latlon"].str[1]
    pairs["tgt_lat"] = pairs["tgt_latlon"].str[0]
    pairs["tgt_lon"] = pairs["tgt_latlon"].str[1]
    return pd.Series(
        haversine_distance_km(
            pairs["src_lat"].values,
            pairs["src_lon"].values,
            pairs["tgt_lat"].values,
            pairs["tgt_lon"].values,
        ),
        index=source_zip.index,
    )


def read_donornet_and_merge(df, file_path, time_name):
    donor_df = pd.read_csv(file_path, low_memory=True, encoding='utf-8')

    # print(donor_df['DONOR_ID'].unique().shape)
    # # Find donor IDs in the patient data that are not present in the donor data
    # missing_donors = df[~df['DONOR_ID'].isin(donor_df['DONOR_ID'])]
    # # Check if any donor IDs are missing and display the missing donor IDs along with patient IDs
    # if missing_donors.empty:
    #     print("All donor IDs in the patient data have a corresponding record in the donor data.")
    # else:
    #     print("The following donor IDs are missing from the donor data along with their corresponding patient IDs:")
    #     # print(missing_donors[['PT_CODE', 'DONOR_ID']])
    #     print(missing_donors.shape)

    table_name = os.path.basename(file_path).split('.')[0]
    df['TX_DATE'] = pd.to_datetime(df['TX_DATE']).dt.date
    donor_df[time_name] = pd.to_datetime(donor_df[time_name])
    # Filter donor_df to include only rows with DONOR_ID present in df['DONOR_ID']
    donor_df_filtered = donor_df[donor_df['DONOR_ID'].isin(df['DONOR_ID'])]
    # Merge df and donor_df_filtered on DONOR_ID to perform the date matching
    merged_df = pd.merge(df[['DONOR_ID', 'TX_DATE']], donor_df_filtered, on='DONOR_ID')
    # Extract date part from donor_record_datetime and compare with TX_DATE
    merged_df['donor_date'] = merged_df[time_name].dt.date
    # # Filter rows where TX_DATE matches donor_date
    # matched_df = merged_df[merged_df['TX_DATE'] == merged_df['donor_date']]
    # Calculate the absolute difference between TX_DATE and donor_date
    merged_df['date_diff'] = (merged_df['TX_DATE'] - merged_df['donor_date']).abs()

    # Calculate the number of non-missing values for each row
    merged_df['non_missing_count'] = merged_df.notna().sum(axis=1)

    # Sort by non-missing values count (descending), date difference (ascending), time_name (descending)
    merged_df = merged_df.sort_values(by=['non_missing_count', 'date_diff', time_name], ascending=[False, True, False])

    # Remove duplicate DONOR_ID entries, keeping the first occurrence
    final_df = merged_df.drop_duplicates(subset=['DONOR_ID'])
    drop_col = ['TX_DATE', 'non_missing_count', 'date_diff', time_name, 'donor_date']
    # Rename columns if there are conflicts with existing column names in df, excluding TX_DATE and DONOR_ID
    # final_df.columns = [
    #     col if col not in df.columns or col in ['TX_DATE', 'DONOR_ID'] else f"{col}_{table_name}"
    #     for col in final_df.columns
    # ]

    # this avoids redundant variable names
    final_df = final_df.rename(
        columns=lambda x: f"{x}_{table_name}" if x in df.columns and x not in ['TX_DATE', 'DONOR_ID'] else x)
    df = pd.merge(df, final_df.drop(columns=drop_col), on='DONOR_ID', how='left')
    # print(df.shape)

    return df


# deceased_donor_data: 1 row/DONOR_ID; matches DonorNet on overlap; clinical dates ~2d before offer.
# Fill only IDs absent from donors.csv; stamp time_col = earliest offer time for that donor (proxy for merge).
# Coverage vs offers (~113k unique donors): donors.csv ~53% (gap ~53k, of which ~89% in deceased — why we fill);
# abgs/cbc/labpanels/labvalues ~95% and share the same ID set (gap ~5.6k, 0% in deceased — do not fill labs here).
DECEASED_TO_DONORNET_COLMAP = {
    "AGE_DON": "age_in_months",  # years -> *12
    "WGT_KG_DON_CALC": "wgt_kg",
    "HGT_CM_DON_CALC": "hgt_cm",
    "BMI_DON_CALC": "donor_bmi",
    "CARDARREST_DOWNTM_DURATION": "cardarrest_downtm_duration",
    "CPR_ADMIN_DURATION": "cpr_admin_duration",
    "HIST_CAD": "hist_cad",
    "HBV_DNA": "hbv_dna",
    "HBV_SUR_ANTIGEN_DON": "hbsag",
    "HBSAB_DON": "hbsab",
    "HCV_NAT": "hcv_nat",
    "HTLV_DON": "htlv",
    "VDRL_DON": "vdrl",
    "EBV_IGG_CAD_DON": "ebv_igg",
    "EBV_IGM_CAD_DON": "ebv_igm",
    "EBNA_DON": "ebna",
    "TOXO_IGG_DON": "toxo_igg",
    "CHAGAS_SEROLOGY": "chagas_serology",
    "WEST_NILE_SEROLOGY": "west_nile_serology",
    "WEST_NILE_NAT": "west_nile_nat",
    "SHFRAC": "shfrac",
    "SEPTAL_WALL": "Septal_wall",
    "POSTERIOR_WALL": "Posterior_wall",
    "WIDTH_AORTIC_KNOB": "Width_aortic_knob",
    "WIDTH_DIAPHRAGM": "Width_diaphragm",
    "DIST_RCPA_LCPA": "Dist_rcpa_lcpa",
}
_HIST_CAD_MAP = {"Y": "YES", "YES": "YES", "N": "NO", "NO": "NO", "U": "U", "UNK": "U", "UNKNOWN": "U"}


def _decode_deceased_cell(x):
    if isinstance(x, (bytes, bytearray)):
        x = x.decode("utf-8", "ignore")
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if len(s) >= 3 and s[:2] in ("b'", 'b"') and s[-1] in ("'", '"'):
        s = s[2:-1]
    return np.nan if s in ("", "nan", "None", "NaN") else s


def fill_missing_donors_from_deceased(
    donor_df,
    offer_df,
    time_col,
    offer_time_col,
    deceased_path="../data/thoracic_data/deceased_donor_data.csv",
):
    """Append deceased static features for offer DONOR_IDs missing from DonorNet donors.csv."""
    present = set(pd.to_numeric(donor_df["DONOR_ID"], errors="coerce").dropna().unique())
    needed = set(pd.to_numeric(offer_df["DONOR_ID"], errors="coerce").dropna().unique())
    missing_ids = needed - present

    usecols = ["DONOR_ID"] + list(DECEASED_TO_DONORNET_COLMAP)
    dd = pd.read_csv(deceased_path, usecols=lambda c: c in usecols, low_memory=False)
    dd["DONOR_ID"] = pd.to_numeric(dd["DONOR_ID"], errors="coerce")
    dd = dd[dd["DONOR_ID"].isin(missing_ids)].drop_duplicates("DONOR_ID")

    # One row per donor; time = earliest offer for that ID so all its offers pass time<=offer.
    offer_t = (
        offer_df.loc[offer_df["DONOR_ID"].isin(dd["DONOR_ID"]), ["DONOR_ID", offer_time_col]]
        .groupby("DONOR_ID", as_index=True)[offer_time_col]
        .min()
    )
    add = dd.rename(columns=DECEASED_TO_DONORNET_COLMAP).copy()
    add[time_col] = add["DONOR_ID"].map(offer_t)
    add = add.dropna(subset=[time_col])

    if "age_in_months" in add.columns:
        add["age_in_months"] = pd.to_numeric(add["age_in_months"], errors="coerce") * 12.0
    if "hist_cad" in add.columns:
        add["hist_cad"] = add["hist_cad"].map(_decode_deceased_cell).map(
            lambda s: _HIST_CAD_MAP.get(str(s).strip().upper(), s) if pd.notna(s) else np.nan
        )
    for c in set(DECEASED_TO_DONORNET_COLMAP.values()) - {"age_in_months", "hist_cad"}:
        if c not in add.columns:
            continue
        if c in donor_df.columns and pd.api.types.is_numeric_dtype(donor_df[c]):
            add[c] = pd.to_numeric(add[c].map(_decode_deceased_cell), errors="coerce")
        else:
            add[c] = add[c].map(_decode_deceased_cell)

    add = add.reindex(columns=donor_df.columns)
    n_before = int(donor_df["DONOR_ID"].nunique())
    out = pd.concat([donor_df, add], ignore_index=True)
    print(
        f"[donors] Filled from deceased_donor_data: {int(add['DONOR_ID'].nunique()):,} donor IDs "
        f"(missing from DonorNet={len(missing_ids):,}; unique {n_before:,} -> {int(out['DONOR_ID'].nunique()):,})"
    )

    return out


def merge_donornet(df, file_path, time_name, df_time_name="initial_response_dt", forward_fill=True, fill_days=7):
    """Merge DonorNet table by DONOR_ID: time<=offer, latest day + richest row; optional N-day forward-fill of NaNs."""
    table_name = os.path.basename(file_path).split(".")[0]
    original_size = df.shape

    # Step 1) Read donor table; keep only selected vars + keys; normalize times; filter to offer donors.
    donor_df = pd.read_csv(file_path, low_memory=True, encoding="utf-8")
    keep = [c for c in donornet_TXP_variables if c in donor_df.columns] + ["DONOR_ID", time_name]
    donor_df = donor_df[keep]
    df[df_time_name] = pd.to_datetime(df[df_time_name]).dt.tz_localize(None)
    donor_df[time_name] = pd.to_datetime(donor_df[time_name]).dt.tz_localize(None)
    donor_df = donor_df[donor_df["DONOR_ID"].isin(df["DONOR_ID"])]

    # Step 2) donors.csv only: append static rows for offer IDs missing from DonorNet.
    if table_name.lower() == "donors":
        donor_df = fill_missing_donors_from_deceased(
            donor_df, df, time_col=time_name, offer_time_col=df_time_name
        )

    # Step 3) Rank donor rows: later day first; same day → more non-missing fields first.
    donor_df = donor_df.assign(
        non_missing_count=donor_df.notna().sum(axis=1),
        donor_day=donor_df[time_name].dt.floor("D"),
    ).sort_values(
        ["DONOR_ID", "donor_day", "non_missing_count", time_name],
        ascending=[True, False, False, False],
    )
    feat_cols = [c for c in donor_df.columns if c not in ("DONOR_ID", time_name, "non_missing_count", "donor_day")]

    # Step 4) Join each offer row to its donor history; keep only donor_time <= offer_time.
    df_work = df.reset_index().rename(columns={"index": "__row_id"})
    n = len(df_work)
    print(f"[{table_name}] merge start | rows={n:,}")

    merged = df_work[["__row_id", "DONOR_ID", df_time_name]].merge(donor_df, on="DONOR_ID", how="left")
    ok = merged[df_time_name].notna() & merged[time_name].notna() & (merged[time_name] <= merged[df_time_name])
    merged = merged.loc[ok].sort_values(
        ["__row_id", "donor_day", "non_missing_count", time_name],
        ascending=[True, False, False, False],
    )

    # Step 5) Pick one donor row per offer (latest/richest); optionally forward-fill NaNs from older rows within fill_days.
    if not forward_fill:
        picked = merged.drop_duplicates("__row_id")
    else:
        def _pick_and_fill(g):
            row = g.iloc[0].copy()  # primary: latest valid day + richest row that day
            hist = g[g["donor_day"] >= row["donor_day"] - pd.Timedelta(days=fill_days)]
            for c in feat_cols:
                if pd.isna(row[c]):
                    v = hist[c].dropna()
                    if not v.empty:
                        row[c] = v.iloc[0]  # nearest older non-null within window (hist already newest-first)
            return row

        picked = (
            merged.groupby("__row_id", sort=False, group_keys=False)
            .apply(_pick_and_fill)
            .reset_index(drop=True)
        )

    # Step 6) Suffix colliding feature names with table name; attach features back to offers.
    drop = {df_time_name, "non_missing_count", time_name, "DONOR_ID", "donor_day", "__row_id"}
    picked = picked.rename(
        columns={c: f"{c}_{table_name}" for c in picked.columns if c in df.columns and c not in (df_time_name, "DONOR_ID")}
    )
    add_cols = [c for c in picked.columns if c not in drop]
    out = df_work.merge(picked[["__row_id"] + add_cols], on="__row_id", how="left")

    matched = set(picked["__row_id"].dropna())
    unmatched = ~out["__row_id"].isin(matched)
    print(
        f"[{table_name}] merge end | matched_rows={len(matched):,}/{n:,} "
        f"({100.0 * len(matched) / max(1, n):.2f}%), unmatched_rows={int(unmatched.sum()):,}, "
        f"unmatched_unique_donor_ids={int(out.loc[unmatched, 'DONOR_ID'].dropna().nunique()):,}"
    )
    out = out.drop(columns=["__row_id"])
    print(f"{original_size} --> {out.shape}")
    return out


# Updated function: now includes variable grouping by category and inserts group headers
def create_baseline_table_grouped(train_df, test_df, full_df, y_data, data_types, variable_groups, lr_significant_vars=None):
    survived_df = full_df[y_data == 1]
    died_df = full_df[y_data == 0]

    index_tuples = []
    data_rows = []

    for group_name, group_vars in variable_groups.items():
        # Replace "Patient" with "Recipient" in group names for consistency
        display_group_name = group_name.replace("Patient ", "Recipient ")
        
        group_has_content = False
        temp_indices = []
        temp_rows = []

        for var in group_vars:
            if lr_significant_vars is not None and not any(sig.startswith(var.strip()) for sig in lr_significant_vars):
                    continue
            
            group_has_content = True

            if var in data_types['numerical']:
                # Mean and std
                train_mean = train_df[var].mean(skipna=True)
                train_std = train_df[var].std(skipna=True)
                test_mean = test_df[var].mean(skipna=True)
                test_std = test_df[var].std(skipna=True)
                survived_mean = survived_df[var].mean(skipna=True)
                survived_std = survived_df[var].std(skipna=True)
                died_mean = died_df[var].mean(skipna=True)
                died_std = died_df[var].std(skipna=True)

                try:
                    _, p_value_traintest = stats.ttest_ind(train_df[var].dropna(), test_df[var].dropna(), equal_var=False)
                except:
                    p_value_traintest = np.nan
                try:
                    _, p_value_outcome = stats.ttest_ind(survived_df[var].dropna(), died_df[var].dropna(), equal_var=False)
                except:
                    p_value_outcome = np.nan
                
                # # Median and IQR
                # train_median = train_df[var].median(skipna=True)
                # train_q1 = train_df[var].quantile(0.25)
                # train_q3 = train_df[var].quantile(0.75)
                # test_median = test_df[var].median(skipna=True)
                # test_q1 = test_df[var].quantile(0.25)
                # test_q3 = test_df[var].quantile(0.75)
                # survived_median = survived_df[var].median(skipna=True)
                # survived_q1 = survived_df[var].quantile(0.25)
                # survived_q3 = survived_df[var].quantile(0.75)
                # died_median = died_df[var].median(skipna=True)
                # died_q1 = died_df[var].quantile(0.25)
                # died_q3 = died_df[var].quantile(0.75)

                temp_indices.append(var)
                # temp_rows.append({
                #     f'Derivation Cohort (n={len(train_df)})': f"{train_mean:.1f} (± {train_std:.1f}); {train_median:.1f} [{train_q1:.1f}, {train_q3:.1f}]",
                #     f'Validation Cohort (n={len(test_df)})': f"{test_mean:.1f} (± {test_std:.1f}); {test_median:.1f} [{test_q1:.1f}, {test_q3:.1f}]",
                #     'P-value ': f"{p_value_traintest:.3f}" if (not np.isnan(p_value_traintest) and p_value_traintest >= 0.001) else '<0.001',
                #     f'Survived (n={len(survived_df)})': f"{survived_mean:.1f} (± {survived_std:.1f}); {survived_median:.1f} [{survived_q1:.1f}, {survived_q3:.1f}]",
                #     f'Died (n={len(died_df)})': f"{died_mean:.1f} (± {died_std:.1f}); {died_median:.1f} [{died_q1:.1f}, {died_q3:.1f}]",
                #     'P-value': f"{p_value_outcome:.3f}" if (not np.isnan(p_value_outcome) and p_value_outcome >= 0.001) else '<0.001'
                # })

                temp_rows.append({
                    f'Derivation Cohort (n={len(train_df)})': f"{train_mean:.1f} (± {train_std:.1f})",
                    f'Validation Cohort (n={len(test_df)})': f"{test_mean:.1f} (± {test_std:.1f})",
                    'P-value ': f"{p_value_traintest:.3f}" if (not np.isnan(p_value_traintest) and p_value_traintest >= 0.001) else '<0.001',
                    f'Survived (n={len(survived_df)})': f"{survived_mean:.1f} (± {survived_std:.1f})",
                    f'Died (n={len(died_df)})': f"{died_mean:.1f} (± {died_std:.1f})",
                    'P-value': f"{p_value_outcome:.3f}" if (not np.isnan(p_value_outcome) and p_value_outcome >= 0.001) else '<0.001'
                })

            elif var in data_types['categorical']:
                train_counts = train_df[var].value_counts(dropna=True)
                test_counts = test_df[var].value_counts(dropna=True)
                all_categories_traintest = sorted(set(train_counts.index).union(set(test_counts.index)))
                known_cats_traintest = [cat for cat in all_categories_traintest if cat not in {'U', 'Unknown', 'None'}]
                train_known_total = sum(train_counts.get(cat, 0) for cat in known_cats_traintest)
                test_known_total = sum(test_counts.get(cat, 0) for cat in known_cats_traintest)
                contingency_table_traintest = []
                for cat in known_cats_traintest:
                    contingency_table_traintest.append([train_counts.get(cat, 0), test_counts.get(cat, 0)])
                try:
                    _, p_value_traintest, _, _ = stats.chi2_contingency(np.array(contingency_table_traintest).T)
                except:
                    p_value_traintest = np.nan

                survived_counts = survived_df[var].value_counts(dropna=True)
                died_counts = died_df[var].value_counts(dropna=True)
                all_categories_outcome = sorted(set(survived_counts.index).union(set(died_counts.index)))
                known_cats_outcome = [cat for cat in all_categories_outcome if cat not in {'U', 'Unknown', 'None'}]
                survived_known_total = sum(survived_counts.get(cat, 0) for cat in known_cats_outcome)
                died_known_total = sum(died_counts.get(cat, 0) for cat in known_cats_outcome)
                contingency_table_outcome = []
                for cat in known_cats_outcome:
                    contingency_table_outcome.append([survived_counts.get(cat, 0), died_counts.get(cat, 0)])
                try:
                    _, p_value_outcome, _, _ = stats.chi2_contingency(np.array(contingency_table_outcome).T)
                except:
                    p_value_outcome = np.nan

                all_known_cats = sorted(list(set(known_cats_traintest) | set(known_cats_outcome)))

                if len(all_known_cats) == 2 and set(all_known_cats) == {'Yes', 'No'}:
                    yes_train = train_counts.get('Yes', 0)
                    yes_test = test_counts.get('Yes', 0)
                    yes_ratio_train = 100 * yes_train / train_known_total if train_known_total else 0
                    yes_ratio_test = 100 * yes_test / test_known_total if test_known_total else 0
                    yes_survived = survived_counts.get('Yes', 0)
                    yes_died = died_counts.get('Yes', 0)
                    yes_ratio_survived = 100 * yes_survived / survived_known_total if survived_known_total else 0
                    yes_ratio_died = 100 * yes_died / died_known_total if died_known_total else 0

                    temp_indices.append(var)
                    temp_rows.append({
                        f'Derivation Cohort (n={len(train_df)})': f"{yes_train}/{train_known_total} ({yes_ratio_train:.1f}%)",
                        f'Validation Cohort (n={len(test_df)})': f"{yes_test}/{test_known_total} ({yes_ratio_test:.1f}%)",
                        'P-value ': f"{p_value_traintest:.3f}" if (not np.isnan(p_value_traintest) and p_value_traintest >= 0.001) else '<0.001',
                        f'Survived (n={len(survived_df)})': f"{yes_survived}/{survived_known_total} ({yes_ratio_survived:.1f}%)",
                        f'Died (n={len(died_df)})': f"{yes_died}/{died_known_total} ({yes_ratio_died:.1f}%)",
                        'P-value': f"{p_value_outcome:.3f}" if (not np.isnan(p_value_outcome) and p_value_outcome >= 0.001) else '<0.001'
                    })
                else:
                    temp_indices.append(var)
                    temp_rows.append({
                        f'Derivation Cohort (n={len(train_df)})': "",
                        f'Validation Cohort (n={len(test_df)})': "",
                        'P-value ': f"{p_value_traintest:.3f}" if (not np.isnan(p_value_traintest) and p_value_traintest >= 0.001) else '<0.001',
                        f'Survived (n={len(survived_df)})': "",
                        f'Died (n={len(died_df)})': "",
                        'P-value': f"{p_value_outcome:.3f}" if (not np.isnan(p_value_outcome) and p_value_outcome >= 0.001) else '<0.001'
                    })

                    for cat in all_known_cats:
                        train_count = train_counts.get(cat, 0)
                        test_count = test_counts.get(cat, 0)
                        train_ratio = 100 * train_count / train_known_total if train_known_total else 0
                        test_ratio = 100 * test_count / test_known_total if test_known_total else 0
                        survived_count = survived_counts.get(cat, 0)
                        died_count = died_counts.get(cat, 0)
                        survived_ratio = 100 * survived_count / survived_known_total if survived_known_total else 0
                        died_ratio = 100 * died_count / died_known_total if died_known_total else 0

                        temp_indices.append(f"\\quad {cat}")
                        temp_rows.append({
                            f'Derivation Cohort (n={len(train_df)})': f"{train_count}/{train_known_total} ({train_ratio:.1f}%)",
                            f'Validation Cohort (n={len(test_df)})': f"{test_count}/{test_known_total} ({test_ratio:.1f}%)",
                            'P-value ': "",
                            f'Survived (n={len(survived_df)})': f"{survived_count}/{survived_known_total} ({survived_ratio:.1f}%)",
                            f'Died (n={len(died_df)})': f"{died_count}/{died_known_total} ({died_ratio:.1f}%)",
                            'P-value': ""
                        })

        if group_has_content:
            for characteristic in temp_indices:
                index_tuples.append((display_group_name, characteristic))
            data_rows.extend(temp_rows)

    if not data_rows:
        return pd.DataFrame()

    index = pd.MultiIndex.from_tuples(index_tuples, names=['Group', 'Characteristic'])
    return pd.DataFrame(data_rows, index=index)


def create_baseline_table(train_df, test_df, data_types, lr_significant_vars=None):
    baseline_rows = []

    for var in data_types['numerical']:
        if var and not any(sig.startswith(var.strip()) for sig in lr_significant_vars):
            continue
        train_mean = train_df[var].mean(skipna=True)
        train_std = train_df[var].std(skipna=True)
        test_mean = test_df[var].mean(skipna=True)
        test_std = test_df[var].std(skipna=True)

        try:
            _, p_value = stats.ttest_ind(train_df[var].dropna(), test_df[var].dropna(), equal_var=False)
        except:
            p_value = np.nan

        baseline_rows.append({
            'Characteristic': var,
            f'Derivation Cohort (n={len(train_df)})': f"{train_mean:.1f} (± {train_std:.1f})",
            f'Validation Cohort (n={len(test_df)})': f"{test_mean:.1f} (± {test_std:.1f})",
            'P-value': f"{p_value:.3f}" if (not np.isnan(p_value) and p_value >= 0.001) else '<0.001'
        })

    for var in data_types['categorical']:
        if var and not any(sig.startswith(var.strip()) for sig in lr_significant_vars):
            continue
        train_counts = train_df[var].value_counts(dropna=True)
        test_counts = test_df[var].value_counts(dropna=True)

        all_categories = sorted(set(train_counts.index).union(set(test_counts.index)))
        known_cats = [cat for cat in all_categories if cat not in {'U', 'Unknown', 'None'}]

        train_known_total = sum(train_counts.get(cat, 0) for cat in known_cats)
        test_known_total = sum(test_counts.get(cat, 0) for cat in known_cats)

        contingency_table = []
        for cat in known_cats:
            contingency_table.append([
                train_counts.get(cat, 0),
                test_counts.get(cat, 0)
            ])
        contingency_table = np.array(contingency_table).T

        try:
            _, p_value, _, _ = stats.chi2_contingency(contingency_table)
        except:
            p_value = np.nan

        if len(known_cats) == 2 and set(known_cats) == {'Yes', 'No'}:
            # Binary variable, only show "Yes" category under the variable name
            yes_train = train_counts.get('Yes', 0)
            yes_test = test_counts.get('Yes', 0)
            yes_ratio_train = 100 * yes_train / train_known_total if train_known_total else 0
            yes_ratio_test = 100 * yes_test / test_known_total if test_known_total else 0

            baseline_rows.append({
                'Characteristic': var,
                f'Derivation Cohort (n={len(train_df)})': f"{yes_train}/{train_known_total} ({yes_ratio_train:.1f}%)",
                f'Validation Cohort (n={len(test_df)})': f"{yes_test}/{test_known_total} ({yes_ratio_test:.1f}%)",
                'P-value': f"{p_value:.3f}" if (not np.isnan(p_value) and p_value >= 0.001) else '<0.001'
            })
        else:
            # Add main variable name
            baseline_rows.append({
                'Characteristic': var,
                f'Derivation Cohort (n={len(train_df)})': "",
                f'Validation Cohort (n={len(test_df)})': "",
                'P-value': f"{p_value:.3f}" if (not np.isnan(p_value) and p_value >= 0.001) else '<0.001'
            })

            # Add each category under this variable
            for cat in known_cats:
                train_count = train_counts.get(cat, 0)
                test_count = test_counts.get(cat, 0)
                train_ratio = 100 * train_count / train_known_total if train_known_total else 0
                test_ratio = 100 * test_count / test_known_total if test_known_total else 0

                baseline_rows.append({
                    'Characteristic': f"\\quad {cat}",
                    f'Derivation Cohort (n={len(train_df)})': f"{train_count}/{train_known_total} ({train_ratio:.1f}%)",
                    f'Validation Cohort (n={len(test_df)})': f"{test_count}/{test_known_total} ({test_ratio:.1f}%)",
                    'P-value': ""
                })

    return pd.DataFrame(baseline_rows)


def create_baseline_table_old(train_df, test_df, data_types, lr_significant_vars=None):
    baseline_rows = []

    for var in data_types['numerical']:
        if var and not any(sig.startswith(var.strip()) for sig in lr_significant_vars):
            continue
        # Numerical variable: mean ± SD and t-test
        train_mean = train_df[var].mean(skipna=True)
        train_std = train_df[var].std(skipna=True)
        test_mean = test_df[var].mean(skipna=True)
        test_std = test_df[var].std(skipna=True)

        try:
            _, p_value = stats.ttest_ind(train_df[var].dropna(), test_df[var].dropna(), equal_var=False)
        except:
            p_value = np.nan

        baseline_rows.append({
            'Characteristic': var,
            'Derivation Cohort (n=78523)': f"{train_mean:.1f} (\u00B1 {train_std:.1f})",
            'Validation Cohort (n=8725)': f"{test_mean:.1f} (\u00B1 {test_std:.1f})",
            'P-value': f"{p_value:.3f}" if (not np.isnan(p_value) and p_value >= 0.001) else '<0.001'
        })

    for var in data_types['categorical']:
        if var and not any(sig.startswith(var.strip()) for sig in lr_significant_vars):
            continue
        # Categorical variable: get value counts
        train_counts = train_df[var].value_counts(dropna=True)
        test_counts = test_df[var].value_counts(dropna=True)

        # Union of all categories appearing in train or test
        all_categories = sorted(set(train_counts.index).union(set(test_counts.index)))

        # Filter out unknowns
        known_cats = [cat for cat in all_categories if cat not in {'U', 'Unknown', 'None'}]

        # Rebuild counts and denominator only from known values
        train_known_total = sum(train_counts.get(cat, 0) for cat in known_cats)
        test_known_total = sum(test_counts.get(cat, 0) for cat in known_cats)

        # Chi-square on known categories only
        contingency_table = []
        for cat in known_cats:
            contingency_table.append([
                train_counts.get(cat, 0),
                test_counts.get(cat, 0)
            ])
        contingency_table = np.array(contingency_table).T

        try:
            _, p_value, _, _ = stats.chi2_contingency(contingency_table)
        except:
            p_value = np.nan

        # Add main variable name
        baseline_rows.append({
            'Characteristic': var,
            'Derivation Cohort (n=78523)': "",
            'Validation Cohort (n=8725)': "",
            'P-value': f"{p_value:.3f}" if (not np.isnan(p_value) and p_value >= 0.001) else '<0.001'
        })

        # Add each category under this variable
        for cat in all_categories:
            train_count = train_counts.get(cat, 0)
            test_count = test_counts.get(cat, 0)
            train_total = train_df.shape[0]
            test_total = test_df.shape[0]
            train_ratio = 100 * train_count / train_known_total
            test_ratio = 100 * test_count / test_known_total

            if cat == 'U':
                continue
                # cat = 'Unknown'

            baseline_rows.append({
                'Characteristic': f"\\quad {cat}",
                'Derivation Cohort (n=78523)': f"{train_count}/{train_known_total} ({train_ratio:.1f}%)",
                'Validation Cohort (n=8725)': f"{test_count}/{test_known_total} ({test_ratio:.1f}%)",
                'P-value': ""
            })

    baseline_table = pd.DataFrame(baseline_rows)
    return baseline_table


# Step 2: Replace the first '_' with ': ' for presenting summary table
def replace_first_underscore(s):
    if s in ID_keywords:
        return s

    if '_' in s:
        return s.replace('_', ': ', 1)
    else:
        return s


# Define a formatting function for presenting summary table
def format_value(x):
    if isinstance(x, (int, float)):
        return '<0.001' if x < 0.001 else f"{x:.3f}"
    return x


def format_ratio(x):
    """OR/HR display: extra decimals near 1.0 (e.g. distance per mile)."""
    x = float(x)
    if 0.95 <= x <= 1.05:
        return f"{x:.4f}".rstrip('0').rstrip('.')
    return f"{x:.3f}"


def format_ratio_ci(or_val, lo, hi):
    return f"{format_ratio(or_val)} ({format_ratio(lo)}-{format_ratio(hi)})"


def _ratio_ci_column_name(ratio_label='HR'):
    return f'{ratio_label} (95\\% CI)'


def _effect_ci_column(df):
    for c in df.columns:
        if c != 'Variable' and '95' in c and 'CI' in c:
            return c
    return _ratio_ci_column_name('HR')


def generate_model_summary(summary_df, p_threshold=0.05, ratio_label='HR'):
    ci_col = _ratio_ci_column_name(ratio_label)
    summary_df = summary_df[
        ~summary_df['Variable'].str.contains('NONE|Unknown|Others|Other', case=False)
    ].copy()

    def _finalize(df):
        return pd.DataFrame({
            'Variable': df['Variable'].values,
            ci_col: df.apply(
                lambda row: format_ratio_ci(row['HR'], row['CI Lower 95%'], row['CI Upper 95%']),
                axis=1,
            ),
            'P-value': df['P-value'].apply(format_value),
        })

    significant_coefs = _finalize(summary_df[summary_df['P-value'] <= p_threshold].copy())
    summary_df = _finalize(summary_df)
    return summary_df, significant_coefs


def model_summary(result, p_threshold=0.05, scale=None, ratio_label='HR'):
    """
    Create a compact coefficient summary table for paper tables.

    Supports:
      - statsmodels-style results: has `.params`, `.conf_int()`, `.pvalues`
      - lifelines CoxTimeVaryingFitter (and similar): has `.summary` DataFrame with
        columns like `exp(coef)`, `exp(coef) lower 95%`, `exp(coef) upper 95%`, `p`.

    Returns:
      - summary_df: columns ['Variable', '{ratio_label} (95% CI)', 'P-value']
      - significant_coefs: same columns but filtered by p_threshold

    ratio_label: 'HR' for Cox/survival, 'OR' for logistic regression.
    """
    # ----------------------------
    # 1) lifelines-style
    # ----------------------------
    if hasattr(result, "summary"):
        s = getattr(result, "summary", None)
        if isinstance(s, pd.DataFrame):
            cols = set(s.columns)
            # lifelines naming
            hr_col = "exp(coef)" if "exp(coef)" in cols else None
            lower_col = "exp(coef) lower 95%" if "exp(coef) lower 95%" in cols else None
            upper_col = "exp(coef) upper 95%" if "exp(coef) upper 95%" in cols else None
            p_col = "p" if "p" in cols else None

            # fallback heuristics for column naming drift
            if hr_col is None:
                for c in cols:
                    if c.strip().lower() == "exp(coef)":
                        hr_col = c
                        break
            if lower_col is None:
                for c in cols:
                    lc = c.strip().lower()
                    if "lower" in lc and "95" in lc:
                        lower_col = c
                        break
            if upper_col is None:
                for c in cols:
                    uc = c.strip().lower()
                    if "upper" in uc and "95" in uc:
                        upper_col = c
                        break
            if p_col is None:
                for c in cols:
                    pc = c.strip().lower()
                    if pc in {"p", "p-value", "pvalue"}:
                        p_col = c
                        break

            if hr_col is not None and lower_col is not None and upper_col is not None and p_col is not None:
                summary_df = pd.DataFrame(
                    {
                        "HR": s[hr_col],
                        "CI Lower 95%": s[lower_col],
                        "CI Upper 95%": s[upper_col],
                        "P-value": s[p_col],
                    }
                ).dropna()

                # Preserve covariate names (lifelines typically stores them in the index).
                summary_df["Variable"] = summary_df.index.astype(str)
                summary_df = summary_df.reset_index(drop=True)
                summary_df = summary_df.sort_values(by="P-value", ascending=True).reset_index(drop=True)

                summary_df, significant_coefs = generate_model_summary(
                    summary_df, p_threshold, ratio_label=ratio_label,
                )
                return summary_df, significant_coefs

    # ----------------------------
    # 2) statsmodels-style
    # ----------------------------
    coef = result.params
    conf = result.conf_int()
    pval = result.pvalues

    # If model was fit on standardized covariates, convert coef/CI back to original x-units:
    # z = (x - mu)/sigma  =>  beta_x = beta_z / sigma
    if scale is not None:
        scale_s = pd.Series(scale)
        for name in coef.index:
            if name in scale_s.index:
                coef.loc[name] = coef.loc[name] / scale_s.loc[name]
                conf.loc[name, 0] = conf.loc[name, 0] / scale_s.loc[name]
                conf.loc[name, 1] = conf.loc[name, 1] / scale_s.loc[name]

    # Calculate HR and CI
    hr = np.exp(coef)
    hr_ci_lower = np.exp(conf[0])
    hr_ci_upper = np.exp(conf[1])

    summary_df = (
        pd.DataFrame(
            {
                "HR": hr,
                "CI Lower 95%": hr_ci_lower,
                "CI Upper 95%": hr_ci_upper,
                "P-value": pval,
            }
        )
        .dropna()
        .sort_values(by="P-value", ascending=True)
        .reset_index()
    )
    summary_df.rename(columns={"index": "Variable"}, inplace=True)

    summary_df, significant_coefs = generate_model_summary(
        summary_df, p_threshold, ratio_label=ratio_label,
    )
    return summary_df, significant_coefs


# Function to convert seconds to HH:MM:SS.sss format
def convert_to_time_format(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{milliseconds:03}"


def create_summary_table_grouped(significant_coefs, variable_groups):
    summary_rows = []
    ci_col = _effect_ci_column(significant_coefs)
    has_fdr = "FDR q" in significant_coefs.columns

    # Get a copy of significant variables to keep track of which have been added
    remaining_significant_vars = significant_coefs.copy()

    def _blank_group_header(name):
        row = {"Variable": r"\textbf{" + name + "}", ci_col: "", "P-value": ""}
        if has_fdr:
            row["FDR q"] = ""
        return row

    def _row_from(row):
        out = {
            "Variable": row["Variable"],
            ci_col: row[ci_col],
            "P-value": row["P-value"],
        }
        if has_fdr:
            out["FDR q"] = row["FDR q"]
        return out

    for group_name, group_vars in variable_groups.items():
        group_rows = []

        for var_prefix in group_vars:
            matched_vars_idx = remaining_significant_vars['Variable'].str.startswith(var_prefix)
            matched_vars = remaining_significant_vars[matched_vars_idx]

            if not matched_vars.empty:
                for index, row in matched_vars.iterrows():
                    group_rows.append(_row_from(row))
                remaining_significant_vars = remaining_significant_vars.drop(matched_vars.index)

        if group_rows:
            summary_rows.append(_blank_group_header(group_name))
            group_rows_df = pd.DataFrame(group_rows)
            group_rows_df = group_rows_df.sort_values(by='Variable')
            summary_rows.extend(group_rows_df.to_dict('records'))

    if not remaining_significant_vars.empty:
        summary_rows.append(_blank_group_header("Other Variables"))
        remaining_significant_vars = remaining_significant_vars.sort_values(by='Variable')
        summary_rows.extend([_row_from(row) for _, row in remaining_significant_vars.iterrows()])

    return pd.DataFrame(summary_rows)


def save_model(model, feature_names, scaler=None, model_name='model', model_dir='../models', calibrator=None):
    """
    Save any trained model with feature information, scaler, and optional calibrator.
    Works for: sklearn models, XGBoost, CoxPH, RSF, etc.
    
    Args:
        model: Trained model object
        feature_names: List of feature names in exact training order
        scaler: StandardScaler or None
        model_name: Name for saved files (e.g., 'cox_wl', 'xgb_txp')
        model_dir: Directory to save models
        calibrator: Calibration model (IsotonicRegression, LogisticRegression for Platt scaling, or None)
    
    Returns:
        Path to saved model file
    """
    os.makedirs(model_dir, exist_ok=True)
    
    package = {
        'model': model,
        'feature_names': feature_names,
        'scaler': scaler,
        'calibrator': calibrator,
        'n_features': len(feature_names)
    }
    
    path = os.path.join(model_dir, f'{model_name}.pkl')
    with open(path, 'wb') as f:
        pickle.dump(package, f)
    
    calibrator_info = f" (with calibrator)" if calibrator is not None else ""
    print(f"Model saved: {path}{calibrator_info}")
    return path


def load_model(model_name, model_dir='../models'):
    """
    Load a saved model with feature information, scaler, and optional calibrator.
    
    Args:
        model_name: Name of saved model (e.g., 'cox_wl', 'xgb_txp')
        model_dir: Directory where models are saved
    
    Returns:
        model, feature_names, scaler, calibrator
        (calibrator will be None if not saved)
    """
    path = os.path.join(model_dir, f'{model_name}.pkl')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    
    with open(path, 'rb') as f:
        package = pickle.load(f)
    
    # Backward compatibility: if calibrator not in package, return None
    calibrator = package.get('calibrator', None)
    calibrator_info = f" (with calibrator)" if calibrator is not None else ""
    print(f"Loaded model: {path} ({package['n_features']} features){calibrator_info}")
    return package['model'], package['feature_names'], package['scaler'], calibrator


def prepare_features(df, feature_names, scaler=None):
    """
    Prepare dataframe for prediction: select features in correct order and scale.
    
    Args:
        df: DataFrame with patient data
        feature_names: List of feature names in exact order expected by model
        scaler: StandardScaler or None
    
    Returns:
        Prepared feature matrix (DataFrame)
    """
    missing = set(feature_names) - set(df.columns)
    if missing:
        raise ValueError(f"Missing features: {missing}")
    
    X = df[feature_names].copy()
    
    if scaler:
        X = pd.DataFrame(scaler.transform(X), columns=feature_names, index=X.index)
    
    return X


def test_proportional_hazards_assumption(cph, data, id_col='WL_ID_CODE',
                                         start_col='start', stop_col='stop',
                                         event_col='event_binary',
                                         output_dir='../images/WL',
                                         penalizer=0.003):
    """
    Test Proportional Hazards (PH) assumption for TIME-VARYING Cox models.

    For time-varying Cox models, PH assumption means:
    - The COEFFICIENT β (effect size) is constant over time
    - NOT that covariate values are constant (they can vary)

    Tests included:
    1. Time*covariate interaction test: Add interaction terms and test significance
    2. Stratified time-period analysis: Fit models on different time periods, compare coefficients
    3. Schoenfeld residuals: Test if residuals correlate with time (if computable)

    Parameters:
    -----------
    cph : CoxTimeVaryingFitter
        Fitted Cox model (baseline model without interactions)
    data : pd.DataFrame
        Data used for testing
    id_col, start_col, stop_col, event_col : str
        Column names for patient ID, start time, stop time, and event indicator
    output_dir : str
        Directory to save plots and results
    penalizer : float
        Penalizer to use when refitting models with interactions

    Returns:
    --------
    dict : Dictionary containing test results, p-values, and plots
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs('../results/WL', exist_ok=True)

    print("\n" + "=" * 80)
    print("TESTING PROPORTIONAL HAZARDS ASSUMPTION (Time-Varying Cox Model)")
    print("=" * 80)
    print("\nKey Distinction:")
    print("  ✓ Time-varying COVARIATES (X(t)) are ALLOWED")
    print("  ✗ Time-varying COEFFICIENTS (β(t)) VIOLATE PH assumption")
    print("\nPH Assumption: β(t) = β (constant effect over time)")
    print("=" * 80)

    results = {}

    # Get feature names (exclude ID, time, and event columns)
    exclude_cols = [id_col, start_col, stop_col, event_col]
    feature_names = [col for col in data.columns if col not in exclude_cols]

    # Get top covariates by absolute coefficient for testing
    coef_abs = cph.summary['coef'].abs().sort_values(ascending=False)
    top_covariates = coef_abs.head(10).index.tolist()

    # ========================================================================
    # Test 1: Time*Covariate Interaction Test
    # ========================================================================
    print("\n1. TIME*COVARIATE INTERACTION TEST")
    print("-" * 80)
    print("Null hypothesis: β(t) = β (coefficient constant over time)")
    print("Alternative: β(t) ≠ β (coefficient varies with time)")
    print("\nMethod: Add time*covariate interaction terms and test if they're significant")
    print("If interactions are significant → PH assumption violated")

    interaction_results = []

    try:
        # Test top 5 covariates (to avoid too many model refits)
        test_covariates = top_covariates[:5]

        for covar in test_covariates:
            if covar not in feature_names:
                continue

            print(f"\n   Testing covariate: {covar[:50]}")

            try:
                # Create data with time*covariate interaction
                data_with_interaction = data.copy()
                # Use stop time as the time variable for interaction
                data_with_interaction[f'{covar}_x_time'] = data_with_interaction[stop_col] * data_with_interaction[
                    covar]

                # Fit model WITH interaction term
                cph_with_interaction = CoxTimeVaryingFitter(penalizer=penalizer, l1_ratio=0)
                cph_with_interaction.fit(
                    data_with_interaction,
                    stop_col=stop_col,
                    event_col=event_col,
                    start_col=start_col,
                    id_col=id_col,
                    show_progress=False
                )

                # Get coefficient and p-value for interaction term
                interaction_name = f'{covar}_x_time'
                if interaction_name in cph_with_interaction.summary.index:
                    interaction_coef = cph_with_interaction.summary.loc[interaction_name, 'coef']
                    interaction_p = cph_with_interaction.summary.loc[interaction_name, 'p']
                    interaction_hr = cph_with_interaction.summary.loc[interaction_name, 'exp(coef)']

                    # Get original coefficient for comparison
                    original_coef = cph.summary.loc[covar, 'coef'] if covar in cph.summary.index else np.nan

                    interaction_results.append({
                        'covariate': covar,
                        'interaction_coef': interaction_coef,
                        'interaction_p': interaction_p,
                        'interaction_hr': interaction_hr,
                        'original_coef': original_coef,
                        'ph_violated': interaction_p < 0.05
                    })

                    status = "VIOLATED" if interaction_p < 0.05 else "OK"
                    print(f"      Interaction coefficient: {interaction_coef:.4f}")
                    print(f"      P-value: {interaction_p:.4f} → PH assumption {status}")
                else:
                    print(f"      Warning: Interaction term not found in model summary")

            except Exception as e:
                print(f"      Error testing {covar}: {e}")
                import traceback
                traceback.print_exc()
                continue

        if interaction_results:
            interaction_df = pd.DataFrame(interaction_results)
            interaction_df = interaction_df.sort_values('interaction_p')

            print("\n   Summary of Interaction Tests:")
            print(interaction_df[['covariate', 'interaction_coef', 'interaction_p', 'ph_violated']].to_string(
                index=False))

            # Save results
            interaction_df.to_csv(f'{output_dir}/PH_Time_Interaction_Tests.csv', index=False)
            print(f"\n   Results saved to {output_dir}/PH_Time_Interaction_Tests.csv")

            results['interaction_tests'] = interaction_df

            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = ['red' if p < 0.05 else 'green' for p in interaction_df['interaction_p']]
            ax.barh(range(len(interaction_df)), -np.log10(interaction_df['interaction_p']), color=colors, alpha=0.7)
            ax.axvline(x=-np.log10(0.05), color='black', linestyle='--', linewidth=2, label='p=0.05 threshold')
            ax.set_yticks(range(len(interaction_df)))
            ax.set_yticklabels([c[:40] for c in interaction_df['covariate']], fontsize=9)
            ax.set_xlabel('-log10(p-value)')
            ax.set_ylabel('Covariate')
            ax.set_title('Time*Covariate Interaction Tests\n(Red = PH violated, Green = PH OK)')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/PH_Interaction_Tests_Plot.png', dpi=300, bbox_inches='tight')
            plt.close()
            print(f"   Plot saved to {output_dir}/PH_Interaction_Tests_Plot.png")

    except Exception as e:
        print(f"   Error in interaction test: {e}")
        import traceback
        traceback.print_exc()

    # ========================================================================
    # Test 2: Stratified Time-Period Analysis
    # ========================================================================
    print("\n2. STRATIFIED TIME-PERIOD ANALYSIS")
    print("-" * 80)
    print("Method: Fit separate models on different time periods")
    print("Compare coefficients across time periods")
    print("If coefficients differ significantly → PH assumption violated")
    print("\nNote: Using event-time percentiles to ensure balanced event counts")

    try:
        # Get event times to define periods based on event distribution
        event_data = data[data[event_col] == 1].copy()

        if len(event_data) < 100:
            print("   Insufficient events for time-period analysis")
        else:
            # Use event-time percentiles to define periods with balanced events
            event_times = sorted(event_data[stop_col].unique())
            p33 = np.percentile(event_times, 33)
            p67 = np.percentile(event_times, 67)
            max_time = data[stop_col].max()

            # Define periods: Early (0 to 33rd percentile), Middle (33rd to 67th), Late (67th+)
            time_periods = [
                (0, p33, "Early"),
                (p33, p67, "Middle"),
                (p67, max_time, "Late")
            ]

            period_coefficients = []

            for t_start, t_end, period_name in time_periods:
                print(f"\n   Fitting model for {period_name} period ({t_start:.0f} - {t_end:.0f} days)")

                # Filter data to this time period
                # Keep all intervals that overlap with this period
                period_data = data[
                    ((data[start_col] < t_end) & (data[stop_col] > t_start))
                ].copy()

                if len(period_data) < 100:  # Need sufficient data
                    print(f"      Insufficient data ({len(period_data)} rows), skipping")
                    continue

                n_events = period_data[event_col].sum()
                if n_events < 50:  # Increased threshold for stability
                    print(f"      Insufficient events ({n_events} < 50), skipping")
                    continue

                print(f"      Data: {len(period_data)} intervals, {n_events} events")

                try:
                    # Clean data: remove columns with zero/low variance
                    exclude_cols = [id_col, start_col, stop_col, event_col]
                    feature_cols = [c for c in period_data.columns if c not in exclude_cols]

                    # Check for zero/low variance columns
                    low_var_cols = []
                    for col in feature_cols:
                        if period_data[col].nunique() <= 1:
                            low_var_cols.append(col)
                        elif period_data[col].std() < 1e-6:
                            low_var_cols.append(col)

                    if low_var_cols:
                        period_data_clean = period_data.drop(columns=low_var_cols)
                        print(f"      Dropped {len(low_var_cols)} low-variance columns")
                    else:
                        period_data_clean = period_data.copy()

                    # Replace infs and NaNs
                    period_data_clean = period_data_clean.replace([np.inf, -np.inf], np.nan)
                    period_data_clean = period_data_clean.dropna(subset=feature_cols)

                    if len(period_data_clean) < 100 or period_data_clean[event_col].sum() < 50:
                        print(f"      Insufficient data after cleaning, skipping")
                        continue

                    # Fit model on this time period
                    cph_period = CoxTimeVaryingFitter(penalizer=penalizer, l1_ratio=0)
                    cph_period.fit(
                        period_data_clean,
                        stop_col=stop_col,
                        event_col=event_col,
                        start_col=start_col,
                        id_col=id_col,
                        show_progress=False
                    )

                    # Extract coefficients for top covariates
                    for covar in top_covariates[:10]:
                        if covar in cph_period.summary.index:
                            coef_val = cph_period.summary.loc[covar, 'coef']
                            period_coefficients.append({
                                'covariate': covar,
                                'period': period_name,
                                'coefficient': coef_val,
                                'time_start': t_start,
                                'time_end': t_end
                            })

                except Exception as e:
                    print(f"      Error fitting model for {period_name} period: {e}")
                    # Print more details for debugging
                    if "convergence" in str(e).lower() or "nan" in str(e).lower():
                        print(f"      (Likely due to insufficient events or low-variance covariates in this period)")
                    continue

        # If we couldn't fit multiple periods, try simpler "early vs. rest" comparison
        if not period_coefficients and len(event_data) >= 100:
            print("\n   Attempting simpler 'Early vs. Rest' comparison...")

            # Use median event time as split
            median_event_time = np.median(event_times)

            for period_name, use_early in [("Early", True), ("Rest", False)]:
                if use_early:
                    period_data = data[data[stop_col] <= median_event_time].copy()
                else:
                    period_data = data[data[stop_col] > median_event_time].copy()

                if len(period_data) < 100:
                    continue

                n_events = period_data[event_col].sum()
                if n_events < 50:
                    continue

                print(f"   Fitting model for {period_name} period ({n_events} events)")

                try:
                    # Clean data
                    exclude_cols = [id_col, start_col, stop_col, event_col]
                    feature_cols = [c for c in period_data.columns if c not in exclude_cols]

                    low_var_cols = [col for col in feature_cols
                                    if period_data[col].nunique() <= 1 or period_data[col].std() < 1e-6]
                    if low_var_cols:
                        period_data = period_data.drop(columns=low_var_cols)

                    period_data = period_data.replace([np.inf, -np.inf], np.nan).dropna(subset=feature_cols)

                    if len(period_data) < 100 or period_data[event_col].sum() < 50:
                        continue

                    cph_period = CoxTimeVaryingFitter(penalizer=penalizer, l1_ratio=0)
                    cph_period.fit(
                        period_data,
                        stop_col=stop_col,
                        event_col=event_col,
                        start_col=start_col,
                        id_col=id_col,
                        show_progress=False
                    )

                    for covar in top_covariates[:10]:
                        if covar in cph_period.summary.index:
                            period_coefficients.append({
                                'covariate': covar,
                                'period': period_name,
                                'coefficient': cph_period.summary.loc[covar, 'coef'],
                                'time_start': 0 if period_name == "Early" else median_event_time,
                                'time_end': median_event_time if period_name == "Early" else max_time
                            })
                except Exception as e:
                    print(f"      Error fitting {period_name} period: {e}")
                    continue

        if period_coefficients:
            period_df = pd.DataFrame(period_coefficients)

            # Pivot to compare coefficients across periods
            coef_pivot = period_df.pivot(index='covariate', columns='period', values='coefficient')

            print("\n   Coefficient Comparison Across Time Periods:")
            print(coef_pivot.to_string())

            # Save results
            period_df.to_csv(f'{output_dir}/PH_Time_Period_Analysis.csv', index=False)
            coef_pivot.to_csv(f'{output_dir}/PH_Time_Period_Coefficients.csv')
            print(f"\n   Results saved to {output_dir}/PH_Time_Period_*.csv")

            results['time_period_analysis'] = period_df
            results['time_period_coefficients'] = coef_pivot

            # Create visualization
            if len(coef_pivot.columns) > 1:
                fig, axes = plt.subplots(2, 5, figsize=(20, 8))
                axes = axes.flatten()

                for idx, covar in enumerate(coef_pivot.index[:10]):
                    if idx >= len(axes):
                        break
                    ax = axes[idx]

                    coefs = coef_pivot.loc[covar].dropna()
                    if len(coefs) > 1:
                        ax.plot(range(len(coefs)), coefs.values, marker='o', linewidth=2, markersize=8)
                        ax.set_xticks(range(len(coefs)))
                        ax.set_xticklabels(coefs.index, rotation=45, ha='right')
                        ax.set_ylabel('Coefficient')
                        ax.set_title(f'{covar[:30]}', fontsize=9)
                        ax.grid(True, alpha=0.3)
                        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)

                        # Check if coefficient varies significantly
                        coef_std = coefs.std()
                        if coef_std > 0.1:  # Threshold for "significant variation"
                            ax.text(0.05, 0.95, 'PH Violated', transform=ax.transAxes,
                                    bbox=dict(boxstyle='round', facecolor='red', alpha=0.3),
                                    fontsize=8, verticalalignment='top')
                        else:
                            ax.text(0.05, 0.95, 'PH OK', transform=ax.transAxes,
                                    bbox=dict(boxstyle='round', facecolor='green', alpha=0.3),
                                    fontsize=8, verticalalignment='top')

                plt.suptitle('Coefficient Stability Across Time Periods\n(Constant coefficients → PH holds)',
                             fontsize=14)
                plt.tight_layout()
                plt.savefig(f'{output_dir}/PH_Time_Period_Analysis_Plot.png', dpi=300, bbox_inches='tight')
                plt.close()
                print(f"   Plot saved to {output_dir}/PH_Time_Period_Analysis_Plot.png")

    except Exception as e:
        print(f"   Error in time-period analysis: {e}")
        import traceback
        traceback.print_exc()

    # ========================================================================
    # Test 3: Schoenfeld Residuals (if computable)
    # ========================================================================
    print("\n3. SCHOENFELD RESIDUALS TEST")
    print("-" * 80)
    print("Method: Test if residuals correlate with time")
    print("If residuals correlate with time → PH assumption violated")

    try:
        # Note: lifelines doesn't directly provide Schoenfeld residuals for CoxTimeVarying
        # We'll use an approximation: compute residuals at event times

        event_data = data[data[event_col] == 1].copy()

        if len(event_data) > 100:  # Need sufficient events
            print(f"   Computing approximate Schoenfeld residuals for {len(event_data)} events")

            # Get unique event times
            event_times = sorted(event_data[stop_col].unique())

            # For each event time, compute approximate residual
            # This is a simplified approach - full implementation would require
            # computing expected vs observed covariate values at each event time

            residual_results = []

            # Sample a subset of event times for efficiency
            sample_times = event_times[::max(1, len(event_times) // 100)]  # Sample up to 100 times

            for t in sample_times[:50]:  # Limit to 50 for efficiency
                # Get data at risk at time t
                at_risk = data[(data[start_col] < t) & (data[stop_col] >= t)]

                if len(at_risk) < 10:
                    continue

                # Get event at time t
                events_at_t = event_data[event_data[stop_col] == t]

                if len(events_at_t) == 0:
                    continue

                # Compute expected covariate value (weighted by partial hazard)
                for covar in top_covariates[:5]:
                    if covar not in at_risk.columns:
                        continue

                    # Expected value = weighted mean by partial hazard
                    partial_hazards = cph.predict_partial_hazard(at_risk)
                    if isinstance(partial_hazards, pd.Series):
                        weights = partial_hazards / partial_hazards.sum()
                    else:
                        weights = pd.Series(partial_hazards.flatten(), index=at_risk.index)
                        weights = weights / weights.sum()

                    expected_val = (at_risk[covar] * weights).sum()

                    # Observed value = mean of events at time t
                    if len(events_at_t) > 0:
                        observed_val = events_at_t[covar].mean()

                        # Residual = observed - expected
                        residual = observed_val - expected_val

                        residual_results.append({
                            'time': t,
                            'covariate': covar,
                            'residual': residual,
                            'expected': expected_val,
                            'observed': observed_val
                        })

            if residual_results:
                residual_df = pd.DataFrame(residual_results)

                # Test correlation between residuals and time for each covariate
                correlation_results = []
                for covar in residual_df['covariate'].unique():
                    covar_residuals = residual_df[residual_df['covariate'] == covar]
                    if len(covar_residuals) > 5:
                        corr = covar_residuals['residual'].corr(covar_residuals['time'])
                        correlation_results.append({
                            'covariate': covar,
                            'residual_time_correlation': corr,
                            'n_points': len(covar_residuals)
                        })

                if correlation_results:
                    corr_df = pd.DataFrame(correlation_results)
                    corr_df = corr_df.sort_values('residual_time_correlation', key=abs, ascending=False)

                    print("\n   Residual-Time Correlations:")
                    print(corr_df.to_string(index=False))

                    corr_df.to_csv(f'{output_dir}/PH_Schoenfeld_Residuals.csv', index=False)
                    print(f"   Results saved to {output_dir}/PH_Schoenfeld_Residuals.csv")

                    results['schoenfeld_residuals'] = corr_df

                    # Plot residuals vs time
                    fig, axes = plt.subplots(1, min(5, len(corr_df)), figsize=(15, 4))
                    if len(corr_df) == 1:
                        axes = [axes]

                    for idx, (_, row) in enumerate(corr_df.head(5).iterrows()):
                        if idx >= len(axes):
                            break
                        ax = axes[idx]
                        covar = row['covariate']
                        covar_data = residual_df[residual_df['covariate'] == covar]

                        ax.scatter(covar_data['time'], covar_data['residual'], alpha=0.6)
                        ax.axhline(y=0, color='red', linestyle='--', linewidth=1)
                        ax.set_xlabel('Time (days)')
                        ax.set_ylabel('Residual')
                        ax.set_title(f'{covar[:30]}\n(corr={row["residual_time_correlation"]:.3f})', fontsize=9)
                        ax.grid(True, alpha=0.3)

                    plt.suptitle('Schoenfeld Residuals vs Time\n(No correlation → PH holds)', fontsize=12)
                    plt.tight_layout()
                    plt.savefig(f'{output_dir}/PH_Schoenfeld_Residuals_Plot.png', dpi=300, bbox_inches='tight')
                    plt.close()
                    print(f"   Plot saved to {output_dir}/PH_Schoenfeld_Residuals_Plot.png")
        else:
            print("   Insufficient events for Schoenfeld residuals test")

    except Exception as e:
        print(f"   Error in Schoenfeld residuals test: {e}")
        import traceback
        traceback.print_exc()

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("PH ASSUMPTION TEST SUMMARY (Time-Varying Cox Model)")
    print("=" * 80)

    # Count violations
    n_violations = 0
    if 'interaction_tests' in results:
        n_violations += results['interaction_tests']['ph_violated'].sum()

    print(f"\nNumber of covariates with PH violations (from interaction test): {n_violations}")

    # Note about time-period analysis
    if 'time_period_analysis' not in results:
        print("\nNote: Time-period analysis unavailable (insufficient events in later periods)")
        print("      This is common when most events occur early in follow-up")
        print("      Relying primarily on interaction test results")

    print("\nInterpretation Guidelines:")
    print("  ✓ Non-significant time*covariate interactions → PH holds")
    if 'time_period_analysis' in results:
        print("  ✓ Stable coefficients across time periods → PH holds")
    print("  ✓ Residuals uncorrelated with time → PH holds")
    print("  ✗ Significant interactions → PH violated (use time-dependent coefficients)")
    if 'time_period_analysis' in results:
        print("  ✗ Varying coefficients across periods → PH violated (consider stratification)")
    print("  ✗ Residuals correlated with time → PH violated")

    print("\nIf PH assumption is violated:")
    print("  - Add time*covariate interaction terms to the model")
    if 'time_period_analysis' in results:
        print("  - Use stratified Cox model (stratify by time periods)")
    print("  - Consider alternative models (Aalen additive, etc.)")

    print(f"\nAll results saved to: {output_dir}")
    print("=" * 80 + "\n")

    results['output_directory'] = output_dir
    results['n_violations'] = n_violations
    return results


def to_npy(x):
    import torch
    from preprocess.helpers import GPU
    return x.cpu().data.numpy() if torch.cuda.is_available() and GPU >= 0 else x.detach().numpy()


def best_threshold(y_true, y_pred):
    prec, rec, thr = precision_recall_curve(y_true, y_pred)
    f1 = 2 * prec * rec / (prec + rec)
    best_thr = thr[f1.argmax()]
    return best_thr


def format_metrics_line(model_name, model_metrics):
    """Compact one-line summary of the latest evaluate() values for a model."""
    def _last(key):
        vals = model_metrics.get(key, [])
        return float(vals[-1]) if vals else float('nan')

    return (
        f'{model_name:28s}  '
        f'AUC={_last("AUC"):.4f}  Brier={_last("Brier Score"):.4f}  '
        f'Acc={_last("Accuracy"):.4f}  F1={_last("F1 Score"):.4f}  '
        f'Prec={_last("Precision"):.4f}  BalAcc={_last("Balanced Accuracy"):.4f}'
    )


def print_metrics_summary(metrics):
    """Print one line per model that has at least one recorded metric."""
    for name in metrics:
        bucket = metrics[name]
        if not any(bucket.get(k) for k in bucket):
            continue
        print(format_metrics_line(name, bucket), flush=True)


def evaluate(model_name, task_name, benchmark_choice, metrics, y_true, y_pred,
             y_pred_raw=None, save=True, save_plots=True, optimize_threshold=False,
             hide_model_name_in_calibration_plots=False):
    n_bins = 10
    strategy = "uniform"
    y_true = np.asarray(y_true).astype(int).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()
    if y_true.size == 0:
        raise ValueError("evaluate: y_true is empty")

    if optimize_threshold:
        threshold = best_threshold(y_true, y_pred)
        print("threshold: {}".format(threshold))

    else:
        threshold = 0.5

    fpr, tpr, thresholds = roc_curve(y_true, y_pred)
    roc_auc = auc(fpr, tpr)
    auprc = average_precision_score(y_true, y_pred)
    y_pred_discrete = (y_pred >= threshold).astype(int)

    if save_plots:
        # Plot ROC curve
        plt.figure()
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='gray', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC curve of {} model with {} setting'.format(model_name, benchmark_choice))
        plt.legend(loc="lower right")
        plt.savefig('../images/{}/ROC Curve {} & {}.png'.format(task_name, model_name, benchmark_choice))
        plt.close()

        # Calibration Plot - Enhanced to show both raw and calibrated if available
        plt.figure(figsize=(9, 6))

        # Plot perfectly calibrated line
        plt.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfectly calibrated', alpha=0.7)

        # Plot raw model calibration if available
        if y_pred_raw is not None:
            prob_true_raw, prob_pred_raw = calibration_curve(y_true, y_pred_raw, n_bins=n_bins, strategy=strategy)
            raw_label = "Raw" if hide_model_name_in_calibration_plots else f'{model_name} (Raw)'
            plt.plot(prob_pred_raw, prob_true_raw, marker='o', linewidth=2,
                     label=raw_label, color='darkorange')
            # annotate bin counts above points (uniform binning to match calibration_curve default)
            edges = np.linspace(0.0, 1.0, n_bins + 1)
            counts_raw, _ = np.histogram(y_pred_raw, bins=edges)
            counts_raw_nonzero = counts_raw[counts_raw > 0]
            for x, yv, c in zip(prob_pred_raw, prob_true_raw, counts_raw_nonzero):
                plt.text(x, yv + 0.015, str(int(c)), color='darkorange', fontsize=8, ha='center', va='bottom')

        # Plot calibrated model
        prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=n_bins, strategy=strategy)
        cal_label = "Re-calibrated" if hide_model_name_in_calibration_plots else f'{model_name} (Re-calibrated)'
        plt.plot(prob_pred, prob_true, marker='s', linewidth=2,
                 label=cal_label, color='royalblue')
        # annotate bin counts above points (uniform binning to match calibration_curve default)
        edges = np.linspace(0.0, 1.0, n_bins + 1)
        counts_cal, _ = np.histogram(y_pred, bins=edges)
        counts_cal_nonzero = counts_cal[counts_cal > 0]
        for x, yv, c in zip(prob_pred, prob_true, counts_cal_nonzero):
            plt.text(x, yv + 0.015, str(int(c)), color='royalblue', fontsize=8, ha='center', va='bottom')

        plt.xlabel('Mean predicted probability')
        plt.ylabel('Fraction of positives')
        plt.title('Calibration Plot')
        plt.legend(loc="upper left")  # loc="lower right"
        plt.grid(True, alpha=0.3)
        plt.savefig(f'../images/{task_name}/Calibration_Plot_{model_name}_comparison.png', bbox_inches='tight', dpi=600)
        plt.close()

        # Also save individual plots for backward compatibility
        plt.figure()
        plt.plot([0, 1], [0, 1], linestyle='--', label='Perfectly calibrated')
        single_label = "Re-calibrated" if hide_model_name_in_calibration_plots else model_name
        plt.plot(prob_pred, prob_true, marker='o', linewidth=1, label=single_label)
        # annotate per-point sample counts on the single calibration plot as well
        for x, yv, c in zip(prob_pred, prob_true, counts_cal_nonzero):
            plt.text(x, yv + 0.015, str(int(c)), color='darkorange', fontsize=8, ha='center', va='bottom')
        plt.xlabel('Mean predicted probability')
        plt.ylabel('Fraction of positives')
        plt.title('Calibration Plot')
        plt.legend(loc="lower right")
        plt.savefig(f'../images/{task_name}/Calibration_Plot_{model_name}.png', bbox_inches='tight', dpi=600)
        plt.close()

    accuracy = accuracy_score(y_true, y_pred_discrete)
    precision = precision_score(y_true, y_pred_discrete, average='binary', zero_division=0)
    f1 = f1_score(y_true, y_pred_discrete, average='binary', zero_division=0)
    balanced_acc = balanced_accuracy_score(y_true, y_pred_discrete)
    brier_score = brier_score_loss(y_true, y_pred)

    # Confusion Matrix (force 2×2 so cm.ravel() is always TN, FP, FN, TP for classes 0/1)
    cm = confusion_matrix(y_true, y_pred_discrete, labels=[0, 1])
    if save_plots:
        disp = ConfusionMatrixDisplay(confusion_matrix=cm)
        disp.plot(cmap=plt.cm.Blues)
        plt.title(f'Confusion Matrix: {model_name} ({benchmark_choice})')
        plt.savefig(f'../images/{task_name}/Confusion_Matrix_{model_name}_{benchmark_choice}.png', bbox_inches='tight')
        plt.close()

    # Error Type Breakdown
    tn, fp, fn, tp = cm.ravel()
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0  # Sensitivity / Recall
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0  # Specificity
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    if save:
        metrics[model_name]['Accuracy'].append(accuracy)
        metrics[model_name]['Precision'].append(precision)
        metrics[model_name]['True Positives (TP)'].append(tpr)
        metrics[model_name]['False Positive (FP)'].append(fpr)
        metrics[model_name]['False Negative (FN)'].append(fnr)
        metrics[model_name]['True Negative (TN)'].append(tnr)
        metrics[model_name]['F1 Score'].append(f1)
        metrics[model_name]['Balanced Accuracy'].append(balanced_acc)
        metrics[model_name]['AUC'].append(roc_auc)
        metrics[model_name]['Brier Score'].append(brier_score)
        # interval-level AUPRC can be more informative under severe imbalance
        if 'AUPRC' in metrics[model_name]:
            metrics[model_name]['AUPRC'].append(auprc)
        print(format_metrics_line(model_name, metrics[model_name]), flush=True)
    else:
        print(accuracy, precision, tpr, fpr, fnr, tnr, f1, balanced_acc, roc_auc, brier_score,)

    return metrics


def get_WL_event_type(patient_row):
    """Determine event type for a patient based on WLType and PType."""
    # 0=censored, 1=transplant, 2=death, 3=removal
    if patient_row['WLType'] == 'txp':
        return 1
    elif patient_row['PType'] == 'dead':
        return 2
    elif patient_row['PType'] == 'removal':
        return 3
    else:
        return 0  # censored, alive
