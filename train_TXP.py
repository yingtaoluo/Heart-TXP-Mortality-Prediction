# train_TXP.py (1Y + 3Y, Logistic P-value = BH-FDR q)  →  ../results/{1,3}YEAR/multivariate_results.csv
#          ↓
# vis/merge_regression_results.py  →  ../results/significant_variables*.csv
#          ↓
# vis/create_grouped_forest_plot.py  →  vis/forest_plot_grouped.png / .pdf


from preprocess.helpers import *
from collections import Counter
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import RandomOverSampler  # or SMOTE
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import ParameterGrid
from sklearn.isotonic import IsotonicRegression
from utils import *
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBClassifier
from statsmodels.stats.multitest import multipletests
import joblib
import shap
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import roc_auc_score

import json
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from scipy.stats import ttest_ind, chi2_contingency, fisher_exact
import os


def summarize_errors_to_latex(X_raw_test: pd.DataFrame,
                              y_test: pd.Series,
                              y_pred_prob: np.ndarray,
                              significant_vars: list,
                              years: int,
                              out_prefix: str):

    y_true_np = np.asarray(y_test)
    threshold = best_threshold(y_true_np, y_pred_prob)
    y_pred_cls = (y_pred_prob >= threshold).astype(int)
    correct_mask = (y_pred_cls == y_true_np)
    fp_mask = (y_pred_cls == 1) & (y_true_np == 0)   # Type I
    fn_mask = (y_pred_cls == 0) & (y_true_np == 1)   # Type II

    # Robust binary series detection: identifies if a series contains only 0s and 1s (allowing for float precision)
    def is_binary_series(s: pd.Series) -> bool:
        vals = pd.to_numeric(s, errors='coerce').dropna().values
        if vals.size == 0:
            return False
        # Map to 0/1 and check if original values are very close to these mapped values
        mapped = (vals >= 0.5).astype(float)
        return np.all(np.isfinite(vals)) and np.all(np.abs(vals - mapped) < 1e-6)

    rows = []
    for var in significant_vars:
        if var not in X_raw_test.columns:
            continue
        col = X_raw_test[var]
        # Determine if binary using robust detection function on the raw data column
        binary_flag = is_binary_series(col)

        def fmt_num(s):
            s = pd.to_numeric(s, errors='coerce')
            return f"{np.nanmean(s):.1f} $\pm$ {np.nanstd(s, ddof=1):.1f}"
        def fmt_bin(s):
            # For binary columns, calculate prevalence (mean of 0s and 1s)
            s_binary = (pd.to_numeric(s, errors='coerce') >= 0.5).astype(float)
            return f"{np.nanmean(s_binary)*100:.1f}\%"

        if binary_flag:
            corr_stat = fmt_bin(col[correct_mask])
            fp_stat = fmt_bin(col[fp_mask])
            fn_stat = fmt_bin(col[fn_mask])
            # p-values for binary: Fisher's exact or Chi-squared
            def prop_p(a, b):
                a_binary = (pd.to_numeric(a, errors='coerce') >= 0.5).astype(float)
                b_binary = (pd.to_numeric(b, errors='coerce') >= 0.5).astype(float)
                a1, a0 = int(np.nansum(a_binary==1)), int(np.nansum(a_binary==0))
                b1, b0 = int(np.nansum(b_binary==1)), int(np.nansum(b_binary==0))
                table = np.array([[a1, a0], [b1, b0]])
                if (table < 5).any():
                    try:
                        _, p = fisher_exact(table)
                    except Exception:
                        p = np.nan
                else:
                    try:
                        _, p, _, _ = chi2_contingency(table)
                    except Exception:
                        p = np.nan
                return p
            p_fp = prop_p(col[fp_mask], col[correct_mask])
            p_fn = prop_p(col[fn_mask], col[correct_mask])
        else:
            # For numeric columns: mean \pm std; p-values via Welch's t-test
            corr_stat = fmt_num(col[correct_mask])
            fp_stat = fmt_num(col[fp_mask])
            fn_stat = fmt_num(col[fn_mask])
            p_fp = ttest_ind(pd.to_numeric(col[fp_mask], errors='coerce'),
                             pd.to_numeric(col[correct_mask], errors='coerce'),
                             equal_var=False, nan_policy='omit').pvalue
            p_fn = ttest_ind(pd.to_numeric(col[fn_mask], errors='coerce'),
                             pd.to_numeric(col[correct_mask], errors='coerce'),
                             equal_var=False, nan_policy='omit').pvalue
        row = {
            'Variable': var,
            'Correct': corr_stat,
            'Type I (FP)': fp_stat,
            'P value': "<0.01" if p_fp < 0.01 else f"{p_fp:.2f}",
            'Type II (FN)': fn_stat,
            'P value ': "<0.01" if p_fn < 0.01 else f"{p_fn:.2f}",
        }
        rows.append(row)

    if not rows:
        return
    df = pd.DataFrame(rows)

    # Escape LaTeX special characters in the 'Variable' column
    def escape_latex_special_chars(text):
        if not isinstance(text, str):
            return text
        # Order matters: escape backslash first
        text = text.replace('\\', '\\textbackslash{}')  # double backslash because of python string escape
        text = text.replace('&', '\\&')
        text = text.replace('%', '\\%')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')
        text = text.replace('~', '\\textasciitilde{}')
        text = text.replace('^', '\\textasciicircum{}')
        return text

    df['Variable'] = df['Variable'].apply(escape_latex_special_chars)

    # Reorder columns as requested
    df = df[['Variable', 'Correct', 'Type I (FP)', 'P value', 'Type II (FN)', 'P value ']]

    # Calculate patient counts for header
    n_correct = len(y_test) - np.sum(fp_mask) - np.sum(fn_mask)
    n_fp = np.sum(fp_mask)
    n_fn = np.sum(fn_mask)
    
    # Update column names to include patient counts
    df.columns = ['Variable', f'Correct (n={n_correct})', f'Type I (FP) (n={n_fp})', 'P value', f'Type II (FN) (n={n_fn})', 'P value ']

    latex = df.to_latex(index=False, escape=False)
    print(latex)


# Post-hoc error analysis: train LR to distinguish FP vs TN and FN vs TP
def analyze_misclassification_logit(X_test: pd.DataFrame,
                                    y_test: pd.Series,
                                    y_pred_prob: np.ndarray,
                                    years: int,
                                    out_prefix: str,
                                    significant_vars: list | None = None):

    y_true_np = np.asarray(y_test)
    threshold = best_threshold(y_true_np, y_pred_prob)
    y_pred_cls = (y_pred_prob >= threshold).astype(int)

    # Masks
    tn_mask = (y_pred_cls == 0) & (y_true_np == 0)
    fp_mask = (y_pred_cls == 1) & (y_true_np == 0)
    tp_mask = (y_pred_cls == 1) & (y_true_np == 1)
    fn_mask = (y_pred_cls == 0) & (y_true_np == 1)

    def fit_subset_lr(X_subset: pd.DataFrame, y_subset: np.ndarray, label_name: str) -> pd.DataFrame:
        # Optionally restrict to significant variables present
        if significant_vars:
            use_cols = [c for c in significant_vars if c in X_subset.columns]
            if len(use_cols) >= 1:
                X_subset = X_subset[use_cols]

        # Standardize, then add intercept for statsmodels
        scaler_local = StandardScaler()
        X_scaled_local = scaler_local.fit_transform(X_subset)
        X_sm = sm.add_constant(X_scaled_local, has_constant='add')

        try:
            model = sm.Logit(y_subset, X_sm)
            res = model.fit(disp=False, maxiter=100)
            params_arr = np.asarray(res.params)
            conf_arr = np.asarray(res.conf_int())
            pvals_arr = np.asarray(res.pvalues)
        except Exception as e:
            # Fallback: fit sklearn LR, approximate CIs not available; return coefficients only
            lr = LogisticRegression(penalty='l2', solver='lbfgs', C=1.0, max_iter=10000, class_weight='balanced', n_jobs=-1)
            lr.fit(X_scaled_local, y_subset)
            coef = lr.coef_.ravel()
            params_arr = np.concatenate([[0.0], coef])
            conf_arr = np.vstack([np.array([np.nan, np.nan]) for _ in range(len(params_arr))])
            pvals_arr = np.array([np.nan for _ in range(len(params_arr))])

        # Map back to original feature names for readability
        feature_names = ['Intercept'] + list(X_subset.columns)
        # Ensure lengths match
        if len(params_arr) != len(feature_names):
            # If statsmodels named the constant differently or excluded it, try to align
            # Fallback: generate generic names of matching length
            feature_names = [f'x{i}' for i in range(len(params_arr))]

        df = pd.DataFrame({
            'Variable': feature_names,
            'Coefficient': params_arr,
            'OddsRatio': np.exp(params_arr),
            'OR_CI_Lower': np.exp(conf_arr[:, 0]) if conf_arr.ndim == 2 and conf_arr.shape[1] >= 2 else np.nan,
            'OR_CI_Upper': np.exp(conf_arr[:, 1]) if conf_arr.ndim == 2 and conf_arr.shape[1] >= 2 else np.nan,
            'PValue': pvals_arr,
            'Cohort': label_name
        })
        # Drop intercept row for reporting
        df = df[df['Variable'] != 'Intercept']
        return df

    # Type I analysis: among true negatives (y=0), FP vs TN
    mask_y0 = (y_true_np == 0)
    results = []
    if mask_y0.any() and (fp_mask.any() or tn_mask.any()):
        y_fp_vs_tn = fp_mask[mask_y0].astype(int)
        X_y0 = X_test.iloc[np.where(mask_y0)[0]]
        results.append(fit_subset_lr(X_y0, y_fp_vs_tn, label_name='Type I (FP vs TN)'))
    else:
        print("Skip Type I LR: insufficient y=0 cases")

    # Type II analysis: among true positives cohort (y=1), FN vs TP
    mask_y1 = (y_true_np == 1)
    if mask_y1.any() and (fn_mask.any() or tp_mask.any()):
        y_fn_vs_tp = fn_mask[mask_y1].astype(int)
        X_y1 = X_test.iloc[np.where(mask_y1)[0]]
        results.append(fit_subset_lr(X_y1, y_fn_vs_tp, label_name='Type II (FN vs TP)'))
    else:
        print("Skip Type II LR: insufficient y=1 cases")

    if results:
        out_df = pd.concat(results, ignore_index=True)
        # Compute importance as distance from null effect (OR=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            importance = np.abs(np.log(out_df['OddsRatio'].astype(float)))
        importance = importance.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        out_df['Importance'] = importance
        # Build formatted OR with CI string: 0.972 (0.946-0.999)
        def fmt_or_ci(or_val, lo, hi):
            try:
                or_f = float(or_val)
                lo_f = float(lo)
                hi_f = float(hi)
                if np.isfinite(or_f) and np.isfinite(lo_f) and np.isfinite(hi_f):
                    return f"{or_f:.3f} ({lo_f:.3f}-{hi_f:.3f})"
                return f"{or_f:.3f} (NA-NA)"
            except Exception:
                return "NA (NA-NA)"
        out_df['OR (95% CI)'] = [
            fmt_or_ci(o, l, u) for o, l, u in zip(out_df['OddsRatio'], out_df['OR_CI_Lower'], out_df['OR_CI_Upper'])
        ]
        # Rank by importance within each cohort
        out_df = out_df.sort_values(['Cohort', 'OddsRatio'], ascending=[True, False])
        
        # Filter out 'Patient year of TXP' variables
        out_df = out_df[~out_df['Variable'].str.contains('Patient year of TXP')]

        # Filter for OR > 1.5
        out_df = out_df[out_df['OddsRatio'] > 1.5]

        # Final display columns
        display_df = out_df[['Cohort', 'Variable', 'OR (95% CI)', 'PValue']]
        # Format PValue column
        display_df['PValue'] = display_df['PValue'].apply(lambda x: "<0.01" if x < 0.01 else f"{x:.2f}")
        # Print a single LaTeX table
        print(display_df.to_latex(index=False))


