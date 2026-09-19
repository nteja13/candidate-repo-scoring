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

## Agent design decision

### Business decision

The model output will be used to prioritize a limited sales work queue rather than classify accounts as simply good or bad leads.

Historical analysis showed that the top 10% of model-ranked accounts contained approximately 41% of historical conversions, which supports ranking as the primary use of the model.

### Agent actions

The agent will translate model ranking and account context into three operational actions:

- `PRIORITIZE_OUTREACH`: high-ranked account with limited existing sales outreach.
- `FOLLOW_UP`: high-ranked account where sales engagement is already underway.
- `NURTURE`: account outside the current priority queue.

The priority queue will be capacity-based rather than using an arbitrary probability threshold.

### Design decision

Model scoring and sales decision logic will remain separate. Deterministic code will handle scoring, ranking, and measurable account signals. The agent layer will orchestrate these components and produce a concise explanation and suggested next step for the sales representative.

This avoids treating the model probability as a guaranteed conversion probability or introducing an unsupported classification threshold.

## Monitoring implementation

### Data-quality monitoring

Implemented executable checks for:

- Required input columns.
- Duplicate account IDs.
- Intent-score missingness.

Historical intent-score missingness is approximately 40.2%, while the current scoring batch is approximately 38.7%. Missing intent values are expected and are handled by the supplied model pipeline.

A prototype warning threshold of 60% missingness is used to detect a substantial deterioration in intent-data coverage. This is an operational heuristic rather than a statistically validated threshold.

### Feature drift

Numeric feature means were compared between the historical reference data and the current scoring batch.

Most features were relatively stable. `trial_active_users` decreased from 0.340 to 0.250, a relative change of approximately -26.5%, which triggered the prototype 25% drift warning threshold.

This warning is treated as a signal for investigation rather than evidence that the model has failed. Relative mean changes can be noisy, particularly for features with small baseline means.

### Prediction drift

The historical mean model score was approximately 0.0661 and the current batch mean score was approximately 0.0655, a relative change of approximately -0.9%.

Prediction-score drift therefore passed the prototype monitoring threshold.

### Monitoring interpretation

The current batch passes schema, duplicate, missingness, and prediction-score checks. One feature-level warning (`trial_active_users`) warrants investigation but does not by itself justify stopping scoring.

The most important long-term monitoring check requires delayed conversion labels. After the 90-day outcome window, scored accounts should be joined with actual conversion outcomes and ranking quality should be monitored over time. This is necessary to detect the dangerous case where input data and score distributions appear normal while the model's relationship with real conversion outcomes deteriorates.