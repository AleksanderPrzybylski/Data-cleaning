"""Own tests for Part 1: add_virtual_column."""

import pandas as pd
import pytest

from solution import add_virtual_column


@pytest.fixture
def fruits():
    return pd.DataFrame({"name": ["banana", "apple"], "quantity": [10, 3], "price": [10, 1]})


def test_example_from_task(fruits):
    result = add_virtual_column(fruits, "quantity * price", "total")
    assert list(result.columns) == ["name", "quantity", "price", "total"]
    assert result["total"].tolist() == [100, 3]


def test_input_dataframe_is_not_changed(fruits):
    before = fruits.copy()
    add_virtual_column(fruits, "quantity * price", "total")
    assert fruits.equals(before)


def test_multiplication_before_addition_and_subtraction(fruits):
    # 10 - 10*10 + 10 = -80 and 3 - 3*1 + 1 = 1
    result = add_virtual_column(fruits, "quantity - price * quantity + price", "x")
    assert result["x"].tolist() == [-80, 1]


def test_same_column_used_twice(fruits):
    result = add_virtual_column(fruits, "quantity * quantity", "squared")
    assert result["squared"].tolist() == [100, 9]


def test_single_column_rule_copies_values(fruits):
    result = add_virtual_column(fruits, "price", "price_copy")
    assert result["price_copy"].tolist() == [10, 1]


def test_float_columns():
    df = pd.DataFrame({"quantity": [2, 3], "unit_price": [1.5, 2.25], "discount": [0.5, 0.0]})
    result = add_virtual_column(df, "quantity * unit_price - discount", "revenue")
    assert result["revenue"].tolist() == pytest.approx([2.5, 6.75])


def test_no_spaces_in_rule(fruits):
    result = add_virtual_column(fruits, "quantity*price", "total")
    assert result["total"].tolist() == [100, 3]


@pytest.mark.parametrize(
    "role",
    [
        "",                      # empty rule
        "   ",                   # only spaces
        "quantity +",            # operator without a column after it
        "* quantity",            # operator without a column before it
        "quantity price",        # two columns without an operator
        "quantity / price",      # division is not supported
        "quantity ** price",     # two operators in a row
        "quantity * 2",          # numbers are not column labels
        "(quantity + price)",    # brackets are not supported
        "quantity1 + price",     # digit in a label
        "weight * price",        # column that does not exist
        "name * quantity",       # text column
    ],
)
def test_invalid_rule_gives_empty_dataframe(fruits, role):
    assert add_virtual_column(fruits, role, "total").empty


@pytest.mark.parametrize("new_column", ["", "total1", "total price", "total-price", None])
def test_invalid_new_column_gives_empty_dataframe(fruits, new_column):
    assert add_virtual_column(fruits, "quantity * price", new_column).empty


def test_existing_column_is_overwritten(fruits):
    result = add_virtual_column(fruits, "quantity * price", "price")
    assert result["price"].tolist() == [100, 3]
    assert fruits["price"].tolist() == [10, 1]