# --- RuleFit (Friedman & Popescu 2008): tree rules + sparse linear model ---
# Install: pip install rulefit   (PyPI 0.3.1 = christophM implementation)
#
# Console section tags (what to put in a paper):
#   [SETUP]       Methods only — feature list, raw vs scaled (see rulefit_features_used_*.json)
#   [PRIMARY]     Main exploratory tables — active terms CSV + held-out AUC/AUPRC
#   [SUPPLEMENT]  Appendix / robustness — rule audit flags, bootstrap feature stability
#   [INTERNAL]    Fitting logs — omit from manuscript
#   [DIAGNOSTIC]  Shared evaluate() metrics dict — compare RuleFit vs Logistic; not narrative text

_RULEFIT_BANNER_W = 70


def _rulefit_banner(tag: str, title: str, purpose: str) -> None:
    bar = '=' * _RULEFIT_BANNER_W
    print(f'\n{bar}\n  [{tag}] {title}\n  Use in paper: {purpose}\n{bar}', flush=True)


def _drop_const_for_rulefit(X_df: pd.DataFrame) -> pd.DataFrame:
    """RuleFit fits its own intercept; drop statsmodels 'const' column."""
    return X_df.drop(columns=['const']) if 'const' in X_df.columns else X_df


def _latest_era_mask_from_raw(X_df: pd.DataFrame):
    """One-hot era column == 1 on raw (pre-scaler) data; None if disabled or missing."""
    if not analyze_full_data or not eval_latest_era_cohort:
        return None
    if latest_era_year_col not in X_df.columns:
        print(f"[latest era] column not found: {latest_era_year_col!r}; skip era eval.", flush=True)
        return None
    return (X_df[latest_era_year_col] == 1)


def _ros_fit_resample(X, y, sampling_strategy=0.2, random_state=None):
    """Oversample minority to target ratio; skip if already at/above target."""
    y_arr = np.asarray(y)
    if y_arr.size == 0:
        return X, y
    _, counts = np.unique(y_arr, return_counts=True)
    if len(counts) < 2:
        return X, y
    majority_n = int(counts.max())
    minority_n = int(counts.min())
    if minority_n >= majority_n * sampling_strategy:
        return X, y
    ros = RandomOverSampler(sampling_strategy=sampling_strategy, random_state=random_state)
    return ros.fit_resample(X, y)


def _eval_on_latest_era(metrics, base_model_name, y_test, y_pred, y_pred_raw=None, era_mask=None):
    """Evaluate on test rows in latest transplant era (2019-2023 when analyze_full_data)."""
    if not analyze_full_data or not eval_latest_era_cohort:
        return metrics
    if era_mask is None:
        return metrics
    era_mask = np.asarray(era_mask, dtype=bool)
    n = int(era_mask.sum())
    if n == 0:
        print(f"[{base_model_name}] latest era: no test rows; skip.", flush=True)
        return metrics
    era_model = f"{base_model_name}_era2019_2023"
    if era_model not in metrics:
        metrics[era_model] = {k: [] for k in metrics[base_model_name].keys()}
    y_t = np.asarray(y_test)[era_mask]
    y_p = np.asarray(y_pred, dtype=float)[era_mask]
    y_raw = np.asarray(y_pred_raw, dtype=float)[era_mask] if y_pred_raw is not None else None
    prev = float(y_t.mean())
    print(
        f"\n[ERA EVAL] {era_model} | n_test={n} | event rate={prev:.3f} | {latest_era_year_col}",
        flush=True,
    )
    return evaluate(
        era_model, 'TXP', benchmark_choice, metrics,
        y_t, y_p, y_pred_raw=y_raw,
        save=True, save_plots=False,
    )


def _apply_rulefit_feature_list(X_df: pd.DataFrame, *, log: bool = False) -> tuple[pd.DataFrame, list]:
    """
  Subset to rulefit_feature_vars from helpers when rulefit_use_feature_list=True.
  Intended to keep trees/rules on Cox/XGB-aligned, clinician-actionable inputs only.
    """
    base = _drop_const_for_rulefit(X_df)
    if not rulefit_use_feature_list or not rulefit_feature_vars:
        cols = list(base.columns)
        return base, cols

    cols, missing, seen = [], [], set()
    for name in rulefit_feature_vars:
        if name in seen:
            continue
        if name in base.columns:
            cols.append(name)
            seen.add(name)
        else:
            missing.append(name)
    if not cols:
        raise ValueError(
            "rulefit_feature_vars: no columns matched X. "
            "Check names against TXP_data columns or set rulefit_use_feature_list=False."
        )
    if log:
        if missing:
            print(f"  Skipped {len(missing)} requested vars (not in CSV): "
                  f"{missing[:8]}{'...' if len(missing) > 8 else ''}", flush=True)
        print(f"  Using {len(cols)} features (of {len(rulefit_feature_vars)} requested).", flush=True)
    return base[cols], cols


def _rulefit_linear_only_vars_in_cols(feature_names) -> list:
    """Era-year dummies present in feature_names when linear-only mode is enabled."""
    if not rulefit_era_year_linear_only:
        return []
    return [c for c in feature_names if c in txp_era_year_vars]


def _rulefit_X_for_rules(rf, X: np.ndarray) -> np.ndarray:
    """Columns passed to rule_ensemble.transform (subset when era vars are linear-only)."""
    idx = getattr(rf, '_rule_col_indices', None)
    if idx is None:
        return X
    return X[:, idx]


def _rulefit_fit_tree_generator(rf, X_rule: np.ndarray, y: np.ndarray):
    """Fit tree_generator on rule-mining columns only; return tree_list for RuleEnsemble."""
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        GradientBoostingRegressor,
        RandomForestClassifier,
        RandomForestRegressor,
    )

    if not rf.exp_rand_tree_size:
        rf.tree_generator.fit(X_rule, y)
    else:
        np.random.seed(rf.random_state)
        tree_sizes = np.random.exponential(
            scale=rf.tree_size - 2,
            size=int(np.ceil(rf.max_rules * 2 / rf.tree_size)),
        )
        tree_sizes = np.asarray(
            [2 + np.floor(tree_sizes[i_]) for i_ in np.arange(len(tree_sizes))],
            dtype=int,
        )
        i = int(len(tree_sizes) / 4)
        while np.sum(tree_sizes[0:i]) < rf.max_rules:
            i += 1
        tree_sizes = tree_sizes[0:i]
        rf.tree_generator.set_params(warm_start=True)
        curr_est_ = 0
        for i_size in np.arange(len(tree_sizes)):
            size = tree_sizes[i_size]
            rf.tree_generator.set_params(n_estimators=curr_est_ + 1)
            rf.tree_generator.set_params(max_leaf_nodes=size)
            random_state_add = rf.random_state if rf.random_state else 0
            rf.tree_generator.set_params(random_state=i_size + random_state_add)
            rf.tree_generator.fit(np.copy(X_rule, order='C'), np.copy(y, order='C'))
            curr_est_ += 1
        rf.tree_generator.set_params(warm_start=False)

    tree_list = rf.tree_generator.estimators_
    if isinstance(rf.tree_generator, (RandomForestRegressor, RandomForestClassifier)):
        tree_list = [[x] for x in rf.tree_generator.estimators_]
    return tree_list


def _rulefit_fit_with_linear_only_vars(rf, X, y, feature_names, linear_only_vars):
    """
    RuleFit fit where linear_only_vars enter L1 linear terms only (never in GBDT rules).
    Trees and rule conditions use the remaining columns.
    """
    import rulefit.rulefit as _rulefit_mod
    from rulefit.rulefit import RuleEnsemble

    linear_only_set = set(linear_only_vars)
    rule_cols = [c for c in feature_names if c not in linear_only_set]
    rule_col_idx = [feature_names.index(c) for c in rule_cols]
    X_rule = X[:, rule_col_idx]

    rf.feature_names = feature_names
    rf._rule_col_indices = rule_col_idx
    rf._linear_only_vars = list(linear_only_vars)

    X_rules = np.zeros([X.shape[0], 0])
    if 'r' in rf.model_type:
        tree_list = _rulefit_fit_tree_generator(rf, X_rule, y)
        rf.rule_ensemble = RuleEnsemble(tree_list=tree_list, feature_names=rule_cols)
        X_rules = rf.rule_ensemble.transform(X_rule)

    if 'l' in rf.model_type:
        rf.winsorizer.train(X)
        winsorized_X = rf.winsorizer.trim(X)
        rf.stddev = np.std(winsorized_X, axis=0)
        rf.mean = np.mean(winsorized_X, axis=0)
        if rf.lin_standardise:
            rf.friedscale.train(X)
            X_regn = rf.friedscale.scale(X)
        else:
            X_regn = X.copy()
    else:
        X_regn = None

    X_concat = np.zeros([X.shape[0], 0])
    if 'l' in rf.model_type:
        X_concat = np.concatenate((X_concat, X_regn), axis=1)
    if 'r' in rf.model_type and X_rules.shape[0] > 0:
        X_concat = np.concatenate((X_concat, X_rules), axis=1)

    if rf.rfmode == 'regress':
        if rf.Cs is None:
            n_alphas, alphas = 100, None
        elif hasattr(rf.Cs, '__len__'):
            n_alphas, alphas = None, 1.0 / rf.Cs
        else:
            n_alphas, alphas = rf.Cs, None
        from sklearn.linear_model import LassoCV
        rf.lscv = LassoCV(
            n_alphas=n_alphas, alphas=alphas, cv=rf.cv, random_state=rf.random_state,
        )
        rf.lscv.fit(X_concat, y)
        rf.coef_ = rf.lscv.coef_
        rf.intercept_ = rf.lscv.intercept_
    else:
        Cs = 10 if rf.Cs is None else rf.Cs
        rf.lscv = _rulefit_mod.LogisticRegressionCV(
            Cs=Cs, cv=rf.cv, penalty='l1', random_state=rf.random_state, solver='liblinear',
        )
        rf.lscv.fit(X_concat, y)
        rf.coef_ = rf.lscv.coef_[0]
        rf.intercept_ = rf.lscv.intercept_[0]
    return rf


def _rulefit_design_matrix(rf, X: np.ndarray) -> np.ndarray:
    """Build design matrix (linear terms + active rules) as in RuleFit.predict."""
    X_concat = np.zeros([X.shape[0], 0])
    if 'l' in rf.model_type:
        if rf.lin_standardise:
            X_concat = np.concatenate((X_concat, rf.friedscale.scale(X)), axis=1)
        else:
            X_concat = np.concatenate((X_concat, X), axis=1)
    if 'r' in rf.model_type:
        rule_coefs = rf.coef_[-len(rf.rule_ensemble.rules):]
        if len(rule_coefs) > 0:
            X_for_rules = _rulefit_X_for_rules(rf, X)
            X_rules = rf.rule_ensemble.transform(X_for_rules, coefs=rule_coefs)
            if X_rules.shape[0] > 0:
                X_concat = np.concatenate((X_concat, X_rules), axis=1)
    return X_concat


def _sync_rulefit_lscv_coefs(rf) -> None:
    """Keep sklearn lscv weights aligned with rf.coef_ (e.g. after post-L1 pruning)."""
    if not hasattr(rf, 'lscv') or not hasattr(rf.lscv, 'coef_'):
        return
    coef = np.asarray(rf.coef_, dtype=float).ravel()
    if rf.lscv.coef_.ndim == 2:
        rf.lscv.coef_[0] = coef
    else:
        rf.lscv.coef_ = coef


