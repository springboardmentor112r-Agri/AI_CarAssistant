-- AutoGuard Database Schema (Reference)
-- SQLAlchemy auto-creates these tables on startup.
-- This file is for documentation / manual inspection only.

CREATE TABLE users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name  TEXT,
    email      TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contracts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    filename       TEXT,
    raw_text       TEXT,
    fairness_score REAL,
    uploaded_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contract_sla (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id         INTEGER NOT NULL REFERENCES contracts(id),
    apr                 REAL,
    term_months         INTEGER,
    monthly_payment     REAL,
    down_payment        REAL,
    mileage_allowance   INTEGER,
    mileage_overage_fee REAL,
    residual_value      REAL,
    early_termination   REAL,
    buyout_price        REAL,
    warranty_summary    TEXT
);

CREATE TABLE contract_flags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES contracts(id),
    severity    TEXT,   -- 'red', 'yellow', 'green'
    message     TEXT
);

CREATE TABLE chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL REFERENCES contracts(id),
    role        TEXT,   -- 'user' or 'assistant'
    content     TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
