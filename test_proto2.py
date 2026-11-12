#!/usr/bin/env python3
"""Proto2 smoke and regression tests for the parameter/policy design.

Run with:
    python test_proto2.py
"""

from datetime import date
import warnings

from taxcalc import (
    AmbiguousVersionError,
    AvailabilityError,
    EXAMPLE_PACK,
    FilingStatus,
    Income,
    LawPack,
    MissingParameterError,
    NoEffectiveVersionError,
    Person,
    Policy,
    TaxUnit,
    build_policy,
    compute_return,
    compute_tax,
    get_ruleset,
    load_pack,
    param,
    resolve,
    since,
    yearly,
)
from taxcalc.params import PARAMETERS, validate


def make_taxpayer() -> TaxUnit:
    return TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary=Person(age=45),
        spouse=Person(age=43),
        dependents=[
            Person(age=5, relationship="child", full_time_student=True),
            Person(age=12, relationship="child", full_time_student=True),
        ],
        income=Income(
            wages_w2=400000,
            taxable_interest=5000,
            ordinary_dividends=55000,
            qualified_dividends=45000,
            long_term_capital_gain_loss=100000,
            other_sched_1=20000,
        ),
    )


def test_resolve_by_year() -> None:
    versions = PARAMETERS[("federal", "income", "standard_deduction")]
    assert resolve(versions, 2023, label="std")["single"] == [13850]
    assert resolve(versions, 2024, label="std")["single"] == [14600]


def test_missing_year_raises() -> None:
    versions = PARAMETERS[("federal", "income", "standard_deduction")]
    try:
        resolve(versions, 2026, label="std")
    except NoEffectiveVersionError as exc:
        assert "2026" in str(exc)
        assert "2023-01-01" in str(exc)
    else:
        raise AssertionError("expected NoEffectiveVersionError for 2026")


def test_overlap_raises() -> None:
    overlapping = [
        yearly(2023, {"default": [1]}),
        yearly(2023, {"default": [2]}),
    ]
    try:
        validate(overlapping, label="overlap")
    except AmbiguousVersionError:
        pass
    else:
        raise AssertionError("expected AmbiguousVersionError for overlapping years")


def test_build_policy() -> None:
    policy = build_policy("federal", "income", 2023)
    assert param(policy, "standard_deduction", "single") == 13850
    assert param(policy, "brackets", "married_joint") == [
        (0.10, 22000),
        (0.12, 89450),
        (0.22, 190750),
    ]
    assert param(policy, "child_credit_amount") == 2000


def test_missing_parameter() -> None:
    policy = build_policy("federal", "income", 2024)
    try:
        param(policy, "amt_exemption")
    except MissingParameterError as exc:
        assert "amt_exemption" in str(exc)
    else:
        raise AssertionError("expected MissingParameterError")


def test_unknown_override() -> None:
    try:
        build_policy("federal", "income", 2024, overrides={"nope": 1})
    except MissingParameterError:
        pass
    else:
        raise AssertionError("expected MissingParameterError for unknown override")


def test_later_parameter_is_absent_earlier() -> None:
    catalog = {
        ("federal", "income", "standard_deduction"): [
            yearly(2023, {"single": [1]}),
            yearly(2024, {"single": [2]}),
        ],
        ("federal", "income", "phaseout_threshold"): [
            since(2025, {"default": [400000]}),
        ],
    }

    p2024 = build_policy("federal", "income", 2024, catalog=catalog)
    assert "phaseout_threshold" not in p2024.parameters
    assert param(p2024, "standard_deduction", "single") == 2

    # 2025 has no standard deduction version yet: a missing year, not a
    # not-yet-existing parameter, so it must raise.
    try:
        build_policy("federal", "income", 2025, catalog=catalog)
    except NoEffectiveVersionError:
        pass
    else:
        raise AssertionError("expected missing 2025 standard deduction to raise")

    catalog[("federal", "income", "standard_deduction")].append(
        yearly(2025, {"single": [3]})
    )
    p2025 = build_policy("federal", "income", 2025, catalog=catalog)
    assert param(p2025, "phaseout_threshold") == 400000
    assert param(p2025, "standard_deduction", "single") == 3


def test_income_2023_regression() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2023))
    assert result.pre_credit_tax == 112121.0
    assert result.total_credits == 4000.0
    assert result.net_tax == 108121.0


def test_income_2024() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2024))
    assert result.pre_credit_tax == 133529.5
    assert result.net_tax == 129529.5


def test_niit() -> None:
    policies = {
        "income": build_policy("federal", "income", 2024),
        "niit": build_policy("federal", "niit", 2024),
    }
    result = compute_return(make_taxpayer(), policies)
    # Rental income is now inside other_sched_1, so it is not part of NII.
    assert result.parts["niit"] == 6080.0  # 160000 * 3.8%
    assert result.total_tax == result.parts["income"] + result.parts["niit"]


def test_income_1040_lines() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(
            wages_w2=100_000,
            taxable_interest=1_000,
            ordinary_dividends=2_000,
            taxable_ira=3_000,
            taxable_pensions_annuities=4_000,
            taxable_social_security=5_000,
            short_term_capital_gain_loss=6_000,
            long_term_capital_gain_loss=7_000,
            other_sched_1=8_000,
            adjustments_sched_1=2_000,
        ),
    )
    result = compute_tax(unit, build_policy("federal", "income", 2024))
    assert result.agi == 134_000.0


