PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE
);

CREATE TABLE merchants (
    merchant_id INTEGER PRIMARY KEY,
    merchant_name TEXT NOT NULL UNIQUE
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    transaction_date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    merchant_id INTEGER,
    category_id INTEGER,
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_id);