# Research Log

## Initial Setup

### Hypothesis

The provided conversion model should be treated as an existing scoring capability rather than something to retrain or optimize. The first step is to understand what signal it provides and whether that signal can support a useful sales prioritization workflow.

### Initial Approach

1. Inspect the provided training and scoring data.
2. Inspect the existing model pipeline.
3. Quantify whether the model provides useful ranking signal.
4. Design an agent around the useful signal found in the data.
5. Add monitoring for silent degradation.

### AI Assistance

This project is being developed with AI-assisted coding/research. Specific prompts, outputs, corrections, and decisions are recorded here as the work progresses.

---

## Data Exploration — Training Data

### Dataset Overview

- Training dataset contains 1,200 historical accounts.
- 78 accounts converted within 90 days, giving a baseline conversion rate of 6.5%.
- Account mix:
  - 632 Prospects
  - 402 Suspects
  - 166 Former Customers
- Intent score is missing for 482 of 1,200 accounts (~40.2%), confirming that this signal has incomplete coverage.

### Initial Business Findings

- Accounts that started a trial converted at 9.87%, compared with 5.73% for accounts without a trial.
- Conversion rates by account type were relatively close:
  - Former Customer: 7.23%
  - Prospect: 6.65%
  - Suspect: 5.97%
- Converted accounts showed somewhat higher average engagement signals, including sales contacts, web touchpoints, trial active users, and intent score.
- These are descriptive associations only and should not be interpreted as causal effects.

### Working Hypothesis

Individual engagement signals show some relationship with conversion, but none appears sufficient on its own. The existing model may provide business value if combining these signals produces a useful ranking of accounts for sales prioritization.

### AI Assistance

**Prompt/context:**

Asked AI to guide step-by-step exploration of the provided training dataset and interpret the conversion baseline, missing intent coverage, account-type conversion rates, trial conversion rates, and engagement differences.

**AI contribution:**

Suggested descriptive analysis of conversion rate, missingness, account segments, trial behavior, and engagement signals.

**Decision:**

Kept the analysis descriptive and avoided treating correlations as causal relationships or performing unnecessary model retraining/optimization.

---

## Existing Model Inspection

### Model Structure

The provided `model.pkl` is a scikit-learn Pipeline containing:

- One-hot encoding for `account_type` and `industry`.
- Median imputation for numeric features, including missing `intent_score`.
- A GradientBoostingClassifier as the final estimator.

The pipeline already handles missing numeric values, so the application should pass the raw model features to the supplied pipeline rather than duplicating preprocessing.

### Historical Ranking Analysis

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

---

## Agent Design Decision

### Business Decision

The model output will be used to prioritize a limited sales work queue rather than classify accounts as simply good or bad leads.

Historical analysis showed that the top 10% of model-ranked accounts contained approximately 41% of historical conversions, which supports ranking as the primary use of the model.

### Agent Actions

The agent translates model ranking and account context into three operational outcomes:

- `PRIORITIZE_OUTREACH`: high-ranked account with no recorded sales outreach in the previous 90 days.
- `FOLLOW_UP`: high-ranked account where sales engagement is already underway.
- `NURTURE`: accounts outside the current priority queue are effectively left in the existing nurture/business-as-usual process rather than actively surfaced by the agent.

The priority queue is capacity-based rather than using an arbitrary probability threshold.

### Design Decision

Model scoring and sales decision logic remain separate. Deterministic code handles scoring, ranking, queue selection, and action selection. LangGraph orchestrates these components and passes the grounded recommendation to the rep-brief generation step.

This avoids treating the model probability as a guaranteed conversion probability or introducing an unsupported classification threshold.

---

## Monitoring Implementation

### Data-Quality Monitoring

Implemented executable checks for:

- Required input columns.
- Duplicate account IDs.
- Intent-score missingness.

Historical intent-score missingness is approximately 40.2%, while the current scoring batch is approximately 38.7%. Missing intent values are expected and are handled by the supplied model pipeline.

