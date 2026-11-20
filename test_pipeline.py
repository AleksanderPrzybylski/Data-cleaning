"""Own tests for Part 2: pipeline.py."""

import pandas as pd
import pytest

import pipeline

HEADER = "Order ID,Region,Product,Quantity ,Unit Price,Discount,Order Date"


def write_csv(tmp_path, lines):
    path = tmp_path / "sales.csv"
    path.write_text("\n".join([HEADER, *lines]) + "\n", encoding="utf-8")
    return path


def clean_lines(tmp_path, lines, report=None):
    return pipeline.clean(pipeline.read_raw(write_csv(tmp_path, lines)), report)


def test_column_names_are_cleaned(tmp_path):
    df = pipeline.read_raw(write_csv(tmp_path, ["SO-1,North,Mouse,2,29.50,,2026-01-01"]))
    assert list(df.columns) == [
        "order_id", "region", "product", "quantity", "unit_price", "discount", "order_date"
    ]


def test_header_and_total_rows_are_removed(tmp_path):
    df = clean_lines(tmp_path, [
        "SO-1,North,Mouse,2,29.50,,2026-01-01",
        HEADER,
        "SO-2,South,Mouse,1,29.50,,2026-01-02",
        "TOTAL,,,3,,0,",
    ])
    assert df["order_id"].tolist() == ["SO-1", "SO-2"]


def test_region_spelling_is_unified(tmp_path):
    df = clean_lines(tmp_path, [
        "SO-1, north,Mouse,1,29.50,,2026-01-01",
        "SO-2,EAST  ,Mouse,1,29.50,,2026-01-01",
        "SO-3,West,Mouse,1,29.50,,2026-01-01",
    ])
    assert df["region"].tolist() == ["North", "East", "West"]


def test_quantity_with_space_and_negative_quantity(tmp_path):
    df = clean_lines(tmp_path, [
        "SO-1,North,Mouse,1 762,29.50,,2026-01-01",
        "SO-2,North,Mouse,-2,29.50,,2026-01-01",
    ])
    assert df["quantity"].tolist() == [1762, -2]


def test_decimal_comma_in_unit_price(tmp_path):
    df = clean_lines(tmp_path, ['SO-1,North,Mouse,1,"29,50",,2026-01-01'])
    assert df["unit_price"].tolist() == [29.5]


def test_missing_price_is_filled_from_product(tmp_path):
    df = clean_lines(tmp_path, [
        "SO-1,North,Keyboard,1,89.00,,2026-01-01",
        "SO-2,North,Keyboard,2,,,2026-01-01",
    ])
    assert df["unit_price"].tolist() == [89.0, 89.0]


def test_empty_discount_becomes_zero(tmp_path):
    df = clean_lines(tmp_path, ["SO-1,North,Mouse,1,29.50,,2026-01-01"])
    assert df["discount"].tolist() == [0.0]


def test_exact_duplicates_are_removed(tmp_path):
    report = {}
    df = clean_lines(tmp_path, [
        "SO-1,North,Mouse,1,29.50,,2026-01-01",
        "SO-1,North,Mouse,1,29.50,,2026-01-01",
    ], report)
    assert len(df) == 1
    assert report["duplicate rows removed"] == 1


def test_revenue_is_quantity_times_price_minus_discount(tmp_path):
    df = pipeline.add_revenue(clean_lines(tmp_path, ["SO-1,North,Mouse,10,29.50,14.75,2026-01-01"]))
    assert df["revenue"].tolist() == pytest.approx([280.25])


def test_revenue_by_region_sums_and_sorts(tmp_path):
    df = pipeline.add_revenue(clean_lines(tmp_path, [
        "SO-1,West,Mouse,2,10.00,,2026-01-01",
        "SO-2,East,Mouse,1,10.00,,2026-01-01",
        "SO-3,West,Mouse,1,10.00,5.00,2026-01-01",
    ]))
    totals = pipeline.revenue_by_region(df)
    assert totals["region"].tolist() == ["East", "West"]
    assert totals["revenue"].tolist() == [10.0, 25.0]


def test_real_file_cleaning_report():
    report = {}
    df = pipeline.clean(pipeline.read_raw("sales.csv"), report)
    assert len(df) == 1500
    assert sorted(df["region"].unique()) == ["Central", "East", "North", "South", "West"]
    assert df[["quantity", "unit_price", "discount"]].notna().all().all()
    assert report == {
        "repeated header rows removed": 1,
        "TOTAL rows removed": 1,
        "region spelling fixed": 15,
        "quantity with space as thousands separator": 4,
        "negative quantity (kept as returns)": 6,
        "unit price with decimal comma": 7,
        "missing unit price filled from product price": 4,
        "empty discount set to 0": 963,
        "duplicate rows removed": 5,
    }


def test_main_writes_revenue_by_region(tmp_path, monkeypatch):
    output = tmp_path / "revenue_by_region.csv"
    monkeypatch.setattr(pipeline, "OUTPUT_FILE", output)
    pipeline.main()
    result = pd.read_csv(output)
    assert list(result.columns) == ["region", "revenue"]
    assert result["region"].tolist() == ["Central", "East", "North", "South", "West"]
    assert result["revenue"].sum() == pytest.approx(2570247.03)
