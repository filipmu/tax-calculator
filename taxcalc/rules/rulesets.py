from __future__ import annotations  # prevents circular import crashes

from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, List, Optional, Tuple

from ..models import CapitalGainDetail, Policy, PreCreditTax, TaxUnit
from ..pack import LawPack, default_pack
from ..params import NoEffectiveVersionError, select, validate
from . import base_rules


@dataclass(frozen=True)
class RuleSet:
    """One snapshot of the rules for a tax, effective over a date range."""
    effective: Tuple[date, date]
    compute_agi: Callable[[TaxUnit, Policy, CapitalGainDetail], float]
    compute_taxable_income: Callable[[TaxUnit, Policy, float], float]
    compute_pre_credit_tax: Callable[
        [TaxUnit, Policy, float, CapitalGainDetail], PreCreditTax
    ]
    compute_credits: Callable[[TaxUnit, Policy, float], float]


# -----------------------------
# Rule registry
# -----------------------------
#
# Keyed by (jurisdiction, tax); the year lives in each RuleSet's effective
# range. One entry can therefore cover several tax years.

RuleKey = Tuple[str, str]  # (jurisdiction, tax)

RULE_SETS: Dict[RuleKey, List[RuleSet]] = {
    ("federal", "income"): [
        RuleSet(
            effective=(date(2023, 1, 1), date(2025, 12, 31)),
            compute_agi=base_rules.compute_agi,
            compute_taxable_income=base_rules.compute_taxable_income,
            compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
            compute_credits=base_rules.compute_credits,
        ),
    ],
}


# -----------------------------
# Rule lookup - no fallback
# -----------------------------

def get_ruleset(policy: Policy, *, pack: Optional[LawPack] = None) -> RuleSet:
    """Return the single rule set effective for the policy's tax year.

    Rule sets come from ``pack`` when given, otherwise from the illustrative
    example pack. There is no fallback between packs or between years.

    Raises ``NoEffectiveVersionError`` when no rule set covers the year.
    """
    rule_sets = pack.rule_sets if pack is not None else default_pack().rule_sets
    key = (policy.jurisdiction, policy.tax)
    try:
        versions = rule_sets[key]
    except KeyError:
        available = ", ".join(
            f"{j}/{t}" for (j, t) in sorted(rule_sets)
        ) or "(none)"
        raise NoEffectiveVersionError(
            f"{policy.jurisdiction}/{policy.tax}: no rule sets are defined. "
            f"Available: {available}"
        ) from None

    return select(
        versions,
        policy.year,
        label=f"{policy.jurisdiction}/{policy.tax} rules",
    )


def _validate_registry() -> None:
    for key, versions in RULE_SETS.items():
        validate(versions, label="/".join(key) + " rules")


_validate_registry()
