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
    ("federal", "income", "child_credit_phaseout_start"): [
        since(2023, {
            "single": [200000],
        }),
    ],
    ("federal", "income", "child_credit_phaseout_step"): [
        since(2023, {"default": [1000]}),
    ],
    ("federal", "income", "child_credit_phaseout_reduction"): [
        since(2023, {"default": [50]}),
    ],
    ("federal", "income", "other_dependent_credit_amount"): [
        since(2023, {"default": [500]}),
    ],
    ("federal", "income", "section_199a_rate"): [
        since(2018, {"default": [0.20]}),
    ],
    ("federal", "niit", "niit_rate"): [
        since(2013, {"default": [0.038]}),
    ],
    ("federal", "niit", "niit_threshold"): [
        since(2013, {
            "single": [200000],
        }),
    ],
    # Minnesota, 2024, single filer.  Same shape as the federal entries.
    ("MN", "income", "brackets"): [
        yearly(2024, {
            "single": [
                (0.0535, 31690),
                (0.0680, 104090),
                (0.0785, 193240),
                (0.0985, float("inf")),
            ],
        }),
    ],
    ("MN", "income", "standard_deduction"): [
        yearly(2024, {
            "single": [14575],
        }),
    ],
    ("MN", "income", "standard_deduction_phaseout_start"): [
        yearly(2024, {
            "single": [232500],
        }),
    ],
    ("MN", "income", "standard_deduction_phaseout_second"): [
        yearly(2024, {
            "single": [321350],
        }),
    ],
    ("MN", "income", "standard_deduction_phaseout_rate"): [
        since(2023, {"default": [0.03]}),
    ],
    ("MN", "income", "standard_deduction_phaseout_rate_second"): [
        since(2023, {"default": [0.10]}),
    ],
    ("MN", "income", "standard_deduction_phaseout_cap"): [
        since(2023, {"default": [0.80]}),
    ],
    ("MN", "income", "dependent_exemption"): [
        yearly(2024, {
            "single": [5050],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_start"): [
        yearly(2024, {
            "single": [232550],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_step"): [
        since(2023, {
            "single": [2500],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_max"): [
        since(2023, {
            "single": [122500],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_rate"): [
        since(2023, {"default": [0.02]}),
    ],
}
