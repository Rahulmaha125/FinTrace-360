-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 02: Staging Layer Tables
-- ==============================================================================

SET search_path TO staging;

DROP TABLE IF EXISTS staging.stg_amlsim_transactions CASCADE;
DROP TABLE IF EXISTS staging.stg_amlsim_accounts CASCADE;

-- 1. Staging Accounts Table
CREATE TABLE staging.stg_amlsim_accounts (
    account_id BIGINT PRIMARY KEY,
    is_sar_alert SMALLINT NOT NULL,
    initial_balance NUMERIC(14, 2) NOT NULL,
    sar_start_step BIGINT NOT NULL,
    bank_id VARCHAR(32) NOT NULL,
    account_segment VARCHAR(32) NOT NULL,
    country_code VARCHAR(8) NOT NULL,
    account_status VARCHAR(16) NOT NULL
);

COMMENT ON TABLE staging.stg_amlsim_accounts IS 'Staging table for cleaned AMLSim account entities';

-- 2. Staging Transactions Table
CREATE TABLE staging.stg_amlsim_transactions (
    transaction_id BIGINT PRIMARY KEY,
    source_account_id BIGINT NOT NULL,
    target_account_id BIGINT NOT NULL,
    amount NUMERIC(14, 2) NOT NULL,
    step_day INTEGER NOT NULL,
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_date DATE NOT NULL,
    originator_bank_id VARCHAR(32) NOT NULL,
    beneficiary_bank_id VARCHAR(32) NOT NULL,
    is_interbank SMALLINT NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    is_alerted_tx SMALLINT NOT NULL
);

COMMENT ON TABLE staging.stg_amlsim_transactions IS 'Staging table for cleaned AMLSim transaction records';

-- Fast Bulk-Load Indexes
CREATE INDEX IF NOT EXISTS idx_stg_tx_source ON staging.stg_amlsim_transactions (source_account_id);
CREATE INDEX IF NOT EXISTS idx_stg_tx_target ON staging.stg_amlsim_transactions (target_account_id);
CREATE INDEX IF NOT EXISTS idx_stg_tx_date ON staging.stg_amlsim_transactions (transaction_date);
CREATE INDEX IF NOT EXISTS idx_stg_tx_alert ON staging.stg_amlsim_transactions (is_alerted_tx);
