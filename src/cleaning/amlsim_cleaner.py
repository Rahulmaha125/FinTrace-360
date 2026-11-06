"""
FinTrace 360 - AMLSim Data Cleaning and Standardization Pipeline
Transforms raw simulated benchmark data into standardized analytical entities.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from src.config.settings import PROCESSED_DATA_DIR, RANDOM_STATE
from src.utils.logger import setup_logger

logger = setup_logger("amlsim_cleaner")

def clean_and_standardize_amlsim(
    df_accounts: pd.DataFrame,
    df_transactions: pd.DataFrame,
    base_date: str = "2023-01-01"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cleans, enriches, and standardizes AMLSim accounts and transactions."""
    logger.info("Initiating standardization and dimensional enrichment...")
    np.random.seed(RANDOM_STATE)

    # 1. Accounts Standardization
    df_acc = df_accounts.copy()
    df_acc.rename(
        columns={
            "nodeid": "account_id",
            "isFraud": "is_sar_alert",
            "init_balance": "initial_balance",
            "fraudStep": "sar_start_step"
        },
        inplace=True
    )

    # Dimensional attributes (simulated institutions & segment types)
    banks = ["BNK_ALPHA", "BNK_BETA", "BNK_GAMMA", "BNK_DELTA", "BNK_EPSILON"]
    bank_weights = [0.35, 0.25, 0.20, 0.12, 0.08]
    df_acc["bank_id"] = np.random.choice(banks, size=len(df_acc), p=bank_weights)

    # Account Segmentation
    # Commercial accounts: higher initial balance
    def assign_segment(bal: float) -> str:
        if bal >= 450.0:
            return "Commercial"
        elif bal >= 250.0:
            return "Private Banking"
        else:
            return "Retail"

    df_acc["account_segment"] = df_acc["initial_balance"].apply(assign_segment)
    df_acc["country_code"] = "US"
    df_acc["account_status"] = "ACTIVE"

    # 2. Transactions Standardization
    df_tx = df_transactions.copy()
    df_tx.reset_index(drop=True, inplace=True)
    df_tx["transaction_id"] = df_tx.index + 1

    df_tx.rename(
        columns={
            "sourceNodeId": "source_account_id",
            "targetNodeId": "target_account_id",
            "value": "amount",
            "time": "step_day"
        },
        inplace=True
    )

    # Timestamp synthesis from base_date and step_day
    start_ts = pd.to_datetime(base_date)
    # Add step_day as days offset, plus pseudo-random hour/minute during business hours
    pseudo_hours = np.random.randint(8, 20, size=len(df_tx))
    pseudo_minutes = np.random.randint(0, 60, size=len(df_tx))
    df_tx["transaction_timestamp"] = (
        start_ts
        + pd.to_timedelta(df_tx["step_day"] - 1, unit="D")
        + pd.to_timedelta(pseudo_hours, unit="h")
        + pd.to_timedelta(pseudo_minutes, unit="m")
    )
    df_tx["transaction_date"] = df_tx["transaction_timestamp"].dt.date

    # Cross-reference bank IDs
    acct_bank_map = df_acc.set_index("account_id")["bank_id"].to_dict()
    df_tx["originator_bank_id"] = df_tx["source_account_id"].map(acct_bank_map)
    df_tx["beneficiary_bank_id"] = df_tx["target_account_id"].map(acct_bank_map)
    df_tx["is_interbank"] = (df_tx["originator_bank_id"] != df_tx["beneficiary_bank_id"]).astype(int)

    # Transaction Type assignment based on amount and interbank status
    def assign_tx_type(row: pd.Series) -> str:
        amt = row["amount"]
        inter = row["is_interbank"]
        if amt >= 400.0:
            return "WIRE"
        elif inter == 1:
            return "ACH_TRANSFER"
        elif amt < 50.0:
            return "INSTANT_PAY"
        else:
            return "INTERNAL_TRANSFER"

    df_tx["transaction_type"] = df_tx.apply(assign_tx_type, axis=1)

    # Alert flag propagation on transaction level
    acct_fraud_map = df_acc.set_index("account_id")["is_sar_alert"].to_dict()
    acct_step_map = df_acc.set_index("account_id")["sar_start_step"].to_dict()

    src_fraud = df_tx["source_account_id"].map(acct_fraud_map)
    dst_fraud = df_tx["target_account_id"].map(acct_fraud_map)
    src_step = df_tx["source_account_id"].map(acct_step_map)
    dst_step = df_tx["target_account_id"].map(acct_step_map)

    # A transaction is an alerted transaction if either counterparty is alerted AND tx occurs on/after alert step
    is_alerted = (
        ((src_fraud == 1) & (df_tx["step_day"] >= src_step)) |
        ((dst_fraud == 1) & (df_tx["step_day"] >= dst_step))
    ).astype(int)
    df_tx["is_alerted_tx"] = is_alerted

    logger.info(
        f"Standardization Complete: Clean Accounts={df_acc.shape}, "
        f"Clean Transactions={df_tx.shape}, Alerted Txs={int(df_tx['is_alerted_tx'].sum())} "
        f"({df_tx['is_alerted_tx'].mean()*100:.2f}%)"
    )

    return df_acc, df_tx

def save_clean_datasets(
    df_acc: pd.DataFrame,
    df_tx: pd.DataFrame,
    output_dir: Path | None = None
) -> tuple[Path, Path]:
    """Exports clean standardized datasets to CSV."""
    out_dir = output_dir or PROCESSED_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    acc_path = out_dir / "amlsim_accounts_clean.csv"
    tx_path = out_dir / "amlsim_transactions_clean.csv"

    logger.info(f"Saving cleaned accounts to: {acc_path}")
    df_acc.to_csv(acc_path, index=False)

    logger.info(f"Saving cleaned transactions to: {tx_path}")
    df_tx.to_csv(tx_path, index=False)

    return acc_path, tx_path
