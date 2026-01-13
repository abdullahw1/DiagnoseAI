-- Initialize the database with proper permissions
-- This file is executed when the PostgreSQL container starts for the first time

-- Ensure the database exists (it should be created by POSTGRES_DB env var)
-- Grant all privileges to the user
GRANT ALL PRIVILEGES ON DATABASE diagnoseai TO diagnoseai_user;

-- Connect to the diagnoseai database
\c diagnoseai;

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO diagnoseai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO diagnoseai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO diagnoseai_user;