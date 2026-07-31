from baselines import *
import torch
import random


TIME_NOW = pd.Timestamp('2024-01-01 00:00:00')

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', None)  # This will allow displaying an unlimited number of columns
# CIG_GRT_10_OLD: U, CMV_STATUS: P, ABO: B, ABO_DON: O, MULTIORG: NAN FOR N,
analyze_full_data = True
eval_latest_era_cohort = True  # only used when analyze_full_data=True
latest_era_year_col = "Patient year of TXP: 2019-2023"
txp_era_year_vars = [
    "Patient year of TXP: 1994-1998",
    "Patient year of TXP: 1999-2003",
    "Patient year of TXP: 2004-2008",
    "Patient year of TXP: 2009-2013",
    "Patient year of TXP: 2014-2018",
    "Patient year of TXP: 2019-2023",
]
expand_var_set = False
model = benchmark_choice = 'ours'  # DRI, RSS, IMPACT, IHTSA, ToRsR, SOTA, all_baseline, ours
t2emodel_to_test = ['CoxPH']  # ['CoxPH', 'DeepHit']  # 'CoxPH', 'RSF', 'DeepHit'
models_to_test = ['Logistic', 'RuleFit', 'XGBoost']  # active branches in train_TXP.py
XGBoost_plot = ['importance', 'local', 'magnitude']  # 'magnitude', 'importance', 'local', 'partial'
txp_model_choices = ['DRI', 'RSS', 'IMPACT', 'IHTSA', 'ToRsR', 'SOTA', 'ours']
wl_model_choices = ['Alshawabkeh', 'Jasseron', 'Hsich', 'Bakhtiyar', 'ours']

rulefit_model_type = 'rl'  # 'r'=rules only (L1 linear combo of rules, 0 feature linear terms); 'rl'=rules+features; 'l'=linear only
# Transplant-era year dummies (txp_era_year_vars): linear L1 terms only — excluded from GBDT rule mining
rulefit_era_year_linear_only = True
rulefit_compare_rules_only = False  # if True + interpret: also fit a second rules-only model when model_type='rl'
# RuleFit uses only these columns (actionable / Cox-aligned). Set rulefit_use_feature_list=False for all 210.
rulefit_use_feature_list = True
expanded_vars = [
    "On Anti-Arrhythmics: Yes ",
    "BUN (mg/dL)",
    "On Anti-Arrhythmics: Yes",
    "Serum Albumin (g/dL)",
    "Total Number of Prior Sternotomies",
    "Cardiac Index (in L/min/m²)",
    "Serum Sodium (mEq/L)",
    "On Vasoactive Support: Yes",
    "PCWP (in mmHg)",
    "Mixed Venous Oxygen Saturation (SvO2) (%)",
    "CPRA (%)",
    "Number of Hospital Admissions in 12 Months",
]
rulefit_feature_vars = expanded_vars + [
    # --- Cox / multivariate significant (1-year mortality) ---
    "Patient age in years",
    "Patient weight (kg)",
    "Patient IV inotropes at TXP: Yes",
    "Donor pre-recovery heparin: Yes",
    "Patient mean PAP at TXP",
    "Patient transfusion between WL and TXP: Yes",
    "Patient body mass index",
    "Patient previous malignancy: Yes",
    "Patient total waitlist days",
    "Patient on ventilator at TXP: Yes",
    "Patient serum total bilirubin at TXP",
    "Ischemic time in hours",
    "Patient dialysis between WL and TXP: Yes",
    "Patient hospitalization status: Hospitalized not in ICU",
    "Patient hospitalization status: In ICU",
    "Patient number of previous TXPs",
    "Patient primary diagnosis: Congenital heart disease",
    "Patient primary diagnosis: Ischemic cardiomyopathy",
    "Patient primary diagnosis: Restrictive cardiomyopathy",
    "Patient primary diagnosis: Transplant graft failure/rejection",
    "Patient HEP B surface antigen: Positive",
    "Nautical miles from donor to TXP center",
    "Patient infection: Yes",
    # --- Often co-selected; clinically actionable at TXP ---
    "Patient eGFR",
    "Patient absolute creatinine at WL",
    "Donor age in years",
    "Donor weight (kg)",
    "Patient dialysis prior to TXP: Yes",
    "Patient On ECMO at TXP: Yes",
    "Patient functional status at TXP",
    "Patient creatinine clearance",
    "Donor gender: Male (Not Female)",
    "Donor age in years",
    "Patient transfusion between WL and TXP",
    "Patient multi-organ TXP: Yes",
] + (txp_era_year_vars if analyze_full_data else [])
# --- Fast preset (exploratory; usually 1–5 min). Set rulefit_fast_mode=False for full fit. ---
rulefit_fast_mode = False
rulefit_max_rules = 50
rulefit_max_active_rules = rulefit_table2_top_n = 8      # cap non-zero rules after L1 (by importance); 0 = no cap
rulefit_max_active_linear = 40      # only when model_type='rl': cap non-zero linear terms after L1; 0=no cap (not “zero linear”)
rulefit_max_rule_conditions = 3   # max AND-clauses per rule (GBDT max_depth)
rulefit_tree_size = 4             # max leaf nodes per tree (with max_depth, paths stay ≤2 splits)
rulefit_n_estimators = 10       # GBDT trees when fast_mode (via tree_generator)
rulefit_train_subsample = 0  # 0 = use all training rows after ROS
rulefit_C = 100                 # L1 inverse reg strength (fast_mode: single LR, no CV)
rulefit_cv = 3                  # only used when rulefit_fast_mode=False
rulefit_exp_rand_tree_size = False
rulefit_max_iter = 1000
rulefit_tol = 1e-3
rulefit_calibrated = True      # skip isotonic in fast mode
rulefit_stability_bootstraps = 8  # 0=skip; refit on 80% subsamples, count top-feature recurrence
rulefit_support_min = 0.05      # below -> tiny_subgroup (unstable)
rulefit_support_max = 0.90       # above -> very_broad (not discriminative)
rulefit_use_raw_features = True  # RuleFit on CSV-scale data (Logistic/XGB still use StandardScaler)
rulefit_lin_standardise = False  # no extra Friedman scaling inside RuleFit when using raw features
rulefit_threshold_decimals = 2   # round split thresholds in exported rules
rulefit_min_leaf_frac = 0.05       # GBDT min_samples_leaf = 5% of RuleFit train n (avoid n≈100 leaves)
# Table 2 (sepsis-paper style): log-rank on train cohort + decomposition p-values
rulefit_table2 = True
rulefit_table2_logrank_alpha = 0.001 # full-rule log-rank must be < this to pass filter
rulefit_table2_require_decomposition = False  # full-rule p < each single-condition p

