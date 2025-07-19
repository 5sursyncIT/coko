-- Initialize multiple databases for Coko project

-- Create databases for different services
CREATE DATABASE coko_auth;
CREATE DATABASE coko_catalog;
CREATE DATABASE coko_reading;
CREATE DATABASE coko_payment;
CREATE DATABASE coko_gamification;
CREATE DATABASE coko_community;

-- Grant privileges to postgres user
GRANT ALL PRIVILEGES ON DATABASE coko_main TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_auth TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_catalog TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_reading TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_payment TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_gamification TO postgres;
GRANT ALL PRIVILEGES ON DATABASE coko_community TO postgres;

-- Connect to each database and create extensions
\c coko_main;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

\c coko_auth;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c coko_catalog;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

\c coko_reading;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

\c coko_payment;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c coko_gamification;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c coko_community;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";