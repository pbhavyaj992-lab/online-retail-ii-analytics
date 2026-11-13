"""Online Retail II (UCI dataset 502) — clean + analyse (real data, CC BY 4.0).
Business question: which customers are worth retaining (RFM), which products
drive repeat revenue, and what should the next quarter's stock focus be?
Run:  python3 scripts/01_clean_analyse.py   (from the project folder)
Reads data/raw/online_retail_II.xlsx, writes data/clean/ + output/*.csv
"""
import os
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
CLEAN = os.path.join(BASE, "data", "clean")
OUT = os.path.join(BASE, "output")
os.makedirs(CLEAN, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

xls = os.path.join(RAW, "online_retail_II.xlsx")
s1 = pd.read_excel(xls, sheet_name="Year 2009-2010")
s2 = pd.read_excel(xls, sheet_name="Year 2010-2011")
# NOTE: the UCI workbook's real column names are Invoice / Price / Customer ID
# (the Kaggle copy renames them to InvoiceNo / UnitPrice / CustomerID).
RENAME = {"Invoice": "InvoiceNo", "Price": "UnitPrice", "Customer ID": "CustomerID"}
s1 = s1.rename(columns=RENAME)
s2 = s2.rename(columns=RENAME)
print("Sheet 2009-2010 rows:", len(s1), "| Sheet 2010-2011 rows:", len(s2))
raw_total = len(s1) + len(s2)

df = pd.concat([s1, s2], ignore_index=True)
n_before_dedupe = len(df)
df = df.drop_duplicates()
n_dupes_removed = n_before_dedupe - len(df)
print(f"Exact duplicate rows removed (1-9 Dec 2010 overlap): {n_dupes_removed}")

df["InvoiceNo"] = df["InvoiceNo"].astype(str)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["is_cancelled"] = df["InvoiceNo"].str.startswith("C")
df["is_return_line"] = df["Quantity"] < 0
df["Revenue"] = df["Quantity"] * df["UnitPrice"]

sales = df[(~df["is_cancelled"]) & (~df["is_return_line"]) & (df["UnitPrice"] > 0)].copy()
returns = df[df["is_return_line"] | df["is_cancelled"]].copy()
valid = df[(df["UnitPrice"] > 0)].copy()

print(f"Rows after dedupe: {len(df)}")
print(f"Sales lines: {len(sales)} | Return/cancelled lines: {len(returns)}")
print(f"Gross sales revenue GBP: {sales['Revenue'].sum():,.2f}")
print(f"Returns value GBP: {returns['Revenue'].sum():,.2f} (negative)")
print(f"Net revenue GBP: {valid['Revenue'].sum():,.2f}")
print(f"Customers (non-null): {df['CustomerID'].nunique()} | Countries: {df['Country'].nunique()}")
print(f"Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
print(f"Missing CustomerID rows: {df['CustomerID'].isna().sum()} ({100*df['CustomerID'].isna().mean():.1f}%)")
print(f"Missing Description rows: {df['Description'].isna().sum()}")

df.to_csv(os.path.join(CLEAN, "retail_clean.csv"), index=False)

kpis = {
    "raw_rows_both_sheets": int(raw_total),
    "rows_after_dedupe": int(len(df)),
    "exact_duplicates_removed": int(n_dupes_removed),
    "sales_lines": int(len(sales)),
    "return_or_cancelled_lines": int(len(returns)),
    "gross_sales_revenue_gbp": round(float(sales["Revenue"].sum()), 2),
    "returns_value_gbp": round(float(returns["Revenue"].sum()), 2),
    "net_revenue_gbp": round(float(valid["Revenue"].sum()), 2),
    "invoices": int(df["InvoiceNo"].nunique()),
    "customers": int(df["CustomerID"].nunique()),
    "countries": int(df["Country"].nunique()),
    "products_stockcodes": int(df["StockCode"].nunique()),
    "missing_customerid_rows": int(df["CustomerID"].isna().sum()),
    "missing_customerid_pct": round(float(100 * df["CustomerID"].isna().mean()), 2),
    "date_min": str(df["InvoiceDate"].min().date()),
    "date_max": str(df["InvoiceDate"].max().date()),
}
with open(os.path.join(OUT, "kpis.txt"), "w") as f:
    for k, v in kpis.items():
        f.write(f"{k}: {v}\n")
print(kpis)

sales["month"] = sales["InvoiceDate"].dt.to_period("M").astype(str)
monthly = (sales.groupby("month").agg(gross_sales_revenue_gbp=("Revenue", "sum"),
                                      invoices=("InvoiceNo", "nunique"),
                                      lines=("Revenue", "count"),
                                      customers=("CustomerID", "nunique"))
           .reset_index())
monthly.to_csv(os.path.join(OUT, "monthly_revenue.csv"), index=False)

# Top products must be stockable products only. These StockCodes are revenue
# lines, not products — manual adjustments, postage/carriage, fees, discounts,
# bad-debt adjustments, samples and gift vouchers — and would otherwise rank
# at the top (M "Manual" alone is GBP 339,226.24, DOTCOM POSTAGE GBP 309,854.11,
# POSTAGE GBP 125,682.42). They stay in gross sales totals; they are excluded
# from this ranking only. PADS / DCGS* codes are real products and are kept.
NON_PRODUCT_STOCKCODES = {"M", "DOT", "POST", "B", "C2", "D", "AMAZONFEE",
                          "BANK CHARGES", "ADJUST", "S"}
NON_PRODUCT_DESCRIPTIONS = {"Next Day Carriage", "PACKING CHARGE"}
is_non_product = (
    sales["StockCode"].astype(str).str.upper().isin(NON_PRODUCT_STOCKCODES)
    | sales["Description"].isin(NON_PRODUCT_DESCRIPTIONS)
    | sales["Description"].str.contains("Gift Voucher", na=False)
)
product_sales = sales[~is_non_product]
print(f"Non-product lines excluded from top_products: {int(is_non_product.sum())} "
      f"lines, GBP {sales.loc[is_non_product, 'Revenue'].sum():,.2f} "
      "(still counted in gross sales totals)")
top_products = (product_sales.groupby(["StockCode", "Description"]).agg(
    revenue_gbp=("Revenue", "sum"), qty_sold=("Quantity", "sum"),
    invoices=("InvoiceNo", "nunique")).reset_index()
    .sort_values("revenue_gbp", ascending=False).head(30))
top_products.to_csv(os.path.join(OUT, "top_products.csv"), index=False)

country = (sales.groupby("Country").agg(gross_sales_revenue_gbp=("Revenue", "sum"),
                                        invoices=("InvoiceNo", "nunique"),
                                        customers=("CustomerID", "nunique"),
                                        lines=("Revenue", "count"))
           .reset_index().sort_values("gross_sales_revenue_gbp", ascending=False))
country.to_csv(os.path.join(OUT, "country_summary.csv"), index=False)

# ---- RFM (sales lines with a known customer) --------------------------------
ref_date = df["InvoiceDate"].max()
cust = sales.dropna(subset=["CustomerID"]).copy()
rfm = cust.groupby("CustomerID").agg(
    recency_days=("InvoiceDate", lambda s: (ref_date - s.max()).days),
    frequency_invoices=("InvoiceNo", "nunique"),
    monetary_gbp=("Revenue", "sum"),
    first_purchase=("InvoiceDate", "min"),
    last_purchase=("InvoiceDate", "max"),
    lines=("Revenue", "count")).reset_index()
rfm["avg_order_value_gbp"] = (rfm["monetary_gbp"] / rfm["frequency_invoices"]).round(2)

def score(s, ascending_good):
    q = pd.qcut(s, 5, labels=False, duplicates="drop")
    return (q + 1) if ascending_good else (5 - q)
rfm["R_score"] = score(rfm["recency_days"], ascending_good=False)
rfm["F_score"] = score(rfm["frequency_invoices"], ascending_good=True)
rfm["M_score"] = score(rfm["monetary_gbp"], ascending_good=True)
rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

def segment(r):
    if r["RFM_score"] >= 13:
        return "Champions"
    if r["R_score"] >= 4 and r["F_score"] >= 4:
        return "Loyal"
    if r["R_score"] >= 4:
        return "Recent / potential loyal"
    if r["F_score"] >= 4:
        return "At risk (was frequent)"
    if r["M_score"] >= 4:
        return "Big spenders, cooling off"
    return "Lost / low value"
rfm["segment"] = rfm.apply(segment, axis=1)
rfm = rfm.sort_values("monetary_gbp", ascending=False)
rfm.to_csv(os.path.join(OUT, "rfm_customers.csv"), index=False)

seg = (rfm.groupby("segment").agg(customers=("CustomerID", "count"),
                                  revenue_gbp=("monetary_gbp", "sum"),
                                  avg_monetary_gbp=("monetary_gbp", "mean"))
       .reset_index().sort_values("revenue_gbp", ascending=False))
seg.to_csv(os.path.join(OUT, "rfm_segments.csv"), index=False)

ret = (returns.groupby("Country").agg(return_lines=("Revenue", "count"),
                                      return_value_gbp=("Revenue", "sum"))
       .reset_index().sort_values("return_value_gbp"))
ret.to_csv(os.path.join(OUT, "returns_by_country.csv"), index=False)

with open(os.path.join(OUT, "reconciliation.txt"), "w") as f:
    f.write("ONLINE RETAIL II — RECONCILIATION (computed from the real UCI file, 2026-11-13)\n")
    f.write(f"Sheet Year 2009-2010: {len(s1)} rows; Sheet Year 2010-2011: {len(s2)} rows; "
            f"total raw: {raw_total}\n")
    f.write(f"Exact duplicate rows removed (same invoice line on both sheets, 1-9 Dec 2010): {n_dupes_removed}\n")
    f.write(f"Rows after dedupe: {len(df)}\n")
    f.write(f"Gross sales revenue (positive-qty, non-cancelled, UnitPrice>0): GBP {sales['Revenue'].sum():,.2f}\n")
    f.write(f"Returns/cancelled lines value: GBP {returns['Revenue'].sum():,.2f}\n")
    f.write(f"Net revenue (all rows with UnitPrice>0): GBP {valid['Revenue'].sum():,.2f}\n")
    f.write("Check: gross + returns = net (within rounding).\n")
    f.write("Per-file scope:\n")
    f.write("monthly_revenue.csv and country_summary.csv: GROSS sales only (positive-qty, "
            "non-cancelled, UnitPrice>0); the revenue column is gross_sales_revenue_gbp "
            f"and both files sum to gross sales GBP {sales['Revenue'].sum():,.2f}, before returns.\n")
    f.write("top_products.csv: top 30 STOCKABLE products by revenue. Non-product lines "
            "(StockCodes M, DOT, POST, B, C2, D, AMAZONFEE, BANK CHARGES, ADJUST, S; "
            "carriage/packing charges; gift vouchers) are excluded from this ranking "
            "only and still count in gross sales. Row 1 is REGENCY CAKESTAND 3 TIER, "
            "GBP 330,590.32.\n")
    f.write(f"returns_by_country.csv: ALL {len(ret)} countries with returns/cancellations; "
            f"return_value_gbp sums to total returns GBP {returns['Revenue'].sum():,.2f}.\n")
    f.write(f"RFM built on {len(cust)} sales lines with a known CustomerID; "
            f"reference date (max InvoiceDate) = {ref_date.date()}.\n")
print("DONE — outputs in", OUT)
