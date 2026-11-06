"""
FinTrace 360 - Feature Engineering Pipeline
Constructs behavioral, transactional, and network features for risk analytics and ML.
"""

from pathlib import Path
import pandas as pd
from src.config.settings import PROCESSED_DATA_DIR
from src.utils.logger import setup_logger

logger = setup_logger("amlsim_features")

def build_account_features(df_accounts: pd.DataFrame, df_transactions: pd.DataFrame) -> pd.DataFrame:
    """Computes comprehensive account-level behavioural, velocity, and network features."""
    logger.info("Computing account-level transactional and graph network features...")

    # Aggregations for Outgoing (Sender) Transactions
    out_agg = df_transactions.groupby("source_account_id").agg(
        out_tx_count=("transaction_id", "count"),
        total_outflow=("amount", "sum"),
        avg_outflow=("amount", "mean"),
        max_outflow=("amount", "max"),
        std_outflow=("amount", "std"),
        unique_beneficiaries=("target_account_id", "nunique"),
        active_days_out=("step_day", "nunique")
    ).reset_index().rename(columns={"source_account_id": "account_id"})

    # Aggregations for Incoming (Receiver) Transactions
    in_agg = df_transactions.groupby("target_account_id").agg(
        in_tx_count=("transaction_id", "count"),
        total_inflow=("amount", "sum"),
        avg_inflow=("amount", "mean"),
        max_inflow=("amount", "max"),
        std_inflow=("amount", "std"),
        unique_originators=("source_account_id", "nunique"),
        active_days_in=("step_day", "nunique")
    ).reset_index().rename(columns={"target_account_id": "account_id"})

    # Merge with base accounts
    feats = df_accounts.merge(out_agg, on="account_id", how="left")
    feats = feats.merge(in_agg, on="account_id", how="left")

    # Fill NaNs for accounts with no incoming or outgoing transactions
    numeric_fill_cols = [
        "out_tx_count", "total_outflow", "avg_outflow", "max_outflow", "std_outflow",
        "unique_beneficiaries", "active_days_out",
        "in_tx_count", "total_inflow", "avg_inflow", "max_inflow", "std_inflow",
        "unique_originators", "active_days_in"
    ]
    feats[numeric_fill_cols] = feats[numeric_fill_cols].fillna(0.0)

    # Derived Behavioral Ratios & Velocity
    feats["total_tx_count"] = feats["out_tx_count"] + feats["in_tx_count"]
    feats["total_volume"] = feats["total_outflow"] + feats["total_inflow"]
    feats["net_flow"] = feats["total_inflow"] - feats["total_outflow"]
    feats["flow_ratio"] = feats["total_inflow"] / (feats["total_outflow"] + 1.0)
    feats["unique_counterparties"] = feats["unique_beneficiaries"] + feats["unique_originators"]
    feats["total_active_days"] = feats[["active_days_out", "active_days_in"]].max(axis=1)
    feats["tx_velocity_per_day"] = feats["total_tx_count"] / (feats["total_active_days"] + 1.0)

    # Structuring & Fan-out / Fan-in Indicators
    # Fan-in index: High incoming count with few or zero outgoing
    feats["fan_in_index"] = feats["in_tx_count"] / (feats["out_tx_count"] + 1.0)
    # Fan-out index: High outgoing count with few incoming
    feats["fan_out_index"] = feats["out_tx_count"] / (feats["in_tx_count"] + 1.0)

    # Rapid turnover velocity
    feats["turnover_ratio"] = feats["total_volume"] / (feats["initial_balance"] + 1.0)

    logger.info(f"Feature Engineering Complete: Account Features shape={feats.shape}")
    return feats

def save_features(df_features: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Saves engineered features to CSV."""
    out_dir = output_dir or PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "amlsim_account_features.csv"
    df_features.to_csv(out_path, index=False)
    logger.info(f"Saved engineered features to: {out_path}")
    return out_path
