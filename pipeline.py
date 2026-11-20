"""Clean sales.csv, add a revenue column and write total revenue per region."""

from pathlib import Path

import pandas as pd

from solution import add_virtual_column

INPUT_FILE = Path("sales.csv")
OUTPUT_FILE = Path("revenue_by_region.csv")

# Raw header -> clean name. New names use only letters and "_",
# because add_virtual_column accepts only such labels.
COLUMN_NAMES = {
    "Order ID": "order_id",
    "Region": "region",
    "Product": "product",
    "Quantity": "quantity",
    "Unit Price": "unit_price",
    "Discount": "discount",
    "Order Date": "order_date",
}


def read_raw(path: Path = INPUT_FILE) -> pd.DataFrame:
    """Read every value as text, so nothing is guessed or lost while reading."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = df.columns.str.strip()          # "Quantity " -> "Quantity"
    return df.rename(columns=COLUMN_NAMES)


def clean(df: pd.DataFrame, report: dict | None = None) -> pd.DataFrame:
    """Fix the problems found in sales.csv. Counts of affected rows go into report."""
    report = {} if report is None else report
    df = df.copy()

    # 1. Rows that are not order lines: a repeated header and a TOTAL summary row.
    is_header = df["order_id"] == "Order ID"
    is_total = df["order_id"].str.strip().str.upper() == "TOTAL"
    report["repeated header rows removed"] = int(is_header.sum())
    report["TOTAL rows removed"] = int(is_total.sum())
    df = df[~is_header & ~is_total]

    # 2. Text columns: trim spaces; regions get one spelling ("west  ", "EAST" -> "West", "East").
    region_before = df["region"]
    for column in ["order_id", "region", "product", "order_date"]:
        df[column] = df[column].str.strip()
    df["region"] = df["region"].str.title()
    report["region spelling fixed"] = int((df["region"] != region_before).sum())

    # 3. Quantity: thousands separator written as a space ("1 762" -> 1762).
    has_space = df["quantity"].str.contains(" ")
    report["quantity with space as thousands separator"] = int(has_space.sum())
    df["quantity"] = pd.to_numeric(df["quantity"].str.replace(" ", "", regex=False))
    report["negative quantity (kept as returns)"] = int((df["quantity"] < 0).sum())

    # 4. Unit price: decimal comma ("59,00" -> 59.00) and missing prices.
    has_comma = df["unit_price"].str.contains(",")
    report["unit price with decimal comma"] = int(has_comma.sum())
    price_text = df["unit_price"].str.replace(",", ".", regex=False)
    df["unit_price"] = pd.to_numeric(price_text.mask(price_text == ""))  # "" -> NaN
    missing_price = df["unit_price"].isna()
    report["missing unit price filled from product price"] = int(missing_price.sum())
    # Every product has exactly one price in the file, so the missing ones can be filled.
    product_price = df.loc[~missing_price].groupby("product")["unit_price"].agg(
        lambda prices: prices.mode().iloc[0]
    )
    df.loc[missing_price, "unit_price"] = df.loc[missing_price, "product"].map(product_price)

    # 5. Discount: empty means no discount.
    no_discount = df["discount"] == ""
    report["empty discount set to 0"] = int(no_discount.sum())
    df["discount"] = pd.to_numeric(df["discount"].replace("", "0"))

    # 6. Order date: real dates instead of text.
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")

    # 7. Exact duplicate lines (same order ID and same values), checked after cleaning.
    duplicated = df.duplicated()
    report["duplicate rows removed"] = int(duplicated.sum())
    df = df[~duplicated]

    return df.reset_index(drop=True)


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """revenue = quantity * unit_price - discount, using the Part 1 function."""
    result = add_virtual_column(df, "quantity * unit_price - discount", "revenue")
    if result.empty:
        raise ValueError("add_virtual_column could not compute revenue")
    return result


def revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    totals = df.groupby("region", as_index=False)["revenue"].sum()
    totals["revenue"] = totals["revenue"].round(2)
    return totals.sort_values("region").reset_index(drop=True)


def main() -> None:
    report = {}
    sales = add_revenue(clean(read_raw(), report))
    totals = revenue_by_region(sales)
    totals.to_csv(OUTPUT_FILE, index=False)

    print("Cleaning report (rows affected):")
    for problem, count in report.items():
        print(f"  {problem}: {count}")
    print(f"\nClean order lines: {len(sales)}")
    print(f"Wrote {OUTPUT_FILE}:\n{totals.to_string(index=False)}")


if __name__ == "__main__":
    main()
