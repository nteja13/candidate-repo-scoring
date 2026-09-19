"""
Experimental holdout assignment for measuring the impact of
agent-assisted sales prioritization.

All accounts can still be scored. The holdout group represents
business-as-usual sales handling rather than agent-assisted
prioritization.

Once 90-day conversion outcomes are available, treatment and
holdout outcomes can be compared to estimate whether the agent
is creating incremental value and to detect possible
self-reinforcing feedback effects.
"""

import hashlib
import pandas as pd


HOLDOUT_FRACTION = 0.10
HOLDOUT_SEED = "cordilla-holdout-v1"


def _assignment_value(account_id: str) -> float:
    """Create a stable pseudo-random value in [0, 1) for an account."""
    value = f"{HOLDOUT_SEED}:{account_id}"
    digest = hashlib.sha256(value.encode()).hexdigest()

    return int(digest[:8], 16) / 0xFFFFFFFF


def assign_experiment_group(
    accounts: pd.DataFrame,
    holdout_fraction: float = HOLDOUT_FRACTION,
) -> pd.DataFrame:
    """
    Assign each account to agent-assisted treatment or business-as-usual holdout.

    Hash-based assignment keeps the experiment reproducible across runs.
    """
    result = accounts.copy()

    result["experiment_group"] = result["account_id"].apply(
        lambda account_id: (
            "holdout"
            if _assignment_value(str(account_id)) < holdout_fraction
            else "agent_assisted"
        )
    )

    return result


def summarize_assignment(accounts: pd.DataFrame) -> dict:
    """Summarize the experimental split."""
    counts = accounts["experiment_group"].value_counts()

    return {
        "total_accounts": len(accounts),
        "agent_assisted": int(counts.get("agent_assisted", 0)),
        "holdout": int(counts.get("holdout", 0)),
        "holdout_rate": round(
            float((accounts["experiment_group"] == "holdout").mean()),
            4,
        ),
    }


def compare_outcomes(
    accounts: pd.DataFrame,
    outcome_column: str = "converted_within_90d",
) -> dict:
    """
    Compare outcomes after the 90-day conversion window has matured.

    This cannot run on accounts_to_score.csv today because those labels
    are not yet available.
    """
    if outcome_column not in accounts.columns:
        return {
            "status": "WAITING_FOR_LABELS",
            "message": (
                "90-day conversion outcomes are not available yet. "
                "Compare treatment and holdout after the outcome window closes."
            ),
        }

    conversion_rates = accounts.groupby(
        "experiment_group"
    )[outcome_column].mean()

    return {
        "status": "READY",
        "agent_assisted_conversion_rate": round(
            float(conversion_rates.get("agent_assisted", 0)),
            4,
        ),
        "holdout_conversion_rate": round(
            float(conversion_rates.get("holdout", 0)),
            4,
        ),
    }


if __name__ == "__main__":
    from pathlib import Path

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    SCORING_DATA_PATH = PROJECT_ROOT / "data" / "accounts_to_score.csv"

    accounts = pd.read_csv(SCORING_DATA_PATH)

    assigned_accounts = assign_experiment_group(accounts)

    print("Experimental Assignment")
    print("-" * 70)
    print(summarize_assignment(assigned_accounts))

    print("\nOutcome Evaluation")
    print("-" * 70)
    print(compare_outcomes(assigned_accounts))