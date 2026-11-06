"""
FinTrace 360 - AMLSim Ingestion Module
Handles robust loading of raw AMLSim accounts and transactions data.
"""

from pathlib import Path
import pandas as pd
from src.config.settings import AMLSIM_RAW_DIR
from src.utils.logger import setup_logger

logger = setup_logger("amlsim_loader")

def load_raw_accounts(filepath: Path | None = None) -> pd.DataFrame:
    """Loads raw AMLSim accounts dataset."""
    path = filepath or (AMLSIM_RAW_DIR / "accounts.csv")
    if not path.exists():
        raise FileNotFoundError(f"Accounts file not found at: {path}")

    logger.info(f"Loading raw accounts from: {path}")
    df = pd.read_csv(
        path,
        dtype={
            "nodeid": "int64",
            "isFraud": "int8",
            "init_balance": "float64",
            "fraudStep": "int64",
        }
    )
    logger.info(f"Loaded accounts: shape={df.shape}, memory={df.memory_usage().sum() / (1024*1024):.2f} MB")
    return df

def load_raw_transactions(filepath: Path | None = None) -> pd.DataFrame:
    """Loads raw AMLSim transactions dataset."""
    path = filepath or (AMLSIM_RAW_DIR / "transactions.csv")
    if not path.exists():
        raise FileNotFoundError(f"Transactions file not found at: {path}")

    logger.info(f"Loading raw transactions from: {path}")
    df = pd.read_csv(
        path,
        dtype={
            "sourceNodeId": "int64",
            "targetNodeId": "int64",
            "value": "float64",
            "time": "int64",
        }
    )
    logger.info(f"Loaded transactions: shape={df.shape}, memory={df.memory_usage().sum() / (1024*1024):.2f} MB")
    return df
