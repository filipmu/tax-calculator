import math

from ..models import (
    CapitalGainDetail,
    CreditDetail,
    Policy,
    PreCreditTax,
    TaxableIncome,
    TaxUnit,
)
from ..params import param
from .deduction_rules import compute_deductions, compute_section_199a_deduction


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


def compute_taxable_income(
    unit: TaxUnit, policy: Policy, agi: float, capital: CapitalGainDetail
) -> TaxableIncome:
    """Apply the larger of the standard and itemized deductions, then section 199A."""
    deductions = compute_deductions(unit, policy, agi)
    taxable_before_qbi = max(0.0, agi - deductions.used)
    section_199a = compute_section_199a_deduction(
        unit, policy, taxable_before_qbi, capital
    )
    return TaxableIncome(
        amount=max(0.0, taxable_before_qbi - section_199a),
        deductions=deductions,
        section_199a_deduction=section_199a,
    )


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


def compute_credits(
    unit: TaxUnit, policy: Policy, pre_credit_tax: float, agi: float
) -> CreditDetail:
    """Child tax credit, other-dependent credit, and foreign tax credit.

    Section 24 treats the child credit and the $500 credit for other
    dependents as one family credit.  The combined amount is reduced by $50
    for each $1,000 (or fraction) by which modified AGI exceeds the filing
    status threshold.  All credits here are nonrefundable; the refundable
    additional child tax credit is not modeled.
    """
    qualifying_children = sum(1 for d in unit.dependents if d.age < 17)
    other_dependents = sum(1 for d in unit.dependents if d.age >= 17)

    child_credit = qualifying_children * param(policy, "child_credit_amount")
    other_credit = other_dependents * param(
        policy, "other_dependent_credit_amount"
    )
    family_before_phaseout = child_credit + other_credit

    threshold = param(
        policy, "child_credit_phaseout_start", unit.filing_status.value
    )
    step = param(policy, "child_credit_phaseout_step")
    reduction = param(policy, "child_credit_phaseout_reduction")

    excess = max(0.0, agi - threshold)
    # A tiny epsilon keeps an exact multiple from being rounded up by floating
    # point error.
    increments = math.ceil(excess / step - 1e-9) if excess > 0.0 else 0
    phaseout = min(family_before_phaseout, increments * reduction)
    family_credit = max(0.0, family_before_phaseout - phaseout)

    total_before_limit = family_credit + unit.foreign_tax_credit
    allowed = min(total_before_limit, pre_credit_tax)

    return CreditDetail(
        qualifying_children=qualifying_children,
        other_dependents=other_dependents,
        child_credit_before_phaseout=child_credit,
        other_dependent_credit_before_phaseout=other_credit,
        family_credit_before_phaseout=family_before_phaseout,
        family_credit_phaseout=phaseout,
        family_credit=family_credit,
        foreign_tax_credit=unit.foreign_tax_credit,
        allowed=allowed,
    )
