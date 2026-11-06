"""
FinTrace 360 - Data Quality Validation Module
Performs comprehensive integrity, null, duplicate, and referential checks.
"""

from typing import Any
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("quality_checker")

def validate_amlsim_data(df_accounts: pd.DataFrame, df_transactions: pd.DataFrame) -> dict[str, Any]:
    """Runs a full suite of data quality checks on AMLSim accounts and transactions."""
    logger.info("Executing comprehensive data quality audit...")

    # 1. Shape and Memory
    acct_shape = df_accounts.shape
    tx_shape = df_transactions.shape
    acct_mem_mb = df_accounts.memory_usage(deep=True).sum() / (1024 * 1024)
    tx_mem_mb = df_transactions.memory_usage(deep=True).sum() / (1024 * 1024)

    # 2. Missing Values
    acct_nulls = df_accounts.isnull().sum().to_dict()
    tx_nulls = df_transactions.isnull().sum().to_dict()

    # 3. Duplicate Records
    acct_dups = int(df_accounts.duplicated().sum())
    acct_id_dups = int(df_accounts["nodeid"].duplicated().sum())
    tx_dups = int(df_transactions.duplicated().sum())

    # 4. Domain & Range Validations
    invalid_init_bal = int((df_accounts["init_balance"] < 0).sum())
    invalid_tx_amounts = int((df_transactions["value"] <= 0).sum())
    invalid_steps = int((df_transactions["time"] < 0).sum())

    # 5. Referential Integrity Check
    valid_nodes = set(df_accounts["nodeid"].unique())
    orphan_sources = int((~df_transactions["sourceNodeId"].isin(valid_nodes)).sum())
    orphan_targets = int((~df_transactions["targetNodeId"].isin(valid_nodes)).sum())

    # 6. Self-loops (source == target)
    self_loops = int((df_transactions["sourceNodeId"] == df_transactions["targetNodeId"]).sum())

    # 7. Class Distribution (Fraud / AML Alerts)
    fraud_counts = df_accounts["isFraud"].value_counts().to_dict()
    fraud_rate = float(df_accounts["isFraud"].mean()) * 100.0

    report = {
        "accounts": {
            "total_rows": acct_shape[0],
            "total_columns": acct_shape[1],
            "memory_mb": round(acct_mem_mb, 2),
            "missing_values": acct_nulls,
            "duplicate_rows": acct_dups,
            "duplicate_node_ids": acct_id_dups,
            "negative_balances": invalid_init_bal,
            "benign_count": int(fraud_counts.get(0, 0)),
            "alerted_count": int(fraud_counts.get(1, 0)),
            "alert_rate_pct": round(fraud_rate, 2),
            "min_balance": round(float(df_accounts["init_balance"].min()), 2),
            "max_balance": round(float(df_accounts["init_balance"].max()), 2),
            "mean_balance": round(float(df_accounts["init_balance"].mean()), 2),
        },
        "transactions": {
            "total_rows": tx_shape[0],
            "total_columns": tx_shape[1],
            "memory_mb": round(tx_mem_mb, 2),
            "missing_values": tx_nulls,
            "duplicate_rows": tx_dups,
            "non_positive_amounts": invalid_tx_amounts,
            "negative_time_steps": invalid_steps,
            "orphan_source_accounts": orphan_sources,
            "orphan_target_accounts": orphan_targets,
            "self_loops": self_loops,
            "min_step": int(df_transactions["time"].min()),
            "max_step": int(df_transactions["time"].max()),
            "min_amount": round(float(df_transactions["value"].min()), 2),
            "max_amount": round(float(df_transactions["value"].max()), 2),
            "mean_amount": round(float(df_transactions["value"].mean()), 2),
            "total_gross_value": round(float(df_transactions["value"].sum()), 2),
        },
        "overall_quality_status": "PASSED" if (
            acct_dups == 0 and acct_id_dups == 0 and tx_dups == 0 and
            sum(acct_nulls.values()) == 0 and sum(tx_nulls.values()) == 0 and
            orphan_sources == 0 and orphan_targets == 0 and
            invalid_init_bal == 0 and invalid_tx_amounts == 0
        ) else "WARNINGS_FOUND"
    }

    logger.info(f"Quality Audit Completed: Status={report['overall_quality_status']}")
    return report
