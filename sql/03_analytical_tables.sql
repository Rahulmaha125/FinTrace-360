-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 03: Star Schema Analytical Warehouse (Dimensions and Facts)
-- ==============================================================================

SET search_path TO analytics;

DROP TABLE IF EXISTS analytics.fact_transactions CASCADE;
DROP TABLE IF EXISTS analytics.fact_account_risk_summary CASCADE;
DROP TABLE IF EXISTS analytics.dim_accounts CASCADE;
DROP TABLE IF EXISTS analytics.dim_banks CASCADE;
DROP TABLE IF EXISTS analytics.dim_dates CASCADE;
DROP TABLE IF EXISTS analytics.dim_transaction_types CASCADE;

-- ------------------------------------------------------------------------------
-- 1. DIMENSION: Banks
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.dim_banks (
    bank_id VARCHAR(32) PRIMARY KEY,
    bank_name VARCHAR(64) NOT NULL,
    institution_type VARCHAR(32) NOT NULL,
    country_code VARCHAR(8) NOT NULL,
    risk_rating VARCHAR(16) DEFAULT 'STANDARD'
);

INSERT INTO analytics.dim_banks (bank_id, bank_name, institution_type, country_code, risk_rating)
VALUES 
    ('BNK_ALPHA', 'Alpha Commercial Bank', 'Tier 1 Commercial', 'US', 'LOW'),
    ('BNK_BETA', 'Beta National Depository', 'Retail Depository', 'US', 'LOW'),
    ('BNK_GAMMA', 'Gamma Merchant Banking', 'Merchant & Corporate', 'US', 'MEDIUM'),
    ('BNK_DELTA', 'Delta Private Credit', 'Private Investment', 'US', 'MEDIUM'),
    ('BNK_EPSILON', 'Epsilon Capital Trust', 'Trust & Wealth Management', 'US', 'ELEVATED')
ON CONFLICT (bank_id) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 2. DIMENSION: Transaction Types
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.dim_transaction_types (
    transaction_type VARCHAR(32) PRIMARY KEY,
    rail_category VARCHAR(32) NOT NULL,
    settlement_speed VARCHAR(32) NOT NULL,
    is_high_value_channel BOOLEAN NOT NULL
);

INSERT INTO analytics.dim_transaction_types (transaction_type, rail_category, settlement_speed, is_high_value_channel)
VALUES
    ('WIRE', 'Gross Settlement', 'Same-Day Real-Time', TRUE),
    ('ACH_TRANSFER', 'Automated Clearing House', 'Batch Next-Day', FALSE),
    ('INTERNAL_TRANSFER', 'Intra-Bank Book Transfer', 'Instant', FALSE),
    ('INSTANT_PAY', 'Fast Retail Payment Rail', 'Instant (<10s)', FALSE)
ON CONFLICT (transaction_type) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 3. DIMENSION: Dates
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.dim_dates (
    date_key INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    full_date DATE UNIQUE NOT NULL,
    day_of_month SMALLINT NOT NULL,
    month_number SMALLINT NOT NULL,
    month_name VARCHAR(16) NOT NULL,
    quarter SMALLINT NOT NULL,
    year_number SMALLINT NOT NULL,
    day_name VARCHAR(16) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Populate Date Dimension (covering 2023 financial year)
INSERT INTO analytics.dim_dates (date_key, full_date, day_of_month, month_number, month_name, quarter, year_number, day_name, is_weekend)
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d::DATE AS full_date,
    EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
    EXTRACT(MONTH FROM d)::SMALLINT AS month_number,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    EXTRACT(YEAR FROM d)::SMALLINT AS year_number,
    TO_CHAR(d, 'Day') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2023-01-01'::DATE, '2023-12-31'::DATE, '1 day'::INTERVAL) d
ON CONFLICT (date_key) DO NOTHING;

-- ------------------------------------------------------------------------------
-- 4. DIMENSION: Accounts
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.dim_accounts (
    account_id BIGINT PRIMARY KEY,
    bank_id VARCHAR(32) NOT NULL REFERENCES analytics.dim_banks(bank_id),
    account_segment VARCHAR(32) NOT NULL,
    country_code VARCHAR(8) NOT NULL,
    account_status VARCHAR(16) NOT NULL,
    initial_balance NUMERIC(14, 2) NOT NULL,
    is_sar_alert BOOLEAN NOT NULL,
    sar_start_step BIGINT NOT NULL
);

-- ------------------------------------------------------------------------------
-- 5. FACT: Transactions
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.fact_transactions (
    transaction_id BIGINT PRIMARY KEY,
    date_key INTEGER NOT NULL REFERENCES analytics.dim_dates(date_key),
    transaction_timestamp TIMESTAMP NOT NULL,
    source_account_id BIGINT NOT NULL REFERENCES analytics.dim_accounts(account_id),
    target_account_id BIGINT NOT NULL REFERENCES analytics.dim_accounts(account_id),
    originator_bank_id VARCHAR(32) NOT NULL REFERENCES analytics.dim_banks(bank_id),
    beneficiary_bank_id VARCHAR(32) NOT NULL REFERENCES analytics.dim_banks(bank_id),
    transaction_type VARCHAR(32) NOT NULL REFERENCES analytics.dim_transaction_types(transaction_type),
    amount NUMERIC(14, 2) NOT NULL,
    is_interbank BOOLEAN NOT NULL,
    is_alerted_tx BOOLEAN NOT NULL,
    step_day INTEGER NOT NULL
);

-- Fact Table Analytical Indexes
CREATE INDEX IF NOT EXISTS idx_fact_tx_date ON analytics.fact_transactions (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_tx_src ON analytics.fact_transactions (source_account_id);
CREATE INDEX IF NOT EXISTS idx_fact_tx_dst ON analytics.fact_transactions (target_account_id);
CREATE INDEX IF NOT EXISTS idx_fact_tx_alert ON analytics.fact_transactions (is_alerted_tx);
CREATE INDEX IF NOT EXISTS idx_fact_tx_amount ON analytics.fact_transactions (amount);
CREATE INDEX IF NOT EXISTS idx_fact_tx_type ON analytics.fact_transactions (transaction_type);

-- ------------------------------------------------------------------------------
-- 6. FACT: Account Risk Summary (Aggregated Profile)
-- ------------------------------------------------------------------------------
CREATE TABLE analytics.fact_account_risk_summary (
    account_id BIGINT PRIMARY KEY REFERENCES analytics.dim_accounts(account_id),
    out_tx_count INTEGER NOT NULL,
    in_tx_count INTEGER NOT NULL,
    total_tx_count INTEGER NOT NULL,
    total_outflow NUMERIC(14, 2) NOT NULL,
    total_inflow NUMERIC(14, 2) NOT NULL,
    total_volume NUMERIC(14, 2) NOT NULL,
    net_flow NUMERIC(14, 2) NOT NULL,
    flow_ratio NUMERIC(14, 4) NOT NULL,
    unique_counterparties INTEGER NOT NULL,
    total_active_days INTEGER NOT NULL,
    tx_velocity_per_day NUMERIC(10, 2) NOT NULL,
    turnover_ratio NUMERIC(14, 2) NOT NULL,
    fan_in_index NUMERIC(10, 2) NOT NULL,
    fan_out_index NUMERIC(10, 2) NOT NULL,
    is_sar_alert BOOLEAN NOT NULL,
    risk_tier VARCHAR(16) NOT NULL
);
