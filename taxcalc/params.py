"""Versioned tax-law parameters and policy construction.

A parameter is stored as a list of ``Parameter`` versions, each with an
effective date range. ``build_policy`` resolves the catalog for one tax year
into plain values, so rules never deal with versioned objects.

There is no fallback: if no version covers the requested tax year, or more
than one does, a clear error is raised.
"""

from datetime import date
from types import MappingProxyType
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import Parameter, Policy
from .pack import LawPack, default_pack


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class NoEffectiveVersionError(LookupError):
    """No version (parameter or rule set) is effective for the tax year."""


class AmbiguousVersionError(LookupError):
    """More than one version is effective for the same tax year."""


class MissingParameterError(KeyError):
    """A required parameter is not available for a policy."""


class AvailabilityError(LookupError):
    """A registry entry (rule set, combiner, ...) is not available."""


# ---------------------------------------------------------------------------
# Constructors
# ---------------------------------------------------------------------------

def yearly(year: int, value: Dict[str, List[Any]]) -> Parameter:
    """A parameter version effective for exactly one tax year."""
    return Parameter(
        effective=(date(year, 1, 1), date(year, 12, 31)),
        value=value,
    )


def since(year: int, value: Dict[str, List[Any]]) -> Parameter:
    """A parameter version effective from `year` onwards until amended."""
    return Parameter(
        effective=(date(year, 1, 1), date.max),
        value=value,
    )


# ---------------------------------------------------------------------------
# Shared resolver (used for parameters and rule sets)
# ---------------------------------------------------------------------------

def is_effective(version: Any, on: date) -> bool:
    """True if `on` falls within the version's effective range (inclusive)."""
    start, end = version.effective
    return start <= on <= end


def _ranges(versions: Sequence[Any]) -> str:
    return ", ".join(
        f"{v.effective[0].isoformat()}..{v.effective[1].isoformat()}"
        for v in versions
    )


def select(versions: Sequence[Any], year: int, *, label: str) -> Any:
    """Return the single version effective for tax year `year`.

    Applicability is tested on 31 December of the tax year (the law in effect
    at year end). Raises ``NoEffectiveVersionError`` if none match and
    ``AmbiguousVersionError`` if more than one matches.
    """
    if not versions:
        raise NoEffectiveVersionError(f"{label}: no versions are defined")

    anchor = date(year, 12, 31)
    matches = [v for v in versions if is_effective(v, anchor)]

    if not matches:
        raise NoEffectiveVersionError(
            f"{label}: no version is effective for tax year {year}. "
            f"Available ranges: {_ranges(versions)}"
        )
    if len(matches) > 1:
        raise AmbiguousVersionError(
            f"{label}: {len(matches)} versions are effective for tax year "
            f"{year}: {_ranges(matches)}"
        )
    return matches[0]


def resolve(
    versions: Sequence[Parameter], year: int, *, label: str
) -> Dict[str, List[Any]]:
    """Resolve parameter versions to the plain value dict for `year`."""
    return select(versions, year, label=label).value


def validate(versions: Sequence[Any], *, label: str) -> None:
    """Raise if versions are empty or their effective ranges overlap."""
    if not versions:
        raise ValueError(f"{label}: no versions are defined")

    ordered = sorted(versions, key=lambda v: v.effective[0])
    for previous, current in zip(ordered, ordered[1:]):
        if current.effective[0] <= previous.effective[1]:
            raise AmbiguousVersionError(
                f"{label}: overlapping effective ranges "
                f"{previous.effective[0].isoformat()}.."
                f"{previous.effective[1].isoformat()} and "
                f"{current.effective[0].isoformat()}.."
                f"{current.effective[1].isoformat()}"
            )


# ---------------------------------------------------------------------------
# Parameter catalog: (jurisdiction, tax, parameter name) -> versions
# ---------------------------------------------------------------------------
#
# Selector keys are FilingStatus values as strings ("single", "married_joint",
# ...) so the catalog stays JSON-friendly. Single-value parameters use the key
# "default" with a one-element list.
#
# 2023 income values are the simplified set used by the prototype notebook.
# 2024 income values come from constants.py. Every value is reviewed for
# accuracy after prototyping.
#
# AMT parameters are intentionally omitted from this catalog; their constants
# remain in constants.py for the legacy TaxCalculator.

