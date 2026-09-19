# Sales Account Prioritization Agent

## 1. Business Problem and Impact

Cordilla Systems has thousands of accounts, while sales representatives have limited time to decide which accounts deserve attention. The goal is not to classify accounts as definitively "good" or "bad," but to use the supplied conversion model as a ranking signal that helps representatives decide which accounts to work next.

The historical dataset contains 1,200 accounts, of which 78 converted within 90 days, giving a 6.5% conversion rate. When ranked using the supplied model, the top 10% contained 32 of the 78 observed conversions. Thus, 10% of historical accounts contained approximately 41% of all conversions, with a 26.67% conversion rate.

As an illustrative capacity scenario, consider working 30 accounts from a batch of 300. Thirty accounts at the historical overall rate correspond to approximately 1.95 conversions, while 30 performing at the historical top-decile rate correspond to approximately 8 conversions—a difference of roughly six.

**Potential incremental value = incremental conversions × average economic value per conversion**

No value per converted account is provided, so I would not invent a dollar estimate. The six-conversion difference is a hypothesis, not a forecast: the ranking analysis is in-sample and the fresh batch has no outcomes.

A false positive wastes limited sales capacity, while a false negative may delay or miss a promising account. Therefore, the model prioritizes work rather than automatically accepting or rejecting accounts, and the representative remains the final decision-maker.

## 2. Agent Design

I built a LangGraph workflow that converts the supplied model output into an actionable, capacity-limited sales queue.

The workflow has four stages:

1. **Score accounts:** Load the supplied scikit-learn pipeline and score all 300 accounts using `predict_proba()`. The existing pipeline handles categorical encoding and numeric missing-value imputation.

2. **Select the priority queue:** Rank accounts by model score and select accounts up to configurable sales capacity. The demo uses 20 accounts, avoiding an invented probability cutoff.

3. **Recommend an action:** Assign `PRIORITIZE_OUTREACH` when there has been no recorded sales contact in the previous 90 days and `FOLLOW_UP` when an existing sales motion is present. Supporting evidence includes MQL activity, trial usage, web touchpoints, and sales contacts.

4. **Generate a rep brief:** Pass the predetermined action and grounded evidence through a mocked LLM boundary. The mock includes an explicit prompt, response validation, and deterministic fallback. The LLM generates rep-facing language but does not determine ranking or sales actions.

The workflow writes `agent/sales_priority_queue.csv`, which acts as a prototype CRM integration boundary. In production, equivalent output could create Salesforce tasks.

The score is treated as a ranking signal rather than a guaranteed conversion probability. Missing intent data is not treated as negative intent because missing values are expected and handled by the supplied pipeline.

## 3. Tools and Framework Choices

The supplied scikit-learn model is used unchanged because retraining and tuning are outside scope. Pandas handles data processing and queue generation.

LangGraph makes the workflow explicit: scoring → queue selection → action recommendation → rep brief. Plain Python would support this simple sequence, but LangGraph provides an extension point for future CRM tools, approvals, retries, or branching.

The mocked LLM is limited to brief generation. Its input contains only the predetermined action and grounded evidence. The response is validated, with deterministic generation used as fallback. A production LLM could therefore replace the mocked call without changing the ranking or decision logic.

## 4. Deployment Approach

In production, I would integrate the workflow with Salesforce. A scheduled job could retrieve eligible accounts, execute scoring and prioritization, and write priority, action, and supporting context back as tasks or account fields.

Queue size should be configurable according to representative capacity. Each scoring run should retain model version, timestamp, score, rank, recommendation, experiment group, and relevant input snapshot for auditing and later outcome analysis.

For initial rollout, accounts can be reproducibly assigned either to agent-assisted prioritization or a business-as-usual holdout. Both groups may continue normal sales activity; the distinction is whether the new agent drives prioritization. Outcomes can then be compared after the 90-day conversion window.

## 5. Monitoring and Failure Detection

Monitoring covers input quality, population drift, prediction behavior, and eventual outcomes.

**Data quality:** The implementation checks required columns, duplicate account IDs, and intent-score missingness. Intent missingness was approximately 40.2% historically and 38.7% currently. The prototype warns above 60%, while missing required columns or duplicates are failures.

**Feature and prediction drift:** Numeric feature means are compared with historical data. Relative changes above 25% generate warnings. `trial_active_users` decreased approximately 26.5% and therefore warns. This threshold is an operational heuristic rather than a statistically validated boundary.

Historical mean model score is approximately 0.0661 versus 0.0655 currently, a -0.9% relative change, so prediction-score drift passes. The feature warning warrants investigation but does not by itself imply model failure.

**Outcome monitoring and feedback-loop detection:** Inputs and scores can remain stable while their relationship with conversions deteriorates. This matters because `sales_contacts_90d` is a model feature and future values may be influenced by sales activity triggered by the agent.

The implementation therefore assigns approximately 10% of accounts to a reproducible business-as-usual holdout using hash-based assignment. All accounts can still be scored, but the holdout is not prioritized by the new agent. Once 90-day outcomes become available, I would compare agent-assisted and holdout outcomes and verify that high-ranked cohorts continue to concentrate conversions. This helps separate ranking quality from effects introduced by the sales workflow.

Input failures should stop the affected scoring run. Warnings should allow scoring to continue while triggering investigation. Sustained outcome deterioration should trigger review rather than automatic retraining.

## 6. Assumptions and Next Steps

The 20-account queue, 10% holdout probability, 25% drift threshold, and 60% intent-missingness threshold are prototype choices rather than validated business thresholds.

Before broader rollout, I would validate ranking using new 90-day outcomes, compare agent-assisted and business-as-usual groups, agree on queue capacity with Sales Operations, obtain economic value per conversion for ROI measurement, and collect representative feedback.

The goal is not full sales automation. It is to make prioritization more consistent, measurable, and observable while preserving representative judgment. If prospective results demonstrate sustained value, the workflow can expand to richer Salesforce integration and a production LLM while preserving grounded inputs, validation, and deterministic fallback.