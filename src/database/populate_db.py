"""
FinTrace 360 - Database Population & SQL Seed Generator
Generates automated SQL ingestion commands and handles database seeding.
"""

from pathlib import Path
from src.config.settings import PROCESSED_DATA_DIR, SQL_DIR
from src.utils.logger import setup_logger

logger = setup_logger("db_populator")

def generate_bulk_load_script(output_sql_path: Path | None = None) -> Path:
    """Generates a PostgreSQL bulk-load script using standard \\copy commands."""
    sql_path = output_sql_path or (SQL_DIR / "09_load_data.sql")

    acc_csv = (PROCESSED_DATA_DIR / "amlsim_accounts_clean.csv").resolve()
    tx_csv = (PROCESSED_DATA_DIR / "amlsim_transactions_clean.csv").resolve()

    # Convert Windows path backslashes to forward slashes for psql compatibility
    acc_path_str = str(acc_csv).replace("\\", "/")
    tx_path_str = str(tx_csv).replace("\\", "/")

    script_content = f"""-- ==============================================================================
-- FinTrace 360: Automated Data Bulk-Load Script
-- Run via: psql -U <user> -d fintrace360 -f sql/09_load_data.sql
-- ==============================================================================

SET client_encoding = 'UTF8';
SET search_path TO staging, analytics, public;

-- 1. Truncate staging tables before reload
TRUNCATE TABLE staging.stg_amlsim_transactions;
TRUNCATE TABLE staging.stg_amlsim_accounts CASCADE;

-- 2. Fast Bulk Load from Clean Processed CSVs
\\copy staging.stg_amlsim_accounts (account_id, is_sar_alert, initial_balance, sar_start_step, bank_id, account_segment, country_code, account_status) FROM '{acc_path_str}' WITH (FORMAT csv, HEADER true, DELIMITER ',');

\\copy staging.stg_amlsim_transactions (source_account_id, target_account_id, amount, step_day, transaction_id, transaction_timestamp, transaction_date, originator_bank_id, beneficiary_bank_id, is_interbank, transaction_type, is_alerted_tx) FROM '{tx_path_str}' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- 3. Execute Star Schema Transformation
\\i sql/08_etl_staging_to_analytics.sql

-- 4. Verify Ingested Counts
SELECT 'staging.stg_amlsim_accounts' AS table_name, COUNT(*) AS row_count FROM staging.stg_amlsim_accounts
UNION ALL
SELECT 'staging.stg_amlsim_transactions', COUNT(*) FROM staging.stg_amlsim_transactions
UNION ALL
SELECT 'analytics.dim_accounts', COUNT(*) FROM analytics.dim_accounts
UNION ALL
SELECT 'analytics.fact_transactions', COUNT(*) FROM analytics.fact_transactions
UNION ALL
SELECT 'analytics.fact_account_risk_summary', COUNT(*) FROM analytics.fact_account_risk_summary;
"""
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    logger.info(f"Generated bulk load script at: {sql_path}")
    return sql_path

if __name__ == "__main__":
    generate_bulk_load_script()