A prototype warning threshold of 60% missingness is used to detect a substantial deterioration in intent-data coverage. This is an operational heuristic rather than a statistically validated threshold.

### Feature Drift

Numeric feature means were compared between the historical reference data and the current scoring batch.

Most features were relatively stable. `trial_active_users` decreased from 0.340 to 0.250, a relative change of approximately -26.5%, which triggered the prototype 25% drift warning threshold.

This warning is treated as a signal for investigation rather than evidence that the model has failed. Relative mean changes can be noisy, particularly for features with small baseline means.

### Prediction Drift

The historical mean model score was approximately 0.0661 and the current batch mean score was approximately 0.0655, a relative change of approximately -0.9%.

Prediction-score drift therefore passed the prototype monitoring threshold.

### Monitoring Interpretation

The current batch passes schema, duplicate, missingness, and prediction-score checks. One feature-level warning (`trial_active_users`) warrants investigation but does not by itself justify stopping scoring.

Input and prediction monitoring alone cannot detect every failure. Scores could remain stable while their relationship with actual conversions deteriorates, so delayed outcome monitoring is also required.

---

## Business Impact Framing

The business decision is not whether an account is definitively "good" or "bad." The decision is which accounts sales representatives should spend limited outreach capacity on next.

Historical data contains 1,200 accounts with 78 conversions, an overall conversion rate of 6.5%. The model's top-ranked 10% contained 32 of the 78 conversions. Therefore, 10% of historical accounts contained approximately 41% of observed conversions, with a 26.67% conversion rate in that group.

As an illustrative capacity scenario, if a representative could work 30 out of a 300-account batch:

- 30 accounts at the historical overall 6.5% rate correspond to approximately 1.95 conversions.
- 30 accounts at the historical top-decile 26.67% rate correspond to approximately 8 conversions.
- The difference is approximately 6 conversions per 300-account batch.

This is a scenario for estimating potential business value, not a forecast. The ranking analysis is in-sample and the fresh scoring batch has no conversion labels. The hypothesis must be validated prospectively.

A financial estimate can be calculated once Cordilla provides the average economic value of a converted account:

**Potential incremental value = incremental conversions × average value per conversion**

False positives consume limited rep capacity on accounts that do not convert. False negatives may cause promising accounts to receive delayed or no outreach. This supports using the model as a prioritization signal with human review rather than as an automatic accept/reject decision.

---

## Feedback-Loop Evaluation

### Risk Identified

A production prioritization system can influence the same sales activity that later appears in its data. In particular, `sales_contacts_90d` is a model feature, while the agent itself is intended to influence which accounts representatives contact.

This creates a potential feedback loop: agent-prioritized accounts may receive more sales attention, making it difficult to determine whether later outcomes reflect model ranking quality, the intervention created by the agent, or both.

### Holdout Design

Implemented a reproducible hash-based experiment assignment with approximately 10% of accounts assigned to a business-as-usual holdout.

Current assignment on the 300-account scoring batch:

- Agent-assisted: 271 accounts
- Holdout: 29 accounts
- Holdout rate: approximately 9.67%

The holdout does not mean "no sales contact." It represents business-as-usual handling without agent-assisted prioritization.

The current implementation provides the assignment and future outcome-comparison mechanism. Production rollout would apply the assignment when deciding whether an account receives agent-assisted prioritization.

Because the fresh batch has no 90-day conversion labels yet, the outcome comparison currently returns `WAITING_FOR_LABELS`. Once outcomes mature, agent-assisted and holdout conversion rates can be compared alongside ranking-quality monitoring.

---

## Mocked LLM Integration

### Design Decision

Added a mocked LLM boundary for rep-facing brief generation.

The LLM is deliberately not responsible for model scoring, account ranking, queue selection, or sales-action selection. Those decisions remain deterministic and testable.

The LLM receives only the predetermined action and grounded supporting evidence and converts them into a concise brief and talk track.

The integration includes:

- An explicit system prompt.
- A structured response contract.
- Response validation.
- A deterministic fallback if generation fails or returns an invalid response.

