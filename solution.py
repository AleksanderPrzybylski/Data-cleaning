import re

import pandas

LABEL_PATTERN = re.compile(r"[A-Za-z_]+")

ROLE_PATTERN = re.compile(r"\s*[A-Za-z_]+\s*(?:[+\-*]\s*[A-Za-z_]+\s*)*")


def _is_valid_label(label) -> bool:
    return isinstance(label, str) and LABEL_PATTERN.fullmatch(label) is not None


def add_virtual_column(df: pandas.DataFrame, role: str, new_column: str) -> pandas.DataFrame:

    if not isinstance(df, pandas.DataFrame) or not isinstance(role, str):
        return pandas.DataFrame([])
    if not _is_valid_label(new_column):
        return pandas.DataFrame([])

    if ROLE_PATTERN.fullmatch(role) is None:
        return pandas.DataFrame([])

    tokens = re.findall(r"[A-Za-z_]+|[+\-*]", role)
    labels = tokens[0::2]
    operators = tokens[1::2]

    for label in labels:
        if label not in df.columns:
            return pandas.DataFrame([])
        if not pandas.api.types.is_numeric_dtype(df[label]) or pandas.api.types.is_bool_dtype(df[label]):
            return pandas.DataFrame([])

    result = None
    current_term = df[labels[0]]
    sign = "+"
    for operator, label in zip(operators, labels[1:]):
        if operator == "*":
            current_term = current_term * df[label]
        else:
            result = _combine(result, current_term, sign)
            sign = operator
            current_term = df[label]
    result = _combine(result, current_term, sign)

    output = df.copy()
    output[new_column] = result
    return output


def _combine(result, term, sign):
    if result is None:
        return term if sign == "+" else -term
    return result + term if sign == "+" else result - term