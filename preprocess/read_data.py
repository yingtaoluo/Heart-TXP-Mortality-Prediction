from .helpers import (
    txp_datetime_format, remove_binary_indicators,
    os, pd, plt, pdb, TIME_NOW, tqdm
)
import datetime
import numpy as np
from lifelines import KaplanMeierFitter
from paths import DATA, DATASETS, RESULTS, CHECKPOINTS, IMAGES, MODELS


# (waiting update) alive to the last status check or end of study [which is censoring]
# (waiting update) death
# (waiting update) removal -> death
# (waiting update) removal -> not sure
# (waiting update) transplant - (follow-up) > death
# (waiting update) transplant - (follow-up) > alive to the last status check or end of study
# also: horizon
def read_from_transplant_data():
    file_path = f'{DATA}/thoracic_data/thoracic_data.csv'
    # (217648, 553)
    # (93913, 553)
    # file_path = f'{DATA}/mybox-selected/STAR_SAS/SAS Dataset 202312/SAS Dataset 202312/Thoracic/2024.04.08_Akinwale_data_cleaning.csv'
    # (217648, 556)
    # (93913, 556)
    # file_path = f'{DATA}/mybox-selected/STAR_SAS/SAS Dataset 202312/SAS Dataset 202312/Thoracic/20240216_unos_commands.csv'
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

    csv_file = f'{DATASETS}/transplant_data.csv'
    # csv_file = f'{DATASETS}/transplant_data_full.csv'
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


