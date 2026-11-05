# African Crop Yield Intelligence

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

Mean absolute error on the log yield (`mae_log`) on the test sets, against the hierarchical baseline.

| Test set | `regional` model | Baseline | `survey` model | Baseline |
|---|---:|---:|---:|---:|
| Future years, known places | 0.310 | 0.398 | 0.765 | 0.828 |
| New places, past years | 0.321 | 0.389 | 0.716 | 0.756 |
| New places, future years | 0.334 | 0.404 | 0.767 | 0.822 |
| `cropcut` direct measurements | | | 0.669 | 0.676 |

Key findings and limitations are detailed in `docs/evaluation.md`:

- Season climate explains about 1.7% of the detrended year-to-year variation of sub-national yields, which bounds what any model can gain from it.
- Survey yields are farmer-reported and exceed crop-cut measurements by about 40% for the model predictions.
- Fifteen tobacco yields of `regional` are unit errors (kilograms recorded as tonnes) that the authors' plausibility filter did not catch.
- 80% prediction intervals cover 85% of `regional` test yields and 77 to 82% of `survey` test yields.

## Installation and Setup

```bash
python3.12 -m venv venv
venv/bin/pip install -r requiremnts.txt
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

## Project Structure

```
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