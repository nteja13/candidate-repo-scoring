from pathlib import Path
import pickle

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = PROJECT_ROOT / "model" / "model.pkl"
SCORING_DATA_PATH = PROJECT_ROOT / "data" / "accounts_to_score.csv"


REQUIRED_FEATURES = [
    "account_type",
    "employee_count",
    "industry",
    "intent_score",
    "mql_count_90d",
    "trial_started",
    "trial_active_users",
    "web_touchpoints_90d",
    "sales_contacts_90d",
]

def load_model(model_path: Path = MODEL_PATH):
    """Load the pre-trained account conversion model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at: {model_path}")

    with open(model_path, "rb") as file:
        model = pickle.load(file)

    return model


def load_accounts(data_path: Path = SCORING_DATA_PATH) -> pd.DataFrame:
    """Load accounts to score and validate required model features."""
    if not data_path.exists():
        raise FileNotFoundError(f"Scoring data not found at: {data_path}")

    accounts = pd.read_csv(data_path)

    missing_columns = [
        column for column in REQUIRED_FEATURES
        if column not in accounts.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required model features: {missing_columns}"
        )

    return accounts

def score_accounts(model, accounts: pd.DataFrame) -> pd.DataFrame:
    """Score accounts and rank them by predicted conversion probability."""
    scored_accounts = accounts.copy()

    probabilities = model.predict_proba(
        scored_accounts[REQUIRED_FEATURES]
    )[:, 1]

    scored_accounts["conversion_probability"] = probabilities

    scored_accounts = scored_accounts.sort_values(
        by="conversion_probability",
        ascending=False,
    ).reset_index(drop=True)

    return scored_accounts


if __name__ == "__main__":
    model = load_model()
    accounts = load_accounts()
    scored_accounts = score_accounts(model, accounts)

    print(f"Model loaded successfully: {type(model).__name__}")
    print(f"Accounts loaded successfully: {len(accounts)}")

    print("\nTop 10 scored accounts:")
    print(
        scored_accounts[
            ["account_id", "conversion_probability"]
        ].head(10).to_string(index=False)
    )