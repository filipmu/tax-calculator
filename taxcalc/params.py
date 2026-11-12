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
