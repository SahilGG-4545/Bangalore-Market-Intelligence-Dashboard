-- ============================================================
-- Bangalore Market Intelligence — SQLite Schema
-- Source data: 6 CSV files in data/
-- Period: Q1 2025 – Q2 2026 (quarterly time-series)
-- ============================================================

-- 1. market_fundamentals
-- Source: data/Market Fundamentals.csv
-- Time-series: one row per (market, quarter, year)
CREATE TABLE IF NOT EXISTS market_fundamentals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name         TEXT    NOT NULL,
    quarter             TEXT    NOT NULL,
    year                INTEGER NOT NULL,
    grade_a_supply_sqft INTEGER,
    occupied_space_sqft INTEGER,
    vacancy_pct         REAL,
    avg_asking_rent     REAL,
    rent_movement_pct   REAL,
    new_supply_sqft     INTEGER,
    absorption_sqft     INTEGER,
    UNIQUE(market_name, quarter, year)
);

-- 2. demand_indicators
-- Source: data/demand indicators.csv
-- Time-series: one row per (market, quarter, year)
CREATE TABLE IF NOT EXISTS demand_indicators (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name             TEXT    NOT NULL,
    quarter                 TEXT    NOT NULL,
    year                    INTEGER NOT NULL,
    leasing_activity_sqft   INTEGER,
    transaction_count       INTEGER,
    avg_transaction_size_sqft INTEGER,
    major_occupiers         TEXT,
    est_seat_demand         INTEGER,
    UNIQUE(market_name, quarter, year)
);

-- 3. competition
-- Source: data/competetion.csv
-- One row per market
CREATE TABLE IF NOT EXISTS competition (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name         TEXT    NOT NULL UNIQUE,
    operators           TEXT,
    wework_centres      INTEGER,
    pricing_min         REAL,
    pricing_max         REAL,
    presence_evidence   TEXT
);

-- 4. market_catalysts
-- Source: data/market catalysts.csv
-- One row per market
CREATE TABLE IF NOT EXISTS market_catalysts (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    market_name                 TEXT    NOT NULL UNIQUE,
    upcoming_infrastructure     TEXT,
    metro_airport_connectivity  TEXT,
    key_developments            TEXT,
    development_period          TEXT,
    upcoming_supply_sqft        INTEGER
);

-- 5. city_summary
-- Source: data/market summary.csv
-- 2 rows: Q1-2026, Q2-2026 (H1 aggregate excluded)
CREATE TABLE IF NOT EXISTS city_summary (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    period              TEXT    NOT NULL UNIQUE,
    vacancy_pct         REAL,
    net_absorption_msf  REAL,
    gross_leasing_msf   REAL,
    new_supply_msf      REAL,
    avg_rent            REAL
);

-- 6. transactions
-- Source: data/transactions.csv
-- Individual lease transactions, Q4 2024 – Q2 2026
CREATE TABLE IF NOT EXISTS transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company             TEXT    NOT NULL,
    market_name         TEXT    NOT NULL,
    area_leased_sqft    INTEGER,
    transaction_date    TEXT,
    rent_per_sqft       REAL,
    sector              TEXT,
    transaction_type    TEXT,
    lease_type          TEXT,
    source              TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fundamentals_market ON market_fundamentals(market_name);
CREATE INDEX IF NOT EXISTS idx_fundamentals_period  ON market_fundamentals(quarter, year);
CREATE INDEX IF NOT EXISTS idx_demand_market        ON demand_indicators(market_name);
CREATE INDEX IF NOT EXISTS idx_demand_period        ON demand_indicators(quarter, year);
CREATE INDEX IF NOT EXISTS idx_transactions_market  ON transactions(market_name);
CREATE INDEX IF NOT EXISTS idx_competition_market   ON competition(market_name);
CREATE INDEX IF NOT EXISTS idx_catalysts_market     ON market_catalysts(market_name);