def test_ruleset_reuse() -> None:
    p2023 = build_policy("federal", "income", 2023)
    p2024 = build_policy("federal", "income", 2024)
    assert get_ruleset(p2023) is get_ruleset(p2024)


def test_ruleset_no_fallback() -> None:
    p2026 = Policy(year=2026, jurisdiction="federal", tax="income")
    try:
        get_ruleset(p2026)
    except NoEffectiveVersionError as exc:
        assert "2026" in str(exc)
    else:
        raise AssertionError("expected NoEffectiveVersionError for 2026 rules")


def test_override_changes_result() -> None:
    base = compute_tax(make_taxpayer(), build_policy("federal", "income", 2024))
    hypothetical = build_policy(
        "federal", "income", 2024,
        overrides={"child_credit_amount": {"default": [4000]}},
    )
    changed = compute_tax(make_taxpayer(), hypothetical)
    assert changed.total_credits == 8000.0
    assert changed.net_tax == base.net_tax - 4000.0


def test_example_pack_is_not_authoritative() -> None:
    assert EXAMPLE_PACK.authoritative is False
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compute_tax(make_taxpayer(), build_policy("federal", "income", 2024))
    assert any("not authoritative" in str(item.message) for item in caught)


def test_return_carries_pack_identity() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_return(
            make_taxpayer(),
            {"income": build_policy("federal", "income", 2024)},
        )
    assert result.pack_name == EXAMPLE_PACK.name
    assert result.authoritative is False
    assert result.provenance == EXAMPLE_PACK.provenance


def test_authoritative_pack_does_not_warn() -> None:
    pack = LawPack(
        name="private-test",
        authoritative=True,
        provenance="test pack",
        catalog=EXAMPLE_PACK.catalog,
        rule_sets=EXAMPLE_PACK.rule_sets,
        addon_taxes=EXAMPLE_PACK.addon_taxes,
        combiners=EXAMPLE_PACK.combiners,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = compute_tax(
            make_taxpayer(),
            build_policy("federal", "income", 2024, pack=pack),
            pack=pack,
        )
    assert not caught
    assert result.net_tax == 129529.5


def test_pack_replaces_example_catalog() -> None:
    catalog = {
        ("federal", "income", "standard_deduction"): [
            yearly(2024, {"single": [1]}),
        ],
    }
    pack = LawPack(
        name="tiny",
        authoritative=True,
        provenance="tiny test catalog",
        catalog=catalog,
        rule_sets={},
        addon_taxes={},
        combiners={},
    )

    policy = build_policy("federal", "income", 2024, pack=pack)
    assert set(policy.parameters) == {"standard_deduction"}

    # The example catalog must not leak into a caller-supplied pack.
    try:
        build_policy("federal", "income", 2023, pack=pack)
    except NoEffectiveVersionError:
        pass
    else:
        raise AssertionError("expected the pack's catalog to have no 2023 data")


def test_addon_tax_is_pluggable() -> None:
    def zero_niit(unit: TaxUnit, policy: Policy, agi: float) -> float:
        return 0.0

    pack = LawPack(
        name="zero-niit",
        authoritative=True,
        provenance="test pack",
        catalog=EXAMPLE_PACK.catalog,
        rule_sets=EXAMPLE_PACK.rule_sets,
        addon_taxes={"niit": zero_niit},
        combiners=EXAMPLE_PACK.combiners,
    )
    policies = {
        "income": build_policy("federal", "income", 2024, pack=pack),
        "niit": build_policy("federal", "niit", 2024, pack=pack),
    }
    result = compute_return(make_taxpayer(), policies, pack=pack)
    assert result.parts["niit"] == 0.0
    assert result.total_tax == result.parts["income"]


def test_missing_addon_tax_raises() -> None:
    pack = LawPack(
        name="no-addons",
        authoritative=True,
        provenance="test pack",
        catalog=EXAMPLE_PACK.catalog,
        rule_sets=EXAMPLE_PACK.rule_sets,
        addon_taxes={},
        combiners=EXAMPLE_PACK.combiners,
    )
    policies = {
        "income": build_policy("federal", "income", 2024, pack=pack),
        "niit": build_policy("federal", "niit", 2024, pack=pack),
    }
    try:
        compute_return(make_taxpayer(), policies, pack=pack)
    except AvailabilityError as exc:
        assert "niit" in str(exc)
    else:
        raise AssertionError("expected AvailabilityError for a missing add-on tax")


def test_load_pack() -> None:
    from taxcalc.example_pack import EXAMPLE_PACK as module_pack

    assert load_pack("taxcalc.example_pack") is module_pack


def main() -> None:
    tests = [
        test_resolve_by_year,
        test_missing_year_raises,
        test_overlap_raises,
        test_build_policy,
        test_missing_parameter,
        test_unknown_override,
        test_later_parameter_is_absent_earlier,
        test_income_2023_regression,
        test_income_2024,
        test_niit,
        test_income_1040_lines,
        test_ruleset_reuse,
        test_ruleset_no_fallback,
        test_override_changes_result,
        test_example_pack_is_not_authoritative,
        test_return_carries_pack_identity,
        test_authoritative_pack_does_not_warn,
        test_pack_replaces_example_catalog,
        test_addon_tax_is_pluggable,
        test_missing_addon_tax_raises,
        test_load_pack,
    ]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for test in tests:
            test()
            print(f"PASSED  {test.__name__}")
    print(f"\nAll {len(tests)} proto2 tests passed.")


if __name__ == "__main__":
    main()
