-- Connect to your Azure PostgreSQL server and run this:
-- psql "host=wawsdb-azure.postgres.database.azure.com port=5432 dbname=postgres user=postgres password=TomttVTPFxEcAg9UbMU9"

-- Create the database
CREATE DATABASE diagnoseai;

-- Create a dedicated user (optional, or use existing postgres user)
-- CREATE USER diagnoseai_user WITH PASSWORD 'your-secure-password';
-- GRANT ALL PRIVILEGES ON DATABASE diagnoseai TO diagnoseai_user;

-- Connect to the new database to set permissions
\c diagnoseai;

-- Grant permissions to postgres user (since you're using that)
GRANT ALL ON SCHEMA public TO postgres;
GRANT CREATE ON SCHEMA public TO postgres;