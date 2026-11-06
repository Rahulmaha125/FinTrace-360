"""
FinTrace 360 - Dynamic Anomaly Detection Engine (Unsupervised)
Trains an on-the-fly Isolation Forest model on arbitrary uploaded financial transactions,
identifying statistical outliers, sudden volume spikes, and unusual behavioral patterns.
"""

from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler
from src.utils.logger import setup_logger

logger = setup_logger("dynamic_anomaly")

def detect_transaction_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.03,
    sample_limit: int = 50000
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Applies unsupervised anomaly detection to arbitrary transaction records.
    Returns: (df_with_anomaly_columns, model_metadata)
    """
    df_out = df.copy()
    n_records = len(df_out)

    if n_records < 10:
        # Too few records for statistical isolation
        df_out["is_anomaly"] = 0
        df_out["anomaly_score"] = 0.0
        df_out["anomaly_tier"] = "NOMINAL"
        df_out["anomaly_reasons"] = "Insufficient sample size (<10 records)"
        return df_out, {"status": "SKIPPED_SMALL_SAMPLE", "anomaly_count": 0}

    # 1. Feature Extraction
    features = pd.DataFrame(index=df_out.index)
    features["amount"] = df_out["amount"].fillna(0.0)
    features["log_amount"] = np.log1p(features["amount"])

    # Mean ratio
    mean_val = features["amount"].mean()
    features["ratio_to_mean"] = features["amount"] / (mean_val + 1e-5)

    # Rolling local deviation (detect spikes within local sequence)
    features["rolling_zscore"] = (
        (features["amount"] - features["amount"].rolling(window=10, min_periods=1).mean())
        / (features["amount"].rolling(window=10, min_periods=1).std().fillna(1.0) + 1e-5)
    ).clip(-10, 10)

    # Velocity / step delta
    if "step_day" in df_out.columns:
        features["step_day"] = df_out["step_day"].fillna(1)
    else:
        features["step_day"] = 1

    feature_cols = ["log_amount", "ratio_to_mean", "rolling_zscore"]

    # Sample if dataset is very large to protect memory
    if n_records > sample_limit:
        sample_indices = df_out.sample(n=sample_limit, random_state=42).index
        X_train = features.loc[sample_indices, feature_cols]
    else:
        X_train = features[feature_cols]

    # Robust scaling
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_all_scaled = scaler.transform(features[feature_cols])

    # 2. Fit Isolation Forest
    iso = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    iso.fit(X_train_scaled)

    # Raw decision function: lower means more anomalous
    raw_scores = iso.decision_function(X_all_scaled)
    preds = iso.predict(X_all_scaled)  # -1 is anomaly, 1 is normal

    df_out["is_anomaly"] = np.where(preds == -1, 1, 0)

    # Convert raw score to 0 - 100 Risk Score (100 = most anomalous)
    # raw_scores typically range from -0.3 to +0.3
    min_s, max_s = raw_scores.min(), raw_scores.max()
    norm_score = 100.0 * (1.0 - (raw_scores - min_s) / (max_s - min_s + 1e-9))
    df_out["anomaly_score"] = np.round(norm_score, 1)

    # 3. Risk Tiers
    p95 = np.percentile(df_out["anomaly_score"], 95)
    p85 = np.percentile(df_out["anomaly_score"], 85)

    def assign_tier(score: float, is_anom: int) -> str:
        if is_anom == 1 or score >= p95:
            return "CRITICAL OUTLIER"
        elif score >= p85:
            return "ELEVATED ANOMALY"
        elif score >= 50:
            return "MODERATE"
        else:
            return "NOMINAL"

    df_out["anomaly_tier"] = [assign_tier(s, a) for s, a in zip(df_out["anomaly_score"], df_out["is_anomaly"])]

    # 4. Human-readable explainability reasoning
    p99_amt = df_out["amount"].quantile(0.99)
    p95_amt = df_out["amount"].quantile(0.95)

    reasons = []
    for _, row in df_out.iterrows():
        r = []
        if row["amount"] >= p99_amt:
            r.append(f"Monetary volume in top 1% (>${p99_amt:,.2f})")
        elif row["amount"] >= p95_amt:
            r.append(f"Monetary volume in top 5% (>${p95_amt:,.2f})")

        if row["anomaly_score"] >= p95:
            r.append("Multivariate statistical outlier in sequence")

        if not r:
            if row["is_anomaly"] == 1:
                r.append("Isolation Forest density outlier")
            else:
                r.append("Within expected operational parameters")

        reasons.append(" • ".join(r))

    df_out["anomaly_reasons"] = reasons

    metadata = {
        "status": "COMPLETED",
        "total_evaluated": n_records,
        "anomalies_detected": int(df_out["is_anomaly"].sum()),
        "contamination_rate_pct": round(contamination * 100, 1),
        "critical_outliers": int((df_out["anomaly_tier"] == "CRITICAL OUTLIER").sum()),
        "elevated_outliers": int((df_out["anomaly_tier"] == "ELEVATED ANOMALY").sum()),
        "max_anomaly_score": float(df_out["anomaly_score"].max()),
        "algorithm": "Isolation Forest (Unsupervised Ensembles)"
    }

    logger.info(f"Anomaly Detection Complete: {metadata['anomalies_detected']} outliers flagged.")
    return df_out, metadata
