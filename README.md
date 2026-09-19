# Cordilla Sales Account Prioritization Agent

A lightweight sales prioritization agent that uses Cordilla's existing account-conversion model to turn model scores into an actionable sales work queue.

The solution scores accounts, ranks them against configurable sales capacity, recommends an action, generates grounded rep-facing context, and monitors the scoring pipeline for data-quality and drift issues.

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
Recommend action
    ├── PRIORITIZE_OUTREACH
    └── FOLLOW_UP
    ↓
Generate grounded rep brief
    ↓
Sales priority queue
```

The demo selects the top 20 accounts as the active work queue. Accounts outside the capacity-limited queue are not actioned and effectively remain in nurture until a future scoring cycle.

The generated queue is saved to:

```text
agent/sales_priority_queue.csv
```

This CSV acts as the prototype CRM integration boundary. In production, the same output could be written back to Salesforce as tasks or account fields.

## Repository Structure

```text
candidate-repo-scoring/
├── agent/
│   ├── agent.py
│   ├── scoring.py
│   └── sales_priority_queue.csv
├── data/
│   ├── accounts_to_score.csv
│   └── training_data.csv
├── model/
│   └── model.pkl
├── monitoring/
│   ├── data_quality.py
│   └── drift.py
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
5. Recommends outreach or follow-up actions.
6. Generates grounded rep-facing briefs.
7. Writes the resulting queue to `agent/sales_priority_queue.csv`.

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

Warnings are intended to trigger investigation rather than automatically stop scoring. Structural failures such as missing required input fields should prevent the affected scoring run.

## Key Historical Finding

The historical dataset contains 1,200 accounts with a 6.5% overall 90-day conversion rate.

When ranked by the supplied model, the top 10% of accounts contained approximately 41% of all observed conversions, with a 26.67% conversion rate.

These results are in-sample and are treated as directional evidence for prioritization, not as expected future performance.

## Design Principles

- Use the existing model as a ranking signal rather than a binary decision-maker.
- Allocate sales attention based on configurable rep capacity rather than an arbitrary probability threshold.
- Keep scoring and business-action logic separate.
- Ground recommendations in observed account data.
- Keep the representative as the final decision-maker.
- Monitor both the inputs and the model's outputs.
- Validate ranking quality against actual conversions once 90-day outcomes become available.

See [`PROPOSAL.md`](PROPOSAL.md) for the business case, architecture, deployment approach, and monitoring strategy.

See [`RESEARCH-LOG.md`](RESEARCH-LOG.md) for analysis, hypotheses, AI-assisted research decisions, corrections, and assumptions.