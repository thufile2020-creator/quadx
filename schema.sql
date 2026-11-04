-- CarbonEase / QUADx illustrative SQLite schema snapshot
-- Source of truth: backend/carbon_api/models.py (SQLAlchemy).
-- Normal setup: run database/init_db.py; Flask creates tables automatically.
-- This schema is provided for teammate review and GitHub documentation.
-- Do not use this file to overwrite a populated database.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS businesses (
    id INTEGER NOT NULL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    industry VARCHAR(100),
    city VARCHAR(100),
    created_at DATETIME NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS ix_businesses_owner_id ON businesses (owner_id);

CREATE TABLE IF NOT EXISTS emission_factors (
    id INTEGER NOT NULL PRIMARY KEY,
    activity_type VARCHAR(30) NOT NULL UNIQUE,
    kg_co2e_per_unit FLOAT NOT NULL,
    unit VARCHAR(30) NOT NULL,
    scope INTEGER NOT NULL,
    source VARCHAR(250) NOT NULL,
    reference_year VARCHAR(20) NOT NULL,
    is_demo BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_records (
    id INTEGER NOT NULL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    period VARCHAR(7) NOT NULL,
    activity_type VARCHAR(30) NOT NULL,
    quantity FLOAT NOT NULL,
    factor_kg_co2e_per_unit FLOAT NOT NULL,
    factor_source VARCHAR(250) NOT NULL,
    factor_is_demo BOOLEAN NOT NULL,
    note VARCHAR(250),
    created_at DATETIME NOT NULL,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);
CREATE INDEX IF NOT EXISTS ix_activity_records_business_id ON activity_records(business_id);
CREATE INDEX IF NOT EXISTS ix_activity_records_period ON activity_records(period);

CREATE TABLE IF NOT EXISTS production_records (
    id INTEGER NOT NULL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    period VARCHAR(7) NOT NULL,
    product_name VARCHAR(120) NOT NULL,
    units INTEGER NOT NULL,
    CONSTRAINT uq_production_business_period UNIQUE (business_id, period),
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);

CREATE TABLE IF NOT EXISTS green_missions (
    id INTEGER NOT NULL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
);
