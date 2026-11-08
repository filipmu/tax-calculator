from .rules.rulesets import get_ruleset
from .rules.base_rules import (
    compute_agi,
    compute_taxable_income,
    compute_pre_credit_tax,
    compute_credits,
)
from .models import TaxUnit, Policy, TaxResult


def compute_net_tax(pre_credit_tax: float, total_credits: float) -> float:
    return max(0.0, pre_credit_tax - total_credits)


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
