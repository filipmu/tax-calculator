from __future__ import annotations  #prevents circular import crashes
from dataclasses import dataclass
from typing import Callable
from ..models import TaxUnit, Policy
from . import base_rules



@dataclass
class RuleSet:
    compute_agi: Callable[[TaxUnit, Policy], float]
    compute_taxable_income: Callable[[TaxUnit, Policy, float], float]
    compute_pre_credit_tax: Callable[[TaxUnit, Policy, float], float]
    compute_credits: Callable[[TaxUnit, Policy, float], float]

# -----------------------------
# Rule registry
# -----------------------------
    

RuleKey = tuple[str, int]  # (jurisdiction, year)
RULE_SETS: dict[RuleKey, RuleSet] = {}

RULE_SETS[("federal", 2023)] = RuleSet(
    compute_agi=base_rules.compute_agi,
    compute_taxable_income=base_rules.compute_taxable_income,
    compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
    compute_credits=base_rules.compute_credits,  # placeholder or real
)



# -----------------------------
# Rule lookup with fallback
# -----------------------------

def get_ruleset(policy: Policy) -> RuleSet:
    jurisdiction = policy.jurisdiction
    year = policy.year

    # Find all years for this jurisdiction
    available_years = [
        y for (j, y) in RULE_SETS.keys() if j == jurisdiction
    ]

    if not available_years:
        raise ValueError(f"No rulesets defined for jurisdiction '{jurisdiction}'")

    # Find all years <= requested year
    eligible_years = [y for y in available_years if y <= year]

    if eligible_years:
        best_year = max(eligible_years)
        return RULE_SETS[(jurisdiction, best_year)]

    # Requested year is earlier than any defined rules
    raise ValueError(
        f"No ruleset available for {jurisdiction} in {year} "
        f"(earliest available is {min(available_years)})"
    )
