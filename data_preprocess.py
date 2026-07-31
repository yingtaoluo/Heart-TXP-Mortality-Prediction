from preprocess import run_txp_data, model, ensure_output_dirs


def main():
    ensure_output_dirs()
    # Cohort build (optional; needs raw UNOS / DonorNet under data/):
    # from preprocess import read_from_transplant_data, create_TXP_static_data
    # read_from_transplant_data()
    # create_TXP_static_data()
    run_txp_data(model)


if __name__ == '__main__':
    main()