test_assumption = False
load_rows = False
load_summary = False
run_all = False
diffusion = False
print_dist = False
interpret = False
hp_search = False
DB = True
calibrated = True
logistic_significance_p_threshold = 0.05  # p-value cutoff for sig vars (tables, sig-only refit, forest merge)

# RandomOverSampler on training set only (test/calib keep natural prevalence)
use_ros = False                  # all models (Logistic, XGBoost, RuleFit)
ros_sampling_strategy = 1.0   # minority:majority ratio; 1.0 = 50:50 balanced

n_shap_est = 100
num_runs = 1
topk = 20
run_what = 'txp'
YEARS = 1
num_threshold = 0.3
cat_threshold = 0.5

# Infrequent categorical levels (< this share of the cohort) are collapsed to 'Other'.
# Binary vars whose minority class is below the same rate are dropped entirely.
rare_category_min_rate = 0.01  # 1% of cohort (no absolute-count rule)

GPU = -1
seed = 0
device = torch.device("cuda:%d" % GPU if torch.cuda.is_available() and GPU >= 0 else "cpu")
random.seed(seed)
np.random.seed(seed)
os.environ["PYTHONHASHSEED"] = str(seed)


# Override list of significant variables to report in error cohort tables
lr_significant_vars = SIGNIFICANT_VARS_OVERRIDE = [
    # Donor Clinical Factors
    'Donor pre-recovery heparin: Yes',
    "Donor HEP B surface antigen: Positive",
    "Donor antibody TO HEP C virus result: Positive",
    "Donor serology anti-CMV: Positive",

    # Donor Demographics
    "Donor age in years",
    "Donor weight (kg)",

    # Donor and Recipient Matching
    "Ischemic time in hours",
    "Nautical miles from donor to TXP center",

    # Patient Acuity and Status
    "Patient HEP C status: Positive",
    'Patient Hepatitis B antibody test: Positive',
    "Patient diabetes mellitus: Type II",
    "Patient dialysis prior to TXP: Yes",
    "Patient functional status at TXP",
    "Patient history of cigarette use: Yes",
    "Patient hospitalization status: Hospitalized not in ICU",
    "Patient hospitalization status: In ICU",
    "Patient infection: Yes",
    "Patient multi-organ TXP: Yes",
    "Patient number of previous TXPs",
    "Patient primary diagnosis: Congenital heart disease",
    "Patient primary diagnosis: Ischemic cardiomyopathy",
    "Patient primary diagnosis: Restrictive cardiomyopathy",
    "Patient primary diagnosis: Transplant graft failure/rejection",
    "Patient total waitlist days",
    "Patient transfusion between WL and TXP: Yes",

    # Patient Demographics
    "Patient age in years",
    "Patient body mass index",
    "Patient education: COLLEGE DEGREE",
    "Patient race: Asian",
    "Patient race: Black",
    "Patient weight (kg)",

    # Patient Device Support
    "Patient On ECMO at TXP: Yes",
    "Patient on ventilator at TXP: Yes",

    # Patient Lab Values
    "Patient eGFR",
    "Patient serum total bilirubin at TXP",

    # Transplant Era
    "Patient year of TXP: 1994-1998",
    "Patient year of TXP: 1999-2003",
    "Patient year of TXP: 2004-2008",
    "Patient year of TXP: 2009-2013",
    "Patient year of TXP: 2014-2018",
    "Patient year of TXP: 2019-2023",
]

