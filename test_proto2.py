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
    CoverageIssue,
    EXAMPLE_PACK,
    FilingStatus,
    Income,
    ItemizedDeductions,
    LawPack,
    MissingParameterError,
    NoEffectiveVersionError,
    Person,
    Policy,
    TaxUnit,
    UnsupportedInputError,
    build_policy,
    check_coverage,
    compute_deductions,
    compute_return,
    compute_tax,
    get_ruleset,
    load_pack,
    optional_param,
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


def single_unit(**income_fields) -> TaxUnit:
    return TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(**income_fields),
    )


def test_income_2023_regression() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2023))
    # The $100,000 long-term gain and $45,000 of qualified dividends are now
    # taxed at preferential rates instead of ordinary rates.
    assert result.pre_credit_tax == 101971.0
    assert result.total_credits == 4000.0
    assert result.net_tax == 97971.0
    assert result.preferential_taxable_income == 145000.0
    assert result.ordinary_taxable_income == 407300.0


def test_income_2024() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2024))
    assert result.pre_credit_tax == 106979.0
    assert result.net_tax == 102979.0
    assert result.preferential_tax == 21750.0
    assert result.ordinary_tax == 85229.0


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
            # This fixture populates other_sched_1, which has a coverage
            # warning of its own; turn coverage off to isolate the pack check.
            coverage="off",
        )
    assert not caught
    assert result.net_tax == 102979.0


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
    def zero_niit(unit: TaxUnit, policy: Policy, income_result) -> float:
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


def test_capital_gain_netting_and_preferential_rates() -> None:
    result = compute_tax(
        single_unit(wages_w2=60_000, long_term_capital_gain_loss=10_000),
        build_policy("federal", "income", 2024),
    )
    capital = result.capital_gains
    assert capital.net_long_term == 10_000.0
    assert capital.preferential_income == 10_000.0
    assert result.agi == 70_000.0
    assert result.taxable_income == 55_400.0
    assert result.ordinary_taxable_income == 45_400.0
    assert result.preferential_taxable_income == 10_000.0
    assert result.ordinary_tax == 5_216.0
    assert result.preferential_tax == 1_256.25
    assert result.pre_credit_tax == 6_472.25


def test_preferential_income_at_zero_rate() -> None:
    result = compute_tax(
        single_unit(wages_w2=20_000, long_term_capital_gain_loss=10_000),
        build_policy("federal", "income", 2024),
    )
    assert result.taxable_income == 15_400.0
    assert result.preferential_taxable_income == 10_000.0
    assert result.preferential_tax == 0.0
    assert result.ordinary_tax == 540.0


def test_capital_loss_limit_and_carryforward() -> None:
    result = compute_tax(
        single_unit(
            wages_w2=60_000,
            short_term_capital_gain_loss=-5_000,
            long_term_capital_gain_loss=-1_000,
        ),
        build_policy("federal", "income", 2024),
    )
    capital = result.capital_gains
    assert capital.allowed_loss == 3_000.0
    assert capital.carryforward_short_term == 3_000.0
    assert capital.carryforward_long_term == 0.0
    assert result.agi == 57_000.0


def test_capital_loss_under_limit_is_fully_deducted() -> None:
    capital = compute_tax(
        single_unit(wages_w2=60_000, short_term_capital_gain_loss=-2_000),
        build_policy("federal", "income", 2024),
    ).capital_gains
    assert capital.allowed_loss == 2_000.0
    assert capital.carryforward_short_term == 0.0


def test_short_gain_offsets_long_loss() -> None:
    capital = compute_tax(
        single_unit(
            wages_w2=60_000,
            short_term_capital_gain_loss=5_000,
            long_term_capital_gain_loss=-8_000,
        ),
        build_policy("federal", "income", 2024),
    ).capital_gains
    assert capital.net_short_term == 0.0
    assert capital.net_long_term == -3_000.0
    assert capital.ordinary_capital_gain == 0.0
    assert capital.preferential_income == 0.0
    assert capital.allowed_loss == 3_000.0
    assert capital.carryforward_short_term == 0.0
    assert capital.carryforward_long_term == 0.0


