# Sales Account Prioritization Agent

## 1. Business Problem and Impact

Cordilla Systems has thousands of customer and non-customer accounts, while sales representatives have limited time to decide which accounts deserve attention. The goal is not to classify accounts as definitively "good" or "bad," but to use the supplied conversion model as a ranking signal that helps representatives decide which accounts to work next.

The historical dataset contains 1,200 accounts, of which 78 converted within 90 days, giving an overall conversion rate of 6.5%. When ranked using the supplied model, the top 10% contained 32 of the 78 observed conversions. Therefore, 10% of historical accounts contained approximately 41% of all conversions, with a 26.67% conversion rate in that group.

As an illustrative capacity scenario, consider a representative able to work 30 accounts from a batch of 300. Thirty accounts at the historical overall rate correspond to approximately 1.95 conversions, while 30 accounts performing at the historical top-decile rate correspond to approximately 8 conversions—a difference of roughly six conversions.

**Potential incremental value = incremental conversions × average economic value per conversion**

Cordilla's value per converted account is not provided, so I would not invent a dollar estimate. The six-conversion difference is a hypothesis, not a forecast: the ranking analysis is in-sample and the fresh 300-account batch has no conversion outcomes. It should therefore be validated prospectively.

A false positive consumes sales capacity on an account that does not convert, while a false negative may delay or prevent outreach to an account that would have converted. For this reason, the model prioritizes work rather than automatically accepting or rejecting accounts, and the representative remains the final decision-maker.

## 2. Agent Design

The supplied model produces a conversion score, but a score alone does not tell a representative what to do. I built a small LangGraph workflow that converts model output into an actionable, capacity-limited sales queue.

The workflow has four stages:

1. **Score accounts:** Load the supplied scikit-learn pipeline and score all 300 accounts using `predict_proba()`. The existing pipeline already handles categorical encoding and numeric missing-value imputation.

2. **Select the priority queue:** Rank accounts by model score and select the highest-ranked accounts up to a configurable capacity. The demo uses 20 accounts. Capacity-based ranking avoids inventing an unvalidated probability threshold.

3. **Recommend an action:** For selected accounts, assign `PRIORITIZE_OUTREACH` when there has been no recorded sales contact in the previous 90 days and `FOLLOW_UP` when an existing sales motion is present. Recommendations include observed evidence such as MQL activity, trial usage, web touchpoints, and sales contacts.

4. **Generate a rep brief:** Convert the structured recommendation into a concise explanation and next step. This step is deterministic in the prototype rather than using an external LLM, keeping the demo reproducible and free of API credentials.

The workflow produces `agent/sales_priority_queue.csv` containing account ID, model score, action, supporting reasons, and next step. This acts as the prototype CRM integration boundary; in production, the same output could create Salesforce tasks.

The score is treated as a ranking signal rather than a guaranteed probability of conversion. Missing intent data is also not interpreted as negative intent because missing values are expected and handled by the supplied model pipeline.

## 3. Tools and Framework Choices

I used the supplied scikit-learn pipeline unchanged because model retraining and tuning were outside the exercise scope. Pandas handles data loading, ranking, monitoring, and queue generation.

LangGraph makes the post-model workflow explicit: scoring → queue selection → action recommendation → rep brief. Plain Python could support the current sequential workflow, but LangGraph provides a clean extension point for future CRM tools, approvals, retries, or decision branches without requiring that complexity today.

I deliberately avoided a live LLM dependency. Scoring, ranking, queue selection, and action selection are deterministic and testable. An LLM could later personalize rep communication, but it should operate only on grounded account evidence rather than invent reasons for prioritization.

## 4. Deployment Approach

In production, I would integrate the workflow with Salesforce rather than introduce a separate application. A scheduled job could retrieve eligible accounts, execute scoring and prioritization, and write priority, recommended action, and supporting context back as Salesforce tasks or account fields.

The schedule should follow the refresh frequency of the underlying signals, and queue size should be configurable according to team or representative capacity rather than fixed at 20.

Each scoring run should retain the model version, timestamp, score, rank, recommendation, and relevant input snapshot. This creates an audit trail and allows recommendations to be connected to eventual 90-day conversion outcomes.

I would initially roll out to a limited representative group, measure adoption and conversion outcomes, and compare the prioritized workflow with the existing process before broader deployment.

## 5. Monitoring and Failure Detection

Monitoring addresses three failure modes: bad input data, changes in the scoring population, and deterioration in the relationship between ranking and actual conversions.

**Data quality:** The implementation checks required columns, duplicate account IDs, and intent-score missingness. Intent missingness was approximately 40.2% historically and 38.7% in the current batch. The prototype warns above 60% missingness, while missing required columns or duplicate account IDs are treated as failures.

**Feature and prediction drift:** Numeric feature means are compared with historical reference data. A relative change greater than 25% generates a warning for investigation. `trial_active_users` decreased approximately 26.5% in the current batch and therefore triggers a warning. The threshold is an operational heuristic, not a statistically validated boundary.

The historical mean model score is approximately 0.0661 versus 0.0655 for the current batch, only about a -0.9% relative change, so prediction-score drift currently passes. The feature warning therefore warrants investigation but does not by itself imply model failure.

**Outcome monitoring:** Input and prediction drift cannot detect every failure. Scores could remain stable while their relationship with real conversions deteriorates. Once 90-day labels become available, I would join outcomes to stored scoring runs and monitor whether high-ranked cohorts continue to concentrate conversions. Sustained deterioration across multiple cohorts should trigger investigation rather than automatic retraining.

Input failures should stop the affected scoring run, while warnings should allow scoring to continue with an investigation alert. This avoids treating normal variation as an outage while making silent degradation visible.

## 6. Assumptions and Next Steps

The 20-account queue, 25% drift threshold, and 60% intent-missingness threshold are prototype operating choices rather than validated business thresholds.

Before broader rollout, I would validate ranking performance using new 90-day outcomes, agree on queue capacity with Sales Operations, obtain the economic value per conversion for ROI measurement, and define ownership for monitoring alerts. Representative feedback should also be collected to determine whether recommendations are useful in the actual sales workflow.

The initial goal is not full sales automation. It is to make account prioritization more consistent, measurable, and observable while preserving representative judgment. If prospective results demonstrate sustained value, the workflow can then expand to richer Salesforce integration and carefully grounded LLM-based personalization.