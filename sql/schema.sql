-- Online Retail II — PostgreSQL schema. One row = one invoice line.
CREATE SCHEMA IF NOT EXISTS retail;

CREATE TABLE retail.transactions (
    invoice_no TEXT, stock_code TEXT, description TEXT,
    quantity INT, invoice_date TIMESTAMP, unit_price NUMERIC(10,2),
    customer_id INT, country TEXT, revenue_gbp NUMERIC(12,2),
    is_cancelled BOOLEAN, is_return_line BOOLEAN);

CREATE INDEX idx_retail_invoice ON retail.transactions (invoice_no);
CREATE INDEX idx_retail_customer ON retail.transactions (customer_id);
CREATE INDEX idx_retail_date ON retail.transactions (invoice_date);

-- RFM table, built by scripts/01_clean_analyse.py -> output/rfm_customers.csv
CREATE TABLE retail.rfm (
    customer_id INT PRIMARY KEY, recency_days INT, frequency_invoices INT,
    monetary_gbp NUMERIC(12,2), avg_order_value_gbp NUMERIC(10,2),
    r_score INT, f_score INT, m_score INT, rfm_score INT, segment TEXT);
