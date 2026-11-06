-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 08: ETL Transformation (Staging -> Analytics Star Schema)
-- ==============================================================================

SET search_path TO analytics, staging, public;

-- 1. Populate dim_accounts from staging
INSERT INTO analytics.dim_accounts (
    account_id,
    bank_id,
    account_segment,
    country_code,
    account_status,
    initial_balance,
    is_sar_alert,
    sar_start_step
)
SELECT 
    account_id,
    bank_id,
    account_segment,
    country_code,
    account_status,
    initial_balance,
    (is_sar_alert = 1) AS is_sar_alert,
    sar_start_step
FROM staging.stg_amlsim_accounts
ON CONFLICT (account_id) DO UPDATE SET
    bank_id = EXCLUDED.bank_id,
    account_segment = EXCLUDED.account_segment,
    initial_balance = EXCLUDED.initial_balance,
    is_sar_alert = EXCLUDED.is_sar_alert;

-- 2. Populate fact_transactions from staging
INSERT INTO analytics.fact_transactions (
    transaction_id,
    date_key,
    transaction_timestamp,
    source_account_id,
    target_account_id,
    originator_bank_id,
    beneficiary_bank_id,
    transaction_type,
    amount,
    is_interbank,
    is_alerted_tx,
    step_day
)
SELECT 
    t.transaction_id,
    TO_CHAR(t.transaction_date, 'YYYYMMDD')::INTEGER AS date_key,
    t.transaction_timestamp,
    t.source_account_id,
    t.target_account_id,
    t.originator_bank_id,
    t.beneficiary_bank_id,
    t.transaction_type,
    t.amount,
    (t.is_interbank = 1) AS is_interbank,
    (t.is_alerted_tx = 1) AS is_alerted_tx,
    t.step_day
FROM staging.stg_amlsim_transactions t
ON CONFLICT (transaction_id) DO NOTHING;

-- 3. Populate fact_account_risk_summary from calculated aggregates
INSERT INTO analytics.fact_account_risk_summary (
    account_id,
    out_tx_count,
    in_tx_count,
    total_tx_count,
    total_outflow,
    total_inflow,
    total_volume,
    net_flow,
    flow_ratio,
    unique_counterparties,
    total_active_days,
    tx_velocity_per_day,
    turnover_ratio,
    fan_in_index,
    fan_out_index,
    is_sar_alert,
    risk_tier
)
WITH out_agg AS (
    SELECT 
        source_account_id AS account_id,
        COUNT(transaction_id) AS out_tx_count,
        SUM(amount) AS total_outflow,
        COUNT(DISTINCT target_account_id) AS unique_destinations,
        COUNT(DISTINCT step_day) AS active_days_out
    FROM analytics.fact_transactions
    GROUP BY source_account_id
),
in_agg AS (
    SELECT 
        target_account_id AS account_id,
        COUNT(transaction_id) AS in_tx_count,
        SUM(amount) AS total_inflow,
        COUNT(DISTINCT source_account_id) AS unique_sources,
        COUNT(DISTINCT step_day) AS active_days_in
    FROM analytics.fact_transactions
    GROUP BY target_account_id
)
SELECT 
    a.account_id,
    COALESCE(o.out_tx_count, 0) AS out_tx_count,
    COALESCE(i.in_tx_count, 0) AS in_tx_count,
    (COALESCE(o.out_tx_count, 0) + COALESCE(i.in_tx_count, 0)) AS total_tx_count,
    COALESCE(o.total_outflow, 0.00) AS total_outflow,
    COALESCE(i.total_inflow, 0.00) AS total_inflow,
    (COALESCE(o.total_outflow, 0.00) + COALESCE(i.total_inflow, 0.00)) AS total_volume,
    (COALESCE(i.total_inflow, 0.00) - COALESCE(o.total_outflow, 0.00)) AS net_flow,
    ROUND(COALESCE(i.total_inflow, 0.00) / (COALESCE(o.total_outflow, 0.00) + 1.0), 4) AS flow_ratio,
    (COALESCE(o.unique_destinations, 0) + COALESCE(i.unique_sources, 0)) AS unique_counterparties,
    GREATEST(COALESCE(o.active_days_out, 0), COALESCE(i.active_days_in, 0), 1) AS total_active_days,
    ROUND((COALESCE(o.out_tx_count, 0) + COALESCE(i.in_tx_count, 0))::NUMERIC / 
          GREATEST(COALESCE(o.active_days_out, 0), COALESCE(i.active_days_in, 0), 1), 2) AS tx_velocity_per_day,
    ROUND((COALESCE(o.total_outflow, 0.00) + COALESCE(i.total_inflow, 0.00)) / (a.initial_balance + 1.0), 2) AS turnover_ratio,
    ROUND(COALESCE(i.in_tx_count, 0)::NUMERIC / (COALESCE(o.out_tx_count, 0) + 1.0), 2) AS fan_in_index,
    ROUND(COALESCE(o.out_tx_count, 0)::NUMERIC / (COALESCE(i.in_tx_count, 0) + 1.0), 2) AS fan_out_index,
    a.is_sar_alert,
    CASE 
        WHEN a.is_sar_alert AND (COALESCE(o.total_outflow, 0.00) + COALESCE(i.total_inflow, 0.00)) / (a.initial_balance + 1.0) >= 50.0 THEN 'CRITICAL'
        WHEN a.is_sar_alert OR (COALESCE(o.total_outflow, 0.00) + COALESCE(i.total_inflow, 0.00)) / (a.initial_balance + 1.0) >= 25.0 THEN 'HIGH'
        WHEN (COALESCE(o.out_tx_count, 0) + COALESCE(i.in_tx_count, 0)) >= 15 THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_tier
FROM analytics.dim_accounts a
LEFT JOIN out_agg o ON a.account_id = o.account_id
LEFT JOIN in_agg i ON a.account_id = i.account_id
ON CONFLICT (account_id) DO NOTHING;
