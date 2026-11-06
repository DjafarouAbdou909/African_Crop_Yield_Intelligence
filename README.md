# African Crop Yield Intelligence

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![LightGBM](https://img.shields.io/badge/LightGBM-4.7.0-9ACD32)
![CRISP-DM](https://img.shields.io/badge/Method-CRISP--DM-informational)
![MAE log](https://img.shields.io/badge/Regional%20MAE%20log-0.310-success)
![Skill](https://img.shields.io/badge/Skill%20vs%20baseline-%2B22%25-success)
![Tests](https://img.shields.io/badge/Tests-106%20passing-brightgreen)

## Overview and Objectives

**African Crop Yield Intelligence** is a Machine Learning project focused on predicting agricultural crop yields across Africa.

The project aims to investigate the ability of machine learning models to generalize to regions and time periods not observed during training. It also focuses on model explainability and the quantification of prediction uncertainty.

## Data and Pipeline

### Data Source

The project uses the **GROW-Africa** dataset (*Groundtruthing Remote-sensing for Optimizing Yield in Africa*).

- **Dataset repository:** [GROW-Africa on Zenodo](https://zenodo.org/records/14961637)
- **Scientific documentation:** [Article published in Scientific Data](https://www.nature.com/articles/s41597-025-05257-5)
- **Local documentation:** Available in the `docs/` directory.

The dataset consists of four main files:

- `GROW-Africa_LSMS_cropcut.csv`: Direct crop yield measurements.
- `GROW-Africa_LSMS_survey.csv`: Farmer survey data.
- `GROW-Africa_Point.csv`: Point-level crop yield data from additional sources.
- `GROW-Africa_Regional.csv`: Regional-level crop yield data.

### Data Processing Pipeline

The project follows the CRISP-DM methodology. Each phase has a notebook in `notebooks/` and a report in `docs/` (written in French).

| Phase | Notebooks | Report |
|---|---|---|
| Business Understanding | `01_business_understanding` | |
| Data Understanding | `02_data_understanding` | `data_audit_report.md`, `data_understanding.md`, `data_dictionary.md` |
| Data Preparation | `03_data_preparation` | `data_preparation.md` |
| Evaluation protocol | `04_evaluation_protocol` | `evaluation_protocol.md` |
| Explanatory variables | `05` to `09` | `explanatory_variables.md` |
| Modeling | `10_modeling` | `modeling.md` |
| Evaluation | `11_evaluation`, `12_uncertainty_interpretation` | `evaluation.md` |
| Deployment | | `deployment.md` |

Main steps:

- **Preparation.** The three yield files (`regional`, `survey`, `cropcut`) are cleaned, flagged and restricted to plausible yields. `point` is out of scope.
- **Evaluation protocol.** Grouped spatial partitions and future periods define a development set, three test sets (temporal, spatial, spatio-temporal) and five grouped folds. A hierarchical geometric mean is the baseline.
- **Explanatory variables.** GADM 4.1 boundaries, season climate from NASA POWER (MERRA-2 temperatures, radiation and wind, IMERG rainfall, FAO-56 reference evapotranspiration), SoilGrids 2.0 soil properties at 0 to 30 cm, and Copernicus DEM elevation and slope. Every downloaded file is checked against its published checksum.
- **Modeling.** LightGBM on the log yield, selected on the development set only, with the grouped cross-validation of the protocol and two internal temporal validations.
- **Evaluation.** One-time evaluation on the test sets and on the external `cropcut` validation, conformal prediction intervals and Shapley contributions.

## Model Performance

### Metrics

Both models predict a continuous yield in tonnes per hectare, so they are evaluated with regression metrics, not accuracy.

| Metric | Role |
|---|---|
| `mae_log` | Main metric. Mean absolute error on the natural log of the yield, a relative error comparable across crops |
| Typical relative error | `exp(mae_log) - 1`, the readable form of the main metric |
| MAE and RMSE (t/ha) | Errors in physical units, dominated by high-yield crops |
| Log bias | Systematic over- or under-estimation |
| R² | Share of the yield variance explained |
| Country macro average | Same weight for every country |
| Skill score | Share of the baseline `mae_log` removed by the model |
| Interval coverage | Share of observed yields inside the prediction interval |

The baseline is a hierarchical geometric mean of past yields (crop and place, then broader levels), with no explanatory variable.

### Results on the test sets

The models were selected on the development set only, frozen in a commit, then evaluated once on the test sets.

| Model | Test set | `mae_log` | Baseline | Skill | Typical relative error | MAE (t/ha) | R² |
|---|---|---:|---:|---:|---:|---:|---:|
| `regional` | Future years, known places | 0.310 | 0.398 | 22% | 36% | 0.91 | 0.77 |
| `regional` | New places, past years | 0.321 | 0.389 | 17% | 38% | 1.15 | 0.06* |
| `regional` | New places, future years | 0.334 | 0.404 | 17% | 40% | 1.12 | 0.76 |
| `survey` | Future waves, known places | 0.765 | 0.828 | 8% | 115% | 1.08 | 0.24 |
| `survey` | New places, past waves | 0.716 | 0.756 | 5% | 105% | 1.05 | 0.22 |
| `survey` | New places, future waves | 0.767 | 0.822 | 7% | 115% | 1.17 | 0.27 |
| `survey` | `cropcut` direct measurements, held-out clusters | 0.669 | 0.676 | 1% | 95% | 0.65 | |

\* Six tobacco yields recorded in kilograms instead of tonnes distort this value. Without them, R² is 0.81 and MAE 0.90 t/ha, while `mae_log` only moves from 0.321 to 0.319.

80% prediction intervals (conformal, calibrated by crop on the development set) cover 85% of `regional` test yields, with an upper to lower bound ratio of about 3, and 77 to 82% of `survey` test yields, with a ratio of about 10.

### Key findings and limitations

Details are in `docs/modeling.md` and `docs/evaluation.md`.

- The `regional` model is reliable for analysis. The `survey` model only brings a modest gain, because neighbouring plots differ widely for reasons the available variables do not capture.
- Season climate explains about 1.7% of the detrended year-to-year variation of sub-national yields, which bounds what any model can gain from it.
- The grouped spatial cross-validation of the protocol hides the value of climate, since the model learns each country and year shock from neighbouring regions of the same year. Two internal temporal validations were added on the development set.
- Survey yields are farmer-reported and exceed crop-cut measurements by about 40% for the model predictions.
- Tree models do not extrapolate the yield trend beyond 2016, the last development year of `regional`.
- Fifteen tobacco yields of `regional` are unit errors that the authors' plausibility filter did not catch. Their correction in the preparation is pending.

## Research: conformal coverage under distribution shift

A preregistered study (`docs/research_conformal_shift.md`, results in `docs/research_conformal_shift_results.md`, notebook `13_conformal_shift_study`) asks whether conformal prediction intervals keep their nominal coverage per country when the model predicts new regions or future years. The plan, the method choice and the single test evaluation were committed in that order.

- Intervals calibrated on average can be badly overconfident for one country: Sudan is covered 34% of the time at a nominal 80% on the internal benchmark.
- Country-stratified, hierarchical and difficulty-normalized conformal methods do not fix this under temporal shift. One hypothesis out of four is confirmed, three are refuted.
- The failure comes from a growing bias of the model on recent years, not from larger dispersion, so widening intervals cannot fix it. Shift detection, or adaptive conformal inference, is the natural next step.

## Installation and Setup

```bash
python3.12 -m venv venv
venv/bin/pip install -r requirements.txt
```

The GROW-Africa files are expected in `data/raw/`. External data are downloaded to `data/external/` and recorded in `data/external/registre.csv` with their SHA-256 checksum. The `data/` directory is not versioned.

## Usage

All commands run from the project root. The full sequence, with indicative durations, is given in `docs/deployment.md`.

```bash
python -m src.data.prepare                      # prepared datasets
python -m src.features.climat                   # NASA POWER series, then: python -m src.features.climat imerg
python -m src.features.variables                # season climate variables
python -m src.features.sols extraire            # SoilGrids layers, then: python -m src.features.sols construire
python -m src.features.relief extraire          # Copernicus DEM tiles, then: python -m src.features.relief construire
python -m src.features.variables_cropcut        # cropcut variables
python -m src.models.experiences regional       # model selection experiments, then: survey
python -m src.models.evaluation_finale          # final models and test evaluation
python -m src.models.prediction regional        # predictions with intervals, also: survey, cropcut
python -m unittest discover -s tests -t .       # test suite
```

### Demo application

A Streamlit application presents the `regional` model: predicted yield with 80% and 90% intervals, Shapley contributions, yearly series against observations, and test performance.

```bash
python -m app.preparer                              # export the model and features to app/ressources
streamlit run app/app.py --server.address localhost # open http://localhost:8501
```

It only needs `app/requirements.txt` and `app/ressources`, so it can be deployed on Streamlit Community Cloud with `app/app.py` as entry point.

## Project Structure

```
app/             Streamlit demo application and its exported resources
data/            raw, external, interim and processed data (not versioned)
docs/            phase reports, data dictionary and model card
notebooks/       one notebook per CRISP-DM step, 01 to 12
src/data/        loading and preparation of the GROW-Africa files
src/evaluation/  partitions, metrics and baseline of the evaluation protocol
src/features/    geography, climate, soil and terrain variables
src/models/      modeling tables, training, selection, evaluation, intervals, interpretation, prediction
tests/           unit tests
```

## References

Geyman, E. C., Ferris, A., Sahajpal, R., Anderson, W., Lee, D., & Hausmann, N. (2025). *An Africa-wide agricultural production database to support policy and satellite-based measurement systems*. Scientific Data.

- [Scientific Article](https://www.nature.com/articles/s41597-025-05257-5)
- [GROW-Africa Dataset](https://doi.org/10.5281/zenodo.14961637)