def _prune_rulefit_active_terms(rf, verbose: bool = True):
    """
    After L1 fit, keep only top rules/linear terms by RuleFit importance.
    Zeros remaining coefficients in rf.coef_ (hard cap on active terms).
    """
    max_r = int(rulefit_max_active_rules or 0)
    max_l = int(rulefit_max_active_linear or 0)
    if max_r <= 0 and max_l <= 0:
        return rf

    if not getattr(rf, 'rule_ensemble', None):
        return rf

    df = rf.get_rules(exclude_zero_coef=False)
    coef = np.asarray(rf.coef_, dtype=float).copy()
    n_before_r = int(((df['type'] == 'rule') & (df['coef'] != 0)).sum())
    n_before_l = int(((df['type'] == 'linear') & (df['coef'] != 0)).sum())

    linear_df = df[df['type'] == 'linear'].reset_index(drop=True)
    rule_df = df[df['type'] == 'rule'].reset_index(drop=True)
    linear_df['coef_idx'] = np.arange(len(linear_df))
    rule_df['coef_idx'] = len(linear_df) + np.arange(len(rule_df))

    if max_l > 0:
        keep_lin = set(
            linear_df[linear_df['coef'] != 0]
            .sort_values('importance', ascending=False)
            .head(max_l)['coef_idx']
        )
        for idx in linear_df['coef_idx']:
            if idx not in keep_lin:
                coef[int(idx)] = 0.0

    if max_r > 0:
        keep_rul = set(
            rule_df[rule_df['coef'] != 0]
            .sort_values('importance', ascending=False)
            .head(max_r)['coef_idx']
        )
        for idx in rule_df['coef_idx']:
            if idx not in keep_rul:
                coef[int(idx)] = 0.0

    rf.coef_ = coef
    _sync_rulefit_lscv_coefs(rf)

    if verbose:
        df2 = rf.get_rules(exclude_zero_coef=False)
        n_after_r = int(((df2['type'] == 'rule') & (df2['coef'] != 0)).sum())
        n_after_l = int(((df2['type'] == 'linear') & (df2['coef'] != 0)).sum())
        msg = f"  [{getattr(rf, '_fit_label', 'RuleFit')}] active terms after cap: "
        msg += f"{n_after_r} rules (was {n_before_r}, max={max_r or '∞'})"
        if max_l > 0:
            msg += f"; {n_after_l} linear (was {n_before_l}, max={max_l})"
        print(msg, flush=True)
    return rf


def rulefit_predict_proba(rf, X: np.ndarray) -> np.ndarray:
    """P(y=1|x) for binary RuleFit (rfmode='classify'). Uses pruned rf.coef_."""
    if getattr(rf, 'rfmode', 'regress') != 'classify':
        raise ValueError("rulefit_predict_proba requires rfmode='classify'")
    X_concat = _rulefit_design_matrix(rf, X)
    coef = np.asarray(rf.coef_, dtype=float).ravel()
    intercept = float(np.asarray(rf.intercept_).ravel()[0])
    logit = intercept + X_concat @ coef
    return 1.0 / (1.0 + np.exp(-logit))


def fit_rulefit(rf, X, y, feature_names, label='RuleFit', verbose: bool = True):
    """
    Fit RuleFit. In rulefit_fast_mode, replace slow LogisticRegressionCV with
    a single L1 LogisticRegression (largest speedup on many rule columns).
    """
    import time
    import rulefit.rulefit as _rulefit_mod
    from sklearn.linear_model import LogisticRegressionCV as _LRCV
    from sklearn.linear_model import LogisticRegression as _LR

    max_iter = rulefit_max_iter
    tol = rulefit_tol
    _orig_lrcv = _rulefit_mod.LogisticRegressionCV

    if rulefit_fast_mode:
        def _lrcv_factory(Cs=10, cv=None, penalty='l1', random_state=None,
                          solver='liblinear', **kwargs):
            return _LR(
                penalty='l1',
                C=rulefit_C,
                solver='saga',
                max_iter=max_iter,
                tol=tol,
                random_state=random_state,
                class_weight='balanced',
                n_jobs=-1,
            )
        l1_mode = f'fast LR (C={rulefit_C}, saga, max_iter={max_iter})'
    else:
        def _lrcv_factory(Cs=10, cv=None, penalty='l1', random_state=None,
                          solver='liblinear', **kwargs):
            kwargs.setdefault('max_iter', max_iter)
            kwargs.setdefault('tol', tol)
            return _LRCV(
                Cs=Cs, cv=cv, penalty=penalty,
                random_state=random_state, solver=solver, **kwargs,
            )
        l1_mode = f'LogisticRegressionCV (cv={rf.cv}, max_iter={max_iter})'

    linear_only = _rulefit_linear_only_vars_in_cols(feature_names)
    use_linear_only_rules = bool(linear_only) and 'r' in rf.model_type

    if verbose:
        msg = f"  [{label}] fitting (max_rules={rf.max_rules}, {l1_mode})"
        if use_linear_only_rules:
            msg += f"; era year dummies linear-only ({len(linear_only)} vars, "
            msg += f"rules on {len(feature_names) - len(linear_only)} features)"
        print(msg + " ...", flush=True)
    t0 = time.perf_counter()
    _rulefit_mod.LogisticRegressionCV = _lrcv_factory
    try:
        if use_linear_only_rules:
            _rulefit_fit_with_linear_only_vars(rf, X, y, feature_names, linear_only)
        else:
            rf.fit(X, y, feature_names=feature_names)
    finally:
        _rulefit_mod.LogisticRegressionCV = _orig_lrcv
    rf._fit_label = label
    _prune_rulefit_active_terms(rf, verbose=verbose)
    elapsed = time.perf_counter() - t0
    if verbose:
        n_cand = len(getattr(rf, 'rule_ensemble', None).rules) if getattr(rf, 'rule_ensemble', None) else 0
        df = rf.get_rules(exclude_zero_coef=False)
        n_act_r = int(((df['type'] == 'rule') & (df['coef'] != 0)).sum())
        print(f"  [{label}] done in {elapsed:.1f}s ({n_cand} candidate rules; "
              f"{n_act_r} active after L1+cap)", flush=True)
    return rf


def _round_floats_in_text(text: str, decimals: int | None = None) -> str:
    """Round numeric literals in rule strings for display (e.g. <= 1.023447 -> <= 1.02)."""
    import re
    if decimals is None:
        decimals = rulefit_threshold_decimals
    return re.sub(
        r'(?<![\w-])(-?\d+\.\d+)(?![\w-])',
        lambda m: f'{float(m.group(1)):.{decimals}f}',
        str(text),
    )


def _round_scalar(x: float, decimals: int | None = None) -> float:
    if decimals is None:
        decimals = rulefit_threshold_decimals
    return round(float(x), decimals)


def export_rulefit_rules(rf, years: int, benchmark: str, top_n: int = 30) -> pd.DataFrame:
    """Print and save non-zero rules / linear terms from a fitted RuleFit model."""
    # rulefit 0.3.1 uses deprecated DataFrame.ix; filter coefs ourselves for pandas>=2
    rules = rf.get_rules(exclude_zero_coef=False)
    rules = rules[rules.coef != 0]
    rules = rules.sort_values('importance', ascending=False)
    rules['rule'] = rules['rule'].apply(_round_floats_in_text)
    rules['coef'] = rules['coef'].apply(lambda c: _round_scalar(c, 4))
    rules['n_conditions'] = rules.apply(
        lambda r: _rule_condition_count(r['rule']) if r['type'] == 'rule' else 0, axis=1,
    )
    long_rules = rules[(rules['type'] == 'rule') & (rules['n_conditions'] > rulefit_max_rule_conditions)]
    if not long_rules.empty:
        print(f"  Warning: {len(long_rules)} rule(s) exceed {rulefit_max_rule_conditions} conditions "
              f"(check tree_generator max_depth); they are still in the CSV.", flush=True)
    os.makedirs(f'../results/{years}YEAR', exist_ok=True)
    out_path = f'../results/{years}YEAR/rulefit_rules_{benchmark}.csv'
    rules.to_csv(out_path, index=False)
    _rulefit_banner(
        'PRIMARY',
        'Final sparse model (active terms after L1)',
        'Table: top rules + key linear terms from CSV; Methods cites full file.',
    )
    print(f"  File: {out_path}")
    print("  y=1 = death. +coef → higher P(death); −coef → lower P(death).")
    print("  support (rules only) = fraction of training patients triggering that rule.")
    n_rules = int((rules['type'] == 'rule').sum())
    n_linear = int((rules['type'] == 'linear').sum())
    print(f"  Non-zero terms: {n_rules} rules + {n_linear} linear (= {len(rules)} total).")

    rules_only = rules[rules['type'] == 'rule'].head(top_n)
    linear_sorted = rules[rules['type'] == 'linear'].sort_values('importance', ascending=False)
    if rulefit_max_active_linear and rulefit_max_active_linear > 0:
        linear_only = linear_sorted.head(rulefit_max_active_linear)
    else:
        linear_only = linear_sorted
    print(f"\n  --- Top {len(rules_only)} rules (for narrative; full list in CSV) ---")
    with pd.option_context('display.max_colwidth', 120):
        if not rules_only.empty:
            print(rules_only.to_string(index=False))
        else:
            print("  (none)")
    print(
        f"\n  --- Top {len(linear_only)} linear terms "
        f"(rulefit_max_active_linear={rulefit_max_active_linear or 'all'}; "
        f"support=1.0 means always-on feature) ---"
    )
    with pd.option_context('display.max_colwidth', 120):
        if not linear_only.empty:
            print(linear_only.to_string(index=False))
        else:
            print("  (none)")
    return rules


def _features_in_rule(rule_str: str, feature_names: list) -> list:
    """Which dataset columns appear in a rule string (longest names first to avoid partial matches)."""
    hits = [f for f in sorted(feature_names, key=len, reverse=True) if f in rule_str]
    return hits


def print_rulefit_performance(y_true, y_pred_prob):
    """Summarize held-out test metrics with simple baselines (mortality ~10% prevalence)."""
    from sklearn.metrics import (
        roc_auc_score, average_precision_score, brier_score_loss,
        balanced_accuracy_score, f1_score,
    )
    y_true = np.asarray(y_true).astype(int).ravel()
    y_pred_prob = np.asarray(y_pred_prob, dtype=np.float64).ravel()
    prev = float(y_true.mean())
    auc = roc_auc_score(y_true, y_pred_prob)
    auprc = average_precision_score(y_true, y_pred_prob)
    brier = brier_score_loss(y_true, y_pred_prob)
    thr = best_threshold(y_true, y_pred_prob)
    y_hat = (y_pred_prob >= thr).astype(int)
    bal_acc = balanced_accuracy_score(y_true, y_hat)
    f1 = f1_score(y_true, y_hat, zero_division=0)
    brier_naive = prev * (1 - prev)

    _rulefit_banner(
        'PRIMARY',
        'Held-out test discrimination (RuleFit)',
        'Report AUC (+ AUPRC if low prevalence). Compare to Logistic on same split.',
    )
    print(f"  Death prevalence:     {prev:.3f}")
    print(f"  AUC:                  {auc:.3f}")
    print(f"  AUPRC:                {auprc:.3f}   (baseline ≈ prevalence {prev:.3f})")
    print(f"  Brier score:          {brier:.3f}   (naive constant prob ≈ {brier_naive:.3f})")
    print(f"  Balanced acc / F1:    {bal_acc:.3f} / {f1:.3f}  (threshold {thr:.3f}; "
          "often uninformative when prevalence ~10%)")
    if auc < 0.55:
        print("  Note: AUC near random — treat rules as exploratory only.")
    elif auc < 0.65:
        print("  Note: modest AUC — pair with bootstrap stability (SUPPLEMENT) before strong claims.")
    else:
        print("  Note: reasonable discrimination for a sparse rule model.")