def test_long_term_carryforward_reduces_preferential_gain() -> None:
    capital = compute_tax(
        single_unit(
            wages_w2=60_000,
            long_term_capital_gain_loss=10_000,
            long_term_capital_loss_carryforward=4_000,
        ),
        build_policy("federal", "income", 2024),
    ).capital_gains
    assert capital.net_long_term == 6_000.0
    assert capital.preferential_income == 6_000.0


def test_mfs_capital_loss_limit() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.MARRIED_SEPARATE,
        primary=Person(age=40),
        spouse=Person(age=40),
        income=Income(
            wages_w2=60_000,
            short_term_capital_gain_loss=-5_000,
        ),
    )
    capital = compute_tax(
        unit, build_policy("federal", "income", 2024)
    ).capital_gains
    assert capital.allowed_loss == 1_500.0
    assert capital.carryforward_short_term == 3_500.0


def test_qualified_dividends_survive_capital_loss() -> None:
    result = compute_tax(
        single_unit(
            wages_w2=60_000,
            ordinary_dividends=2_000,
            qualified_dividends=2_000,
            short_term_capital_gain_loss=-5_000,
        ),
        build_policy("federal", "income", 2024),
    )
    assert result.capital_gains.preferential_income == 2_000.0
    assert result.capital_gains.allowed_loss == 3_000.0
    assert result.agi == 59_000.0


def test_capital_loss_carryforward_round_trip() -> None:
    policy = build_policy("federal", "income", 2024)
    first = compute_tax(
        single_unit(wages_w2=60_000, short_term_capital_gain_loss=-10_000),
        policy,
    ).capital_gains
    assert first.allowed_loss == 3_000.0
    assert first.carryforward_short_term == 7_000.0

    # Feed the reported carryforward back in as next year's input.
    expected = [(3_000.0, 4_000.0), (3_000.0, 1_000.0), (1_000.0, 0.0)]
    carry = first.carryforward_short_term
    for allowed, remaining in expected:
        detail = compute_tax(
            single_unit(
                wages_w2=60_000,
                short_term_capital_loss_carryforward=carry,
            ),
            policy,
        ).capital_gains
        assert detail.allowed_loss == allowed
        assert detail.carryforward_short_term == remaining
        carry = detail.carryforward_short_term


def test_coverage_reports_partial_inputs() -> None:
    policies = {"income": build_policy("federal", "income", 2024)}
    unit = single_unit(
        wages_w2=100_000,
        other_sched_1=5_000,
        tax_exempt_interest=1_000,
        taxable_social_security=2_000,
    )
    unit.dependents.append(Person(age=18))

    issues = check_coverage(unit, policies)
    codes = {issue.code for issue in issues}
    assert codes == {
        "other-sched-1-unmodeled",
        "amt-unmodeled",
        "social-security-taxability-unmodeled",
        "dependent-credit-unmodeled",
    }
    assert all(issue.severity == "warning" for issue in issues)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_return(unit, policies)
    assert {issue.code for issue in result.coverage} == codes

    quiet = compute_return(unit, policies, coverage="off")
    assert quiet.coverage == ()


def test_refundable_ctc_is_flagged() -> None:
    unit = single_unit(wages_w2=10_000)
    unit.dependents.append(Person(age=5, relationship="child"))
    policies = {"income": build_policy("federal", "income", 2024)}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_return(unit, policies)
    assert "refundable-ctc-unmodeled" in {
        issue.code for issue in result.coverage
    }
    assert result.parts["income"] == 0.0


def test_coverage_mode_is_validated() -> None:
    unit = single_unit(wages_w2=100_000)
    policies = {"income": build_policy("federal", "income", 2024)}
    try:
        compute_return(unit, policies, coverage="nope")
    except ValueError as exc:
        assert "coverage" in str(exc)
    else:
        raise AssertionError("expected ValueError for an unknown coverage mode")