The mocked call keeps the repository reproducible without external API credentials while exposing a clear replacement point for a production LLM.

### AI-Assisted Design Decision

External/AI-assisted review suggested strengthening the submission with an experimental holdout and a visible LLM integration.

I accepted those ideas but narrowed their scope. I rejected using the LLM to decide sales actions or introducing arbitrary probability/intent thresholds because those rules were not supported by the supplied data.

I also avoided adding unrelated policy fields, additional drift metrics, or deployment assumptions solely to make the architecture appear more complex.

The resulting design keeps the model and business decisions deterministic while using the LLM only where natural-language generation adds value.

---

## AI Correction / Override

During early AI-assisted reasoning, a rough expected model-score range of approximately 0.04–0.18 was considered before directly inspecting the supplied model output.

Running the actual repository model showed historical scores ranging approximately from 0.036 to 0.270. I discarded the rough assumption and used the measured repository values instead.

This correction also reinforced the decision not to invent a probability cutoff. The implementation uses capacity-based ranking because the supplied evidence supports relative prioritization more clearly than an arbitrary score threshold.

---

## Final Summary: Key Numbers, Hypotheses, and Assumptions

### Key Numbers

- Historical accounts: 1,200
- Historical 90-day conversions: 78
- Historical overall conversion rate: 6.5%
- Historical top 10% by model score: 120 accounts
- Conversions in historical top 10%: 32
- Historical top-decile conversion rate: 26.67%
- Share of historical conversions captured in top 10%: approximately 41%
- Fresh scoring batch: 300 accounts
- Demo sales priority queue: 20 accounts
- Experimental assignment: 271 agent-assisted / 29 holdout
- Observed holdout rate: approximately 9.67%
- Historical intent-score missingness: approximately 40.2%
- Current intent-score missingness: approximately 38.7%
- Historical mean model score: approximately 0.0661
- Current mean model score: approximately 0.0655
- Current prediction-score relative change: approximately -0.9%
- Largest observed numeric mean change: `trial_active_users`, approximately -26.5%

### Main Hypothesis

If the supplied model continues to rank future accounts meaningfully, directing limited sales capacity toward higher-ranked accounts should concentrate representative effort on accounts with stronger conversion potential.

As an illustrative scenario, 30 accounts at the historical 6.5% overall conversion rate correspond to approximately 1.95 conversions, while 30 accounts at the historical top-decile rate correspond to approximately 8 conversions.

The roughly six-conversion difference is a business-value hypothesis, not a forecast.

### Key Assumptions

- Historical behavior is sufficiently relevant to use as a reference for the current scoring population.
- The supplied model remains useful as a ranking signal; no claim is made that its scores are perfectly calibrated probabilities.
- Historical ranking results are in-sample and must not be treated as prospective performance.
- The fresh 300-account batch has no conversion labels, so current ranking quality cannot yet be measured.
- Queue size should ultimately be determined by real sales capacity; 20 accounts is a configurable prototype choice.
- The approximately 10% holdout is a prototype experiment choice. The hash-based assignment should be audited for balance before a real rollout.
- The 25% feature-drift warning threshold and 60% intent-missingness warning threshold are operational prototype heuristics, not statistically validated thresholds.
- Missing `intent_score` is expected and should not automatically be interpreted as low intent.
- The CSV output represents a mocked CRM integration boundary; production deployment would integrate with Salesforce.
- The current holdout module demonstrates reproducible assignment and future outcome comparison; it is not yet integrated into the agent's CRM-routing path.
- Rep-facing language uses a mocked LLM boundary with grounded inputs, response validation, and deterministic fallback; no external API credentials are required.
- Representatives remain the final decision-makers.

### What Should Be Validated Next

After 90-day conversion outcomes become available, join them to stored scoring results, compare agent-assisted and business-as-usual holdout outcomes, and verify that high-ranked cohorts continue to concentrate conversions.

This prospective evaluation is the key safeguard against silent degradation and possible self-reinforcing effects even when input data and prediction distributions appear stable.