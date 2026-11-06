"""
FinTrace 360 - Power BI Data Export Pipeline
Prepares self-contained, pre-aggregated analytical datasets for direct Power BI Desktop ingestion.
"""

from pathlib import Path
import pandas as pd
from src.config.settings import POWERBI_DIR, PROCESSED_DATA_DIR
from src.utils.logger import setup_logger

logger = setup_logger("export_powerbi_data")

def export_powerbi_datasets():
    """Generates targeted analytical CSV datasets for each Power BI dashboard page."""
    logger.info("Exporting pre-configured data models for Power BI dashboards...")

    # Load clean data
    df_acc = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_accounts_clean.csv")
    df_tx = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_transactions_clean.csv")
    df_feats = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_account_features.csv")

    # 1. Dashboard 1: Executive Overview Dataset
    pbi_exec_dir = POWERBI_DIR / "executive_overview"
    pbi_exec_dir.mkdir(parents=True, exist_ok=True)
    daily_exec = df_tx.groupby(["step_day", "transaction_date", "originator_bank_id", "transaction_type"]).agg(
        total_tx=("transaction_id", "count"),
        gross_volume=("amount", "sum"),
        avg_amount=("amount", "mean"),
        alerted_tx=("is_alerted_tx", "sum"),
        alerted_volume=("amount", lambda s: s[df_tx.loc[s.index, "is_alerted_tx"] == 1].sum())
    ).reset_index()
    daily_exec.to_csv(pbi_exec_dir / "executive_daily_trends.csv", index=False)
    logger.info(f"Exported Executive Overview dataset to: {pbi_exec_dir}")

    # 2. Dashboard 2: Transaction Behaviour Dataset
    pbi_tx_dir = POWERBI_DIR / "transaction_analytics"
    pbi_tx_dir.mkdir(parents=True, exist_ok=True)
    tx_behaviour = df_tx[[
        "transaction_id", "source_account_id", "target_account_id", "amount",
        "step_day", "transaction_timestamp", "originator_bank_id", "beneficiary_bank_id",
        "is_interbank", "transaction_type", "is_alerted_tx"
    ]].copy()
    # Amount Tier
    tx_behaviour["amount_tier"] = pd.cut(
        tx_behaviour["amount"],
        bins=[0, 50, 100, 250, 400, 1000],
        labels=["Micro (<$50)", "Low ($50-100)", "Medium ($100-250)", "High ($250-400)", "Commercial ($400+)"]
    )
    tx_behaviour.to_csv(pbi_tx_dir / "transactions_behaviour_sample.csv", index=False)
    logger.info(f"Exported Transaction Behaviour dataset to: {pbi_tx_dir}")

    # 3. Dashboard 3: AML Risk Analytics Dataset
    pbi_risk_dir = POWERBI_DIR / "aml_risk_analytics"
    pbi_risk_dir.mkdir(parents=True, exist_ok=True)
    # Risk priority classification
    df_risk = df_feats.copy()
    def assign_priority(row: pd.Series) -> str:
        if row["turnover_ratio"] >= 100.0 and row["in_tx_count"] >= 20:
            return "CRITICAL - HIGH VELOCITY FAN-IN HUB"
        elif row["turnover_ratio"] >= 50.0:
            return "ELEVATED - EXCESSIVE TURNOVER"
        elif row["is_sar_alert"] == 1:
            return "PRIORITY - TOPOLOGY ALERT (CYCLE/FAN-IN)"
        else:
            return "STANDARD MONITORING"

    df_risk["investigation_priority"] = df_risk.apply(assign_priority, axis=1)
    df_risk.to_csv(pbi_risk_dir / "aml_risk_triage_queue.csv", index=False)
    logger.info(f"Exported AML Risk Analytics dataset to: {pbi_risk_dir}")

if __name__ == "__main__":
    export_powerbi_datasets()