def test_income_input_validation() -> None:
    try:
        Income(ordinary_dividends=10, qualified_dividends=20)
    except ValueError as exc:
        assert "qualified_dividends" in str(exc)
    else:
        raise AssertionError("expected qualified dividends above ordinary to raise")

    for field in (
        "short_term_capital_loss_carryforward",
        "long_term_capital_loss_carryforward",
    ):
        try:
            Income(**{field: -1})
        except ValueError as exc:
            assert field in str(exc)
        else:
            raise AssertionError(f"expected negative {field} to raise")


def test_unsupported_input_error_message() -> None:
    error = UnsupportedInputError([
        CoverageIssue(
            code="x-unmodeled", detail="not modeled", severity="error"
        )
    ])
    assert "x-unmodeled" in str(error)
    assert error.issues[0].code == "x-unmodeled"


def test_age_65_stops_the_calculation() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=65, blind=True),
        income=Income(wages_w2=100_000),
    )
    policies = {"income": build_policy("federal", "income", 2024)}

    try:
        compute_return(unit, policies)
    except UnsupportedInputError as exc:
        assert "age-65-additional-deduction-unmodeled" in str(exc)
        assert "blind-additional-deduction-unmodeled" in str(exc)
    else:
        raise AssertionError("expected an unsupported-input error")

    # Exploratory mode computes anyway and reports the issues.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_return(unit, policies, coverage="warn")
    assert {
        "age-65-additional-deduction-unmodeled",
        "blind-additional-deduction-unmodeled",
    } <= {issue.code for issue in result.coverage}


def deduction_policy(**overrides) -> Policy:
    """A 2026 policy with the Schedule A parameters, for rule-level tests."""
    parameters = {
        "standard_deduction": {"single": [16100]},
        "brackets": {"single": [
            (0.10, 12400),
            (0.12, 50400),
            (0.22, 105700),
            (0.24, 201775),
            (0.32, 256225),
            (0.35, 640600),
            (0.37, float("inf")),
        ]},
        "medical_expense_floor": {"default": [0.075]},
        "salt_cap": {"single": [40400]},
        "salt_cap_phaseout_threshold": {"single": [505000]},
        "salt_cap_phaseout_rate": {"default": [0.30]},
        "salt_cap_floor": {"single": [10000]},
        "charitable_cash_limit": {"default": [0.60]},
        "charitable_floor": {"default": [0.005]},
        "itemized_deduction_limit_rate": {"default": [2 / 37]},
    }
    parameters.update(overrides)
    return Policy(
        year=2026,
        jurisdiction="federal",
        tax="income",
        parameters=parameters,
    )


def test_itemized_deductions_beat_the_standard_deduction() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=200_000),
        itemized=ItemizedDeductions(
            state_local_income_taxes=12_000,
            real_estate_taxes=8_000,
            mortgage_interest=15_000,
            cash_contributions_50pct_orgs=10_000,
        ),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_tax(unit, build_policy("federal", "income", 2024))

    deductions = result.deductions
    assert deductions is not None
    assert deductions.standard == 14_600.0
    assert deductions.state_local_taxes == 10_000.0
    assert deductions.mortgage_interest == 15_000.0
    assert deductions.charitable == 10_000.0
    assert deductions.itemized == 35_000.0
    assert deductions.used == 35_000.0
    assert deductions.is_itemizing
    assert result.taxable_income == 165_000.0
    assert result.pre_credit_tax == 32_642.5


def test_standard_deduction_wins_when_itemized_is_smaller() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=100_000),
        itemized=ItemizedDeductions(state_local_income_taxes=2_000),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = compute_tax(unit, build_policy("federal", "income", 2024))

    assert result.deductions.itemized == 2_000.0
    assert result.deductions.used == 14_600.0
    assert not result.deductions.is_itemizing
    assert result.taxable_income == 85_400.0


