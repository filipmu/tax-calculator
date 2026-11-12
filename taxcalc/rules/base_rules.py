from ..models import TaxUnit, Policy
from ..params import param

def compute_agi(unit: TaxUnit, policy: Policy) -> float:
    # Sum all income sources. Qualified dividends are a subset of ordinary
    # dividends, so they are not added separately.
    gross_income = (
        unit.income.wages_w2
        + unit.income.taxable_interest
        + unit.income.ordinary_dividends
        + unit.income.taxable_ira
        + unit.income.taxable_pensions_annuities
        + unit.income.taxable_social_security
        + unit.income.short_term_capital_gain_loss
        + unit.income.long_term_capital_gain_loss
        + unit.income.other_sched_1
    )

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

def compute_pre_credit_tax(unit: TaxUnit, policy: Policy, taxable_income: float) -> float:
    brackets = param(policy, "brackets", unit.filing_status.value)
    tax = 0.0
    remaining = taxable_income
    last_upper_limit = 0.0

    for rate, upper_limit in brackets:
        if remaining <= 0:
            break

        # Income taxed in this bracket
        bracket_amount = min(remaining, upper_limit - last_upper_limit)

        tax += bracket_amount * rate
        remaining -= bracket_amount
        last_upper_limit = upper_limit

    # If income exceeds the last bracket's upper limit, tax the remainder
    # at the top rate
    if remaining > 0:
        top_rate = brackets[-1][0]
        tax += remaining * top_rate

    return tax

def compute_credits(unit: TaxUnit, policy: Policy, pre_credit_tax: float) -> float:
    # Count dependents under 17 (placeholder logic)
    qualifying_children = sum(1 for d in unit.dependents if d.age < 17)

    # Simple, non-refundable child credit
    ctc = qualifying_children * param(policy, "child_credit_amount")

    # Non-refundable: cannot exceed pre-credit tax
    return min(ctc, pre_credit_tax)