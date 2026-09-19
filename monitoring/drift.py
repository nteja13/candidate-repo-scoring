from pathlib import Path
import pandas as pd
import pickle


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "model" / "model.pkl"
TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "training_data.csv"
SCORING_DATA_PATH = PROJECT_ROOT / "data" / "accounts_to_score.csv"


NUMERIC_FEATURES = [
    "employee_count",
    "intent_score",
    "mql_count_90d",
    "trial_started",
    "trial_active_users",
    "web_touchpoints_90d",
    "sales_contacts_90d",
]

def compare_numeric_means(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compare numeric feature means between reference and current data."""
    results = []

    for feature in NUMERIC_FEATURES:
        reference_mean = reference_df[feature].mean()
        current_mean = current_df[feature].mean()

        if reference_mean == 0:
            relative_change = 0.0
        else:
            relative_change = (
                (current_mean - reference_mean) / reference_mean
            )

        results.append(
            {
                "feature": feature,
                "reference_mean": reference_mean,
                "current_mean": current_mean,
                "relative_change": relative_change,
            }
        )

    return pd.DataFrame(results)


def add_drift_status(
    drift_report: pd.DataFrame,
    warning_threshold: float = 0.25,
) -> pd.DataFrame:
    """Flag large relative changes for investigation."""
    report = drift_report.copy()

    report["status"] = report["relative_change"].apply(
        lambda change: (
            "WARN"
            if abs(change) > warning_threshold
            else "PASS"
        )
    )
    return report



def compare_prediction_scores(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
) -> dict:
    """Compare model score distributions between reference and current data."""
    with open(MODEL_PATH, "rb") as file:
        model = pickle.load(file)

    reference_scores = model.predict_proba(reference_df)[:, 1]
    current_scores = model.predict_proba(current_df)[:, 1]

    reference_mean = float(reference_scores.mean())
    current_mean = float(current_scores.mean())

    relative_change = (
        (current_mean - reference_mean) / reference_mean
        if reference_mean != 0
        else 0.0
    )

    return {
        "check": "prediction_score_drift",
        "reference_mean_score": round(reference_mean, 4),
        "current_mean_score": round(current_mean, 4),
        "relative_change": round(relative_change, 4),
        "status": "WARN" if abs(relative_change) > 0.25 else "PASS",
    }


if __name__ == "__main__":
    reference_df = pd.read_csv(TRAINING_DATA_PATH)
    current_df = pd.read_csv(SCORING_DATA_PATH)

    # 1. Numeric feature drift
    drift_report = compare_numeric_means(
        reference_df,
        current_df,
    )

    drift_report = add_drift_status(drift_report)

    print("Numeric Feature Drift")
    print("-" * 70)

    print(
        drift_report.to_string(
            index=False,
            formatters={
                "reference_mean": "{:.3f}".format,
                "current_mean": "{:.3f}".format,
                "relative_change": "{:+.1%}".format,
            },
        )
    )

    # 2. Prediction score drift
    prediction_drift = compare_prediction_scores(
        reference_df,
        current_df,
    )

    print("\nPrediction Score Drift")
    print("-" * 70)
    print(prediction_drift)