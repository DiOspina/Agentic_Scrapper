-- Agenttic PostgreSQL Initialization Script
-- This script runs on first container startup to set up the database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS n8n;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default search path
ALTER DATABASE agenttic SET search_path = public, n8n, analytics;

-- Create custom types for enum-like columns
DO $$ BEGIN
    CREATE TYPE execution_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE execution_type AS ENUM ('scraping', 'analysis', 'synthesis', 'full_pipeline');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE document_status AS ENUM ('uploaded', 'processing', 'processed', 'failed', 'deleted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE document_type AS ENUM ('pdf', 'csv', 'txt', 'markdown', 'docx', 'xlsx', 'html', 'json');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE workflow_status AS ENUM ('draft', 'active', 'paused', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE workflow_trigger AS ENUM ('manual', 'scheduled', 'webhook', 'event', 'file_upload');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE agent_type AS ENUM ('scraper', 'analyst', 'synthesizer', 'orchestrator');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE log_level AS ENUM ('debug', 'info', 'warning', 'error', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE alert_status AS ENUM ('pending', 'sent', 'failed', 'delivered', 'read');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE alert_channel AS ENUM ('email', 'telegram', 'whatsapp', 'slack', 'webhook', 'sms');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE metric_type AS ENUM ('performance', 'quality', 'business', 'system', 'custom');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'user', 'viewer', 'api_client');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Create indexes for better performance (will be created by SQLAlchemy but good to have here)
-- These are created by the models, but we can add some additional ones

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE agenttic TO agenttic;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agenttic;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agenttic;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO agenttic;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO agenttic;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO agenttic;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO agenttic;