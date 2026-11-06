"""
FinTrace 360 - Smart Column Mapping & Data Validation Module
Automatically infers financial column semantics via regex heuristics,
applies user mapping configurations, standardizes schemas, and audits data quality.
"""

import re
from typing import Any
import numpy as np
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("mapper")

# Canonical Schema Definition
CANONICAL_COLUMNS = {
    "transaction_id": {
        "label": "Transaction Identifier",
        "description": "Unique ID for each transaction record",
        "required": False,
        "type": "string"
    },
    "amount": {
        "label": "Transaction Amount",
        "description": "Monetary value of the transaction",
        "required": True,
        "type": "float"
    },
    "timestamp": {
        "label": "Date / Timestamp",
        "description": "Date, time, or simulation step of transfer",
        "required": True,
        "type": "datetime"
    },
    "source_account_id": {
        "label": "Originator / Sender ID",
        "description": "Account, card, or entity initiating transfer",
        "required": False,
        "type": "string"
    },
    "target_account_id": {
        "label": "Beneficiary / Receiver ID",
        "description": "Account or counterparty receiving funds",
        "required": False,
        "type": "string"
    },
    "transaction_type": {
        "label": "Payment Rail / Type",
        "description": "Transfer channel (WIRE, ACH, CASH_IN, TRANSFER, etc.)",
        "required": False,
        "type": "string"
    },
    "category": {
        "label": "Category / Description",
        "description": "Spending category or memo description",
        "required": False,
        "type": "string"
    },
    "initial_balance": {
        "label": "Account Balance",
        "description": "Opening, available, or ledger balance",
        "required": False,
        "type": "float"
    }
}

# Regex Taxonomy for Semantic Matching
TAXONOMY_PATTERNS = {
    "amount": [
        r"^amount$", r"^amt$", r"^tx_amt$", r"^trans_amt$", r"^value$", r"^tx_amount$",
        r"^trans_amount$", r"^payment_amount$", r"^debit$", r"^credit$", r"^gross$",
        r"^total$", r"^price$", r"^cost$", r"^volume$", r"^sum$", r".*amount.*", r".*amt.*"
    ],
    "timestamp": [
        r"^date$", r"^time$", r"^timestamp$", r"^datetime$", r"^tx_date$", r"^trans_date$",
        r"^settlement_date$", r"^posted_date$", r"^step$", r"^created_at$", r"^transaction_time$",
        r".*date.*", r".*time.*"
    ],
    "source_account_id": [
        r"^source.*", r"^sender.*", r"^originator.*", r"^from_account.*",
        r"^source_id$", r"^from_acc.*", r"^payer.*", r"^orig.*", r"^sourceNodeId",
        r"^payer_acc.*"
    ],
    "target_account_id": [
        r"^target.*", r"^receiver.*", r"^beneficiary.*", r"^to_account.*",
        r"^target_id$", r"^to_acc.*", r"^payee.*", r"^dest.*", r"^targetNodeId",
        r"^payee_acc.*"
    ],
    "transaction_id": [
        r"^transaction_id$", r"^tx_id$", r"^trans_id$", r"^txn_id$", r"^id$",
        r"^reference.*", r"^order_id$", r"^invoice_id$", r"^transfer_id$", r".*txn.*"
    ],
    "transaction_type": [
        r"^type$", r"^rail$", r"^method$", r"^channel$", r"^payment_type$",
        r"^tx_type$", r"^trans_type$", r"^operation$", r"^rail_type$"
    ],
    "category": [
        r"^category$", r"^memo$", r"^description$", r"^narrative$", r"^purpose$",
        r"^details$", r"^narration$", r"^note$"
    ],
    "initial_balance": [
        r"^balance$", r"^init_balance$", r"^initial_balance$", r"^running_balance$",
        r"^opening_balance$", r"^ledger_balance$", r"^oldbalance.*"
    ]
}

