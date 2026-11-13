# Data dictionary — Online Retail II (UCI workbook, `data/raw/online_retail_II.xlsx`)

Two sheets, same columns. Real UCI column names are Invoice / Price / Customer ID;
the pipeline renames them to InvoiceNo / UnitPrice / CustomerID.

| Column | Type | Notes |
|---|---|---|
| InvoiceNo | text | Invoice number. In the UCI file this is numeric — there are no 'C'-prefixed cancelled numbers, unlike the Kaggle copy. Cancellations are identified by negative Quantity. |
| StockCode | text | Product code (e.g. 85123A; 'M' = Manual, 'DOT' = DOTCOM POSTAGE) |
| Description | text | Product name; 4,275 rows missing |
| Quantity | int | Negative = return / cancellation line |
| InvoiceDate | datetime | 1 Dec 2009 – 9 Dec 2011 |
| UnitPrice | GBP | Unit price in pounds sterling |
| CustomerID | int | 22.8% of rows missing — RFM covers identified customers only |
| Country | text | 43 countries; UK is 85% of revenue |

Clean file: `data/clean/retail_clean.csv` (1,033,036 rows after removing 34,335 exact
duplicates from the 1–9 Dec 2010 sheet overlap), with Revenue, is_cancelled, is_return_line.
RFM: `output/rfm_customers.csv` (reference date = max InvoiceDate, 9 Dec 2011).
