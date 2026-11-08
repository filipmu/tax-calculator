from .rules.rulesets import get_ruleset
from .models import TaxUnit, Policy, TaxResult




def compute_tax(unit: TaxUnit, policy: Policy) -> TaxResult:

    rules = get_ruleset(policy)

    agi = rules.compute_agi(unit, policy)
    taxable_income = rules.compute_taxable_income(unit, policy, agi)
    pre_credit_tax = rules.compute_pre_credit_tax(unit, policy, taxable_income)
    total_credits = rules.compute_credits(unit, policy, pre_credit_tax)
    net_tax = compute_net_tax(pre_credit_tax, total_credits)

    return TaxResult(
        agi=agi,
        taxable_income=taxable_income,
        pre_credit_tax=pre_credit_tax,
        total_credits=total_credits,
        net_tax=net_tax,
    )


def compute_agi(unit: TaxUnit, policy: Policy) -> float:
    # Sum all income sources
    gross_income = (
        unit.income.wages_w2
        + unit.income.interest
        + unit.income.ordinary_dividends
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

    # Placeholder for itemized deductions (future expansion)
    itemized = getattr(unit, "itemized_deductions", None)

    # Choose the larger of standard or itemized
    deduction = max(std_ded, itemized) if itemized is not None else std_ded

    return max(0.0, agi - deduction)


def compute_pre_credit_tax(unit: TaxUnit, policy: Policy, taxable_income: float) -> float:
    brackets = policy.brackets[unit.filing_status]
    tax = 0.0
    remaining = taxable_income
    last_threshold = 0.0

    for rate, threshold in brackets:
        if remaining <= 0:
            break

        # Income taxed in this bracket
        bracket_amount = min(remaining, threshold - last_threshold)

        tax += bracket_amount * rate
        remaining -= bracket_amount
        last_threshold = threshold

    # If income exceeds the last threshold, tax the remainder at the top rate
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

def compute_net_tax(pre_credit_tax: float, total_credits: float) -> float:
    return max(0.0, pre_credit_tax - total_credits)