"""
FinTrace 360 - SQL Logic & Query Verification Test
Executes core analytical queries (CTEs, Window Functions, Aggregations)
against the ingested benchmark dataset to verify syntax and computation.
"""

from pathlib import Path
import sqlite3
import pandas as pd
from src.config.settings import PROCESSED_DATA_DIR
from src.utils.logger import setup_logger

logger = setup_logger("test_sql_logic")

def test_sql_queries():
    """Validates SQL query logic against an in-memory database populated with clean data."""
    logger.info("Initializing in-memory database to verify SQL analytical queries...")
    conn = sqlite3.connect(":memory:")

    # Load clean datasets
    df_acc = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_accounts_clean.csv")
    df_tx = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_transactions_clean.csv")
    df_feats = pd.read_csv(PROCESSED_DATA_DIR / "amlsim_account_features.csv")

    df_acc.to_sql("dim_accounts", conn, index=False)
    df_tx.to_sql("fact_transactions", conn, index=False)
    df_feats.to_sql("fact_account_risk_summary", conn, index=False)

    logger.info("Verifying Query 1: Basic Executive KPIs...")
    q1 = """
    SELECT 
        COUNT(*) AS total_transactions,
        ROUND(SUM(amount), 2) AS total_gross_value_usd,
        ROUND(AVG(amount), 2) AS average_transaction_value_usd,
        SUM(CASE WHEN is_alerted_tx = 1 THEN 1 ELSE 0 END) AS total_alerted_transactions,
        ROUND(100.0 * SUM(CASE WHEN is_alerted_tx = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS alert_rate_pct
    FROM fact_transactions;
    """
    res1 = pd.read_sql_query(q1, conn)
    assert res1["total_transactions"][0] == 120558
    assert res1["total_alerted_transactions"][0] == 24842
    logger.info(f"Query 1 PASSED: {res1.to_dict(orient='records')[0]}")

    logger.info("Verifying Query 2: CTE + Window Function (Cumulative & Rolling 7-Day)...")
    q2 = """
    WITH daily_aggregates AS (
        SELECT 
            step_day,
            COUNT(transaction_id) AS daily_tx_count,
            ROUND(SUM(amount), 2) AS daily_gross_value
        FROM fact_transactions
        GROUP BY step_day
    )
    SELECT 
        step_day,
        daily_tx_count,
        daily_gross_value,
        ROUND(SUM(daily_gross_value) OVER (ORDER BY step_day), 2) AS cumulative_volume,
        ROUND(AVG(daily_gross_value) OVER (
            ORDER BY step_day 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2) AS rolling_7d_volume
    FROM daily_aggregates
    ORDER BY step_day
    LIMIT 5;
    """
    res2 = pd.read_sql_query(q2, conn)
    assert len(res2) == 5
    logger.info(f"Query 2 PASSED:\n{res2}")

    logger.info("Verifying Query 3: Window Function (Dense Rank by Inflow & Outflow)...")
    q3 = """
    SELECT 
        account_id,
        bank_id,
        total_tx_count,
        total_volume,
        turnover_ratio,
        is_sar_alert,
        DENSE_RANK() OVER (ORDER BY total_volume DESC) AS volume_rank
    FROM fact_account_risk_summary
    ORDER BY total_volume DESC
    LIMIT 5;
    """
    res3 = pd.read_sql_query(q3, conn)
    assert len(res3) == 5
    assert res3["volume_rank"][0] == 1
    logger.info(f"Query 3 PASSED:\n{res3}")

    logger.info("Verifying Query 4: Risk Analytics (Fan-In Smurfing Hubs)...")
    q4 = """
    SELECT 
        target_account_id AS beneficiary_account_id,
        COUNT(DISTINCT source_account_id) AS distinct_senders,
        COUNT(transaction_id) AS incoming_transfers,
        ROUND(SUM(amount), 2) AS total_inflow_usd
    FROM fact_transactions
    GROUP BY target_account_id
    HAVING COUNT(DISTINCT source_account_id) >= 10
    ORDER BY distinct_senders DESC
    LIMIT 5;
    """
    res4 = pd.read_sql_query(q4, conn)
    assert len(res4) == 5
    logger.info(f"Query 4 PASSED:\n{res4}")

    conn.close()
    logger.info("ALL SQL ANALYTICAL QUERIES SUCCESSFULLY VERIFIED!")

if __name__ == "__main__":
    test_sql_queries()