PARAMETERS: Dict[Tuple[str, str, str], List[Parameter]] = {
    ("federal", "income", "standard_deduction"): [
        yearly(2023, {
            "single": [13850],
            "married_joint": [27700],
            "married_separate": [13850],
            "head_of_household": [20800],
            "qualifying_widow": [27700],
        }),
        yearly(2024, {
            "single": [14600],
            "married_joint": [29200],
            "married_separate": [14600],
            "head_of_household": [21900],
            "qualifying_widow": [29200],
        }),
    ],
    # Schedule A limits.  These are illustrative for the example pack; a
    # private pack carries the reviewed values.
    ("federal", "income", "medical_expense_floor"): [
        since(2023, {"default": [0.075]}),
    ],
    ("federal", "income", "salt_cap"): [
        yearly(2023, {
            "single": [10000],
            "married_joint": [10000],
            "married_separate": [5000],
            "head_of_household": [10000],
            "qualifying_widow": [10000],
        }),
        yearly(2024, {
            "single": [10000],
            "married_joint": [10000],
            "married_separate": [5000],
            "head_of_household": [10000],
            "qualifying_widow": [10000],
        }),
    ],
    ("federal", "income", "charitable_cash_limit"): [
        since(2023, {"default": [0.60]}),
    ],
    ("federal", "income", "brackets"): [
        yearly(2023, {
            "single": [
                (0.10, 11000),
                (0.12, 44725),
                (0.22, 95375),
            ],
            "married_joint": [
                (0.10, 22000),
                (0.12, 89450),
                (0.22, 190750),
            ],
            "married_separate": [
                (0.10, 11000),
                (0.12, 44725),
                (0.22, 95375),
            ],
            "head_of_household": [
                (0.10, 15700),
                (0.12, 59850),
                (0.22, 95350),
            ],
            "qualifying_widow": [
                (0.10, 23200),
                (0.12, 89450),
                (0.22, 190750),
            ],
        }),
        yearly(2024, {
            "single": [
                (0.10, 11600),
                (0.12, 47150),
                (0.22, 100525),
                (0.24, 191950),
                (0.32, 243725),
                (0.35, 609350),
                (0.37, float("inf")),
            ],
            "married_joint": [
                (0.10, 23200),
                (0.12, 94300),
                (0.22, 201050),
                (0.24, 383900),
                (0.32, 487450),
                (0.35, 731200),
                (0.37, float("inf")),
            ],
            "married_separate": [
                (0.10, 11600),
                (0.12, 47150),
                (0.22, 100525),
                (0.24, 191950),
                (0.32, 243725),
                (0.35, 365600),
                (0.37, float("inf")),
            ],
            "head_of_household": [
                (0.10, 16550),
                (0.12, 63100),
                (0.22, 100500),
                (0.24, 191950),
                (0.32, 243700),
                (0.35, 609350),
                (0.37, float("inf")),
            ],
            "qualifying_widow": [
                (0.10, 23200),
                (0.12, 94300),
                (0.22, 201050),
                (0.24, 383900),
                (0.32, 487450),
                (0.35, 731200),
                (0.37, float("inf")),
            ],
        }),
    ],
    ("federal", "income", "capital_gain_brackets"): [
        yearly(2023, {
            "single": [
                (0.00, 44625),
                (0.15, 492300),
                (0.20, float("inf")),
            ],
            "married_joint": [
                (0.00, 89250),
                (0.15, 553850),
                (0.20, float("inf")),
            ],
            "married_separate": [
                (0.00, 44625),
                (0.15, 276900),
                (0.20, float("inf")),
            ],
            "head_of_household": [
                (0.00, 59750),
                (0.15, 523050),
                (0.20, float("inf")),
            ],
            "qualifying_widow": [
                (0.00, 89250),
                (0.15, 553850),
                (0.20, float("inf")),
            ],
        }),
        yearly(2024, {
            "single": [
                (0.00, 47025),
                (0.15, 518900),
                (0.20, float("inf")),
            ],
            "married_joint": [
                (0.00, 94050),
                (0.15, 583750),
                (0.20, float("inf")),
            ],
            "married_separate": [
                (0.00, 47025),
                (0.15, 291850),
                (0.20, float("inf")),
            ],
            "head_of_household": [
                (0.00, 63000),
                (0.15, 551350),
                (0.20, float("inf")),
            ],
            "qualifying_widow": [
                (0.00, 94050),
                (0.15, 583750),
                (0.20, float("inf")),
            ],
        }),
    ],
    ("federal", "income", "capital_loss_limit"): [
        since(2023, {
            "single": [3000],
            "married_joint": [3000],
            "married_separate": [1500],
            "head_of_household": [3000],
            "qualifying_widow": [3000],
        }),
    ],
    ("federal", "income", "child_credit_amount"): [
        since(2023, {"default": [2000]}),
    ],
    # Section 24 family credit.  The child credit and the $500-per-dependent
    # other-dependent credit phase out together, by $50 for each $1,000 (or
    # fraction) of modified AGI above the threshold.  The thresholds are
    # statutory and not indexed.
    ("federal", "income", "child_credit_phaseout_start"): [
        since(2023, {
            "single": [200000],
            "married_joint": [400000],
            "married_separate": [200000],
            "head_of_household": [200000],
            "qualifying_widow": [200000],
        }),
    ],
    ("federal", "income", "child_credit_phaseout_step"): [
        since(2023, {"default": [1000]}),
    ],
    ("federal", "income", "child_credit_phaseout_reduction"): [
        since(2023, {"default": [50]}),
    ],
    ("federal", "income", "other_dependent_credit_amount"): [
        since(2023, {"default": [500]}),
    ],
    # Section 199A deduction rate for qualified REIT dividends / PTP income.
    ("federal", "income", "section_199a_rate"): [
        since(2018, {"default": [0.20]}),
    ],
    ("federal", "niit", "niit_rate"): [
        since(2013, {"default": [0.038]}),
    ],
    ("federal", "niit", "niit_threshold"): [
        since(2013, {
            "single": [200000],
            "married_joint": [250000],
            "married_separate": [125000],
            "head_of_household": [200000],
            "qualifying_widow": [250000],
        }),
    ],
    # ------------------------------------------------------------------
    # Minnesota income tax (Form M1)
    # ------------------------------------------------------------------
    # Minnesota starts from federal AGI, then subtracts its own standard
    # deduction, dependent exemptions, and items such as U.S. government
    # interest.  Amounts are from the M1 instructions and the Department of
    # Revenue's annual bracket release.  The 2027 amounts were not published
    # when this catalog was written, so a 2027 policy fails loudly instead of
    # reusing 2026.
    ("MN", "income", "brackets"): [
        yearly(2023, {
            "single": [
                (0.0535, 30070),
                (0.0680, 98760),
                (0.0785, 183340),
                (0.0985, float("inf")),
            ],
            "married_joint": [
                (0.0535, 43950),
                (0.0680, 174610),
                (0.0785, 304970),
                (0.0985, float("inf")),
            ],
            "married_separate": [
                (0.0535, 21975),
                (0.0680, 87305),
                (0.0785, 152485),
                (0.0985, float("inf")),
            ],
            "head_of_household": [
                (0.0535, 37010),
                (0.0680, 148730),
                (0.0785, 243720),
                (0.0985, float("inf")),
            ],
            "qualifying_widow": [
                (0.0535, 43950),
                (0.0680, 174610),
                (0.0785, 304970),
                (0.0985, float("inf")),
            ],
        }),
        yearly(2024, {
            "single": [
                (0.0535, 31690),
                (0.0680, 104090),
                (0.0785, 193240),
                (0.0985, float("inf")),
            ],
            "married_joint": [
                (0.0535, 46330),
                (0.0680, 184040),
                (0.0785, 321450),
                (0.0985, float("inf")),
            ],
            "married_separate": [
                (0.0535, 23165),
                (0.0680, 92020),
                (0.0785, 160725),
                (0.0985, float("inf")),
            ],
            "head_of_household": [
                (0.0535, 39010),
                (0.0680, 156760),
                (0.0785, 256880),
                (0.0985, float("inf")),
            ],
            "qualifying_widow": [
                (0.0535, 46330),
                (0.0680, 184040),
                (0.0785, 321450),
                (0.0985, float("inf")),
            ],
        }),
        yearly(2025, {
            "single": [
                (0.0535, 32570),
                (0.0680, 106990),
                (0.0785, 198630),
                (0.0985, float("inf")),
            ],
            "married_joint": [
                (0.0535, 47620),
                (0.0680, 189180),
                (0.0785, 330410),
                (0.0985, float("inf")),
            ],
            "married_separate": [
                (0.0535, 23810),
                (0.0680, 94590),
                (0.0785, 165205),
                (0.0985, float("inf")),
            ],
            "head_of_household": [
                (0.0535, 40100),
                (0.0680, 161130),
                (0.0785, 264050),
                (0.0985, float("inf")),
            ],
            "qualifying_widow": [
                (0.0535, 47620),
                (0.0680, 189180),
                (0.0785, 330410),
                (0.0985, float("inf")),
            ],
        }),
        yearly(2026, {
            "single": [
                (0.0535, 33310),
                (0.0680, 109430),
                (0.0785, 203150),
                (0.0985, float("inf")),
            ],
            "married_joint": [
                (0.0535, 48700),
                (0.0680, 193480),
                (0.0785, 337930),
                (0.0985, float("inf")),
            ],
            "married_separate": [
                (0.0535, 24350),
                (0.0680, 96740),
                (0.0785, 168965),
                (0.0985, float("inf")),
            ],
            "head_of_household": [
                (0.0535, 41010),
                (0.0680, 164800),
                (0.0785, 270060),
                (0.0985, float("inf")),
            ],
            "qualifying_widow": [
                (0.0535, 48700),
                (0.0680, 193480),
                (0.0785, 337930),
                (0.0985, float("inf")),
            ],
        }),
    ],
    ("MN", "income", "standard_deduction"): [
        yearly(2023, {
            "single": [13825],
            "married_joint": [27650],
            "married_separate": [13825],
            "head_of_household": [20800],
            "qualifying_widow": [27650],
        }),
        yearly(2024, {
            "single": [14575],
            "married_joint": [29150],
            "married_separate": [14575],
            "head_of_household": [21900],
            "qualifying_widow": [29150],
        }),
        yearly(2025, {
            "single": [14950],
            "married_joint": [29900],
            "married_separate": [14950],
            "head_of_household": [22500],
            "qualifying_widow": [29900],
        }),
        yearly(2026, {
            "single": [15300],
            "married_joint": [30600],
            "married_separate": [15300],
            "head_of_household": [23000],
            "qualifying_widow": [30600],
        }),
    ],
    # Standard deduction limitation: 3% of AGI above the first threshold plus
    # 10% above the second, capped at 80% of the deduction.
    ("MN", "income", "standard_deduction_phaseout_start"): [
        yearly(2023, {
            "single": [220650],
            "married_joint": [220650],
            "married_separate": [110325],
            "head_of_household": [220650],
            "qualifying_widow": [220650],
        }),
        yearly(2024, {
            "single": [232500],
            "married_joint": [232500],
            "married_separate": [116250],
            "head_of_household": [232500],
            "qualifying_widow": [232500],
        }),
        yearly(2025, {
            "single": [238950],
            "married_joint": [238950],
            "married_separate": [119475],
            "head_of_household": [238950],
            "qualifying_widow": [238950],
        }),
        yearly(2026, {
            "single": [244400],
            "married_joint": [244400],
            "married_separate": [122200],
            "head_of_household": [244400],
            "qualifying_widow": [244400],
        }),
    ],
    ("MN", "income", "standard_deduction_phaseout_second"): [
        yearly(2023, {
            "single": [304970],
            "married_joint": [304970],
            "married_separate": [152485],
            "head_of_household": [304970],
            "qualifying_widow": [304970],
        }),
        yearly(2024, {
            "single": [321350],
            "married_joint": [321350],
            "married_separate": [160675],
            "head_of_household": [321350],
            "qualifying_widow": [321350],
        }),
        yearly(2025, {
            "single": [330300],
            "married_joint": [330300],
            "married_separate": [165150],
            "head_of_household": [330300],
            "qualifying_widow": [330300],
        }),
        yearly(2026, {
            "single": [337800],
            "married_joint": [337800],
            "married_separate": [168900],
            "head_of_household": [337800],
            "qualifying_widow": [337800],
        }),
    ],
    ("MN", "income", "standard_deduction_phaseout_rate"): [
        since(2023, {"default": [0.03]}),
    ],
    ("MN", "income", "standard_deduction_phaseout_rate_second"): [
        since(2023, {"default": [0.10]}),
    ],
    ("MN", "income", "standard_deduction_phaseout_cap"): [
        since(2023, {"default": [0.80]}),
    ],
    ("MN", "income", "dependent_exemption"): [
        yearly(2023, {
            "single": [4800],
            "married_joint": [4800],
            "married_separate": [4800],
            "head_of_household": [4800],
            "qualifying_widow": [4800],
        }),
        yearly(2024, {
            "single": [5050],
            "married_joint": [5050],
            "married_separate": [5050],
            "head_of_household": [5050],
            "qualifying_widow": [5050],
        }),
        yearly(2025, {
            "single": [5200],
            "married_joint": [5200],
            "married_separate": [5200],
            "head_of_household": [5200],
            "qualifying_widow": [5200],
        }),
        yearly(2026, {
            "single": [5300],
            "married_joint": [5300],
            "married_separate": [5300],
            "head_of_household": [5300],
            "qualifying_widow": [5300],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_start"): [
        yearly(2023, {
            "single": [220650],
            "married_joint": [330950],
            "married_separate": [165475],
            "head_of_household": [275800],
            "qualifying_widow": [330950],
        }),
        yearly(2024, {
            "single": [232550],
            "married_joint": [348850],
            "married_separate": [174425],
            "head_of_household": [290700],
            "qualifying_widow": [348850],
        }),
        yearly(2025, {
            "single": [239050],
            "married_joint": [358550],
            "married_separate": [179275],
            "head_of_household": [298800],
            "qualifying_widow": [358550],
        }),
        yearly(2026, {
            "single": [244500],
            "married_joint": [366700],
            "married_separate": [183350],
            "head_of_household": [305600],
            "qualifying_widow": [366700],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_step"): [
        since(2023, {
            "single": [2500],
            "married_joint": [2500],
            "married_separate": [1250],
            "head_of_household": [2500],
            "qualifying_widow": [2500],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_max"): [
        since(2023, {
            "single": [122500],
            "married_joint": [122500],
            "married_separate": [61250],
            "head_of_household": [122500],
            "qualifying_widow": [122500],
        }),
    ],
    ("MN", "income", "dependent_exemption_phaseout_rate"): [
        since(2023, {"default": [0.02]}),
    ],
}


# ---------------------------------------------------------------------------
# Policy construction and access
# ---------------------------------------------------------------------------

def build_policy(
    jurisdiction: str,
    tax: str,
    year: int,
    *,
    overrides: Optional[Dict[str, Any]] = None,
    catalog: Optional[Dict[Tuple[str, str, str], List[Parameter]]] = None,
    pack: Optional[LawPack] = None,
) -> Policy:
    """Resolve every parameter for (jurisdiction, tax, year) into a Policy.

    Parameters are read from, in order of precedence: an explicit ``catalog``,
    the ``catalog`` of the given ``pack``, or the illustrative example pack.

    Parameters introduced in a later year are absent from earlier policies
    (they did not exist yet). A parameter whose data stops before the
    requested year is an error, because a new version is missing.

    `overrides` replaces a resolved value wholesale, for what-if analysis.
    Overriding a name that is not in the catalog is an error.
    """
    if catalog is None:
        catalog = pack.catalog if pack is not None else default_pack().catalog
    overrides = overrides or {}

    names = sorted(
        name for (j, t, name) in catalog
        if j == jurisdiction and t == tax
    )
    if not names:
        raise MissingParameterError(
            f"{jurisdiction}/{tax}: no parameters are defined"
        )

    unknown = set(overrides) - set(names)
    if unknown:
        raise MissingParameterError(
            f"{jurisdiction}/{tax}/{year}: cannot override unknown "
            f"parameter(s): {', '.join(sorted(unknown))}"
        )

    resolved: Dict[str, Any] = {}
    for name in names:
        if name in overrides:
            resolved[name] = overrides[name]
            continue

        versions = catalog[(jurisdiction, tax, name)]
        try:
            resolved[name] = resolve(
                versions,
                year,
                label=f"{jurisdiction}/{tax}/{name}",
            )
        except NoEffectiveVersionError:
            earliest = min(version.effective[0] for version in versions)
            if year < earliest.year:
                # The parameter did not exist yet in this tax year, so it is
                # simply absent from the policy. A rule that needs it will
                # fail in param() with a clear message.
                continue
            # The parameter exists but its data stops before this year: a new
            # version is missing.
            raise

    if not resolved:
        raise NoEffectiveVersionError(
            f"{jurisdiction}/{tax}: no parameters are effective for tax "
            f"year {year}"
        )

    return Policy(
        year=year,
        jurisdiction=jurisdiction,
        tax=tax,
        parameters=MappingProxyType(resolved),
    )


def _unwrap(selected: Any) -> Any:
    """Return the scalar inside a one-element list, but leave brackets alone.

    Scalars are stored as one-element lists for uniformity; a list of bracket
    tuples stays a list even if it has a single bracket.
    """
    if (
        isinstance(selected, list)
        and len(selected) == 1
        and not isinstance(selected[0], tuple)
    ):
        return selected[0]
    return selected


def param(policy: Policy, name: str, selector: Optional[str] = None) -> Any:
    """Return a resolved parameter value from a policy.

    - selector given  -> that selector's value
    - value is {"default": [...]} -> the default value
    - otherwise       -> the {selector: [...]} dict

    One-element lists of scalars are unwrapped, so a standard deduction comes
    back as ``29200`` while a bracket list stays a list of tuples.
    """
    try:
        value = policy.parameters[name]
    except KeyError:
        available = ", ".join(sorted(policy.parameters)) or "(none)"
        raise MissingParameterError(
            f"{policy.jurisdiction}/{policy.tax}/{policy.year}: no parameter "
            f"'{name}'. Available: {available}"
        ) from None

    if selector is not None:
        try:
            return _unwrap(value[selector])
        except KeyError:
            available = ", ".join(value)
            raise MissingParameterError(
                f"{policy.jurisdiction}/{policy.tax}/{policy.year}: parameter "
                f"'{name}' has no selector '{selector}'. "
                f"Available: {available}"
            ) from None

    if set(value) == {"default"}:
        return _unwrap(value["default"])
    return value


def optional_param(
    policy: Policy,
    name: str,
    selector: Optional[str] = None,
    default: Any = None,
) -> Any:
    """Like ``param``, but return ``default`` when the parameter is absent.

    Use this for a provision that did not exist yet in an earlier tax year
    (for example, the SALT phase-down that starts in 2025).  An absent
    parameter is different from a parameter whose versions stop early:
    ``build_policy`` already raises in the second case, so this helper never
    hides a missing version.
    """
    if name not in policy.parameters:
        return default
    return param(policy, name, selector)


# ---------------------------------------------------------------------------
# Import-time validation
# ---------------------------------------------------------------------------

def _validate_catalog() -> None:
    for key, versions in PARAMETERS.items():
        validate(versions, label="/".join(key))

        selector_sets = [set(v.value) for v in versions]
        if any(s != selector_sets[0] for s in selector_sets[1:]):
            raise ValueError(
                f"{'/'.join(key)}: versions use different selector keys"
            )


_validate_catalog()
