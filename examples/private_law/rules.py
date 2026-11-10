"""Example private rule wiring.

A ``RuleSet`` is a snapshot of the four income-tax steps.  This template reuses
the public rule functions but only for tax year 2024.  To change the logic,
write your own functions and point the rule set at them; never edit an
existing rule set in place.

If you need a year beyond 2024, add a new rule set (or extend this one's
effective range) and make sure the private catalog covers that year.
"""

from datetime import date

from taxcalc.rules import base_rules
from taxcalc.rules.rulesets import RuleSet

RULE_SETS = {
    ("federal", "income"): [
        RuleSet(
            effective=(date(2024, 1, 1), date(2024, 12, 31)),
            compute_agi=base_rules.compute_agi,
            compute_taxable_income=base_rules.compute_taxable_income,
            compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
            compute_credits=base_rules.compute_credits,
        ),
    ],
}
