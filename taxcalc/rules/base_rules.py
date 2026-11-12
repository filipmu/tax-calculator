from ..models import CapitalGainDetail, Policy, PreCreditTax, TaxUnit
from ..params import param


def compute_agi(
    unit: TaxUnit, policy: Policy, capital: CapitalGainDetail
) -> float:
    # Sum all income sources except capital gains, which arrive netted and
    # limited by the Schedule D worksheet.  Qualified dividends are a subset
    # of ordinary dividends, so they are not added separately.
    gross_income = (
        unit.income.wages_w2
        + unit.income.taxable_interest
        + unit.income.ordinary_dividends
        + unit.income.taxable_ira
        + unit.income.taxable_pensions_annuities
        + unit.income.taxable_social_security
        + unit.income.other_sched_1
    )
    gross_income += capital.agi_amount

    # Above-the-line adjustments from Schedule 1, Part II
    adjustments = unit.income.adjustments_sched_1

    # AGI cannot be negative
    return max(0.0, gross_income - adjustments)


def compute_taxable_income(unit: TaxUnit, policy: Policy, agi: float) -> float:
    # Standard deduction
    std_ded = param(policy, "standard_deduction", unit.filing_status.value)

    # Itemized deductions are not part of TaxUnit, so only the standard
    # deduction is available on this path.
    return max(0.0, agi - std_ded)


def _bracket_tax(amount: float, brackets) -> float:
    """Tax `amount` against a cumulative list of (rate, upper_limit) brackets."""
    tax = 0.0
    remaining = amount
    last_upper_limit = 0.0

    for rate, upper_limit in brackets:
        if remaining <= 0:
            break

        bracket_amount = min(remaining, upper_limit - last_upper_limit)
        tax += bracket_amount * rate
        remaining -= bracket_amount
        last_upper_limit = upper_limit

    # Brackets that end at a finite number (the illustrative 2023 tables) tax
    # the excess at the top rate.
    if remaining > 0:
        tax += remaining * brackets[-1][0]

    return tax


def compute_pre_credit_tax(
    unit: TaxUnit,
    policy: Policy,
    taxable_income: float,
    capital: CapitalGainDetail,
) -> PreCreditTax:
    """Ordinary brackets plus 0/15/20% rates on preferential income."""
    brackets = param(policy, "brackets", unit.filing_status.value)
    capital_gain_brackets = param(
        policy, "capital_gain_brackets", unit.filing_status.value
    )

    # Preferential income cannot exceed taxable income.  Deductions reduce
    # ordinary income first, which is the Qualifying Dividends and Capital Gain
    # Tax Worksheet ordering.
    preferential_taxable = min(
        max(0.0, capital.preferential_income), taxable_income
    )
    ordinary_taxable = taxable_income - preferential_taxable

    ordinary_tax = _bracket_tax(ordinary_taxable, brackets)
    # Stacking the preferential income above ordinary income is the same as
    # taking the difference of the bracket tax at the two heights.
    preferential_tax = _bracket_tax(
        ordinary_taxable + preferential_taxable, capital_gain_brackets
    ) - _bracket_tax(ordinary_taxable, capital_gain_brackets)

    return PreCreditTax(
        ordinary_taxable_income=ordinary_taxable,
        preferential_taxable_income=preferential_taxable,
        ordinary_tax=ordinary_tax,
        preferential_tax=preferential_tax,
    )


def compute_credits(unit: TaxUnit, policy: Policy, pre_credit_tax: float) -> float:
    # Count dependents under 17 (placeholder logic)
    qualifying_children = sum(1 for d in unit.dependents if d.age < 17)

    # Simple, non-refundable child credit
    ctc = qualifying_children * param(policy, "child_credit_amount")

    # Non-refundable: cannot exceed pre-credit tax
    return min(ctc, pre_credit_tax)