def test_medical_expenses_use_the_agi_floor() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=100_000),
        itemized=ItemizedDeductions(medical_dental_expenses=20_000),
    )
    # 20,000 - 7.5% x 100,000
    assert compute_deductions(
        unit, build_policy("federal", "income", 2024), 100_000
    ).medical == 12_500.0


def test_salt_cap_phases_down_for_high_income() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=550_000),
        itemized=ItemizedDeductions(state_local_income_taxes=48_000),
    )
    # 40,400 - 30% x (550,000 - 505,000)
    detail = compute_deductions(unit, deduction_policy(), 550_000)
    assert detail.state_local_taxes == 26_900.0


def test_charitable_floor_and_section_68_limitation() -> None:
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=700_000),
        itemized=ItemizedDeductions(
            state_local_income_taxes=50_000,
            mortgage_interest=40_000,
            cash_contributions_50pct_orgs=19_600,
        ),
    )
    detail = compute_deductions(unit, deduction_policy(), 700_000)

    # SALT phases down to the $10,000 floor.
    assert detail.state_local_taxes == 10_000.0
    # 19,600 - 0.5% x 700,000
    assert detail.charitable == 16_100.0
    # 2/37 x (700,000 - 640,600), capped at the deductions themselves.
    assert round(detail.limitation, 2) == 3_210.81
    assert round(detail.itemized, 2) == 62_889.19


def test_itemized_parameters_resolve_from_the_catalog() -> None:
    policy = build_policy("federal", "income", 2024)
    assert param(policy, "salt_cap", "single") == 10_000
    assert param(policy, "salt_cap", "married_separate") == 5_000
    assert param(policy, "medical_expense_floor") == 0.075
    assert param(policy, "charitable_cash_limit") == 0.60
    # Provisions that start later are absent, not defaulted.
    assert optional_param(policy, "salt_cap_phaseout_threshold") is None
    assert optional_param(policy, "itemized_deduction_limit_rate") is None


def test_itemized_deductions_reject_negative_amounts() -> None:
    try:
        ItemizedDeductions(medical_dental_expenses=-1)
    except ValueError as exc:
        assert "medical_dental_expenses" in str(exc)
    else:
        raise AssertionError("expected a negative deduction to raise")


def test_itemized_coverage_checks() -> None:
    policies = {"income": build_policy("federal", "income", 2024)}
    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=100_000),
        itemized=ItemizedDeductions(
            mortgage_interest=10_000,
            noncash_contributions=5_000,
        ),
    )
    codes = {issue.code for issue in check_coverage(unit, policies)}
    assert codes == {
        "mortgage-debt-limit-unmodeled",
        "noncash-charity-limit-unmodeled",
    }

    unit.itemized = ItemizedDeductions(casualty_theft_losses=1_000)
    try:
        compute_return(unit, policies)
    except UnsupportedInputError as exc:
        assert "casualty-loss-unmodeled" in str(exc)
    else:
        raise AssertionError("expected an unsupported casualty loss")


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
        test_capital_gain_netting_and_preferential_rates,
        test_preferential_income_at_zero_rate,
        test_capital_loss_limit_and_carryforward,
        test_capital_loss_under_limit_is_fully_deducted,
        test_short_gain_offsets_long_loss,
        test_long_term_carryforward_reduces_preferential_gain,
        test_mfs_capital_loss_limit,
        test_qualified_dividends_survive_capital_loss,
        test_capital_loss_carryforward_round_trip,
        test_coverage_reports_partial_inputs,
        test_refundable_ctc_is_flagged,
        test_coverage_mode_is_validated,
        test_income_input_validation,
        test_unsupported_input_error_message,
        test_age_65_stops_the_calculation,
        test_itemized_deductions_beat_the_standard_deduction,
        test_standard_deduction_wins_when_itemized_is_smaller,
        test_medical_expenses_use_the_agi_floor,
        test_salt_cap_phases_down_for_high_income,
        test_charitable_floor_and_section_68_limitation,
        test_itemized_parameters_resolve_from_the_catalog,
        test_itemized_deductions_reject_negative_amounts,
        test_itemized_coverage_checks,
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
