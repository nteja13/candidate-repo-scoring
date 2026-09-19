# Cordilla Sales Account Prioritization Agent

A lightweight sales prioritization agent that uses Cordilla's existing account-conversion model to turn model scores into an actionable sales work queue.

The solution scores accounts, ranks them against configurable sales capacity, recommends deterministic sales actions, generates grounded rep-facing briefs through a mocked LLM boundary, and monitors the scoring pipeline for data-quality, drift, and eventual outcome issues.

## What the Agent Does

The workflow is implemented with LangGraph:

```text
Account batch
    ↓
Score accounts
    ↓
Rank by model score
    ↓
Select priority queue
    ↓
Recommend deterministic action
    ├── PRIORITIZE_OUTREACH
    └── FOLLOW_UP
    ↓
Generate grounded rep brief
    (mocked LLM + validation + fallback)
    ↓
Sales priority queue
```

The demo selects the top 20 accounts as the active work queue. Accounts outside the capacity-limited queue are not surfaced for agent-assisted action and effectively remain in the existing nurture/business-as-usual process.

The generated queue is saved to:

```text
agent/sales_priority_queue.csv
```

This CSV acts as the prototype CRM integration boundary. In production, equivalent recommendations could be written back to Salesforce as tasks or account fields.

## Repository Structure

```text
candidate-repo-scoring/
├── agent/
│   ├── agent.py
│   ├── scoring.py
│   ├── llm_mock.py
│   └── sales_priority_queue.csv
├── data/
│   ├── accounts_to_score.csv
│   └── training_data.csv
├── model/
│   └── model.pkl
├── monitoring/
│   ├── data_quality.py
│   ├── drift.py
│   └── holdout.py
├── PROPOSAL.md
├── RESEARCH-LOG.md
├── requirements.txt
└── README.md
```

## Setup

Python 3.11 is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No external LLM API credentials are required because the prototype uses a mocked LLM boundary.

## Run the Agent

From the repository root:

```bash
python agent/agent.py
```

The agent:

1. Loads the supplied scikit-learn model.
2. Scores the 300 accounts in `accounts_to_score.csv`.
3. Ranks accounts by model score.
4. Selects a configurable priority queue.
5. Deterministically recommends outreach or follow-up actions.
6. Passes the action and grounded evidence to the mocked LLM for rep-facing brief generation.
7. Validates generated output and provides a deterministic fallback.
8. Writes the priority queue to `agent/sales_priority_queue.csv`.

The LLM does not determine account ranking or sales actions. Its role is limited to turning already-grounded recommendations into concise rep-facing language.

## Run Monitoring

Run the data-quality checks:

```bash
python monitoring/data_quality.py
```

Checks include:

- Required input columns
- Duplicate account IDs
- Intent-score missingness

Run the drift checks:

```bash
python monitoring/drift.py
```

These compare the current scoring batch with historical reference data and report numeric feature drift and prediction-score drift.

Run the experimental holdout assignment:

```bash
python monitoring/holdout.py
```

The holdout module reproducibly assigns approximately 10% of accounts to a business-as-usual comparison group. On the current 300-account batch, the assignment produces 271 agent-assisted accounts and 29 holdout accounts.

The holdout does not mean "no sales contact." It represents normal sales handling without agent-assisted prioritization. The current module demonstrates reproducible assignment and future outcome comparison; it is not yet connected to the agent's CRM-routing path.

Because the current scoring batch does not yet contain 90-day conversion outcomes, holdout evaluation reports `WAITING_FOR_LABELS`. Once outcomes mature, agent-assisted and holdout results can be compared.

Warnings are intended to trigger investigation rather than automatically stop scoring. Structural failures such as missing required input fields should prevent the affected scoring run.

## Key Historical Finding

The historical dataset contains 1,200 accounts with a 6.5% overall 90-day conversion rate.

When ranked by the supplied model, the top 10% of accounts contained approximately 41% of all observed conversions, with a 26.67% conversion rate.

These results are in-sample and are treated as directional evidence for prioritization, not as expected future performance.

## Design Principles

- Use the existing model as a ranking signal rather than a binary decision-maker.
- Allocate sales attention based on configurable rep capacity rather than an arbitrary probability threshold.
- Keep scoring, ranking, and business-action logic deterministic and testable.
- Use the mocked LLM only for grounded rep-facing language generation.
- Validate generated LLM output and retain a deterministic fallback.
- Keep the representative as the final decision-maker.
- Monitor input quality, feature drift, and prediction drift.
- Use prospective outcomes and a business-as-usual holdout to evaluate incremental impact and possible feedback-loop effects.

See [`PROPOSAL.md`](PROPOSAL.md) for the business case, architecture, deployment approach, and monitoring strategy.

See [`RESEARCH-LOG.md`](RESEARCH-LOG.md) for analysis, hypotheses, AI-assisted research decisions, corrections, and assumptions.