def basic_cohort_stats(data_path=f'{DATASETS}/transplant_data.csv'):
    """
    Compute high-level cohort statistics for key clinical patterns:
      1) Waitlist death without transplant/removal (death at last known date)
      2) Waitlist removal then censored (alive) at removal date
      3) Transplant followed by death (post‑TXP death)
      4) Transplant and no recorded death before censoring (alive or re‑TXP)
    Also reports some sub‑stats within transplant‑alive group.
    """
    df = pd.read_csv(
        data_path,
        low_memory=False,
        encoding='utf-8',
        parse_dates=['REMOVAL_DATE', 'LAST_DATE']
    )

    total = len(df)
    print(f"\n=== Basic Cohort Statistics ===")
    print(f"Total patients/rows in transplant_data: {total:,}")

    # 1) Waitlist death without transplant/removal (death reported at last date)
    mask1 = (
        (df['WLType'] == 'wl') &
        (df['PType'] == 'dead') &
        df['REMOVAL_DATE'].notna()
    )

    # 2) Waitlist removal then censored alive at removal date
    mask2 = (
        (df['WLType'] == 'wl') &
        (df['PType'] == 'alive') &
        df['REMOVAL_DATE'].notna()
    )

    # 3) Transplant -> death (post‑TXP death)
    mask3 = (
        (df['WLType'] == 'txp') &
        (df['PType'] == 'dead') &
        df['LAST_DATE'].notna()
    )

    # 4) Transplant and no recorded death before censoring (alive or re‑TXP)
    mask4 = (
        (df['WLType'] == 'txp') &
        df['PType'].isin(['alive', 'retxp'])
    )

    def _report(name, mask):
        count = int(mask.sum())
        pct = 100.0 * count / total if total > 0 else 0.0
        print(f"{name}: {count:,} ({pct:.2f}%)")
        return count

    print("\n--- Main clinical patterns ---")
    c1 = _report("1) WL death without TXP (PType='dead', WLType='wl')", mask1)
    c2 = _report("2) WL removal, censored alive (PType='alive', WLType='wl')", mask2)
    c3 = _report("3) TXP then death (PType='dead', WLType='txp')", mask3)
    c4 = _report("4) TXP, no death before censoring (PType in ['alive','retxp'], WLType='txp')", mask4)

    other = total - (c1 + c2 + c3 + c4)
    if other > 0:
        pct_other = 100.0 * other / total
        print(f"Other / uncategorized: {other:,} ({pct_other:.2f}%)")

    # REM_CD (reason for removal) lookup for reporting
    REM_CD_LABELS = {
        2.0: "Deceased Donor tx, removed by tx center",
        3.0: "Txed at another center",
        4.0: "Deceased Donor tx, removed by tx center",
        5.0: "Medically Unsuitable",
        6.0: "Refused transplant",
        7.0: "Transferred to another center",
        8.0: "Died",
        9.0: "Other",
        10.0: "Candidate listed in error",
        11.0: "Cand. listed for unaccept. antigens only",
        12.0: "Cand. condition improved, tx not needed",
        13.0: "Cand. cond. deteriorated, too sick to tx",
        14.0: "Tx at another center (multiple-listing)",
        15.0: "Living Donor tx, removed by tx center",
        16.0: "Candidate Removed in Error",
        17.0: "Changed to KP (by system)",
        18.0: "Deceased Donor Emergency Tx",
        19.0: "Deceased Donor Multi-Organ Tx",
        20.0: "Program inactive for 2+ years",
        21.0: "Patient died during TX procedure",
        22.0: "Transplanted in another country",
        23.0: "Patient died during Living Donor TX procedure",
        24.0: "Unable to contact candidate",
        40.0: "Waiting for KP, will not Accept Isol. Organ",
        41.0: "Also Waiting for Isol Organ; recvd Kidney",
        42.0: "Also Waiting for Isol Organ; recvd Pancreas",
        43.0: "Also Waiting for KP; recvd KP",
        44.0: "Also Waiting for KP; recvd Kidney Alone",
        45.0: "Also Waiting for KP; recvd Pancreas Alone",
    }

    # 1) WL death without TXP — breakdown by REM_CD (reason for removal)
    if 'REM_CD' in df.columns and c1 > 0:
        print("\n--- 1) WL death without TXP — by REM_CD (reason for removal) ---")
        wl_dead = df.loc[mask1, 'REM_CD']
        wl_dead = wl_dead.dropna()
        n1 = len(wl_dead)
        for rem_cd, cnt in wl_dead.value_counts().sort_index().items():
            label = REM_CD_LABELS.get(float(rem_cd) if pd.notna(rem_cd) else rem_cd, str(rem_cd))
            pct1 = 100.0 * cnt / n1 if n1 > 0 else 0
            print(f"  REM_CD {rem_cd}: {int(cnt):,} ({pct1:.2f}% of case 1) — {label}")
        if n1 < c1:
            print(f"  (missing REM_CD: {c1 - n1:,})")

    # 2) WL removal, censored alive — breakdown by REM_CD
    if 'REM_CD' in df.columns and c2 > 0:
        print("\n--- 2) WL removal, censored alive — by REM_CD (reason for removal) ---")
        wl_alive = df.loc[mask2, 'REM_CD'].dropna()
        n2 = len(wl_alive)
        for rem_cd, cnt in wl_alive.value_counts().sort_index().items():
            label = REM_CD_LABELS.get(float(rem_cd) if pd.notna(rem_cd) else rem_cd, str(rem_cd))
            pct2 = 100.0 * cnt / n2 if n2 > 0 else 0
            print(f"  REM_CD {rem_cd}: {int(cnt):,} ({pct2:.2f}% of case 2) — {label}")
        if n2 < c2:
            print(f"  (missing REM_CD: {c2 - n2:,})")

    # Sub‑stats within transplanted & not dead group
    txp_alive = df[mask4].copy()
    if len(txp_alive) > 0:
        print("\n--- Details within transplanted & not dead group (case 4) ---")

        # Touching cutoff date (LAST_DATE at TIME_NOW)
        if 'LAST_DATE' in txp_alive.columns:
            touch_cutoff = txp_alive['LAST_DATE'] == TIME_NOW.normalize()
            _report("4.a) LAST_DATE at cutoff TIME_NOW (touching study end)", touch_cutoff)

        # Immediate censoring after TXP (TXPSurv == 0)
        if 'TXPSurv' in txp_alive.columns:
            immediate_censor = txp_alive['TXPSurv'] == 0
            _report("4.b) TXPSurv == 0 (immediate censor after TXP)", immediate_censor)

        # Censored by re‑transplant
        retxp = txp_alive['PType'] == 'retxp'
        _report("4.c) Censored by re‑transplant (PType='retxp')", retxp)

        # Remaining: censored at last known alive time (not cutoff, not immediate, not retxp)
        others_4 = ~(touch_cutoff | immediate_censor | retxp)
        _report("4.d) Censored at last known alive time (not cutoff / immediate / retxp)", others_4)

    def _report_time_stats(series, name, unit='days'):
        """Print mean, std, P25, P50, P75, IQR for a numeric series (days)."""
        s = series.dropna()
        n = len(s)
        if n == 0:
            print(f"  {name}: n=0 (no valid values)")
            return
        q = s.quantile([0.25, 0.5, 0.75])
        iqr = float(q[0.75] - q[0.25])
        print(f"  {name} (n={n:,}): mean={float(s.mean()):.1f} ± std={float(s.std()):.1f} {unit}, "
              f"P25={float(q[0.25]):.1f}, P50={float(q[0.5]):.1f}, P75={float(q[0.75]):.1f}, IQR={iqr:.1f}")

    def _report_numeric_feature(series, name, unit=""):
        """Print missing rate + mean/std/min/max/quantiles for a numeric feature."""
        s0 = pd.to_numeric(series, errors="coerce")
        n_all = int(len(s0))
        n_miss = int(s0.isna().sum())
        s = s0.dropna()
        if len(s) == 0:
            print(f"  {name}: n=0 (all missing; total={n_all:,})")
            return
        q = s.quantile([0.0, 0.25, 0.5, 0.75, 1.0])
        unit_str = f" {unit}" if unit else ""
        print(
            f"  {name}: n={len(s):,} (missing={n_miss:,}/{n_all:,}, {100.0*n_miss/max(n_all,1):.2f}%) | "
            f"mean={float(s.mean()):.3f} ± std={float(s.std()):.3f}{unit_str} | "
            f"min={float(q[0.0]):.3f}, P25={float(q[0.25]):.3f}, P50={float(q[0.5]):.3f}, "
            f"P75={float(q[0.75]):.3f}, max={float(q[1.0]):.3f}"
        )

    # --- Waiting time (WLSurv) and post-TXP survival (TXPSurv) ---
    print("\n--- Waiting time (WLSurv, days) ---")
    if 'WLSurv' in df.columns:
        _report_time_stats(df['WLSurv'], "WLSurv (all)")
    else:
        print("  WLSurv column not found.")

    print("\n--- Post-transplant survival (TXPSurv, days) ---")
    if 'TXPSurv' in df.columns and 'WLType' in df.columns:
        txp = df.loc[df['WLType'] == 'txp', 'TXPSurv']
        _report_time_stats(txp, "TXPSurv (WLType='txp')")
    else:
        print("  TXPSurv / WLType not found.")

    # --- Total follow-up: init to last = WLSurv + TXPSurv (days) ---
    print("\n--- Total follow-up (init to last, days) = WLSurv + TXPSurv ---")
    if 'WLSurv' in df.columns and 'TXPSurv' in df.columns:
        total_days = df['WLSurv'].fillna(0) + df['TXPSurv'].fillna(0)
        _report_time_stats(total_days, "Total (WLSurv + TXPSurv)")
    else:
        print("  WLSurv or TXPSurv not found.")

    # --- 3-year bounded total survival: min(WLSurv + TXPSurv, 3 years) ---
    print("\n--- 3-year bounded total survival (days) = min(WLSurv + TXPSurv, 1095) ---")
    if 'WLSurv' in df.columns and 'TXPSurv' in df.columns:
        horizon_days = 365 * 3
        total_days = df['WLSurv'].fillna(0) + df['TXPSurv'].fillna(0)
        bounded_total_days = total_days.clip(upper=horizon_days)
        _report_time_stats(bounded_total_days, "Total bounded at 3 years")
        reached_horizon_pct = 100.0 * (total_days >= horizon_days).mean()
        print(f"  Reached 3-year horizon (before truncation): {reached_horizon_pct:.2f}%")
    else:
        print("  WLSurv or TXPSurv not found.")

    # --- Time trend: count by year of LAST_DATE ---
    print("\n--- Time trend (count by year of LAST_DATE) ---")
    if 'LAST_DATE' in df.columns:
        df_year = df.copy()
        df_year['LAST_DATE'] = pd.to_datetime(df_year['LAST_DATE'], errors='coerce')
        df_year = df_year.dropna(subset=['LAST_DATE'])
        df_year['year'] = df_year['LAST_DATE'].dt.year
        by_year = df_year.groupby('year').size()
        for yr, cnt in by_year.items():
            print(f"  {int(yr)}: {cnt:,}")
    else:
        print("  LAST_DATE not found.")

    # --- Feature stats: number of previous donor offers ---
    print("\n--- Feature stats: number of previous donor offers ---")
    candidate_cols = [
        "num_prior_offers",
        "num_previous_donor_offers",
        "num_previous_donor_offer",
        "num_prev_offers",
        "prev_offer_count",
        "previous_offer_count",
        "n_previous_donor_offers",
    ]
    prev_offer_col = next((c for c in candidate_cols if c in df.columns), None)
    if prev_offer_col is None:
        print(
            "  Column not found. Looked for one of: "
            + ", ".join([f"'{c}'" for c in candidate_cols])
        )
    else:
        _report_numeric_feature(df[prev_offer_col], f"{prev_offer_col} (all)", unit="offers")

        # Also report by the 4 main clinical pattern masks if available
        groups = [
            ("case 1 (WLType='wl', PType='dead')", mask1),
            ("case 2 (WLType='wl', PType='alive')", mask2),
            ("case 3 (WLType='txp', PType='dead')", mask3),
            ("case 4 (WLType='txp', PType in ['alive','retxp'])", mask4),
        ]
        for label, m in groups:
            try:
                _report_numeric_feature(df.loc[m, prev_offer_col], f"{prev_offer_col} ({label})", unit="offers")
            except Exception:
                # Keep stats reporting robust even if masks/columns are malformed in some datasets.
                print(f"  {prev_offer_col} ({label}): unable to compute (mask/column issue)")