def audit_rulefit_rules(rules_df: pd.DataFrame, feature_names: list, years: int, benchmark: str) -> pd.DataFrame:
    """
    Flag rules that are often NOT robust (very broad / tiny subgroup / huge coef).
    Saves results/{years}YEAR/rulefit_rules_{benchmark}_audit.csv
    """
    df = rules_df.copy()
    flags, feat_lists, notes = [], [], []
    for _, row in df.iterrows():
        f, note = [], []
        if row['type'] == 'rule':
            if row['support'] > rulefit_support_max:
                f.append('very_broad')
                note.append(f"support={row['support']:.1%} (most patients trigger)")
            if row['support'] < rulefit_support_min:
                f.append('tiny_subgroup')
                note.append(f"support={row['support']:.1%} (few patients)")
            if abs(row['coef']) > 2.0:
                f.append('large_coef')
                note.append("|coef|>2 (may be unstable in small groups)")
            feats = _features_in_rule(str(row['rule']), feature_names)
            if not feats:
                f.append('parse_fail')
        flags.append('ok' if not f else '+'.join(f))
        feat_lists.append('; '.join(_features_in_rule(str(row['rule']), feature_names)))
        notes.append('; '.join(note))
    df['rule'] = df['rule'].apply(_round_floats_in_text)
    df['robustness_flag'] = flags
    df['features_mentioned'] = feat_lists
    df['audit_note'] = notes

    rules_only = df[df['type'] == 'rule'].copy()
    n_ok = int((rules_only['robustness_flag'] == 'ok').sum())
    n_flagged = len(rules_only) - n_ok

    _rulefit_banner(
        'SUPPLEMENT',
        'Rule quality audit (training support & coef size)',
        'Filter flagged rules before quoting in text; full table in audit CSV.',
    )
    print(f"  Rules: {n_ok}/{len(rules_only)} pass (no flags); {n_flagged} flagged "
          f"(linear terms not audited — support always 1.0).")
    print("  Flags: ok | very_broad (support>{:.0%}) | tiny_subgroup (<{:.0%}) | large_coef (|coef|>2)".format(
        rulefit_support_max, rulefit_support_min))
    flagged = rules_only[rules_only['robustness_flag'] != 'ok'].sort_values('importance', ascending=False)
    if not flagged.empty:
        print(f"\n  --- Flagged rules ({len(flagged)}) — deprioritize in narrative ---")
        show = flagged[['rule', 'coef', 'support', 'robustness_flag', 'audit_note']].head(12)
        with pd.option_context('display.max_colwidth', 80):
            print(show.to_string(index=False))
    else:
        print("  No flagged rules.")

    out = f'../results/{years}YEAR/rulefit_rules_{benchmark}_audit.csv'
    df.to_csv(out, index=False)
    print(f"\n  File: {out}")
    return df


def rulefit_bootstrap_feature_stability(X_fit, y_fit, feature_names, seed: int, label: str = 'RuleFit'):
    """
    Refit RuleFit on 80% bootstrap samples; report how often each feature
    appears in top-importance rules. High frequency + same coef sign -> more robust.
    """
    from collections import Counter

    n_boot = rulefit_stability_bootstraps
    if n_boot <= 0:
        return None
    top_k = min(8, topk)
    rng = np.random.RandomState(seed)
    feat_hits = Counter()
    feat_pos = Counter()
    feat_neg = Counter()

    _rulefit_banner(
        'SUPPLEMENT',
        f'Bootstrap feature stability ({n_boot} refits, top-{top_k} rules each)',
        'Which clinical themes recur — not exact thresholds. Appendix / sensitivity.',
    )
    feat_in_boot = Counter()
    for b in range(n_boot):
        n = X_fit.shape[0]
        idx = rng.choice(n, size=int(0.8 * n), replace=True)
        X_b, y_b = X_fit[idx], y_fit[idx]
        tree_gen = _make_rulefit_tree_generator(X_b.shape[0], seed + b, verbose=False)
        rf = RuleFit(
            tree_size=rulefit_tree_size,
            max_rules=rulefit_max_rules,
            rfmode='classify',
            model_type=rulefit_model_type,
            exp_rand_tree_size=rulefit_exp_rand_tree_size,
            tree_generator=tree_gen,
            random_state=seed + b,
            cv=rulefit_cv,
        )
        fit_rulefit(rf, X_b, y_b, feature_names, label='bootstrap', verbose=False)
        rules = rf.get_rules(exclude_zero_coef=False)
        rules = rules[rules.coef != 0].sort_values('importance', ascending=False).head(top_k)
        seen_this_boot = set()
        for _, row in rules.iterrows():
            if row['type'] != 'rule':
                continue
            for feat in _features_in_rule(str(row['rule']), feature_names):
                feat_hits[feat] += 1
                seen_this_boot.add(feat)
                if row['coef'] > 0:
                    feat_pos[feat] += 1
                else:
                    feat_neg[feat] += 1
        for feat in seen_this_boot:
            feat_in_boot[feat] += 1

    rows = []
    for feat, hits in feat_hits.most_common():
        pos, neg = feat_pos[feat], feat_neg[feat]
        sign_consistency = max(pos, neg) / hits if hits else 0
        boot_frac = feat_in_boot[feat] / n_boot
        rows.append({
            'feature': feat,
            'top_rule_mentions': hits,
            'in_top_rules_boot_frac': boot_frac,
            'coef_positive_frac': pos / hits if hits else np.nan,
            'robust_hint': 'strong' if boot_frac >= 0.6 and sign_consistency >= 0.75
            else ('moderate' if boot_frac >= 0.4 else 'weak'),
        })
    stab = pd.DataFrame(rows)
    out = f'../results/{YEARS}YEAR/rulefit_feature_stability_{benchmark_choice}.csv'
    stab.to_csv(out, index=False)
    print(f"  Completed {n_boot} bootstrap refits (fitting logs suppressed).")
    print(stab.head(12).to_string(index=False))
    print(f"\n  File: {out}")
    print("  in_top_rules_boot_frac = share of bootstraps with feature in top rules")
    print("  robust_hint: strong = ≥60% bootstraps & consistent coef sign across mentions")
    return stab


def _rulefit_min_samples_leaf(n_train: int) -> int:
    return max(5, int(np.ceil(rulefit_min_leaf_frac * n_train)))


def _rule_condition_count(rule_str: str) -> int:
    """Number of AND-clauses in a rule string (linear terms => 0)."""
    s = str(rule_str).strip()
    if not s or 'linear' in s.lower():
        return 0
    return s.count(' & ') + 1


def _split_rule_clauses(rule_str: str) -> list[str]:
    return [p.strip() for p in str(rule_str).split(' & ') if p.strip()]


def _parse_rule_clause(clause: str, feature_names: list) -> tuple[str, str, float]:
    clause = clause.strip()
    for feat in sorted(feature_names, key=len, reverse=True):
        if clause.startswith(feat):
            rest = clause[len(feat):].strip()
            for op in ('<=', '>=', '<', '>'):
                if rest.startswith(op):
                    return feat, op, float(rest[len(op):].strip())
    raise ValueError(f'Cannot parse rule clause: {clause}')


def _feature_values_1d(X_df: pd.DataFrame, feat: str) -> np.ndarray:
    """Single feature column as 1d float array (handles duplicate column names)."""
    if feat not in X_df.columns:
        raise KeyError(feat)
    col = X_df[feat]
    if isinstance(col, pd.DataFrame):
        col = col.iloc[:, 0]
    return pd.to_numeric(col, errors='coerce').to_numpy(dtype=float, copy=False)


def _clause_mask(X_df: pd.DataFrame, clause: str, feature_names: list) -> np.ndarray:
    feat, op, val = _parse_rule_clause(clause, feature_names)
    x = _feature_values_1d(X_df, feat)
    if op == '<=':
        m = x <= val
    elif op == '<':
        m = x < val
    elif op == '>=':
        m = x >= val
    else:
        m = x > val
    return np.asarray(m, dtype=bool) & np.isfinite(x)


def _rule_endorsement_mask(X_df: pd.DataFrame, rule_str: str, feature_names: list) -> np.ndarray:
    mask = np.ones(len(X_df), dtype=bool)
    for clause in _split_rule_clauses(rule_str):
        mask &= _clause_mask(X_df, clause, feature_names)
    return mask


def _rulefit_logrank_p(y: np.ndarray, mask: np.ndarray, horizon_days: float) -> float:
    """Log-rank test: endorsers (mask=True) vs non-endorsers at fixed follow-up."""
    from lifelines.statistics import logrank_test
    y = np.asarray(y).ravel().astype(int)
    mask = np.asarray(mask).ravel().astype(bool)
    n1, n0 = int(mask.sum()), int((~mask).sum())
    if n1 < 5 or n0 < 5 or y[mask].sum() < 1 or y[~mask].sum() < 1:
        return np.nan
    T = np.full(len(y), horizon_days, dtype=float)
    res = logrank_test(
        T[mask], T[~mask],
        event_observed_A=y[mask], event_observed_B=y[~mask],
    )
    return float(res.p_value)


def _rulefit_direction(y: np.ndarray, mask: np.ndarray) -> str:
    y = np.asarray(y).ravel().astype(float)
    mask = np.asarray(mask).ravel().astype(bool)
    if mask.sum() == 0 or (~mask).sum() == 0:
        return 'unknown'
    return 'increasing' if y[mask].mean() > y[~mask].mean() else 'decreasing'


def _fmt_logrank_p(p: float) -> str:
    """
    Sepsis-paper Table 2 style: 3.29E−14, 1.29E−09 (2-digit mantissa, padded exponent);
    mid-range p as 0.004001 / 0.000421 (trailing zeros kept). '0' only if p == 0.
    """
    import re
    if not np.isfinite(p):
        return 'NA'
    if p == 0.0:
        return '0'
    if p < 1e-3:
        s = f'{p:.2E}'
        m = re.match(r'^([\d.]+)E([+-])(\d+)$', s)
        if m:
            mant, sign, exp = m.group(1), m.group(2), m.group(3)
            u_sign = '−' if sign == '-' else '+'
            return f'{mant}E{u_sign}{exp.zfill(2)}'
        return s.replace('E-', 'E−').replace('e-', 'E−')
    return f'{p:.4f}'


def _rule_passes_table2_filter(
    full_p: float,
    clause_ps: list[float],
    support: float,
) -> bool:
    if not np.isfinite(full_p) or full_p >= rulefit_table2_logrank_alpha:
        return False
    if support < rulefit_support_min or support > rulefit_support_max:
        return False
    if rulefit_table2_require_decomposition and clause_ps:
        if not all(np.isfinite(cp) and cp > full_p for cp in clause_ps):
            return False
    return True


def build_rulefit_table2(
    rules_df: pd.DataFrame,
    X_df: pd.DataFrame,
    y: np.ndarray,
    feature_names: list,
    years: int,
    benchmark: str,
) -> pd.DataFrame:
    """
    Sepsis-paper Table 2: top rules with log-rank p (full rule + decomposition).
    Survival setup: fixed horizon (years*365 days), event=1-year death.
    Analysis cohort: training patients (no ROS) for support and log-rank.
    """
    horizon = float(years * 365)
    y = np.asarray(y).ravel().astype(int)
    candidates = rules_df[rules_df['type'] == 'rule'].copy()
    if 'n_conditions' not in candidates.columns:
        candidates['n_conditions'] = candidates['rule'].map(_rule_condition_count)
    candidates = candidates[candidates['n_conditions'] <= rulefit_max_rule_conditions]
    candidates = candidates.sort_values('importance', ascending=False)

    scored = []
    for _, row in candidates.iterrows():
        rule_str = str(row['rule'])
        try:
            mask = _rule_endorsement_mask(X_df, rule_str, feature_names)
        except (ValueError, KeyError, TypeError):
            continue
        support = float(mask.mean())
        full_p = _rulefit_logrank_p(y, mask, horizon)
        direction = _rulefit_direction(y, mask)
        clauses = _split_rule_clauses(rule_str)
        clause_ps = []
        clause_rows = []
        for clause in clauses:
            try:
                cm = _clause_mask(X_df, clause, feature_names)
                cp = _rulefit_logrank_p(y, cm, horizon)
            except (ValueError, KeyError):
                cp = np.nan
            clause_ps.append(cp)
            clause_rows.append({'clause': clause, 'logrank_p': cp})
        if not _rule_passes_table2_filter(full_p, clause_ps, support):
            continue
        scored.append({
            'rule': rule_str,
            'coef': row['coef'],
            'importance': row['importance'],
            'support': support,
            'support_n': int(mask.sum()),
            'direction': direction,
            'full_logrank_p': full_p,
            'clauses': clause_rows,
        })

    scored.sort(key=lambda r: r['importance'], reverse=True)
    scored = scored[:rulefit_table2_top_n]

    rows = []
    for rank, item in enumerate(scored, start=1):
        n_sup = item['support_n']
        sup_pct = int(round(100 * item['support']))
        # Paper style: leading number = |support set| (patients endorsing rule), not table rank
        header = f"{n_sup}(support={sup_pct}%,direction={item['direction']})"
        rows.append({
            'rule_rank': rank,
            'support_n': n_sup,
            'row_type': 'composite',
            'rule': header,
            'support': item['support'],
            'direction': item['direction'],
            'logrank_p': item['full_logrank_p'],
            'logrank_p_fmt': _fmt_logrank_p(item['full_logrank_p']),
            'coef': item['coef'],
            'importance': item['importance'],
        })
        for cr in item['clauses']:
            rows.append({
                'rule_rank': rank,
                'support_n': n_sup,
                'row_type': 'component',
                'rule': cr['clause'],
                'support': np.nan,
                'direction': '',
                'logrank_p': cr['logrank_p'],
                'logrank_p_fmt': _fmt_logrank_p(cr['logrank_p']),
                'coef': np.nan,
                'importance': np.nan,
            })

    out_df = pd.DataFrame(rows)
    os.makedirs(f'../results/{years}YEAR', exist_ok=True)
    stem = f'../results/{years}YEAR/rulefit_table2_{benchmark}'
    out_df.to_csv(f'{stem}.csv', index=False)

    filtered_path = f'../results/{years}YEAR/rulefit_table2_filtered_{benchmark}.csv'
    pd.DataFrame([{
        'rule': s['rule'], 'support_n': s['support_n'], 'support': s['support'],
        'direction': s['direction'], 'full_logrank_p': s['full_logrank_p'],
        'coef': s['coef'], 'importance': s['importance'], 'n_clauses': len(s['clauses']),
    } for s in scored]).to_csv(filtered_path, index=False)

    return out_df


