"""
FinTrace 360 - Custom Ingestion & Analytics Pipeline Unit Tests
Validates parsing, mapping heuristics, validation audit, dynamic metrics, and anomaly detection.
"""

import io
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.ingestion.custom_loader import parse_uploaded_file
from src.validation.mapper import (
    detect_column_mapping, apply_column_mapping,
    detect_dataset_archetype, audit_dataset_quality
)
from src.analytics.dynamic_engine import compute_executive_kpis, compute_daily_trajectory
from src.ml.dynamic_anomaly import detect_transaction_anomalies
from src.utils.exporter import export_dataframe_to_csv, generate_executive_summary_report

def test_full_custom_pipeline():
    # 1. Create a synthetic dirty banking CSV
    csv_text = """trans_id,tx_date,payer_acc,payee_acc,tx_amt,rail_type
TXN_101,2024-01-01,ACC_1001,ACC_2001,"$1,500.50",WIRE
TXN_102,2024-01-01,ACC_1002,ACC_2001,"₹250.00",ACH
TXN_103,2024-01-02,ACC_1003,ACC_2001,"€400.00",WIRE
TXN_104,2024-01-02,ACC_1004,ACC_2002,"50.00",INSTANT
TXN_105,2024-01-03,ACC_1005,ACC_2002,"120.00",ACH
TXN_106,2024-01-03,ACC_1001,ACC_2003,"50000.00",WIRE
TXN_107,2024-01-04,ACC_1002,ACC_2003,"30.00",INSTANT
TXN_108,2024-01-04,ACC_1003,ACC_2001,"45.00",ACH
TXN_109,2024-01-05,ACC_1004,ACC_2002,"80.00",ACH
TXN_110,2024-01-05,ACC_1005,ACC_2003,"110.00",INSTANT
TXN_111,2024-01-06,ACC_1001,ACC_2001,"150.00",WIRE
TXN_112,2024-01-06,ACC_1002,ACC_2002,"90.00",ACH
"""
    raw_bytes = csv_text.encode("utf-8")

    # Ingestion
    load_res = parse_uploaded_file(raw_bytes, "test_bank_tx.csv")
    assert load_res.success is True
    assert load_res.df is not None
    assert len(load_res.df) == 12

    # Column Mapping
    mapping = detect_column_mapping(load_res.df)
    assert mapping["amount"] == "tx_amt"
    assert mapping["timestamp"] == "tx_date"
    assert mapping["source_account_id"] == "payer_acc"
    assert mapping["target_account_id"] == "payee_acc"
    assert mapping["transaction_id"] == "trans_id"

    # Application
    clean_df, warnings = apply_column_mapping(load_res.df, mapping)
    assert len(clean_df) == 12
    assert clean_df["amount"].iloc[0] == 1500.50
    assert clean_df["amount"].iloc[1] == 250.00

    # Archetype & Quality
    archetype = detect_dataset_archetype(clean_df)
    assert archetype == "BIPARTITE_NETWORK"

    audit = audit_dataset_quality(clean_df)
    assert audit["total_records"] == 12
    assert audit["gross_volume_usd"] > 50000.0

    # Dynamic Analytics
    kpis = compute_executive_kpis(clean_df)
    assert kpis["total_transactions"] == 12

    daily = compute_daily_trajectory(clean_df)
    assert len(daily) >= 5

    # Dynamic Anomaly Detection
    df_anom, meta = detect_transaction_anomalies(clean_df, contamination=0.1)
    assert "is_anomaly" in df_anom.columns
    assert "anomaly_score" in df_anom.columns
    # The $50,000 transaction should have the highest anomaly score
    high_tx = df_anom[df_anom["amount"] == 50000.0].iloc[0]
    assert high_tx["anomaly_score"] >= 90.0

    # Exporters
    csv_bytes = export_dataframe_to_csv(df_anom)
    assert len(csv_bytes) > 0

    report = generate_executive_summary_report(kpis, audit, meta)
    assert "FinTrace 360" in report
    assert "50,000" in report or "Gross Settlement Flow" in report
    print("ALL CUSTOM PIPELINE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_custom_pipeline()
