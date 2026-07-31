from preprocess import *
# from preprocess.next_offer_data_preprocess import run_next_offer_eda


def main():
    # Run EDA for next offer data
    # read_from_transplant_data()
    # basic_cohort_stats()
    # plot_waitlist_mortality_by_year()
    # run_wl_data(model)
    # summary_transplant_data()
    # create_WL_dynamic_data()
    # create_TXP_static_data()
    # create_followup_dynamic_data()
    run_txp_data(model)
    # run_next_offer_eda()
    # run_time_to_next_offer_analysis()
    # run_donor_accept_analysis()
    # run_waitlist_time_to_censoring_analysis()
    # run_rl_data_process()
    # final_df_to_training_tensors()

    # if run_all:
    #     for m in txp_model_choices:
    #         run_txp_data(m)
    # else:
    #     run_txp_data(model)


if __name__ == '__main__':
    main()

