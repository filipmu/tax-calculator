from ..models import TaxUnit, Policy

def compute_agi(unit: TaxUnit, policy: Policy) -> float:
    # Sum all income sources. Qualified dividends are a subset of ordinary
    # dividends, so they are not added separately.
    gross_income = (
        unit.income.wages_w2
        + unit.income.interest
        + unit.income.ordinary_dividends
        + unit.income.short_term_capital_gains
        + unit.income.long_term_capital_gains
        + unit.income.self_employment
        + unit.income.rental
        + unit.income.other
    )

    # Sum above‑the‑line adjustments
    adjustments = (
        unit.income.ira_deduction
        + unit.income.student_loan_interest_deduction
    )

    # AGI cannot be negative
    return max(0.0, gross_income - adjustments)

def compute_taxable_income(unit: TaxUnit, policy: Policy, agi: float) -> float:
    # Standard deduction
    std_ded = policy.standard_deduction[unit.filing_status]

    # Itemized deductions are not part of TaxUnit, so only the standard
    # deduction is available on this path.
    return max(0.0, agi - std_ded)

def compute_pre_credit_tax(unit: TaxUnit, policy: Policy, taxable_income: float) -> float:
    brackets = policy.brackets[unit.filing_status]
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
    ctc = qualifying_children * policy.child_credit_amount

    # Non-refundable: cannot exceed pre-credit tax
    return min(ctc, pre_credit_tax)