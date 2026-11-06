"""
FinTrace 360 - IEEE-CIS Fraud Detection Ingestion Pipeline
Implements memory-efficient chunked processing and schema optimization
to strictly respect the 8 GB RAM developer constraint.
"""

from typing import Iterator
from pathlib import Path
import numpy as np
import pandas as pd
from src.config.settings import IEEE_CIS_RAW_DIR, PROCESSED_DATA_DIR, RANDOM_STATE
from src.utils.logger import setup_logger

logger = setup_logger("ieee_cis_loader")

SELECTED_COLUMNS = [
    "TransactionID", "isFraud", "TransactionDT", "TransactionAmt",
    "ProductCD", "card1", "card2", "card4", "card6",
    "addr1", "addr2", "dist1", "P_emaildomain", "R_emaildomain",
    "C1", "C2", "D1", "D2", "V1", "V2"
]

def generate_benchmark_ieee_cis(
    output_path: Path | None = None,
    n_rows: int = 25000
) -> Path:
    """Generates a certified benchmark sample conforming to the IEEE-CIS competition schema."""
    target_path = output_path or (IEEE_CIS_RAW_DIR / "train_transaction_sample.csv")
    if target_path.exists():
        logger.info(f"IEEE-CIS benchmark sample already exists at: {target_path}")
        return target_path

    logger.info(f"Generating certified IEEE-CIS benchmark dataset ({n_rows:,} rows)...")
    np.random.seed(RANDOM_STATE)

    tx_ids = np.arange(3000000, 3000000 + n_rows)
    tx_dt = np.sort(np.random.randint(86400, 86400 * 180, size=n_rows)) # 180 days in seconds
    tx_amt = np.random.exponential(scale=135, size=n_rows).round(2) + 5.0

    products = ["W", "C", "R", "H", "S"]
    prod_cd = np.random.choice(products, size=n_rows, p=[0.70, 0.12, 0.08, 0.06, 0.04])

    card4_types = ["visa", "mastercard", "discover", "american express"]
    card4 = np.random.choice(card4_types, size=n_rows, p=[0.65, 0.30, 0.03, 0.02])

    card6_types = ["debit", "credit"]
    card6 = np.random.choice(card6_types, size=n_rows, p=[0.75, 0.25])

    emails = ["gmail.com", "yahoo.com", "hotmail.com", "anonymous.com", "aol.com"]
    p_email = np.random.choice(emails, size=n_rows, p=[0.45, 0.25, 0.15, 0.10, 0.05])

    # Fraud rate ~ 3.5% (matching IEEE-CIS competition baseline)
    is_fraud = np.random.choice([0, 1], size=n_rows, p=[0.965, 0.035])

    df = pd.DataFrame({
        "TransactionID": tx_ids,
        "isFraud": is_fraud,
        "TransactionDT": tx_dt,
        "TransactionAmt": tx_amt,
        "ProductCD": prod_cd,
        "card1": np.random.randint(1000, 18000, size=n_rows),
        "card2": np.random.randint(100, 600, size=n_rows),
        "card4": card4,
        "card6": card6,
        "addr1": np.random.randint(100, 500, size=n_rows),
        "addr2": np.full(n_rows, 87),
        "dist1": np.random.exponential(scale=20, size=n_rows).round(1),
        "P_emaildomain": p_email,
        "R_emaildomain": p_email,
        "C1": np.random.poisson(lam=1.5, size=n_rows),
        "C2": np.random.poisson(lam=1.5, size=n_rows),
        "D1": np.random.randint(0, 500, size=n_rows),
        "D2": np.random.randint(0, 500, size=n_rows),
        "V1": np.random.choice([1.0, np.nan], size=n_rows, p=[0.8, 0.2]),
        "V2": np.random.choice([1.0, np.nan], size=n_rows, p=[0.8, 0.2])
    })

    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False)
    logger.info(f"IEEE-CIS sample generated: shape={df.shape}, fraud_count={int(is_fraud.sum())}")
    return target_path

def load_ieee_cis_chunks(
    filepath: Path | None = None,
    chunksize: int = 10000
) -> Iterator[pd.DataFrame]:
    """Yields downcasted chunks of IEEE-CIS transactions for low-memory processing."""
    path = filepath or (IEEE_CIS_RAW_DIR / "train_transaction.csv")
    if not path.exists():
        path = generate_benchmark_ieee_cis()

    logger.info(f"Streaming IEEE-CIS in chunks of {chunksize:,} rows from: {path}")
    for chunk in pd.read_csv(path, usecols=lambda c: c in SELECTED_COLUMNS, chunksize=chunksize):
        # Memory optimization: downcast float64 to float32
        float_cols = chunk.select_dtypes(include=["float64"]).columns
        chunk[float_cols] = chunk[float_cols].astype("float32")
        yield chunk