def summary_transplant_data(data_path=f'{DATASETS}/transplant_data.csv', output_dir=IMAGES):
    """
    Analyze waitlist mortality and all-cause mortality using Kaplan-Meier survival analysis.

    Parameters
    ----------
    data_path : str
        Path to the transplant_data.csv file
    output_dir : str
        Directory to save the survival plots
        
    Returns
    -------
    dict
        Dictionary containing summary statistics for both analyses
    """
    # Load the processed transplant data
    df = pd.read_csv(data_path, low_memory=False, encoding='utf-8')
    print(f"\n=== Summary Transplant Data Analysis ===")
    print(f"Total records: {len(df):,}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # ========================================================================
    # 1. Waitlist Mortality Analysis
    # ========================================================================
    print("\n--- Waitlist Mortality Analysis ---")
    wl_data = df[df['WLType'] == 'wl'].copy()
    print(f"Patients on waitlist (WLType='wl'): {len(wl_data):,}")
    
    # Filter to patients who died on waitlist
    wl_death_data = wl_data[(wl_data['PType'] == 'dead') & (~wl_data['Removed'])].copy()
    wl_alive_data = wl_data[(wl_data['PType'] == 'alive') & (~wl_data['Removed'])].copy()
    wl_removal_data = wl_data[wl_data['Removed']].copy()
    
    print(f"  - Died on waitlist: {len(wl_death_data):,}")
    print(f"  - Alive (censored): {len(wl_alive_data):,}")
    print(f"  - Removed (censored): {len(wl_removal_data):,}")
    
    # Prepare data for Kaplan-Meier: combine deaths and censored (alive + removal)
    wl_analysis_data = pd.concat([
        wl_death_data[['WLSurv', 'PType']],
        wl_alive_data[['WLSurv', 'PType']],
        wl_removal_data[['WLSurv', 'PType']]
    ])
    
    # Convert time to years and create event indicator
    wl_analysis_data = wl_analysis_data[wl_analysis_data['WLSurv'].notna()].copy()
    wl_analysis_data['time_years'] = wl_analysis_data['WLSurv'] / 365.25
    wl_analysis_data['event'] = (wl_analysis_data['PType'] == 'dead').astype(int)
    
    if len(wl_analysis_data) > 0:
        # Fit Kaplan-Meier estimator
        kmf_wl = KaplanMeierFitter()
        kmf_wl.fit(
            durations=wl_analysis_data['time_years'],
            event_observed=wl_analysis_data['event']
        )
        
        # Plot survival curve
        fig, ax = plt.subplots(figsize=(10, 6))
        kmf_wl.plot_survival_function(ax=ax, ci_show=True, show_censors=False)
        ax.set_xlabel('Time (Years)', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        ax.set_title('Waitlist Mortality: Kaplan-Meier Survival Curve', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(['Waitlist Survival', '95% CI'], fontsize=10)
        
        # Add summary statistics
        n_total = len(wl_analysis_data)
        n_events = wl_analysis_data['event'].sum()
        n_censored = (wl_analysis_data['event'] == 0).sum()
        median_survival = kmf_wl.median_survival_time_
        
        stats_text = f'N = {n_total:,}\n'
        stats_text += f'Events (deaths) = {n_events:,} ({n_events/n_total*100:.1f}%)\n'
        stats_text += f'Censored = {n_censored:,} ({n_censored/n_total*100:.1f}%)'
        if pd.notna(median_survival) and np.isfinite(median_survival):
            stats_text += f'\nMedian survival = {median_survival:.2f} years'
        
        ax.text(0.05, 0.15, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'Waitlist_Mortality_Survival.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  - Plot saved to: {output_path}")
        plt.close()
        
        results['waitlist_mortality'] = {
            'n_total': n_total,
            'n_events': n_events,
            'n_censored': n_censored,
            'event_rate': n_events / n_total,
            'median_survival_years': median_survival if pd.notna(median_survival) and np.isfinite(median_survival) else None
        }
    
    # ========================================================================
    # 2. All-Cause Mortality Analysis (Waitlist + Post-Transplant)
    # ========================================================================
    print("\n--- All-Cause Mortality Analysis ---")
    
    # For waitlist deaths: use WLSurv as time
    wl_deaths = wl_death_data[['WLSurv', 'PType']].copy()
    wl_deaths['time_years'] = wl_deaths['WLSurv'] / 365.25
    wl_deaths['event'] = 1  # All are deaths
    
    # For post-transplant deaths: use WLSurv + TXPSurv as total time
    txp_death_data = df[(df['WLType'] == 'txp') & (df['PType'] == 'dead')].copy()
    txp_alive_data = df[(df['WLType'] == 'txp') & (df['PType'] == 'alive')].copy()
    
    print(f"Patients who received transplant: {len(df[df['WLType'] == 'txp']):,}")
    print(f"  - Died after transplant: {len(txp_death_data):,}")
    print(f"  - Alive after transplant: {len(txp_alive_data):,}")
    
    # Calculate total time from waitlist entry to death (for post-transplant deaths)
    txp_deaths = txp_death_data[
        (txp_death_data['WLSurv'].notna()) & 
        (txp_death_data['TXPSurv'].notna())
    ].copy()
    txp_deaths['total_time_days'] = txp_deaths['WLSurv'] + txp_deaths['TXPSurv']
    txp_deaths['time_years'] = txp_deaths['total_time_days'] / 365.25
    txp_deaths['event'] = 1  # All are deaths
    
    # For post-transplant alive patients: use WLSurv + TXPSurv as total time (censored)
    txp_alive = txp_alive_data[
        (txp_alive_data['WLSurv'].notna()) & 
        (txp_alive_data['TXPSurv'].notna())
    ].copy()
    txp_alive['total_time_days'] = txp_alive['WLSurv'] + txp_alive['TXPSurv']
    txp_alive['time_years'] = txp_alive['total_time_days'] / 365.25
    txp_alive['event'] = 0  # Censored (alive)
    
    # Combine all data: waitlist deaths, post-transplant deaths, and post-transplant alive
    all_cause_data = pd.concat([
        wl_deaths[['time_years', 'event']],
        txp_deaths[['time_years', 'event']],
        txp_alive[['time_years', 'event']],
        wl_alive_data[['WLSurv', 'PType']].assign(
            time_years=lambda x: x['WLSurv'] / 365.25,
            event=0
        )[['time_years', 'event']],
        wl_removal_data[['WLSurv', 'PType']].assign(
            time_years=lambda x: x['WLSurv'] / 365.25,
            event=0
        )[['time_years', 'event']]
    ])
    
    all_cause_data = all_cause_data[all_cause_data['time_years'].notna()].copy()
    
    if len(all_cause_data) > 0:
        # Fit Kaplan-Meier estimator
        kmf_all = KaplanMeierFitter()
        kmf_all.fit(
            durations=all_cause_data['time_years'],
            event_observed=all_cause_data['event']
        )
        
        # Plot survival curve
        fig, ax = plt.subplots(figsize=(10, 6))
        kmf_all.plot_survival_function(ax=ax, ci_show=True, show_censors=False)
        ax.set_xlabel('Time from Waitlist Entry (Years)', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        ax.set_title('All-Cause Mortality: Kaplan-Meier Survival Curve\n(Waitlist + Post-Transplant Deaths)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(['All-Cause Survival', '95% CI'], fontsize=10)
        
        # Add summary statistics
        n_total_all = len(all_cause_data)
        n_events_all = all_cause_data['event'].sum()
        n_censored_all = (all_cause_data['event'] == 0).sum()
        median_survival_all = kmf_all.median_survival_time_
        
        stats_text = f'N = {n_total_all:,}\n'
        stats_text += f'Events (deaths) = {n_events_all:,} ({n_events_all/n_total_all*100:.1f}%)\n'
        stats_text += f'Censored = {n_censored_all:,} ({n_censored_all/n_total_all*100:.1f}%)'
        if pd.notna(median_survival_all) and np.isfinite(median_survival_all):
            stats_text += f'\nMedian survival = {median_survival_all:.2f} years'
        
        ax.text(0.05, 0.15, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'All_Cause_Mortality_Survival.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  - Plot saved to: {output_path}")
        plt.close()
        
        results['all_cause_mortality'] = {
            'n_total': n_total_all,
            'n_events': n_events_all,
            'n_censored': n_censored_all,
            'event_rate': n_events_all / n_total_all,
            'median_survival_years': median_survival_all if pd.notna(median_survival_all) and np.isfinite(median_survival_all) else None,
            'n_waitlist_deaths': len(wl_deaths),
            'n_post_txp_deaths': len(txp_deaths)
        }
    
    # ========================================================================
    # 3. Transplant Mortality Analysis (Post-Transplant Only)
    # ========================================================================
    print("\n--- Transplant Mortality Analysis (Post-Transplant Only) ---")
    
    # Get all transplant patients (those who received transplant)
    txp_patients = df[df['WLType'] == 'txp'].copy()
    print(f"Patients who received transplant: {len(txp_patients):,}")
    
    # Filter to patients with valid TXPSurv data
    txp_analysis_data = txp_patients[txp_patients['TXPSurv'].notna()].copy()
    
    # Separate deaths and alive
    txp_death_analysis = txp_analysis_data[txp_analysis_data['PType'] == 'dead'].copy()
    txp_alive_analysis = txp_analysis_data[txp_analysis_data['PType'] == 'alive'].copy()
    txp_retxp_analysis = txp_analysis_data[txp_analysis_data['PType'] == 'retxp'].copy()
    
    print(f"  - Died after transplant: {len(txp_death_analysis):,}")
    print(f"  - Alive (censored): {len(txp_alive_analysis):,}")
    print(f"  - Re-transplanted (censored): {len(txp_retxp_analysis):,}")
    
    # Prepare data for Kaplan-Meier: use TXPSurv (time after transplant)
    txp_km_data = pd.concat([
        txp_death_analysis[['TXPSurv', 'PType']],
        txp_alive_analysis[['TXPSurv', 'PType']],
        txp_retxp_analysis[['TXPSurv', 'PType']]
    ])
    
    # Convert time to years and create event indicator
    txp_km_data['time_years'] = txp_km_data['TXPSurv'] / 365.25
    txp_km_data['event'] = (txp_km_data['PType'] == 'dead').astype(int)
    
    if len(txp_km_data) > 0:
        # Fit Kaplan-Meier estimator
        kmf_txp = KaplanMeierFitter()
        kmf_txp.fit(
            durations=txp_km_data['time_years'],
            event_observed=txp_km_data['event']
        )
        
        # Plot survival curve
        fig, ax = plt.subplots(figsize=(10, 6))
        kmf_txp.plot_survival_function(ax=ax, ci_show=True, show_censors=False)
        ax.set_xlabel('Time After Transplant (Years)', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        ax.set_title('Transplant Mortality: Kaplan-Meier Survival Curve\n(Post-Transplant Survival)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(['Post-Transplant Survival', '95% CI'], fontsize=10)
        
        # Add summary statistics
        n_total_txp = len(txp_km_data)
        n_events_txp = txp_km_data['event'].sum()
        n_censored_txp = (txp_km_data['event'] == 0).sum()
        median_survival_txp = kmf_txp.median_survival_time_
        
        stats_text = f'N = {n_total_txp:,}\n'
        stats_text += f'Events (deaths) = {n_events_txp:,} ({n_events_txp/n_total_txp*100:.1f}%)\n'
        stats_text += f'Censored = {n_censored_txp:,} ({n_censored_txp/n_total_txp*100:.1f}%)'
        if pd.notna(median_survival_txp) and np.isfinite(median_survival_txp):
            stats_text += f'\nMedian survival = {median_survival_txp:.2f} years'
        
        ax.text(0.05, 0.15, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_path = os.path.join(output_dir, 'Transplant_Mortality_Survival.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  - Plot saved to: {output_path}")
        plt.close()
        
        results['transplant_mortality'] = {
            'n_total': n_total_txp,
            'n_events': n_events_txp,
            'n_censored': n_censored_txp,
            'event_rate': n_events_txp / n_total_txp,
            'median_survival_years': median_survival_txp if pd.notna(median_survival_txp) and np.isfinite(median_survival_txp) else None
        }
    
    # Print summary
    print("\n=== Summary Statistics ===")
    if 'waitlist_mortality' in results:
        wl = results['waitlist_mortality']
        print(f"\nWaitlist Mortality:")
        print(f"  Total patients: {wl['n_total']:,}")
        print(f"  Death events: {wl['n_events']:,} ({wl['event_rate']*100:.1f}%)")
        print(f"  Censored: {wl['n_censored']:,} ({wl['n_censored']/wl['n_total']*100:.1f}%)")
        if wl['median_survival_years']:
            print(f"  Median survival: {wl['median_survival_years']:.2f} years")
    
    if 'all_cause_mortality' in results:
        ac = results['all_cause_mortality']
        print(f"\nAll-Cause Mortality:")
        print(f"  Total patients: {ac['n_total']:,}")
        print(f"  Death events: {ac['n_events']:,} ({ac['event_rate']*100:.1f}%)")
        print(f"    - Waitlist deaths: {ac['n_waitlist_deaths']:,}")
        print(f"    - Post-transplant deaths: {ac['n_post_txp_deaths']:,}")
        print(f"  Censored: {ac['n_censored']:,} ({ac['n_censored']/ac['n_total']*100:.1f}%)")
        if ac['median_survival_years']:
            print(f"  Median survival: {ac['median_survival_years']:.2f} years")
    
    if 'transplant_mortality' in results:
        txp = results['transplant_mortality']
        print(f"\nTransplant Mortality (Post-Transplant Only):")
        print(f"  Total patients: {txp['n_total']:,}")
        print(f"  Death events: {txp['n_events']:,} ({txp['event_rate']*100:.1f}%)")
        print(f"  Censored: {txp['n_censored']:,} ({txp['n_censored']/txp['n_total']*100:.1f}%)")
        if txp['median_survival_years']:
            print(f"  Median survival: {txp['median_survival_years']:.2f} years")
    
    return results


def plot_waitlist_mortality_by_year(data_path=f'{DATASETS}/transplant_data.csv', output_dir=IMAGES):
    """
    Plot year vs all-cause mortality rate and patient count for patients on waitlist.
    
    For each year, calculates:
    - Patient count: All patients who were on the waitlist at any point during that year
    - Mortality rate: Patients who died in that year / Patients on waitlist in that year
    
    Creates a dual-axis plot showing:
    - Line: All-cause mortality rate by year
    - Bars: Count of patients on waitlist in that year
    
    Parameters
    ----------
    data_path : str
        Path to the transplant_data.csv file
    output_dir : str
        Directory to save the plot
        
    Returns
    -------
    pd.DataFrame
        DataFrame with year, patient_count, death_count, and mortality_rate columns
    """
    # Load the processed transplant data
    df = pd.read_csv(data_path, low_memory=False, encoding='utf-8')
    print(f"\n=== Waitlist Mortality by Year Analysis ===")
    print(f"Total records: {len(df):,}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert INIT_DATE to datetime
    df['INIT_DATE'] = pd.to_datetime(df['INIT_DATE'], errors='coerce')
    df = df[df['INIT_DATE'].notna()].copy()
    
    # Calculate waitlist period for each patient
    # Start date: INIT_DATE
    # End date: INIT_DATE + WLSurv (when they left waitlist)
    # Note: INIT_DATE + WLSurv could be:
    #   - Death date (if PType == 'dead' and WLType == 'wl')
    #   - Transplant date (if WLType == 'txp')
    #   - Removal date (if Removed == True)
    #   - Censoring date (if PType == 'alive' and WLType == 'wl')
    df['wl_start_date'] = df['INIT_DATE']
    df['wl_end_date'] = df['INIT_DATE'] + pd.to_timedelta(df['WLSurv'], unit='D')
    
    # For patients still alive/on waitlist, extend to TIME_NOW if needed
    # (This handles cases where WLSurv might be censored)
    alive_on_waitlist = (df['PType'] == 'alive') & (df['WLType'] == 'wl')
    df.loc[alive_on_waitlist, 'wl_end_date'] = df.loc[alive_on_waitlist, 'wl_end_date'].clip(upper=TIME_NOW)
    
    # Calculate death date ONLY for patients who actually died (all-cause mortality)
    # Important: Only set death_date when PType == 'dead' to avoid counting removals as deaths
    df['death_date'] = pd.NaT
    death_mask = df['PType'] == 'dead'
    
    # Waitlist deaths: death occurred at INIT_DATE + WLSurv
    # Only count if PType == 'dead' AND WLType == 'wl' (not removed, not transplanted)
    wl_death_mask = death_mask & (df['WLType'] == 'wl')
    df.loc[wl_death_mask, 'death_date'] = df.loc[wl_death_mask, 'wl_end_date']
    
    # Post-transplant deaths: death occurred at INIT_DATE + WLSurv + TXPSurv
    # Only count if PType == 'dead' AND WLType == 'txp'
    txp_death_mask = death_mask & (df['WLType'] == 'txp')
    df.loc[txp_death_mask, 'death_date'] = (
        df.loc[txp_death_mask, 'INIT_DATE'] + 
        pd.to_timedelta(df.loc[txp_death_mask, 'WLSurv'], unit='D') +
        pd.to_timedelta(df.loc[txp_death_mask, 'TXPSurv'], unit='D')
    )

    # Get year range (but only analyze 1988-2023 as other years are incomplete)
    min_year = 1989
    max_year = 2023
    
    print(f"Analyzing years: {min_year} - {max_year} (other years excluded as incomplete)")
    
    # For each year, find:
    # 1. Patients on waitlist during that year (waitlist period overlaps with the year)
    # 2. Deaths that occurred in that year
    
    yearly_stats = []
    
    for year in range(min_year, max_year + 1):
        year_start = pd.Timestamp(f'{year}-01-01')
        year_end = pd.Timestamp(f'{year}-12-31 23:59:59')
        
        # Patients on waitlist during this year
        # A patient is on waitlist in a year if:
        # wl_start_date <= year_end AND wl_end_date >= year_start
        on_waitlist_mask = (
            (df['wl_start_date'] <= year_end) & 
            (df['wl_end_date'] >= year_start)
        )
        patients_on_waitlist = on_waitlist_mask.sum()
        
        # Deaths that occurred in this year
        deaths_in_year = (
            (df['death_date'] >= year_start) & 
            (df['death_date'] <= year_end)
        ).sum()
        
        # Calculate mortality rate
        mortality_rate = deaths_in_year / patients_on_waitlist if patients_on_waitlist > 0 else 0
        
        yearly_stats.append({
            'year': year,
            'patient_count': patients_on_waitlist,
            'death_count': deaths_in_year,
            'mortality_rate': mortality_rate
        })
    
    yearly_stats_df = pd.DataFrame(yearly_stats)
    
    # Filter to only show years 1988-2023 (other years are incomplete)
    yearly_stats_df = yearly_stats_df[
        (yearly_stats_df['year'] >= min_year) &
        (yearly_stats_df['year'] <= max_year)
    ].copy()
    
    print(f"\nTotal years analyzed: {len(yearly_stats_df)}")
    print(f"Year range: {yearly_stats_df['year'].min():.0f} - {yearly_stats_df['year'].max():.0f}")
    print(f"\nSample statistics:")
    print(yearly_stats_df.head(10))
    print(f"\n...")
    print(yearly_stats_df.tail(10))
    
    # Create the plot
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Left y-axis: Mortality rate (line)
    color_line = 'blue'
    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('All-Cause Mortality Rate', fontsize=12, color=color_line, fontweight='bold')
    line = ax1.plot(yearly_stats_df['year'], yearly_stats_df['mortality_rate'], 
                    color=color_line, marker='o', linewidth=2, markersize=6, 
                    label='All-Cause Mortality Rate')
    ax1.tick_params(axis='y', labelcolor=color_line)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(bottom=0)
    
    # Right y-axis: Patient count (bars)
    ax2 = ax1.twinx()
    color_bars = 'grey'
    ax2.set_ylabel('Patient Count', fontsize=12, color=color_bars, fontweight='bold')
    bars = ax2.bar(yearly_stats_df['year'], yearly_stats_df['patient_count'], 
                   color=color_bars, alpha=0.6, width=0.8, label='Patient Count')
    ax2.tick_params(axis='y', labelcolor=color_bars)
    ax2.set_ylim(bottom=0)
    
    # Set x-axis to show all years (maybe every 2-3 years for readability)
    step = max(1, len(yearly_stats_df) // 30)  # Show about 30 labels
    ax1.set_xticks(yearly_stats_df['year'][::step])
    ax1.set_xticklabels(yearly_stats_df['year'][::step], rotation=45, ha='right')
    
    # Title
    plt.title('All-Cause Mortality Rate and Patient Count by Year\n(Patients on Waitlist)', 
              fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'Waitlist_Mortality_by_Year.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.close()
    
    # Print summary statistics
    print(f"\n=== Summary Statistics ===")
    print(f"Total deaths across all years: {yearly_stats_df['death_count'].sum():,}")
    print(f"Average patients on waitlist per year: {yearly_stats_df['patient_count'].mean():.0f}")
    print(f"Average mortality rate: {yearly_stats_df['mortality_rate'].mean():.4f}")
    print(f"\nYear with highest mortality rate:")
    max_mort_year = yearly_stats_df.loc[yearly_stats_df['mortality_rate'].idxmax()]
    print(f"  Year: {max_mort_year['year']:.0f}, Rate: {max_mort_year['mortality_rate']:.4f}, Patients: {max_mort_year['patient_count']:.0f}, Deaths: {max_mort_year['death_count']:.0f}")
    print(f"\nYear with lowest mortality rate:")
    min_mort_year = yearly_stats_df.loc[yearly_stats_df['mortality_rate'].idxmin()]
    print(f"  Year: {min_mort_year['year']:.0f}, Rate: {min_mort_year['mortality_rate']:.4f}, Patients: {min_mort_year['patient_count']:.0f}, Deaths: {min_mort_year['death_count']:.0f}")
    print(f"\nYear with most patients on waitlist:")
    max_pat_year = yearly_stats_df.loc[yearly_stats_df['patient_count'].idxmax()]
    print(f"  Year: {max_pat_year['year']:.0f}, Patients: {max_pat_year['patient_count']:.0f}, Rate: {max_pat_year['mortality_rate']:.4f}, Deaths: {max_pat_year['death_count']:.0f}")
    
    return yearly_stats_df

