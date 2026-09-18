# Research Log

## Initial setup

### Hypothesis

The provided conversion model should be treated as an existing scoring capability rather than something to retrain or optimize. The first step is to understand what signal it provides and whether that signal can support a useful sales prioritization workflow.

### Initial approach

1. Inspect the provided training and scoring data.
2. Inspect the existing model pipeline.
3. Quantify whether the model provides useful ranking signal.
4. Design an agent around the useful signal found in the data.
5. Add monitoring for silent degradation.

### AI assistance

This project is being developed with AI-assisted coding/research. Specific prompts, outputs, corrections, and decisions will be recorded here as the work progresses.

## Data exploration — training data

### Dataset overview

- Training dataset contains 1,200 historical accounts.
- 78 accounts converted within 90 days, giving a baseline conversion rate of 6.5%.
- Account mix:
  - 632 Prospects
  - 402 Suspects
  - 166 Former Customers
- Intent score is missing for 482 of 1,200 accounts (~40.2%), confirming that this signal has incomplete coverage.

### Initial business findings

- Accounts that started a trial converted at 9.87%, compared with 5.73% for accounts without a trial.
- Conversion rates by account type were relatively close:
  - Former Customer: 7.23%
  - Prospect: 6.65%
  - Suspect: 5.97%
- Converted accounts showed somewhat higher average engagement signals, including sales contacts, web touchpoints, trial active users, and intent score.
- These are descriptive associations only and should not be interpreted as causal effects.

### Working hypothesis

Individual engagement signals show some relationship with conversion, but none appears sufficient on its own. The existing model may provide business value if combining these signals produces a useful ranking of accounts for sales prioritization.

### AI assistance

Prompt/context:
Asked AI to guide step-by-step exploration of the provided training dataset and interpret the conversion baseline, missing intent coverage, account-type conversion rates, trial conversion rates, and engagement differences.

AI contribution:
Suggested descriptive analysis of conversion rate, missingness, account segments, trial behavior, and engagement signals.

Decision:
Kept the analysis descriptive and avoided treating correlations as causal relationships or performing unnecessary model retraining/optimization.

## Existing model inspection

### Model structure

The provided `model.pkl` is a scikit-learn Pipeline containing:

- One-hot encoding for `account_type` and `industry`.
- Median imputation for numeric features, including missing `intent_score`.
- A GradientBoostingClassifier as the final estimator.

The pipeline already handles missing numeric values, so the application should pass the raw model features to the supplied pipeline rather than duplicating preprocessing.

### Historical ranking analysis

The model was scored against the provided training data to understand whether its output could support account prioritization.

Observed results:

- Overall historical conversion rate: 6.5% (78 / 1,200).
- Top 10% by model score:
  - 120 accounts
  - 32 conversions
  - 26.67% conversion rate
  - ~4.1x the overall historical conversion rate
  - Captured ~41.0% of all historical conversions.
- Top 25% by model score: 16.33% conversion rate.
- Bottom 50% by model score: 2.83% conversion rate.
- In-sample ROC-AUC: ~0.759.

### Interpretation

The historical results suggest that the existing model provides a useful ranking signal. This supports using the model to prioritize a limited sales outreach queue rather than treating every account equally.

These metrics were calculated on the same historical dataset used to train the supplied model. Therefore, they are directional evidence of ranking usefulness and should not be presented as expected future or production performance.