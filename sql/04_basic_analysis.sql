-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 04: Basic Business Analytics & KPI Aggregations
-- ==============================================================================

SET search_path TO analytics, staging, public;

-- ------------------------------------------------------------------------------
-- QUERY 1: Executive KPI Portfolio Totals
-- Purpose: Compute high-level operational metrics for executive leadership.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_transactions,
    ROUND(SUM(amount), 2) AS total_gross_value_usd,
    ROUND(AVG(amount), 2) AS average_transaction_value_usd,
    ROUND(MIN(amount), 2) AS minimum_transaction_amount_usd,
    ROUND(MAX(amount), 2) AS maximum_transaction_amount_usd,
    COUNT(DISTINCT source_account_id) AS distinct_originator_accounts,
    COUNT(DISTINCT target_account_id) AS distinct_beneficiary_accounts,
    SUM(CASE WHEN is_alerted_tx THEN 1 ELSE 0 END) AS total_alerted_transactions,
    ROUND(SUM(CASE WHEN is_alerted_tx THEN amount ELSE 0 END), 2) AS alerted_gross_value_usd,
    ROUND(100.0 * SUM(CASE WHEN is_alerted_tx THEN 1 ELSE 0 END) / COUNT(*), 2) AS alert_rate_percentage
FROM analytics.fact_transactions;

-- ------------------------------------------------------------------------------
-- QUERY 2: Transaction Channel / Payment Rail Breakdown
-- Purpose: Analyze transaction count, total value, and ticket size by payment rail.
-- ------------------------------------------------------------------------------
SELECT 
    t.transaction_type,
    dt.rail_category,
    dt.settlement_speed,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(100.0 * COUNT(t.transaction_id) / SUM(COUNT(t.transaction_id)) OVER (), 2) AS count_share_pct,
    ROUND(SUM(t.amount), 2) AS total_amount_usd,
    ROUND(100.0 * SUM(t.amount) / SUM(SUM(t.amount)) OVER (), 2) AS volume_share_pct,
    ROUND(AVG(t.amount), 2) AS avg_ticket_size_usd
FROM analytics.fact_transactions t
JOIN analytics.dim_transaction_types dt ON t.transaction_type = dt.transaction_type
GROUP BY t.transaction_type, dt.rail_category, dt.settlement_speed
ORDER BY total_amount_usd DESC;

-- ------------------------------------------------------------------------------
-- QUERY 3: Bank-Wise Inflow, Outflow, and Net Clearing Position
-- Purpose: Evaluate liquidity and flow balance across partner banking entities.
-- ------------------------------------------------------------------------------
SELECT 
    b.bank_id,
    b.bank_name,
    COUNT(t.transaction_id) AS outbound_transactions,
    ROUND(SUM(t.amount), 2) AS gross_outflow_usd,
    ROUND(AVG(t.amount), 2) AS avg_transfer_size_usd,
    SUM(CASE WHEN t.is_interbank THEN 1 ELSE 0 END) AS interbank_outbound_count,
    SUM(CASE WHEN t.is_alerted_tx THEN 1 ELSE 0 END) AS bank_alerted_tx_count
FROM analytics.dim_banks b
LEFT JOIN analytics.fact_transactions t ON b.bank_id = t.originator_bank_id
GROUP BY b.bank_id, b.bank_name
ORDER BY gross_outflow_usd DESC;

-- ------------------------------------------------------------------------------
-- QUERY 4: Account Tier & Balance Segment Distribution
-- Purpose: Understand account segmentation and SAR alert rates by segment.
-- ------------------------------------------------------------------------------
SELECT 
    account_segment,
    COUNT(*) AS total_accounts,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS account_share_pct,
    ROUND(AVG(initial_balance), 2) AS avg_opening_balance,
    SUM(CASE WHEN is_sar_alert THEN 1 ELSE 0 END) AS sar_alert_count,
    ROUND(100.0 * SUM(CASE WHEN is_sar_alert THEN 1 ELSE 0 END) / COUNT(*), 2) AS segment_alert_rate_pct
FROM analytics.dim_accounts
GROUP BY account_segment
ORDER BY avg_opening_balance DESC;
