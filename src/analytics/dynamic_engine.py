"""
FinTrace 360 - Dynamic Financial Analytics Engine
Computes real-time financial KPIs, time-series velocity, counterparty exposure,
and payment channel breakdowns on arbitrary standardized DataFrames.
"""

from typing import Any
import numpy as np
import pandas as pd
from src.utils.logger import setup_logger

logger = setup_logger("dynamic_engine")

def compute_executive_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes headline financial health and settlement volume indicators."""
    total_tx = len(df)
    gross_volume = float(df["amount"].sum()) if total_tx > 0 else 0.0
    avg_ticket = float(df["amount"].mean()) if total_tx > 0 else 0.0
    median_ticket = float(df["amount"].median()) if total_tx > 0 else 0.0
    max_tx = float(df["amount"].max()) if total_tx > 0 else 0.0

    # Active operational horizon
    if "timestamp" in df.columns and pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        days_span = max(1, (df["timestamp"].max() - df["timestamp"].min()).days + 1)
    elif "step_day" in df.columns:
        days_span = max(1, int(df["step_day"].max() - df["step_day"].min()) + 1)
    else:
        days_span = 1

    daily_burn_rate = gross_volume / days_span
    tx_velocity_per_day = total_tx / days_span

    # Entities
    unique_senders = df["source_account_id"].nunique() if "source_account_id" in df.columns else 1
    unique_receivers = df["target_account_id"].nunique() if "target_account_id" in df.columns else 1
    total_entities = max(unique_senders, unique_receivers)

    # Anomaly indicator if available
    anomaly_count = int(df["is_anomaly"].sum()) if "is_anomaly" in df.columns else 0
    anomaly_volume = float(df.loc[df["is_anomaly"] == 1, "amount"].sum()) if "is_anomaly" in df.columns else 0.0
    anomaly_rate_pct = (anomaly_count / total_tx * 100.0) if total_tx > 0 else 0.0

    return {
        "total_transactions": total_tx,
        "gross_volume_usd": gross_volume,
        "avg_ticket_usd": avg_ticket,
        "median_ticket_usd": median_ticket,
        "max_ticket_usd": max_tx,
        "days_span": days_span,
        "daily_burn_rate": daily_burn_rate,
        "tx_velocity_per_day": tx_velocity_per_day,
        "total_entities": total_entities,
        "unique_senders": unique_senders,
        "unique_receivers": unique_receivers,
        "anomaly_count": anomaly_count,
        "anomaly_volume_usd": anomaly_volume,
        "anomaly_rate_pct": round(anomaly_rate_pct, 2)
    }

def compute_daily_trajectory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates transactions by date/step for time-series visualization.
    Computes daily volume, transaction counts, and 7-day rolling moving averages.
    """
    df_work = df.copy()

    if "timestamp" in df_work.columns and pd.api.types.is_datetime64_any_dtype(df_work["timestamp"]):
        df_work["date_bucket"] = df_work["timestamp"].dt.date
    elif "step_day" in df_work.columns:
        df_work["date_bucket"] = df_work["step_day"].astype(str)
    else:
        df_work["date_bucket"] = "Day 1"

    # Aggregations
    agg_funcs = {
        "amount": ["sum", "count", "mean"]
    }
    if "is_anomaly" in df_work.columns:
        agg_funcs["is_anomaly"] = "sum"

    grouped = df_work.groupby("date_bucket")
    daily = grouped.agg(
        daily_volume=("amount", "sum"),
        tx_count=("amount", "count"),
        avg_amount=("amount", "mean")
    ).reset_index()

    if "is_anomaly" in df_work.columns:
        anomaly_daily = df_work[df_work["is_anomaly"] == 1].groupby("date_bucket")["amount"].sum().reset_index()
        anomaly_daily.rename(columns={"amount": "anomaly_volume"}, inplace=True)
        daily = daily.merge(anomaly_daily, on="date_bucket", how="left")
        daily["anomaly_volume"] = daily["anomaly_volume"].fillna(0.0)
    else:
        daily["anomaly_volume"] = 0.0

    # 7-period rolling volume average
    daily["rolling_avg_volume"] = daily["daily_volume"].rolling(window=7, min_periods=1).mean()
    daily["baseline_volume"] = daily["daily_volume"] - daily["anomaly_volume"]

    return daily

def compute_counterparty_exposure(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Ranks top counterparty hubs by cumulative volume and transaction frequency."""
    records = []

    if "target_account_id" in df.columns and df["target_account_id"].nunique() > 1:
        # Beneficiaries / Receivers
        recv = df.groupby("target_account_id").agg(
            total_inflow=("amount", "sum"),
            inbound_tx_count=("amount", "count"),
            avg_ticket=("amount", "mean")
        ).reset_index().rename(columns={"target_account_id": "entity_id"})
        recv["role"] = "Beneficiary (Inflow)"
        records.append(recv.sort_values(by="total_inflow", ascending=False).head(top_n))

    if "source_account_id" in df.columns and df["source_account_id"].nunique() > 1:
        # Originators / Senders
        send = df.groupby("source_account_id").agg(
            total_inflow=("amount", "sum"),
            inbound_tx_count=("amount", "count"),
            avg_ticket=("amount", "mean")
        ).reset_index().rename(columns={"source_account_id": "entity_id", "total_inflow": "total_outflow", "inbound_tx_count": "outbound_tx_count"})
        send["role"] = "Originator (Outflow)"
        records.append(send.sort_values(by="total_outflow", ascending=False).head(top_n))

    if records:
        return pd.concat(records, ignore_index=True)

    # Fallback to category if single-account ledger
    if "category" in df.columns:
        cat_agg = df.groupby("category").agg(
            total_volume=("amount", "sum"),
            tx_count=("amount", "count"),
            avg_ticket=("amount", "mean")
        ).reset_index().sort_values(by="total_volume", ascending=False).head(top_n)
        cat_agg["role"] = "Spending Category"
        cat_agg.rename(columns={"category": "entity_id"}, inplace=True)
        return cat_agg

    return pd.DataFrame()

def compute_channel_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates gross monetary volume across payment rails or transaction categories."""
    target_col = "transaction_type" if "transaction_type" in df.columns and df["transaction_type"].nunique() > 1 else "category"

    if target_col in df.columns:
        breakdown = df.groupby(target_col).agg(
            volume=("amount", "sum"),
            tx_count=("amount", "count")
        ).reset_index().rename(columns={target_col: "channel_name"})
        breakdown["pct_share"] = (breakdown["volume"] / breakdown["volume"].sum() * 100.0).round(2)
        return breakdown.sort_values(by="volume", ascending=False)

    return pd.DataFrame({"channel_name": ["Standard Settlement"], "volume": [df["amount"].sum()], "tx_count": [len(df)], "pct_share": [100.0]})