def print_rulefit_table2(table2_df: pd.DataFrame, years: int, benchmark: str):
    """Print manuscript-style Table 2 to console."""
    if table2_df.empty:
        print('  No rules passed Table 2 filter (log-rank + decomposition).', flush=True)
        return
    _rulefit_banner(
        'PRIMARY',
        f'Table 2 — top RuleFit rules ({rulefit_table2_top_n} max, sepsis-paper format)',
        'Main manuscript table: composite rule + decomposition; log-rank on train cohort.',
    )
    stem = f'../results/{years}YEAR/rulefit_table2_{benchmark}'
    print(f"  Files: {stem}.csv, results/{years}YEAR/rulefit_table2_filtered_{benchmark}.csv")
    print(f"  Filter: full-rule log-rank p < {rulefit_table2_logrank_alpha}", end='')
    if rulefit_table2_require_decomposition:
        print('; full p < each component p (decomposition).', flush=True)
    else:
        print('.', flush=True)
    print(f"  Cohort: training set (no ROS); fixed {years}-year horizon; event=death.\n")
    w_rule, w_p = 52, 14
    print(f"  {'Rules':<{w_rule}}  {'P value (log rank)':>{w_p}}")
    print(f"  {'-' * w_rule}  {'-' * w_p}")
    for _, row in table2_df.iterrows():
        print(f"  {row['rule']:<{w_rule}}  {row['logrank_p_fmt']:>{w_p}}")


def _make_rulefit_tree_generator(n_train: int, seed: int, verbose: bool = True):
    """GBDT used inside RuleFit; caps rule length via max_depth and min leaf size."""
    from sklearn.ensemble import GradientBoostingClassifier
    n_est = rulefit_n_estimators if rulefit_fast_mode else max(
        10, int(np.ceil(rulefit_max_rules / max(rulefit_tree_size, 1))),
    )
    min_leaf = _rulefit_min_samples_leaf(n_train)
    max_depth = int(rulefit_max_rule_conditions)
    if verbose:
        print(f"  GBDT max_depth={max_depth} (≤{rulefit_max_rule_conditions} AND-clauses per rule), "
              f"min_samples_leaf={min_leaf} ({rulefit_min_leaf_frac:.0%} of n_train={n_train})",
              flush=True)
    return GradientBoostingClassifier(
        n_estimators=n_est,
        max_depth=max_depth,
        max_leaf_nodes=rulefit_tree_size,
        min_samples_leaf=min_leaf,
        learning_rate=0.1,
        subsample=0.5 if rulefit_fast_mode else 1.0,
        random_state=seed,
    )


# Step 1: Load data
if analyze_full_data:
    X = pd.read_csv('../datasets/{}YEAR/TXP_data_{}_imputed_full.csv'.format(YEARS, benchmark_choice))
    y = pd.read_csv('../datasets/{}YEAR/TXP_label_{}_full.csv'.format(YEARS, benchmark_choice)).squeeze()
else:
    X = pd.read_csv('../datasets/{}YEAR/TXP_data_{}_imputed.csv'.format(YEARS, benchmark_choice))
    y = pd.read_csv('../datasets/{}YEAR/TXP_label_{}.csv'.format(YEARS, benchmark_choice)).squeeze()
    if not expand_var_set:
        X = X.drop(columns=expanded_vars, errors="ignore")

if not analyze_full_data:
    X = X.drop(columns=txp_era_year_vars, errors="ignore")

y = y.map({1: 0, 0: 1})  # for mortality rate prediction
print(X.shape)
print(len(y[y==0]))
print(len(y[y==1]))
print(len(y[y==1])/len(X))

X_raw = X.copy()  # original CSV scale — used by RuleFit when rulefit_use_raw_features=True
latest_era_mask_all = _latest_era_mask_from_raw(X_raw)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
X = sm.add_constant(X, has_constant='add')

metrics = {model_name: {'Accuracy': [], 'Precision': [], 'True Positives (TP)': [], 'False Positive (FP)': [],
                        'False Negative (FN)': [], 'True Negative (TN)': [],
                        'F1 Score': [], 'Balanced Accuracy': [], 'AUC': [], 'Brier Score': [],
                        }
           for model_name in models_to_test}

if 'Logistic' in models_to_test:
    # Used for evaluate(): add a new metric bucket for the sig-only refit
    metrics['Logistic_sigonly'] = {k: [] for k in metrics['Logistic'].keys()}

