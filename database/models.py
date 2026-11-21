"""Security/database owner: future SQLite schema for synthetic customers, policies, claims and decoys."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS policies(
    policy_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    plan_name TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_policies_customer ON policies(customer_id);
CREATE TABLE IF NOT EXISTS claims(
    claim_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0)
);
CREATE INDEX IF NOT EXISTS idx_claimss_customer ON claims(customer_id);
CREATE TABLE IF NOT EXISTS audit_events(
    event_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    event_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
"""