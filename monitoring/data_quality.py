from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCORING_DATA_PATH = PROJECT_ROOT / "data" / "accounts_to_score.csv"


REQUIRED_COLUMNS = [
    "account_id",
    "account_type",
    "snapshot_date",
    "employee_count",
    "industry",
    "intent_score",
    "mql_count_90d",
    "trial_started",
    "trial_active_users",
    "web_touchpoints_90d",
    "sales_contacts_90d",
]


def check_required_columns(df: pd.DataFrame) -> dict:
    """Check whether all expected input columns are present."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    return {
        "check": "required_columns",
        "status": "FAIL" if missing_columns else "PASS",
        "missing_columns": missing_columns,
    }
    

def check_duplicate_accounts(df: pd.DataFrame) -> dict:
    """Check for duplicate account IDs in the scoring batch."""
    duplicate_count = int(df["account_id"].duplicated().sum())

    return {
        "check": "duplicate_accounts",
        "status": "FAIL" if duplicate_count > 0 else "PASS",
        "duplicate_count": duplicate_count,
    }
    
def check_intent_missingness(
    df: pd.DataFrame,
    warning_threshold: float = 0.60,
) -> dict:
    """Check whether intent-score coverage has degraded substantially."""
    missing_rate = float(df["intent_score"].isna().mean())

    return {
        "check": "intent_score_missingness",
        "status": "WARN" if missing_rate > warning_threshold else "PASS",
        "missing_rate": round(missing_rate, 4),
        "warning_threshold": warning_threshold,
    }
    
    
if __name__ == "__main__":
    accounts = pd.read_csv(SCORING_DATA_PATH)

    checks = [
        check_required_columns(accounts),
        check_duplicate_accounts(accounts),
        check_intent_missingness(accounts),
    ]

    print("Data Quality Monitoring")
    print("-" * 40)

    for check in checks:
        print(check)