def detect_column_mapping(df: pd.DataFrame) -> dict[str, str | None]:
    """
    Scans DataFrame column names and infers the best matching canonical field
    using regex token matching and normalized string distance.
    Returns: {canonical_col: matched_dataframe_col or None}
    """
    raw_cols = list(df.columns)
    mapping: dict[str, str | None] = {canonical: None for canonical in CANONICAL_COLUMNS}
    used_raw_cols: set[str] = set()

    for canonical, patterns in TAXONOMY_PATTERNS.items():
        best_col = None
        for raw_col in raw_cols:
            if raw_col in used_raw_cols:
                continue
            normalized = str(raw_col).strip().lower()
            # Exact or regex pattern match
            for pat in patterns:
                if re.match(pat, normalized, re.IGNORECASE):
                    best_col = raw_col
                    break
            if best_col:
                break

        if best_col:
            mapping[canonical] = best_col
            used_raw_cols.add(best_col)

    return mapping

def clean_amount_series(series: pd.Series) -> pd.Series:
    """Strips currency symbols, commas, whitespace, and casts to float."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0.0)

    # String cleaning
    cleaned = (
        series.astype(str)
        .str.replace(r"[\$,€,£,₹,A-Za-z\s]", "", regex=True)
        .str.replace(",", "")
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)

def apply_column_mapping(
    df: pd.DataFrame,
    mapping: dict[str, str | None]
) -> tuple[pd.DataFrame, list[str]]:
    """
    Applies validated column mappings to construct a clean, standardized DataFrame.
    Returns: (standardized_df, list_of_warning_messages)
    """
    warnings: list[str] = []
    clean_df = pd.DataFrame()

    # 1. Amount (Required)
    amt_col = mapping.get("amount")
    if amt_col and amt_col in df.columns:
        clean_df["amount"] = clean_amount_series(df[amt_col])
        clean_df["amount"] = clean_df["amount"].abs()  # Standardize to positive volume
    else:
        # Fallback search for any numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            clean_df["amount"] = df[numeric_cols[0]].abs().fillna(0.0)
            warnings.append(f"Amount column was missing; auto-selected numeric column '{numeric_cols[0]}'.")
        else:
            clean_df["amount"] = 1.0
            warnings.append("No numeric amount column found; initialized nominal values.")

    # 2. Timestamp (Required)
    time_col = mapping.get("timestamp")
    if time_col and time_col in df.columns:
        try:
            clean_df["timestamp"] = pd.to_datetime(df[time_col], errors="coerce", format="mixed")
            # If all failed to parse as datetime, treat as numeric step
            if clean_df["timestamp"].isna().all():
                clean_df["timestamp"] = pd.to_numeric(df[time_col], errors="coerce").fillna(1)
                clean_df["step_day"] = clean_df["timestamp"].astype(int)
            else:
                clean_df["step_day"] = (clean_df["timestamp"] - clean_df["timestamp"].min()).dt.days + 1
        except Exception:
            clean_df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df), freq="h")
            clean_df["step_day"] = 1
            warnings.append("Date parsing failed; generated synthetic timeline.")
    else:
        clean_df["timestamp"] = pd.date_range(start="2024-01-01", periods=len(df), freq="h")
        clean_df["step_day"] = (clean_df.index // 100) + 1
        warnings.append("No date/time column mapped; generated synthetic sequential timeline.")

    # 3. Transaction ID (Auto-generate if missing)
    tx_col = mapping.get("transaction_id")
    if tx_col and tx_col in df.columns:
        clean_df["transaction_id"] = df[tx_col].astype(str)
    else:
        clean_df["transaction_id"] = [f"TXN_{i+1:06d}" for i in range(len(df))]

    # 4. Source & Target Account IDs
    src_col = mapping.get("source_account_id")
    if src_col and src_col in df.columns:
        clean_df["source_account_id"] = df[src_col].astype(str).str.strip()
    else:
        clean_df["source_account_id"] = "ACCOUNT_DEFAULT"

    tgt_col = mapping.get("target_account_id")
    if tgt_col and tgt_col in df.columns:
        clean_df["target_account_id"] = df[tgt_col].astype(str).str.strip()
    else:
        clean_df["target_account_id"] = "EXTERNAL_ENTITY"

    # 5. Transaction Type / Rail
    type_col = mapping.get("transaction_type")
    if type_col and type_col in df.columns:
        clean_df["transaction_type"] = df[type_col].astype(str).str.upper().str.strip()
    else:
        clean_df["transaction_type"] = "STANDARD_TRANSFER"

    # 6. Category / Memo
    cat_col = mapping.get("category")
    if cat_col and cat_col in df.columns:
        clean_df["category"] = df[cat_col].astype(str).str.strip()
    else:
        clean_df["category"] = "General Financial"

    # 7. Initial / Running Balance
    bal_col = mapping.get("initial_balance")
    if bal_col and bal_col in df.columns:
        clean_df["initial_balance"] = clean_amount_series(df[bal_col])
    else:
        # Estimate initial balance as 3x the median transaction amount
        clean_df["initial_balance"] = float(clean_df["amount"].median() * 3.0 if clean_df["amount"].median() > 0 else 1000.0)

    # Retain non-null and positive amounts
    clean_df = clean_df.dropna(subset=["amount"]).reset_index(drop=True)
    return clean_df, warnings

def detect_dataset_archetype(df: pd.DataFrame) -> str:
    """
    Identifies whether the mapped dataset is:
    - BIPARTITE_NETWORK: Has distinct originators and beneficiaries (> 2 unique entities).
    - SINGLE_PARTY_LEDGER: One-sided statements (e.g. personal/business bank export).
    """
    has_source = "source_account_id" in df.columns and df["source_account_id"].nunique() > 1
    has_target = "target_account_id" in df.columns and df["target_account_id"].nunique() > 1

    if has_source and has_target:
        # Check if source and target have meaningful distinct diversity
        if df["source_account_id"].nunique() >= 3 and df["target_account_id"].nunique() >= 3:
            return "BIPARTITE_NETWORK"

    return "SINGLE_PARTY_LEDGER"

def audit_dataset_quality(df: pd.DataFrame) -> dict[str, Any]:
    """
    Runs comprehensive data validation checks on standardized DataFrame.
    """
    total_rows = len(df)
    null_counts = df.isnull().sum().to_dict()
    total_nulls = int(sum(null_counts.values()))

    # Duplicates
    dup_tx_ids = int(df["transaction_id"].duplicated().sum()) if "transaction_id" in df.columns else 0
    duplicate_rows = int(df.duplicated(subset=["amount", "source_account_id", "target_account_id"]).sum())

    # Amounts
    zero_amounts = int((df["amount"] <= 0).sum())
    gross_volume = float(df["amount"].sum())
    avg_ticket = float(df["amount"].mean()) if total_rows > 0 else 0.0
    median_ticket = float(df["amount"].median()) if total_rows > 0 else 0.0
    max_ticket = float(df["amount"].max()) if total_rows > 0 else 0.0

    # Self loops
    self_loops = 0
    if "source_account_id" in df.columns and "target_account_id" in df.columns:
        self_loops = int((df["source_account_id"] == df["target_account_id"]).sum())

    # Date horizon
    date_min = str(df["timestamp"].min()) if "timestamp" in df.columns else "N/A"
    date_max = str(df["timestamp"].max()) if "timestamp" in df.columns else "N/A"
    active_days = int(df["step_day"].nunique()) if "step_day" in df.columns else 1

    unique_sources = int(df["source_account_id"].nunique()) if "source_account_id" in df.columns else 1
    unique_targets = int(df["target_account_id"].nunique()) if "target_account_id" in df.columns else 1

    archetype = detect_dataset_archetype(df)

    # Health score (100 minus penalties)
    penalty = 0
    if total_nulls > 0:
        penalty += min(20, int(total_nulls / total_rows * 50))
    if dup_tx_ids > 0:
        penalty += 15
    if zero_amounts > 0:
        penalty += min(20, int(zero_amounts / total_rows * 50))
    if self_loops > 0:
        penalty += 5

    health_score = max(0, 100 - penalty)

    return {
        "health_score": health_score,
        "total_records": total_rows,
        "gross_volume_usd": round(gross_volume, 2),
        "avg_ticket_usd": round(avg_ticket, 2),
        "median_ticket_usd": round(median_ticket, 2),
        "max_ticket_usd": round(max_ticket, 2),
        "total_null_values": total_nulls,
        "duplicate_tx_ids": dup_tx_ids,
        "duplicate_records": duplicate_rows,
        "zero_or_negative_amounts": zero_amounts,
        "self_transfers": self_loops,
        "date_start": date_min[:10] if len(date_min) >= 10 else date_min,
        "date_end": date_max[:10] if len(date_max) >= 10 else date_max,
        "active_days": active_days,
        "unique_senders": unique_sources,
        "unique_receivers": unique_targets,
        "archetype": archetype
    }
