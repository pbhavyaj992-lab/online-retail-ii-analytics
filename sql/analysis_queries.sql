-- 1. Monthly revenue (sales lines only)
SELECT date_trunc('month', invoice_date) AS month,
       SUM(revenue_gbp) AS revenue_gbp, COUNT(DISTINCT invoice_no) AS invoices
FROM retail.transactions WHERE NOT is_return_line AND NOT is_cancelled
GROUP BY 1 ORDER BY 1;

-- 2. Reconciliation: gross, returns, net
SELECT SUM(CASE WHEN NOT is_return_line AND NOT is_cancelled THEN revenue_gbp ELSE 0 END) AS gross_gbp,
       SUM(CASE WHEN is_return_line OR is_cancelled THEN revenue_gbp ELSE 0 END) AS returns_gbp,
       SUM(revenue_gbp) AS net_gbp
FROM retail.transactions WHERE unit_price > 0;

-- 3. Top products by revenue (stockable products only: manual adjustments,
-- postage/carriage, fees, discounts and gift vouchers are revenue lines, not
-- products, and are excluded from this ranking only, matching scripts/01_clean_analyse.py)
SELECT stock_code, description, SUM(revenue_gbp) AS revenue_gbp,
       SUM(quantity) AS qty_sold, COUNT(DISTINCT invoice_no) AS invoices
FROM retail.transactions WHERE NOT is_return_line AND NOT is_cancelled
  AND UPPER(stock_code) NOT IN ('M','DOT','POST','B','C2','D','AMAZONFEE','BANK CHARGES','ADJUST','S')
  AND description NOT IN ('Next Day Carriage','PACKING CHARGE')
  AND description NOT LIKE '%Gift Voucher%'
GROUP BY 1, 2 ORDER BY revenue_gbp DESC LIMIT 30;

-- 4. Revenue by country
SELECT country, SUM(revenue_gbp) AS revenue_gbp,
       COUNT(DISTINCT invoice_no) AS invoices, COUNT(DISTINCT customer_id) AS customers
FROM retail.transactions WHERE NOT is_return_line AND NOT is_cancelled
GROUP BY 1 ORDER BY revenue_gbp DESC;

-- 5. RFM segments
SELECT segment, COUNT(*) AS customers, SUM(monetary_gbp) AS revenue_gbp,
       AVG(monetary_gbp) AS avg_monetary_gbp
FROM retail.rfm GROUP BY 1 ORDER BY revenue_gbp DESC;

-- 6. Missing CustomerID share (data-quality check)
SELECT COUNT(*) FILTER (WHERE customer_id IS NULL) AS missing_customer_rows,
       COUNT(*) AS rows,
       100.0 * COUNT(*) FILTER (WHERE customer_id IS NULL) / COUNT(*) AS missing_pct
FROM retail.transactions;
