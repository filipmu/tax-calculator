"""Minnesota individual income tax (Form M1).

Minnesota starts from federal adjusted gross income, subtracts its own
deduction and dependent exemptions, and applies the M1 brackets.  This module
models the standard deduction, including the high-income limitation, the
dependent exemption phase-out, and the subtraction for U.S. government interest
(which Minnesota does not tax).

Not modeled, and reported by ``coverage.py``:

* Minnesota itemized deductions (Schedule M1SA);
* the Social Security subtraction and other Schedule M1M items;
* Minnesota additions, such as interest on another state's bonds;
* the Minnesota alternative minimum tax and nonrefundable credits.
"""

import math
from typing import Tuple

from ..models import AddonTaxResult, MNResult, Policy, TaxResult, TaxUnit
from ..params import param
from .base_rules import _bracket_tax


def _standard_deduction(
    unit: TaxUnit, policy: Policy, agi: float
) -> Tuple[float, float]:
    """Return (deduction before limitation, limitation).

    The limitation is 3% of AGI above the first threshold plus 10% above the
    second threshold, capped at 80% of the deduction.
    """
    filing_status = unit.filing_status.value
    base = param(policy, "standard_deduction", filing_status)
    first = param(policy, "standard_deduction_phaseout_start", filing_status)
    second = param(policy, "standard_deduction_phaseout_second", filing_status)

    first_band = min(max(0.0, agi - first), second - first)
    second_band = max(0.0, agi - second)
    reduction = (
        param(policy, "standard_deduction_phaseout_rate") * first_band
        + param(policy, "standard_deduction_phaseout_rate_second") * second_band
    )
    cap = param(policy, "standard_deduction_phaseout_cap") * base
    return base, min(reduction, cap)


def _dependent_exemptions(
    unit: TaxUnit, policy: Policy, agi: float
) -> Tuple[float, float]:
    """Return (exemptions before phase-out, phase-out amount).

    The phase-out is 2% of the exemption amount for each $2,500 of AGI above
    the filing-status threshold ($1,250 for married filing separately).  Once
    the excess passes the maximum, no exemption remains.
    """
    filing_status = unit.filing_status.value
    total = unit.num_dependents * param(
        policy, "dependent_exemption", filing_status
    )
    if total == 0.0:
        return 0.0, 0.0

    start = param(
        policy, "dependent_exemption_phaseout_start", filing_status
    )
    excess = agi - start
    if excess <= 0.0:
        return total, 0.0

    maximum = param(
        policy, "dependent_exemption_phaseout_max", filing_status
    )
    if excess > maximum:
        return total, total

    step = param(policy, "dependent_exemption_phaseout_step", filing_status)
    # A tiny epsilon keeps an exact multiple from being rounded up by floating
    # point error.
    steps = math.ceil(excess / step - 1e-9)
    reduction = (
        steps * param(policy, "dependent_exemption_phaseout_rate") * total
    )
    return total, min(reduction, total)


def compute_mn_return(
    unit: TaxUnit, policy: Policy, federal_agi: float
) -> MNResult:
    """Compute Minnesota taxable income and tax from federal AGI."""
    treasury = unit.income.us_treasury_interest
    mn_agi = max(0.0, federal_agi - treasury)

    # The limitation worksheets use Form M1 line 1, which is federal AGI
    # before the Minnesota subtractions.
    standard, standard_limitation = _standard_deduction(
        unit, policy, federal_agi
    )
    exemptions, exemption_phaseout = _dependent_exemptions(
        unit, policy, federal_agi
    )

    mn_taxable_income = max(
        0.0,
        mn_agi
        - (standard - standard_limitation)
        - (exemptions - exemption_phaseout),
    )
    brackets = param(policy, "brackets", unit.filing_status.value)

    return MNResult(
        federal_agi=federal_agi,
        treasury_subtraction=treasury,
        standard_deduction_before_limitation=standard,
        standard_deduction_limitation=standard_limitation,
        dependent_exemptions_before_phaseout=exemptions,
        dependent_exemption_phaseout=exemption_phaseout,
        mn_taxable_income=mn_taxable_income,
        tax=_bracket_tax(mn_taxable_income, brackets),
    )


def compute_mn_tax(
    unit: TaxUnit, policy: Policy, income_result: TaxResult
) -> AddonTaxResult:
    """Add-on rule entry point: Minnesota tax on the federal AGI."""
    result = compute_mn_return(unit, policy, income_result.agi)
    return AddonTaxResult(amount=result.tax, detail=result)
