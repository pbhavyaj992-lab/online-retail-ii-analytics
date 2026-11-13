# Power BI model — Online Retail II Analytics

No .pbix is in this repo (no Power BI Desktop here). Build it from this document:
load `data/clean/retail_clean.csv` and `output/rfm_customers.csv`, or connect
Power BI to the PostgreSQL schema in `sql/schema.sql`.

## Star schema
- **FactTransactions** (grain: one invoice line) — `data/clean/retail_clean.csv`.
  Revenue, Quantity, UnitPrice, is_cancelled, is_return_line.
- **DimCustomer** — from `output/rfm_customers.csv`: CustomerID, recency_days,
  frequency_invoices, monetary_gbp, R/F/M scores, segment.
- **DimProduct** — StockCode, Description.
- **DimDate** — InvoiceDate, month, year, quarter.
- **DimCountry** — Country.
- Relationships: FactTransactions → DimCustomer, → DimProduct, → DimDate, → DimCountry.

## DAX measures
```dax
Gross Revenue = SUMX(FILTER(FactTransactions, NOT FactTransactions[is_return_line]
    && NOT FactTransactions[is_cancelled]), FactTransactions[Revenue])
Returns Value = SUMX(FILTER(FactTransactions, FactTransactions[is_return_line]
    || FactTransactions[is_cancelled]), FactTransactions[Revenue])
Net Revenue = SUM(FactTransactions[Revenue])
Invoices = DISTINCTCOUNT(FactTransactions[InvoiceNo])
Customers = DISTINCTCOUNT(FactTransactions[CustomerID])
Avg Order Value = DIVIDE([Gross Revenue], [Invoices])
Champions Revenue = CALCULATE([Gross Revenue], DimCustomer[segment] = "Champions")
Champions Share % = DIVIDE([Champions Revenue], [Gross Revenue])
Missing CustomerID % = 100 * DIVIDE(
    COUNTROWS(FILTER(FactTransactions, ISBLANK(FactTransactions[CustomerID]))),
    COUNTROWS(FactTransactions))
```

## Pages
1. **Overview** — gross/net revenue, invoices, customers; monthly revenue line; revenue by country.
2. **RFM / retention** — customers and revenue by segment; Champions spotlight; recency vs monetary scatter.
3. **Products** — top 30 products by revenue and units; stock-focus list.
4. **Returns & data quality** — returns value by country; missing CustomerID share; cancelled lines.
