"""Schedule A itemized deductions and the standard/itemized choice.

Each category is reported at the amount actually allowed, after its own limit:

* medical expenses above the floor (7.5% of AGI);
* state and local taxes under the cap, including the post-2024 phase-down;
* mortgage interest and points as entered;
* charitable contributions under the percentage-of-AGI limit, plus the 0.5%
  floor that starts in 2026.

Starting in 2026, section 68 reduces total itemized deductions by 2/37 of the
lesser of the deductions or the excess of income over the start of the 37%
bracket.  The bracket start comes from the same ``brackets`` parameter used for
the ordinary tax, so it tracks each year's inflation adjustment.

Losses that need facts the calculator does not hold (a federally declared
disaster, gambling winnings) are not deducted; ``coverage.py`` reports them.
"""

from ..models import DeductionDetail, Policy, TaxUnit
from ..params import optional_param, param


def _medical_expenses(unit: TaxUnit, policy: Policy, agi: float) -> float:
    paid = unit.itemized.medical_dental_expenses
    floor = param(policy, "medical_expense_floor") * agi
    return max(0.0, paid - floor)


def _state_local_taxes(unit: TaxUnit, policy: Policy, agi: float) -> float:
    """SALT actually paid, limited by the cap in effect for the year.

    From 2025 the cap is reduced by 30% of MAGI above a threshold, but never
    below a floor.  Both extra parameters arrive with the 2025 versions, so the
    phase-down is dormant in earlier years.
    """
    itemized = unit.itemized
    paid = (
        itemized.state_local_income_taxes
        + itemized.real_estate_taxes
        + itemized.personal_property_taxes
    )

    filing_status = unit.filing_status.value
    cap = param(policy, "salt_cap", filing_status)

    threshold = optional_param(
        policy, "salt_cap_phaseout_threshold", filing_status
    )
    if threshold is not None:
        reduction = param(policy, "salt_cap_phaseout_rate") * max(
            0.0, agi - threshold
        )
        cap = max(param(policy, "salt_cap_floor", filing_status), cap - reduction)

    return min(paid, cap)


def _charitable(unit: TaxUnit, policy: Policy, agi: float) -> float:
    """Charitable contributions after the floor and the percentage limit.

    The 60% limit is applied to all contributions.  The separate 30% limit for
    appreciated property and the five-year carryforward are not modeled;
    ``coverage.py`` warns when noncash contributions are entered.
    """
    itemized = unit.itemized
    paid = (
        itemized.cash_contributions_50pct_orgs
        + itemized.cash_contributions_other
        + itemized.donor_advised_fund_contributions
        + itemized.noncash_contributions
    )
    if paid <= 0:
        return 0.0

    floor = optional_param(policy, "charitable_floor", default=0.0) * agi
    limit = param(policy, "charitable_cash_limit") * agi
    return min(max(0.0, paid - floor), limit)


def _top_bracket_start(brackets) -> float:
    """Income where the top ordinary bracket begins."""
    if len(brackets) < 2:
        return float("inf")
    return brackets[-2][1]


def _overall_limitation(
    policy: Policy, agi: float, itemized_total: float, brackets
) -> float:
    """Section 68 reduction (2026 onward; absent from earlier policies)."""
    rate = optional_param(
        policy, "itemized_deduction_limit_rate", default=0.0
    )
    if rate == 0.0 or itemized_total <= 0.0:
        return 0.0

    # Our taxable income before itemized deductions is AGI: there are no other
    # below-the-line deductions in the model.
    excess = max(0.0, agi - _top_bracket_start(brackets))
    return rate * min(itemized_total, excess)


def compute_deductions(
    unit: TaxUnit, policy: Policy, agi: float
) -> DeductionDetail:
    """Return the standard deduction and the allowed Schedule A amounts."""
    filing_status = unit.filing_status.value
    standard = param(policy, "standard_deduction", filing_status)

    itemized = unit.itemized
    if itemized is None:
        return DeductionDetail(standard=standard)

    medical = _medical_expenses(unit, policy, agi)
    state_local = _state_local_taxes(unit, policy, agi)
    mortgage = itemized.mortgage_interest + itemized.mortgage_points
    charitable = _charitable(unit, policy, agi)

    before_limitation = medical + state_local + mortgage + charitable
    limitation = _overall_limitation(
        policy,
        agi,
        before_limitation,
        param(policy, "brackets", filing_status),
    )

    return DeductionDetail(
        standard=standard,
        medical=medical,
        state_local_taxes=state_local,
        mortgage_interest=mortgage,
        charitable=charitable,
        limitation=limitation,
    )
