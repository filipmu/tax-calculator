"""Example private parameter catalog.

Same shape as ``taxcalc/params.py``: a dict keyed by
``(jurisdiction, tax, parameter_name)``, with a list of dated versions.

This template only supplies the ``single`` selector because the example filer
files single.  Add the selectors you actually need; anything you omit raises a
clear ``MissingParameterError`` if a rule asks for it.

The values below are illustrative.  Replace them with reviewed figures.
"""

from typing import Dict, List, Tuple

from taxcalc import Parameter, since, yearly

PARAMETERS: Dict[Tuple[str, str, str], List[Parameter]] = {
    ("federal", "income", "standard_deduction"): [
        yearly(2024, {
            "single": [14600],
        }),
    ],
    ("federal", "income", "brackets"): [
        yearly(2024, {
            "single": [
                (0.10, 11600),
                (0.12, 47150),
                (0.22, 100525),
                (0.24, 191950),
                (0.32, 243725),
                (0.35, 609350),
                (0.37, float("inf")),
            ],
        }),
    ],
    ("federal", "income", "capital_gain_brackets"): [
        yearly(2024, {
            "single": [
                (0.00, 47025),
                (0.15, 518900),
                (0.20, float("inf")),
            ],
        }),
    ],
    ("federal", "income", "capital_loss_limit"): [
        since(2023, {
            "single": [3000],
        }),
    ],
    ("federal", "income", "medical_expense_floor"): [
        since(2023, {"default": [0.075]}),
    ],
    ("federal", "income", "salt_cap"): [
        yearly(2024, {
            "single": [10000],
        }),
    ],
    ("federal", "income", "charitable_cash_limit"): [
        since(2023, {"default": [0.60]}),
    ],
    ("federal", "income", "child_credit_amount"): [
        since(2023, {"default": [2000]}),
    ],
    ("federal", "niit", "niit_rate"): [
        since(2013, {"default": [0.038]}),
    ],
    ("federal", "niit", "niit_threshold"): [
        since(2013, {
            "single": [200000],
        }),
    ],
}
