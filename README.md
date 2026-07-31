# Heart-TXP-Mortality-Prediction

Heart transplant mortality prediction (Logistic / XGBoost / RuleFit).

## Setup

```bash
conda env create -f environment.yml
conda activate base
```

Raw UNOS data is **not** included (restricted). Put your data next to this repo, or inside it:

```
../data/          or  ./data/
../datasets/      or  ./datasets/
```

This project will find either layout automatically.

## Run

From the repo folder:

```bash
python data_preprocess.py   # build training tables (needs raw data)
python train_TXP.py         # train / evaluate
```

Settings (year horizon, models, etc.) are in `preprocess/helpers.py`.

Results are written to `results/`, `checkpoints/`, `images/`, `models/`.
