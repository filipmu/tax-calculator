import warnings
from typing import Callable, Dict, Mapping, Optional

from .models import Policy, ReturnResult, TaxResult, TaxUnit
from .pack import LawPack, default_pack
from .params import AvailabilityError
from .rules.rulesets import get_ruleset


def compute_net_tax(pre_credit_tax: float, total_credits: float) -> float:
    return max(0.0, pre_credit_tax - total_credits)


# -----------------------------
# Combining taxes (example pack)
# -----------------------------
#
# `parts` holds one amount per tax name. The convention (chosen so AMT can be
# added later without reshaping the pipeline):
#
#   "income" -> regular income tax
#   "niit"   -> add-on tax, summed on top
#   "amt"    -> tentative minimum tax, compared with income (future work)
#
# A combiner decides which parts add and which compare. These definitions are
# example data; a LawPack supplies the combiners actually used.

def federal_combine(parts: Mapping[str, float]) -> float:
    return parts.get("income", 0.0) + parts.get("niit", 0.0)


COMBINERS: Dict[str, Callable[[Mapping[str, float]], float]] = {
    "federal": federal_combine,
}


# -----------------------------
# Return pipeline
# -----------------------------

def compute_return(
    unit: TaxUnit,
    policies: Mapping[str, Policy],
    *,
    pack: Optional[LawPack] = None,
) -> ReturnResult:
    """Compute several tax policies and combine them into a return total.

    ``policies["income"]`` is required because it supplies AGI. AGI is
    computed once and passed to every add-on tax rule.

    All law data comes from ``pack``. If none is given, the illustrative
    example pack is used, and a warning is emitted because it is not
    authoritative.
    """
    if pack is None:
        pack = default_pack()

    if not pack.authoritative:
        warnings.warn(
            f"Law pack {pack.name!r} is not authoritative: {pack.provenance}",
            stacklevel=2,
        )

    if "income" not in policies:
        raise ValueError(
            "compute_return requires an 'income' policy (it supplies AGI)"
        )

    income_policy = policies["income"]
    rules = get_ruleset(income_policy, pack=pack)

    agi = rules.compute_agi(unit, income_policy)
    taxable_income = rules.compute_taxable_income(unit, income_policy, agi)
    pre_credit_tax = rules.compute_pre_credit_tax(
        unit, income_policy, taxable_income
    )
    total_credits = rules.compute_credits(unit, income_policy, pre_credit_tax)
    net_tax = compute_net_tax(pre_credit_tax, total_credits)

    income_result = TaxResult(
        agi=agi,
        taxable_income=taxable_income,
        pre_credit_tax=pre_credit_tax,
        total_credits=total_credits,
        net_tax=net_tax,
    )

    parts: Dict[str, float] = {"income": net_tax}
    detail: Dict[str, object] = {"income": income_result}

    for tax, policy in policies.items():
        if tax == "income":
            continue

        try:
            addon = pack.addon_taxes[tax]
        except KeyError:
            available = ", ".join(sorted(pack.addon_taxes)) or "(none)"
            raise AvailabilityError(
                f"{policy.jurisdiction}/{tax}: no add-on tax rule is defined "
                f"in pack {pack.name!r}. Available: {available}"
            ) from None

        parts[tax] = addon(unit, policy, agi)

    try:
        combiner = pack.combiners[income_policy.jurisdiction]
    except KeyError:
        available = ", ".join(sorted(pack.combiners)) or "(none)"
        raise AvailabilityError(
            f"{income_policy.jurisdiction}: no combiner is defined in pack "
            f"{pack.name!r}. Available: {available}"
        ) from None

    return ReturnResult(
        agi=agi,
        parts=parts,
        detail=detail,
        total_tax=combiner(parts),
        pack_name=pack.name,
        authoritative=pack.authoritative,
        provenance=pack.provenance,
    )


def compute_tax(
    unit: TaxUnit,
    policy: Policy,
    *,
    pack: Optional[LawPack] = None,
) -> TaxResult:
    """Back-compatible single-tax entry point for an income policy."""
    if policy.tax != "income":
        raise ValueError(
            f"compute_tax expects an 'income' policy, got '{policy.tax}'. "
            "Use compute_return for multiple taxes."
        )
    return compute_return(unit, {"income": policy}, pack=pack).detail["income"]
