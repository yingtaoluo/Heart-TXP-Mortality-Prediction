import pandas as pd
import pdb
import os
from sas7bdat import SAS7BDAT


def convert_sas_to_csv(sas_file_path, csv_file_path):
    """
    Convert a sas7bdat file to a csv file.

    Parameters:
    sas_file_path (str): the path to the input sas7bdat file.
    csv_file_path (str): the path where the output csv file will be saved.
    """
    # Reading the sas7bdat file
    with SAS7BDAT(sas_file_path) as file:
        df = file.to_data_frame()

    # Saving the DataFrame to a csv file
    df.to_csv(csv_file_path, index=False)


# file = './data/thoracic_data/thoracic_data1'
# data = pd.io.stata.read_stata(file+'.dta')
# data.to_csv(file+'.csv')

# file = './data/SAS Dataset/Thoracic/formats'
# convert_sas_to_csv(file+'.sas7bdat', file+'.csv')


def convert_to_csv(file_path, output_path):
    if os.path.exists(output_path):
        print(f"CSV exists, skip：{output_path}")
        return
    if file_path.endswith('.sas7bdat'):
        df = pd.read_sas(file_path)
    elif file_path.endswith('.dta') or file_path.endswith('.DTA'):
        df = pd.read_stata(file_path, convert_categoricals=False)
    elif file_path.endswith('.DAT') or file_path.endswith('.dat'):
        # You may need to adjust parameters based on the structure of your DAT files
        df = pd.read_csv(file_path, delimiter='\t', header=None, skiprows=1,
                         names=['Value', 'Code', 'Flag', 'Description'], encoding='latin1')
    else:
        return
    print("Processing {}".format(file_path))
    df.to_csv(output_path, index=False)
    print(f"conversion done：{output_path}")


def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            print(file)
            if file.endswith('.sas7bdat') or file.endswith('.DTA') or file.endswith('.dta') \
                    or file.endswith('.DAT') or file.endswith('.dat'):
                file_path = os.path.join(root, file)
                # remove the original extension name
                base_name = os.path.splitext(file)[0]
                output_path = os.path.join(root, base_name + '.csv')
                convert_to_csv(file_path, output_path)


def process_donornet(file_path):
    df = pd.read_parquet(file_path, engine='pyarrow')
    df.to_csv(file_path[:-7]+'csv', index=False)


# df = pd.read_stata("../data/CTR_IDS/donor_ctr_ids.dta", convert_categoricals=False)
# pdb.set_trace()

# target_directory = '../data/CODE DICTIONARY'
# target_directory = '../data/mybox-selected/STAR_SAS/SAS Dataset 202312/SAS Dataset 202312/Thoracic'
# target_directory = "../data/mybox-selected/STAR_STATA/CODE DICTIONARY - FORMATS 202312/Thoracic"
# target_directory = "../data/donornet/DonorNet_SAS"
target_directory = "../data/CTR_IDS"
process_directory(target_directory)

# process_donornet('../data/donornet/donors.parquet')
# process_donornet('../data/donornet/offers.parquet')
