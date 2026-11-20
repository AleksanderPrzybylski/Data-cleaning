# Virtual columns in a pandas DataFrame

## Setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/AleksanderPrzybylski/Recruitment-task.git
cd Recruitment-task
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell)
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

## Running the pipeline

```bash
python pipeline.py
```

It reads sales.csv, prints how many rows each cleaning step affected, and writes revenue_by_region.csv (columns region, revenue).

## Running the tests

All tests (sample tests and my own) run with one command from the repository folder:

```bash
python -m pytest
```

## Assumptions (Part 1)

- **Supported rules:** column labels joined by +, - and *, with any spaces. * is applied before + and -, as in normal arithmetic, so a - b * c means a - (b * c).
- **Not supported:** numbers, brackets, division and a leading minus. A rule with any of these returns an empty DataFrame.
- **Which labels are validated:** new_column and every label used in role must contain only letters and _. Other columns of df are not checked, because the function does not use them.
- **Columns in the rule must be numeric.** A text or boolean column returns an empty DataFrame, because "name * quantity" would otherwise repeat strings without any error.
- **Copy, not change:** the function returns a new DataFrame and never changes the one passed in.
- **Existing column:** if new_column already exists, it is overwritten in the returned copy.
- **Example in the task:** the example passes "total" as the new column name, but the printed result is headed price_total. I treated this as a typo: the new column gets the name that is passed in.
- **No eval:** the rule is checked with a regular expression and calculated directly with pandas. eval/df.eval are not used, so a label like "and" or "if" cannot be misread as Python code.

## Data problems in sales.csv and how they are handled

sales.csv has 1,507 lines after its header: 1,505 order lines, one repeated header and one TOTAL row. After cleaning, 1,500 order lines remain.

| Problem | Rows affected | How it is handled |
|---|---|---|
| Header "Quantity " has a trailing space; headers contain spaces | all | Spaces stripped and columns renamed to order_id, region, product, quantity, unit_price, discount, order_date (only letters and _, as add_virtual_column requires) |
| Header line repeated in the middle of the file | 1 | Removed: it is not an order line |
| TOTAL summary row at the end | 1 | Removed: it is not an order line |
| Region with extra spaces or different case (" South", "EAST", "west  ", "central", ...) | 15 | Spaces stripped and first letter capitalised, giving 5 regions: Central, East, North, South, West |
| Quantity with a space as thousands separator ("1 762") | 4 | Space removed, read as 1762 (see decisions) |
| Negative quantity (-2, -5, ...) | 6 | Kept as returns (see decisions) |
| Unit price with a decimal comma ("59,00") | 7 | Comma replaced by a dot, read as 59.00 |
| Missing unit price | 4 | Filled with the product's price (see decisions) |
| Empty discount | 963 | Set to 0, as the task says empty means no discount |
| Exact duplicate lines (same order ID and all values) | 5 | Duplicates removed, one copy kept |

No row that could be fixed was dropped. Only the repeated header, the TOTAL row and the 5 duplicate copies were removed.

### Decisions

- **"1 762" is 1762.** These four values (1762, 1745, 1371, 1427) are much larger than the usual 1–40, but the TOTAL row of the export (quantity 37150) only adds up when they are read this way. So the source system itself counts them as these numbers. I kept them. Together they add 324,349.00 to total revenue (206,815.00 of it in North), so they should be confirmed with the data owner.
- **Negative quantities are returns.** They are kept as they are, so they reduce revenue. The data cannot show whether they are returns or sign typos. Keeping them matches how the source system adds up quantity in its TOTAL row.
- **Missing prices are filled from the product.** Every product has exactly one unit price in the whole file (for example, Keyboard is always 89.00). Order SO-11477 confirms this: its discount of 164.65 is exactly 5% of 37 × 89.00.
- **Duplicates.** Lines identical in every column, including order ID, are treated as export duplicates and counted once. The check runs after cleaning, so two lines that differ only in formatting are also found.
- **Revenue** is quantity * unit_price - discount per line, calculated with add_virtual_column. Totals per region are rounded to 2 decimal places.
- **Discounts** were checked: none is larger than the line value, so no line has negative revenue except returns.
- **Order dates** are all valid YYYY-MM-DD dates (2026-01-02 to 2026-09-29). They are converted to dates but not used for revenue.

## Result

revenue_by_region.csv:

| region | revenue |
|---|---|
| Central | 515824.67 |
| East | 442219.91 |
| North | 665897.52 |
| South | 504036.04 |
| West | 442268.89 |