lr_significant_vars_offer_accept = [
    "Patient age in years",
    "Patient gender: Male (Not Female)",
    "Patient race: Black",
    "Patient race: Hispanic",
    "BNP Test Type: NT Pro BNP",
    "CPRA (%)",
    "Distance (km) between donor and recipient",
    "Donor Agent Dosage Units: units/hr",
    "Donor Alkaline Phosphatase (u/L)",
    "Donor Anti-HCV status: Positive",
    "Donor Inotropic Medication Type: Levophed",
    "Donor Plt (thous/mcL)",
    "Donor Toxicology Screen: Yes",
    "Donor Vent Mode: A/C",
    "Donor Ventricular Tachyardia (cc)",
    "Donor West Nile serology: N",
    "Donor age in months",
    "Donor and recipient in same UNOS region: 1",
    "Donor diaphragm width (cm)",
    "Donor shortening fraction (SF)",
    "History of Peripheral Thromboembolic Events: Yes",
    "Natural Log of Rank on Donor Match Run",
    "Number of Hospital Admissions in 12 Months",
    "Number of donor offers",
    "On Oral Anticoagulant when INR was Obtained: Yes",
    "On Vasoactive Support: Yes",
    "Patient initial waitlist status: New Status 1",
    "Patient initial waitlist status: Old Status 1A",
    "Patient initial waitlist status: Old Status 1B",
    "Patient initial waitlist status: Old Status 2",
    "Resting Heart Rate (in bpm)",
    "Serum Sodium (mEq/L)",
    "Support (Device/Inotrope): Inotrope Support",
    "Systolic Blood Pressure (in mmHg)",
    "Total Number of Prior Sternotomies"
]

# Forest plot: rescale per-unit OR (from logistic on standardized X) to clinical increments.
# Key = exact Variable name in significant_variables_for_forest_plot.csv.
# Value = (multiplier, short_label for y-axis). multiplier=1 labels only, no rescale.
forest_plot_or_units = {
    "Patient age in years": (10, "per 10 y"),
    "Donor age in years": (10, "per 10 y"),
    "Patient total waitlist days": (100, "per 100 d"),
    "Patient eGFR": (10, "per 10 mL/min/1.73 m²"),
    "Patient creatinine clearance": (10, "per 10 mL/min"),
    "Patient mean PAP at TXP": (10, "per 10 mmHg"),
    "Patient serum total bilirubin at TXP": (1, "per 1 mg/dL"),
    "Nautical miles from donor to TXP center": (100, "per 100 nm"),
    "Patient body mass index": (5, "per 5 kg/m²"),
    "Patient weight (kg)": (10, "per 10 kg"),
    "Donor weight (kg)": (10, "per 10 kg"),
}

