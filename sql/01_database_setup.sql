-- ==============================================================================
-- FinTrace 360: Financial Transaction Intelligence & Risk Analytics
-- Script 01: Database, Schemas, and Role Setup
-- ==============================================================================

-- 1. Create Dedicated Database (run separately if not connected)
-- CREATE DATABASE fintrace360;
-- \c fintrace360;

-- 2. Create Isolated Schemas for Staging and Production Analytics
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA staging IS 'Raw data ingestion staging layer mirroring source files';
COMMENT ON SCHEMA analytics IS 'Dimensional Star Schema warehouse optimized for BI and compliance queries';

-- 3. Set Schema Search Path
SET search_path TO analytics, staging, public;