for seed in range(num_runs):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)
    X_calib, X_test, y_calib, y_test = train_test_split(X_test, y_test, test_size=0.33, random_state=seed)
    X_train_index = X_train.index
    X_calib_index = X_calib.index
    X_test_index = X_test.index
    X_train_base, y_train_base = X_train.copy(), y_train.copy()
    latest_era_test_mask = (
        latest_era_mask_all.loc[X_test.index].to_numpy(dtype=bool)
        if latest_era_mask_all is not None else None
    )

    counter = Counter(y_train)
    scale = counter[0] / counter[1] if DB else 1

    if 'Logistic' in models_to_test:
        if hp_search:
            param_file = '../checkpoints/{}YEAR/best_params_{}_{}.json'.format(YEARS, benchmark_choice, 'Linear')
            model = LogisticRegression(max_iter=10000, random_state=0, solver='saga', n_jobs=-1)

            # Define the parameter grid to include elastic net and no regularization
            # param_grid = [
            #     {'penalty': ['elasticnet'], 'C': [0.001, 0.01, 0.1], 'l1_ratio': [0.5]},
            #     {'penalty': ['l2'], 'C': [0.1, 1]}   # 'C' value is ignored when penalty='none'
            # ]
            # for ours only
            param_grid = [
                {'penalty': ['elasticnet'], 'C': [0.01], 'l1_ratio': [0.75]},
            ]

            # Grid search for best hyperparameters on the validation set
            grid_search = GridSearchCV(model, param_grid, cv=5, scoring='roc_auc', n_jobs=-1)
            grid_search.fit(X_train, y_train)

            # Best model
            best_model = grid_search.best_estimator_
            print(f"Best parameters: {grid_search.best_params_}")

            # Get coefficients and intercept
            coefficients = best_model.coef_
            intercept = best_model.intercept_
            print("Coefficients for each feature:\n", coefficients)
            print("Intercept:\n", intercept)

            y_pred_test = best_model.predict_proba(X_test)[:, 1]
            evaluate('Logistic', y_test, y_pred_test, save=False)

            # Save the best parameters to the file
            with open(param_file, 'w') as file:
                json.dump(grid_search.best_params_, file)
            print(f"Best parameters saved to {param_file}")


        logit_model = LogisticRegression(
            solver='saga',
            penalty='elasticnet',
            l1_ratio=0.5,  # 0 = pure L2, 1 = pure L1, 0.5 = 50/50 mix
            C=1 / 200.0,
            # max_iter=100000,
            random_state=seed,
            n_jobs=-1,
            class_weight={0: 1, 1: counter[0]/counter[1]} if DB else {0: 1, 1: 1}
        )

        if use_ros:
            print(f"  Logistic train: ROS on (sampling_strategy={ros_sampling_strategy})", flush=True)
            X_train_lr, y_train_lr = _ros_fit_resample(
                X_train_base, y_train_base,
                sampling_strategy=ros_sampling_strategy,
                random_state=seed,
            )
        else:
            print("  Logistic train: ROS off (natural prevalence)", flush=True)
            X_train_lr, y_train_lr = X_train_base, y_train_base
        if hasattr(y_train_lr, 'value_counts'):
            print(y_train_lr.value_counts())
        else:
            print(pd.Series(y_train_lr).value_counts())
        logit_model.fit(X_train_lr, y_train_lr)
        
        # Get raw predictions before any calibration
        y_pred_prob = prob_test = logit_model.predict_proba(X_test)[:, 1]

        model_file = '../checkpoints/{}YEAR/logit_model_{}.pkl'.format(YEARS, benchmark_choice)

        # Initialize calibrator variable
        logit_calibrator = None

        if calibrated:
            # prob_uncal = logit_model.predict_proba(X_calib)[:, 1]
            # iso_reg = IsotonicRegression(out_of_bounds='clip')
            # iso_reg.fit(prob_uncal, y_calib)
            # y_pred_prob = logit_model.predict_proba(X_test)[:, 1]
            # y_pred_prob = iso_reg.transform(y_pred_prob)

            # Step 1: get uncalibrated probabilities from the base model
            prob_uncal = logit_model.predict_proba(X_calib)[:, 1]
            # Step 2: convert to logits (avoid 0 or 1 issues)
            eps = 1e-15
            logits_uncal = np.log(prob_uncal + eps) - np.log(1 - prob_uncal + eps)
            # Step 3: fit a simple logistic regression on these logits
            platt_reg = LogisticRegression(solver='saga')
            platt_reg.fit(logits_uncal.reshape(-1, 1), y_calib)
            # Step 4: apply to test set
            prob_test = logit_model.predict_proba(X_test)[:, 1]
            logits_test = np.log(prob_test + eps) - np.log(1 - prob_test + eps)
            y_pred_prob = platt_reg.predict_proba(logits_test.reshape(-1, 1))[:, 1]
            logit_calibrator = platt_reg  # Save calibrator for model saving
            
            # === Recalibration Visualization for Logistic Regression ===
            print("\n=== Logistic Regression Recalibration Analysis ===")
            
            # Get raw predictions and calibrated predictions
            raw_probs = prob_test  # Raw logistic regression probabilities
            calibrated_probs = y_pred_prob  # Calibrated probabilities
            
            # Create before/after recalibration plot
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
            
            # Plot 1: Raw vs Calibrated probabilities scatter
            ax1.scatter(raw_probs, calibrated_probs, alpha=0.6, s=20)
            ax1.plot([0, 1], [0, 1], 'r--', label='Perfect Calibration')
            ax1.set_xlabel('Raw Logistic Regression Probability')
            ax1.set_ylabel('Calibrated Probability')
            ax1.set_title('Raw vs Calibrated Probabilities (Logistic Regression)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Distribution of raw probabilities
            ax2.hist(raw_probs, bins=50, alpha=0.7, color='blue', edgecolor='black')
            ax2.set_xlabel('Raw Logistic Regression Probability')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Distribution of Raw Probabilities')
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Distribution of calibrated probabilities
            ax3.hist(calibrated_probs, bins=50, alpha=0.7, color='green', edgecolor='black')
            ax3.set_xlabel('Calibrated Probability')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Distribution of Calibrated Probabilities')
            ax3.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f'../images/logistic_recalibration_analysis_{YEARS}Y.png', dpi=300, bbox_inches='tight')
            # plt.show()
            
            # Print statistics
            print(f"Raw probabilities - Mean: {raw_probs.mean():.4f}, Std: {raw_probs.std():.4f}")
            print(f"Calibrated probabilities - Mean: {calibrated_probs.mean():.4f}, Std: {calibrated_probs.std():.4f}")
            print(f"Correlation between raw and calibrated: {np.corrcoef(raw_probs, calibrated_probs)[0,1]:.4f}")
            
            # === Step-by-step calculation examples ===
            print("\n=== Step-by-step Recalibration Calculation Examples ===")
            
            # Select 2 samples with different raw probabilities
            sample_indices = [0, 1]  # First two samples
            
            for i, sample_idx in enumerate(sample_indices):
                print(f"\n--- Sample {i+1} (Index {sample_idx}) ---")
                
                # Follow the exact same steps as the code
                # Step 1: Raw logistic regression probability (from test set)
                raw_prob = prob_test[sample_idx]
                print(f"Step 1 - Raw LR probability (test): {raw_prob:.6f}")
                
                # Step 2: Convert to logits (exactly as in code)
                logit_test = np.log(raw_prob + eps) - np.log(1 - raw_prob + eps)
                print(f"Step 2 - Convert to logits: log({raw_prob:.6f} + {eps}) - log(1 - {raw_prob:.6f} + {eps}) = {logit_test:.6f}")
                
                # Step 3: Apply Platt scaling (exactly as in code)
                logit_input = logit_test.reshape(-1, 1)
                calibrated_prob = platt_reg.predict_proba(logit_input)[0, 1]
                print(f"Step 3 - Apply Platt scaling: platt_reg.predict_proba([[{logit_test:.6f}]]) = {calibrated_prob:.6f}")
                
                # Show the internal Platt scaling calculation
                platt_coef = platt_reg.coef_[0][0]
                platt_intercept = platt_reg.intercept_[0]
                platt_logit = platt_intercept + platt_coef * logit_test
                manual_calibrated = 1 / (1 + np.exp(-platt_logit))
                
                print(f"Step 3a - Platt coefficients: intercept={platt_intercept:.6f}, coef={platt_coef:.6f}")
                print(f"Step 3b - Platt logit: {platt_intercept:.6f} + {platt_coef:.6f} * {logit_test:.6f} = {platt_logit:.6f}")
                print(f"Step 3c - Manual calculation: 1/(1+exp(-{platt_logit:.6f})) = {manual_calibrated:.6f}")
                print(f"Step 3d - Verification: sklearn={calibrated_prob:.6f}, manual={manual_calibrated:.6f}")
                
                # Show the transformation
                reduction_factor = calibrated_prob / raw_prob
                print(f"Final transformation: {raw_prob:.6f} → {calibrated_prob:.6f} (reduction factor: {reduction_factor:.4f})")
            
            # Show transformation for high probability cases
            high_prob_mask = raw_probs > 0.5
            if high_prob_mask.sum() > 0:
                print(f"\nHigh probability cases (raw > 0.5): {high_prob_mask.sum()}")
                print(f"Raw mean for high prob cases: {raw_probs[high_prob_mask].mean():.4f}")
                print(f"Calibrated mean for high prob cases: {calibrated_probs[high_prob_mask].mean():.4f}")
                print(f"Reduction factor: {calibrated_probs[high_prob_mask].mean() / raw_probs[high_prob_mask].mean():.4f}")
            
            # Show transformation for very high probability cases
            very_high_prob_mask = raw_probs > 0.7
            if very_high_prob_mask.sum() > 0:
                print(f"\nVery high probability cases (raw > 0.7): {very_high_prob_mask.sum()}")
                print(f"Raw mean for very high prob cases: {raw_probs[very_high_prob_mask].mean():.4f}")
                print(f"Calibrated mean for very high prob cases: {calibrated_probs[very_high_prob_mask].mean():.4f}")
                print(f"Reduction factor: {calibrated_probs[very_high_prob_mask].mean() / raw_probs[very_high_prob_mask].mean():.4f}")

            import numpy as np

            eps = 1e-15
            p_uncal = 0.8
            logit_uncal = np.log(p_uncal + eps) - np.log(1 - p_uncal + eps)

            # Assume your fitted platt_reg exists
            p_calibrated = platt_reg.predict_proba([[logit_uncal]])[0, 1]

            print(f"Uncalibrated p = {p_uncal:.3f}, logit = {logit_uncal:.3f}, calibrated p = {p_calibrated:.3f}")

            # Coefficients (for each feature)
            print("Coefficients:", platt_reg.coef_)

            # Intercept (bias term)
            print("Intercept:", platt_reg.intercept_)

            # Predicted probabilities
            x_vals = np.linspace(-10, 10, 200)
            probs = platt_reg.predict_proba(x_vals.reshape(-1, 1))[:, 1]

            # Plot
            plt.figure(figsize=(7, 5))
            plt.plot(x_vals, probs, label="Predicted P(y=1|x)", linewidth=2)
            plt.axvline(0, color='gray', linestyle='--', label="Decision boundary")
            plt.title("Logistic Regression: Input vs Output Probability")
            plt.xlabel("Input feature x")
            plt.ylabel("Predicted Probability P(y=1|x)")
            plt.legend()
            plt.grid(True)
            # plt.show()

        # Pass raw predictions for comparison plotting
        y_pred_raw = prob_test if calibrated else None
        metrics = evaluate('Logistic', 'TXP', benchmark_choice, metrics,
                           y_test, y_pred_prob, y_pred_raw, True)
        metrics = _eval_on_latest_era(
            metrics, 'Logistic', y_test, y_pred_prob, y_pred_raw, latest_era_test_mask,
        )
        # evaluate('Logistic', y_test, y_pred_prob, y_pred_raw=prob_test if calibrated else None)
        
        # Save model (on last seed iteration)
        if seed == num_runs - 1:
            feature_names = X.columns.tolist()  # Includes 'const' column
            save_model(logit_model, feature_names, scaler, f'logit_txp_{YEARS}yr_{benchmark_choice}',
                       calibrator=logit_calibrator)

        if os.path.exists(model_file) and load_summary:
            logit_summary = joblib.load(model_file)
        else:
            logit_summary = sm.Logit(y_train_lr, X_train_lr).fit_regularized(alpha=20)  # use hp in json
            joblib.dump(logit_summary, model_file)

        # Raw (pre-FDR) p is printed once below for comparison; tables also store raw p + FDR q.
        logit_inference = sm.Logit(y_train_lr, X_train_lr).fit(disp=False)

        _raw_p = pd.Series(
            logit_inference.pvalues.to_numpy(dtype=float),
            index=logit_inference.params.index,
            dtype=float,
        )
        _covar_mask = pd.Series(_raw_p.index != "const", index=_raw_p.index)
        # multipletests: any NaN in the input → all FDR q become NaN. Exclude non-finite p.
        _finite = _covar_mask & _raw_p.notna() & np.isfinite(_raw_p.to_numpy(dtype=float))
        _p_fdr = pd.Series(np.nan, index=_raw_p.index, dtype=float)
        if int(_finite.sum()) > 0:
            _p_fdr.loc[_finite] = multipletests(
                _raw_p.loc[_finite].to_numpy(dtype=float),
                alpha=logistic_significance_p_threshold,
                method="fdr_bh",
            )[1]

        thr = logistic_significance_p_threshold
        _raw_sig = (_raw_p <= thr) & _covar_mask
        _fdr_sig = (_p_fdr <= thr) & _finite
        lost_sig = _raw_p.index[_raw_sig & _finite & ~_fdr_sig].tolist()
        gained_sig = _raw_p.index[~_raw_sig & _fdr_sig].tolist()
        nan_p_vars = _raw_p.index[_covar_mask & ~_finite].tolist()

        print("\n[Logistic FDR] pre- vs post-adjustment significance "
              f"(threshold={thr}):", flush=True)
        print(
            f"  raw significant: {int(_raw_sig.sum())}  |  "
            f"FDR significant: {int(_fdr_sig.sum())}  |  "
            f"non-finite raw p excluded from FDR: {len(nan_p_vars)}",
            flush=True,
        )
        if nan_p_vars:
            print(
                "  Covariates with non-finite raw p (skipped in FDR family):",
                flush=True,
            )
            for v in nan_p_vars:
                print(f"    - {v}: raw p={_raw_p[v]}", flush=True)
        if lost_sig:
            print("  Lost significance after FDR (raw sig → FDR non-sig):", flush=True)
            for v in lost_sig:
                print(
                    f"    - {v}: raw p={format_value(float(_raw_p[v]))}, "
                    f"FDR q={format_value(float(_p_fdr[v]))}",
                    flush=True,
                )
        else:
            print("  Lost significance after FDR: (none)", flush=True)
        if gained_sig:
            print("  Gained significance after FDR (raw non-sig → FDR sig):", flush=True)
            for v in gained_sig:
                print(
                    f"    - {v}: raw p={format_value(float(_raw_p[v]))}, "
                    f"FDR q={format_value(float(_p_fdr[v]))}",
                    flush=True,
                )
        else:
            print("  Gained significance after FDR: (none)", flush=True)

        # OR/CI/raw p from the SAME unregularized MLE (logit_inference).
        # Regularized fit (logit_summary) is for prediction only — mixing it with
        # inference p makes CI-cross-null disagree with p (e.g. BMI/weight).
        model_info = logit_inference.summary2().tables[0]
        # Do not reuse name `scale` — that holds class-imbalance ratio for XGB scale_pos_weight.
        feature_scale = pd.Series(scaler.scale_, index=[c for c in X.columns if c != 'const'])
        coefficients, _ = model_summary(
            logit_inference, logistic_significance_p_threshold, scale=feature_scale, ratio_label='OR',
        )

        raw_by_var = _raw_p
        fdr_by_var = _p_fdr
        ci_col = [c for c in coefficients.columns if '95' in c and 'CI' in c][0]

        def _fmt_p(var: str, series: pd.Series) -> str:
            if var == "const" or var not in series.index or pd.isna(series.loc[var]):
                return "NA"
            return format_value(float(series.loc[var]))

        coefficients = coefficients.copy()
        coefficients["P-value"] = coefficients["Variable"].map(lambda v: _fmt_p(v, raw_by_var))
        coefficients["FDR q"] = coefficients["Variable"].map(lambda v: _fmt_p(v, fdr_by_var))
        # Stable column order for CSVs / LaTeX
        coefficients = coefficients[["Variable", ci_col, "P-value", "FDR q"]]

        # Significant set = FDR q <= threshold; drop intercept
        sig_mask = coefficients["Variable"].map(
            lambda v: (
                v != "const"
                and v in fdr_by_var.index
                and pd.notna(fdr_by_var.loc[v])
                and float(fdr_by_var.loc[v]) <= thr
            )
        )
        significant_coefs = coefficients.loc[sig_mask].copy()

        # Persist tables only once to keep outputs stable / non-spammy
        if seed == 0:
            coefficients.to_csv('../results/{}YEAR/multivariate_results.csv'.format(YEARS))
            significant_coefs.to_csv('../results/{}YEAR/significant_multivariate_results.csv'.format(YEARS))

            grouped_significant_coefs = create_summary_table_grouped(significant_coefs, variable_name_groups)
            print(grouped_significant_coefs.to_latex(index=False, escape=False))

        # --- Dynamic sig-only refit + evaluate (no helpers preset; per-seed true sig vars) ---
        if 'Logistic_sigonly' in metrics:
            sig_vars = [
                v for v in significant_coefs['Variable'].tolist()
                if v in X_train_lr.columns and v != 'const'
            ]
            keep_cols = ['const'] + sig_vars  # always keep intercept

            # Defensive: ensure all keep_cols exist (should, but helps if naming drift happens)
            keep_cols = [c for c in keep_cols if c in X_train_lr.columns]
            if len(keep_cols) == 0:
                keep_cols = ['const'] if 'const' in X_train_lr.columns else X_train_lr.columns.tolist()

            X_train_sig = X_train_lr[keep_cols]
            X_test_sig = X_test[keep_cols]
            X_calib_sig = X_calib[keep_cols]

            # Refit using the same regularization strength
            try:
                logit_sigonly_summary = sm.Logit(y_train_lr, X_train_sig).fit_regularized(alpha=20)

                eps = 1e-15
                prob_test_sigonly_raw = np.asarray(logit_sigonly_summary.predict(X_test_sig), dtype=float)

                platt_reg_sigonly = None
                if calibrated:
                    prob_uncal_calib = np.asarray(logit_sigonly_summary.predict(X_calib_sig), dtype=float)
                    logits_uncal_calib = np.log(prob_uncal_calib + eps) - np.log(1 - prob_uncal_calib + eps)

                    platt_reg_sigonly = LogisticRegression(solver='saga', max_iter=10000)
                    platt_reg_sigonly.fit(logits_uncal_calib.reshape(-1, 1), y_calib)

                    logits_test_sigonly = np.log(prob_test_sigonly_raw + eps) - np.log(
                        1 - prob_test_sigonly_raw + eps
                    )
                    prob_test_sigonly = platt_reg_sigonly.predict_proba(
                        logits_test_sigonly.reshape(-1, 1)
                    )[:, 1]
                    y_pred_sigonly = prob_test_sigonly
                    y_pred_raw_sigonly = prob_test_sigonly_raw
                else:
                    y_pred_sigonly = prob_test_sigonly_raw
                    y_pred_raw_sigonly = None

                metrics = evaluate(
                    'Logistic_sigonly', 'TXP', benchmark_choice, metrics,
                    y_test, y_pred_sigonly, y_pred_raw=y_pred_raw_sigonly,
                    save=True, save_plots=False,
                )
                metrics = _eval_on_latest_era(
                    metrics, 'Logistic_sigonly', y_test, y_pred_sigonly,
                    y_pred_raw_sigonly, latest_era_test_mask,
                )
            except Exception as e:
                print(f"[Logistic sig-only] failed seed={seed}: {e}", flush=True)

    if 'XGBoost' in models_to_test:
        # Convert the datasets into DMatrix, which is a high-performance XGBoost data structure
        dtrain = xgb.DMatrix(X_train_base, label=y_train_base)
        dtest = xgb.DMatrix(X_test, label=y_test)
        best_score = -1
        best_params = None

        if hp_search:
            for params in ParameterGrid({
                'max_depth': [0, 1, 3, 6],
                'eta': [0.03, 0.1, 0.3],
                'subsample': [0.8, 0.9],
                'colsample_bytree': [0.8, 0.9],
            }):
                model = xgb.XGBClassifier(eval_metric='auc', **params)
                model.fit(X_train_base, y_train_base)
                y_pred = model.predict_proba(X_test)[:, 1]
                auc = roc_auc_score(y_test, y_pred)

                if auc > best_score:
                    best_score = auc
                    best_params = params

            print("Best AUC:", best_score)
            print("Best params:", best_params)

        else:
            model_file = '../checkpoints/{}YEAR/XGBoost_model_{}.pkl'.format(YEARS, benchmark_choice)

            # Prepare model using sklearn API
            xgb_model = XGBClassifier(
                objective='binary:logistic',
                eval_metric='auc',
                max_depth=3,
                learning_rate=0.1,  # same as eta
                subsample=0.8,
                colsample_bytree=0.8,
                n_estimators=100,  # equivalent to num_boost_round
                scale_pos_weight=scale,  # <-- This addresses imbalance
                random_state=seed
            )

            ros = RandomOverSampler(sampling_strategy=ros_sampling_strategy)
            steps = [('ros', ros), ('xgb', xgb_model)] if use_ros else [('xgb', xgb_model)]
            if use_ros:
                print(f"  XGBoost train: ROS on (sampling_strategy={ros_sampling_strategy})", flush=True)
            else:
                print("  XGBoost train: ROS off (natural prevalence)", flush=True)
            pipe = Pipeline(steps=steps)
            pipe.fit(X_train_base, y_train_base)
            # xgb_model.fit(X_train, y_train)
            
            # Get raw predictions before any calibration
            y_pred_prob_xgb = prob_test_xgb = xgb_model.predict_proba(X_test)[:, 1]

            # Initialize calibrator variable
            xgb_calibrator = None

            if calibrated:
                # # Calibrated version
                # xgb_model = CalibratedClassifierCV(
                #     estimator=xgb_model,
                #     method='isotonic',  # 'isotonic' or 'sigmoid'
                #     cv=5
                # )

                prob_uncal = xgb_model.predict_proba(X_calib)[:, 1]
                iso_reg = IsotonicRegression(out_of_bounds='clip')
                iso_reg.fit(prob_uncal, y_calib)
                prob_test_xgb = xgb_model.predict_proba(X_test)[:, 1]
                y_pred_prob_xgb = iso_reg.transform(prob_test_xgb)
                xgb_calibrator = iso_reg  # Save calibrator for model saving

                # # avoid log(0)
                # eps = 1e-15
                # prob_uncal = xgb_model.predict_proba(X_calib)[:, 1]
                # logits_uncal = np.log(prob_uncal + eps) - np.log(1 - prob_uncal + eps)
                # # Fit a small logistic regression (Platt scaling)
                # platt_reg = LogisticRegression(solver='saga')
                # platt_reg.fit(logits_uncal.reshape(-1, 1), y_calib)
                # prob_test_uncal = xgb_model.predict_proba(X_test)[:, 1]
                # logits_test = np.log(prob_test_uncal + eps) - np.log(1 - prob_test_uncal + eps)
                # y_pred_prob_xgb = platt_reg.predict_proba(logits_test.reshape(-1, 1))[:, 1]
                # xgb_calibrator = platt_reg  # If using Platt scaling instead

            # Pass raw predictions for comparison plotting
            y_pred_raw = prob_test_xgb if calibrated else None
            metrics = evaluate('XGBoost', 'TXP', benchmark_choice, metrics,
                               y_test, y_pred_prob_xgb, y_pred_raw, True)
            metrics = _eval_on_latest_era(
                metrics, 'XGBoost', y_test, y_pred_prob_xgb, y_pred_raw, latest_era_test_mask,
            )
            
            # Save model (on last seed iteration)
            if seed == num_runs - 1:
                feature_names = X.columns.tolist()  # Includes 'const' column
                save_model(xgb_model, feature_names, scaler, f'xgb_txp_{YEARS}yr_{benchmark_choice}',
                           calibrator=xgb_calibrator)

            # === Error cohort summarization (Correct vs Type I/II) ===
            # Use pre-scale X_raw (same row index as X/X_test), not a re-read CSV that
            # may be a different cohort (_full vs not) or force wrong iloc positions.
            X_raw_test = X_raw.loc[X_test.index]

            # Use provided significant variable list, filtered to available columns
            significant_vars = [v for v in SIGNIFICANT_VARS_OVERRIDE if v in X_raw_test.columns]
            if len(significant_vars) == 0:
                significant_vars = [c for c in X_raw_test.columns if c in X_test.columns][:30]

            summarize_errors_to_latex(
                X_raw_test=X_raw_test,
                y_test=y_test.reset_index(drop=True),
                y_pred_prob=y_pred_prob_xgb,
                significant_vars=significant_vars,
                years=YEARS,
                out_prefix=f'XGB_{benchmark_choice}'
            )
            # Train LR models on error cohorts to identify drivers of misclassification
            analyze_misclassification_logit(
                X_test=X_test,
                y_test=y_test.reset_index(drop=True),
                y_pred_prob=y_pred_prob_xgb,
                years=YEARS,
                out_prefix=f'XGB_{benchmark_choice}',
                significant_vars=significant_vars
            )
            # === End error cohort summarization ===

            joblib.dump(xgb_model, model_file)

        if seed == 0 and interpret:
            # from xgboost import plot_tree
            # plot_tree(xgb_model, num_trees=0)

            if 'importance' in XGBoost_plot:
                from sklearn.inspection import permutation_importance

                result = permutation_importance(
                    xgb_model, X_test, y_test,
                    n_repeats=10,
                    random_state=0,
                    scoring='roc_auc'
                )

                sorted_idx = np.argsort(result.importances_mean)[::-1]
                for i in sorted_idx:
                    print(f"{X_test.columns[i]}: "
                          f"Mean drop = {result.importances_mean[i]:.4f}, "
                          f"Std = {result.importances_std[i]:.4f}")

                # Plot the feature importance and extract the top k features
                xgb.plot_importance(xgb_model, max_num_features=topk)
                # plt.show()

                # Get the feature importance directly from the xgb_model
                importance = xgb_model.get_booster().get_score(importance_type='weight')

                # Convert the importance to a DataFrame
                importance_df = pd.DataFrame(importance.items(), columns=['Feature', 'Importance'])
                importance_df = importance_df.sort_values(by='Importance', ascending=False)

                # Get the top k features
                topk_features_by_importance = importance_df.head(topk)['Feature'].tolist()

                # Convert the test set to numpy array for SHAP calculations
                X_test_np = X_test.values

                # Create the SHAP explainer and calculate SHAP values
                explainer = shap.Explainer(xgb_model)
                shap_values = explainer(X_test_np, check_additivity=False)

                # Get the column indices for the top k features by XGBoost importance
                topk_feature_indices = [X_test.columns.get_loc(feature) for feature in topk_features_by_importance]
                # shap.summary_plot(shap_values[:, topk_feature_indices], features=X_test[topk_features_by_importance])

                lr_significant_features = significant_coefs['Variable'].tolist()
                topk_feature_indices = [X_test.columns.get_loc(feature) for feature in lr_significant_features]
                # shap.summary_plot(shap_values[:, topk_feature_indices], features=X_test[lr_significant_features])

                if 'local' in XGBoost_plot:
                    # Assume key variables are identified
                    key_variables = topk_features_by_importance

                    # Extract key variables from the test set
                    key_variable_data = X_test[key_variables]

                    # Calculate similarity (using cosine similarity here as an example)
                    similarity_matrix = cosine_similarity(key_variable_data)

                    # Let's assume you want to analyze a specific individual in the test set
                    target_index = 0  # Index of the individual you are analyzing
                    similar_indices = np.argsort(similarity_matrix[target_index])[::-1][
                                      1:11]  # Get top 10 similar patients

                    # Loop over the selected similar individuals
                    for i in similar_indices:
                        print(f"\nSHAP analysis for individual {i}:")
                        # Get the SHAP values for the selected individual
                        shap_values_individual = shap_values[i, topk_feature_indices]
                        # Ensure all arrays have the same length
                        data_individual = X_test.iloc[i, topk_feature_indices].values
                        
                        # Debug: Check array lengths
                        print(f"SHAP values length: {len(shap_values_individual)}")
                        print(f"Data length: {len(data_individual)}")
                        print(f"Feature names length: {len(topk_features_by_importance)}")
                        
                        # Ensure all arrays have the same length by truncating to the minimum length
                        min_length = min(len(shap_values_individual), len(data_individual), len(topk_features_by_importance))
                        shap_values_individual = shap_values_individual[:min_length]
                        data_individual = data_individual[:min_length]
                        feature_names_truncated = topk_features_by_importance[:min_length]
                        
                        print(f"Truncated to length: {min_length}")
                        
                        # Create explanation object with properly aligned arrays
                        explanation = shap.Explanation(
                            values=shap_values_individual,
                            base_values=shap_values.base_values[i],
                            data=data_individual,
                            feature_names=feature_names_truncated
                        )

                        fig, ax = plt.subplots(figsize=(30, 15))
                        plt.subplots_adjust(left=0.3, right=0.95, top=0.95, bottom=0.1)
                        shap.waterfall_plot(explanation, max_display=10, show=False)
                        plt.show()

                    # # List of indices for the individuals you want to analyze
                    # individual_indices = [0, 10, 20, 30, 40, 50]  # Replace with your desired indices
                    # # Loop over the selected individuals
                    # for i in individual_indices:
                    #     print(f"\nSHAP analysis for individual {i}:")
                    #     # Get the SHAP values for the selected individual
                    #     shap_values_individual = shap_values[i, topk_feature_indices]
                    #     shap.waterfall_plot(shap.Explanation(values=shap_values_individual,
                    #                                          base_values=shap_values.base_values[i],
                    #                                          data=X_test.iloc[i, topk_feature_indices],
                    #                                          feature_names=topk_features_by_importance))
                    #     plt.show()

            if 'magnitude' in XGBoost_plot:
                X_test_np = X_test.values
                explainer = shap.Explainer(xgb_model)
                shap_values = explainer(X_test_np, check_additivity=False)

                # Calculate the mean absolute SHAP value for each feature
                mean_shap_values = np.abs(shap_values.values).mean(axis=0)
                feature_names = X_test.columns

                # Create a DataFrame to hold the feature names and their mean SHAP values
                shap_importance = pd.DataFrame({
                    'Feature': feature_names,
                    'Mean Absolute SHAP Value': mean_shap_values
                })
                shap_importance = shap_importance.sort_values(by='Mean Absolute SHAP Value', ascending=False)
                topk_shap_importance = shap_importance.head(topk)
                topk_features = [X_test.columns.get_loc(var) for var in topk_shap_importance['Feature'].tolist()]
                shap.summary_plot(shap_values[:, topk_features], features=X_test[topk_shap_importance['Feature']])

            if 'partial' in XGBoost_plot:
                from sklearn.inspection import PartialDependenceDisplay
                # Analyze the interaction between two features and the effect of a single feature
                features = ['Patient height (cm)', 'Patient weight (kg)']
                # Plot the partial dependence
                PartialDependenceDisplay.from_estimator(xgb_model, X_test, features)

            if print_year_dist:
                # Extract year columns and calculate Mortality rate and patient count for each year
                year_columns = [
                    'Patient year of TXP_1988-1990',
                    'Patient year of TXP_1991-1995',
                    'Patient year of TXP_1996-2000',
                    'Patient year of TXP_2001-2005',
                    'Patient year of TXP_2006-2010',
                    'Patient year of TXP_2011-2015',
                    'Patient year of TXP_2016-2020',
                    'Patient year of TXP_2021-2023',
                ]

                Mortality_rates = []
                predicted_mortality_rates = []
                patient_counts = []

                for year_col in year_columns:
                    # Get the year from the column name and convert to integer
                    year = int(year_col.split('_')[-1].split('.')[0])

                    # Calculate Mortality rate and patient count for the current year
                    Mortality_rate = y[X[year_col] == 1].mean()
                    patient_count = X[year_col].sum()

                    Mortality_rates.append((year, Mortality_rate))
                    patient_counts.append((year, patient_count))

                    year_mask = X[year_col] == 1
                    dtest_year = xgb.DMatrix(X[year_mask], label=y[year_mask])

                    # Predict probabilities for the patients in the current year
                    y_pred_prob_year = xgb_model.predict(dtest_year)
                    print(y_pred_prob_year)
                    # Convert probabilities to binary outcomes (0 or 1)
                    y_pred_prob_year = (y_pred_prob_year > 0.5).astype(int)

                    # Calculate the mean predicted probability as the predicted mortality rate
                    predicted_mortality_rate = y_pred_prob_year.mean()
                    predicted_mortality_rates.append(
                        (int(year_col.split('_')[-1].split('.')[0]), predicted_mortality_rate))

                # Convert to DataFrame for plotting
                Mortality_df = pd.DataFrame(Mortality_rates, columns=['Year', 'Mortality Rate'])
                patient_count_df = pd.DataFrame(patient_counts, columns=['Year', 'Patient Count'])
                Predicted_Mortality_df = pd.DataFrame(predicted_mortality_rates,
                                                      columns=['Year', 'Predicted Mortality Rate'])

                # Plot the Mortality rate and patient count
                fig, ax1 = plt.subplots(figsize=(10, 6))

                # Plot Mortality rate (line plot)
                ax1.plot(Mortality_df['Year'], Mortality_df['Mortality Rate'], marker='o', color='blue', linestyle='-',
                         label='Actual Mortality Rate')

                # Plot Predicted Mortality rate (line plot)
                ax1.plot(Predicted_Mortality_df['Year'], Predicted_Mortality_df['Predicted Mortality Rate'], marker='o',
                         color='red', linestyle='--',
                         label='Predicted Mortality Rate')

                ax1.set_xlabel('Year of TXP')
                ax1.set_ylabel('Mortality Rate', color='blue')
                ax1.tick_params(axis='y', labelcolor='blue')

                # Set x-ticks to be integers
                ax1.set_xticks(Mortality_df['Year'])
                ax1.set_xticklabels(Mortality_df['Year'].astype(int), rotation=45)

                # Update legend
                ax1.legend(loc='upper left')

                # Create a second y-axis for the patient count
                ax2 = ax1.twinx()
                ax2.bar(patient_count_df['Year'], patient_count_df['Patient Count'], alpha=0.6, color='gray',
                        label='Patient Count')
                ax2.set_ylabel('Patient Count', color='gray')
                ax2.tick_params(axis='y', labelcolor='gray')

                # Title and layout
                plt.title('Mortality Rate and Patient Count by Year of Transplant (TXP)')
                fig.tight_layout()

                # Show the plot
                # plt.show()

    if 'RuleFit' in models_to_test:
        try:
            from rulefit import RuleFit
        except ImportError as e:
            raise ImportError(
                "RuleFit not installed. Run: pip install rulefit"
            ) from e

        from sklearn.ensemble import GradientBoostingClassifier

        _rulefit_banner(
            'SETUP',
            'Data & features for RuleFit',
            'Methods: curated predictors, raw clinical units, ROS if enabled; cite JSON feature list.',
        )
        if rulefit_use_raw_features:
            print("  Features: raw CSV scale (not StandardScaler).", flush=True)
        else:
            print("  Features: same scaling as Logistic/XGB.", flush=True)
        if use_ros:
            print(f"  RuleFit train: ROS on (sampling_strategy={ros_sampling_strategy})", flush=True)

        if not rulefit_use_raw_features:
            X_train_rf_src = X_train_base.drop(columns=['const'], errors='ignore')
            X_calib_rf_src = X_calib.drop(columns=['const'], errors='ignore')
            X_test_rf_src = X_test.drop(columns=['const'], errors='ignore')
        else:
            X_train_rf_src = X_raw.loc[X_train_index]
            X_calib_rf_src = X_raw.loc[X_calib_index]
            X_test_rf_src = X_raw.loc[X_test_index]

        X_train_rf_df, feature_cols_rf = _apply_rulefit_feature_list(X_train_rf_src, log=True)
        X_test_rf_df, _ = _apply_rulefit_feature_list(X_test_rf_src, log=False)
        X_calib_rf_df, _ = _apply_rulefit_feature_list(X_calib_rf_src, log=False)
        X_train_rf = X_train_rf_df.values.astype(np.float64)
        X_test_rf = X_test_rf_df.values.astype(np.float64)
        X_calib_rf = X_calib_rf_df.values.astype(np.float64)
        y_rf_train = np.asarray(y_train_base)

        os.makedirs(f'../results/{YEARS}YEAR', exist_ok=True)
        with open(f'../results/{YEARS}YEAR/rulefit_features_used_{benchmark_choice}.json', 'w') as _rf:
            _linear_only_rf = [c for c in feature_cols_rf if c in txp_era_year_vars]
            json.dump({
                'rulefit_use_feature_list': rulefit_use_feature_list,
                'rulefit_use_raw_features': rulefit_use_raw_features,
                'rulefit_threshold_decimals': rulefit_threshold_decimals,
                'rulefit_era_year_linear_only': rulefit_era_year_linear_only,
                'linear_only_features': _linear_only_rf,
                'rule_mining_features': [c for c in feature_cols_rf if c not in _linear_only_rf],
                'n_features': len(feature_cols_rf),
                'features': feature_cols_rf,
            }, _rf, indent=2)
        print(f"  Feature list saved: results/{YEARS}YEAR/rulefit_features_used_{benchmark_choice}.json",
              flush=True)

        if use_ros:
            X_rf_fit, y_rf_fit = _ros_fit_resample(
                X_train_rf, y_rf_train,
                sampling_strategy=ros_sampling_strategy,
                random_state=seed,
            )
        else:
            X_rf_fit, y_rf_fit = X_train_rf, y_rf_train

        if rulefit_train_subsample and X_rf_fit.shape[0] > rulefit_train_subsample:
            rng = np.random.RandomState(seed)
            idx = rng.choice(X_rf_fit.shape[0], rulefit_train_subsample, replace=False)
            X_rf_fit = X_rf_fit[idx]
            y_rf_fit = y_rf_fit[idx]

        _rulefit_banner(
            'INTERNAL',
            'Fitting RuleFit on training set',
            'Omit from paper — only timing / candidate-rule count.',
        )
        print(f"  fast={rulefit_fast_mode}, n_train={X_rf_fit.shape[0]}, "
              f"n_features={len(feature_cols_rf)}, model_type={rulefit_model_type}", flush=True)
        tree_gen = _make_rulefit_tree_generator(X_rf_fit.shape[0], seed)
        rulefit_model = RuleFit(
            tree_size=rulefit_tree_size,
            max_rules=rulefit_max_rules,
            memory_par=0.01,
            rfmode='classify',
            model_type=rulefit_model_type,
            lin_standardise=rulefit_lin_standardise,
            exp_rand_tree_size=rulefit_exp_rand_tree_size,
            tree_generator=tree_gen,
            random_state=seed,
            cv=rulefit_cv,
        )
        fit_rulefit(rulefit_model, X_rf_fit, y_rf_fit, feature_cols_rf, label='RuleFit')

        y_pred_prob_rulefit = prob_test_rulefit = rulefit_predict_proba(rulefit_model, X_test_rf)
        rulefit_calibrator = None
        use_calib = calibrated and rulefit_calibrated
        if use_calib:
            prob_uncal = rulefit_predict_proba(rulefit_model, X_calib_rf)
            iso_reg = IsotonicRegression(out_of_bounds='clip')
            iso_reg.fit(prob_uncal, y_calib)
            prob_test_rulefit = rulefit_predict_proba(rulefit_model, X_test_rf)
            y_pred_prob_rulefit = iso_reg.transform(prob_test_rulefit)
            rulefit_calibrator = iso_reg

        y_pred_raw_rf = prob_test_rulefit if use_calib else None
        _rulefit_banner(
            'DIAGNOSTIC',
            'evaluate() metrics (RuleFit + prior models in dict)',
            'Optional Table: compare AUC to Logistic; ignore F1 if model rarely predicts death.',
        )
        metrics = evaluate(
            'RuleFit', 'TXP', benchmark_choice, metrics,
            y_test, y_pred_prob_rulefit, y_pred_raw_rf,
            save=True, save_plots=not rulefit_fast_mode,
        )
        metrics = _eval_on_latest_era(
            metrics, 'RuleFit', y_test, y_pred_prob_rulefit, y_pred_raw_rf, latest_era_test_mask,
        )
        rules_df = export_rulefit_rules(rulefit_model, YEARS, benchmark_choice, top_n=topk)
        if rulefit_table2:
            table2_df = build_rulefit_table2(
                rules_df, X_train_rf_df, y_rf_train, feature_cols_rf, YEARS, benchmark_choice,
            )
            print_rulefit_table2(table2_df, YEARS, benchmark_choice)
        print_rulefit_performance(y_test, y_pred_prob_rulefit)
        audit_rulefit_rules(rules_df, feature_cols_rf, YEARS, benchmark_choice)
        if rulefit_stability_bootstraps > 0:
            rulefit_bootstrap_feature_stability(
                X_rf_fit, y_rf_fit, feature_cols_rf, seed=seed,
            )
        if seed == num_runs - 1:
            save_model(
                rulefit_model, feature_cols_rf,
                None if rulefit_use_raw_features else scaler,
                f'rulefit_txp_{YEARS}yr_{benchmark_choice}',
                calibrator=rulefit_calibrator,
            )
            print("  [INTERNAL] Model checkpoint for deployment — not a manuscript table.", flush=True)

        if seed == 0 and interpret and not rulefit_fast_mode and rulefit_compare_rules_only:
            print("\n--- RuleFit rules-only (model_type='r') ---")
            rf_rules_only = RuleFit(
                tree_size=rulefit_tree_size,
                max_rules=rulefit_max_rules,
                rfmode='classify',
                model_type='r',
                exp_rand_tree_size=rulefit_exp_rand_tree_size,
                tree_generator=_make_rulefit_tree_generator(X_rf_fit.shape[0], seed),
                random_state=seed,
                cv=rulefit_cv,
            )
            fit_rulefit(rf_rules_only, X_rf_fit, y_rf_fit, feature_cols_rf, label='RuleFit-rules')
            y_rules = rulefit_predict_proba(rf_rules_only, X_test_rf)
            evaluate(
                'RuleFit-rules', 'TXP', benchmark_choice, metrics,
                y_test, y_rules, save=False, save_plots=False,
            )
            export_rulefit_rules(
                rf_rules_only, YEARS, f'{benchmark_choice}_rules_only', top_n=topk,
            )

    print('\n' + '=' * 72, flush=True)
    print(f'METRICS SUMMARY (seed={seed})', flush=True)
    print_metrics_summary(metrics)
