"""Coverage checks: fail loudly when a populated input is not modeled.

Severity convention:

- ``error``: the input is ignored entirely, so the result would be wrong with
  no other signal.
- ``warning``: the input is included, but only partially modeled.

Every gap in the rules should have a check here.  When a gap is implemented,
delete its check in the same change.
"""

from typing import List, Mapping, Optional, Sequence

from .models import CoverageIssue, Policy, TaxResult, TaxUnit
from .pack import LawPack


class UnsupportedInputError(ValueError):
    """Raised when a calculation would silently ignore a populated input."""

    def __init__(self, issues: Sequence[CoverageIssue]) -> None:
        self.issues = tuple(issues)
        details = "\n".join(
            f"  - {issue.code}: {issue.detail}" for issue in self.issues
        )
        super().__init__(
            "the calculation does not model every populated input:\n"
            + details
        )


def check_coverage(
    unit: TaxUnit,
    policies: Mapping[str, Policy],
    *,
    pack: Optional[LawPack] = None,
) -> List[CoverageIssue]:
    """Return every input the active income rules do not fully model.

    ``pack`` is reserved for packs that add coverage checks of their own; the
    checks below describe the rules shipped with the package.
    """
    issues: List[CoverageIssue] = []

    if "income" not in policies:
        return issues

    income = unit.income

    if income.other_sched_1:
        issues.append(CoverageIssue(
            code="other-sched-1-unmodeled",
            detail=(
                "other_sched_1 is treated as ordinary income. Self-employment "
                "tax, any QBI/section 199A deduction on business income in "
                "other_sched_1, and rental passive-loss limits are not modeled."
            ),
            severity="warning",
        ))

    if income.tax_exempt_interest or income.private_activity_bond_interest:
        issues.append(CoverageIssue(
            code="amt-unmodeled",
            detail=(
                "tax_exempt_interest and private_activity_bond_interest affect "
                "the alternative minimum tax, which is not modeled."
            ),
            severity="warning",
        ))

    if income.taxable_social_security:
        issues.append(CoverageIssue(
            code="social-security-taxability-unmodeled",
            detail=(
                "taxable_social_security is used as entered. The taxable "
                "portion under section 86 is not computed."
            ),
            severity="warning",
        ))

    if unit.foreign_tax_credit:
        issues.append(CoverageIssue(
            code="foreign-tax-credit-limit-unmodeled",
            detail=(
                "foreign_tax_credit is used as entered. The Form 1116 "
                "limitation, foreign-source income, and carryover are not "
                "recomputed."
            ),
            severity="warning",
        ))

    itemized = unit.itemized
    if itemized is not None:
        if itemized.casualty_theft_losses:
            issues.append(CoverageIssue(
                code="casualty-loss-unmodeled",
                detail=(
                    "casualty_theft_losses is not modeled. Only losses from a "
                    "federally declared disaster are deductible, and the "
                    "calculator does not hold the declaration or apply the "
                    "10%-of-AGI limit."
                ),
                severity="error",
            ))

        if itemized.gambling_losses:
            issues.append(CoverageIssue(
                code="gambling-loss-unmodeled",
                detail=(
                    "gambling_losses is not modeled because gambling winnings "
                    "are not an input; the deduction is limited to winnings."
                ),
                severity="error",
            ))

        if itemized.mortgage_interest or itemized.mortgage_points:
            issues.append(CoverageIssue(
                code="mortgage-debt-limit-unmodeled",
                detail=(
                    "mortgage interest and points are deducted as entered. The "
                    "$750,000 acquisition-debt limit, the grandfathered "
                    "pre-2017 limit, and the points-timing rules are not "
                    "modeled."
                ),
                severity="warning",
            ))

        if itemized.noncash_contributions:
            issues.append(CoverageIssue(
                code="noncash-charity-limit-unmodeled",
                detail=(
                    "noncash contributions are subject to the 30%-of-AGI limit "
                    "and a five-year carryforward. The calculator applies the "
                    "60% limit to all charitable contributions."
                ),
                severity="warning",
            ))

    # Minnesota starts from federal AGI, so its own deduction, exemptions, and
    # subtractions are a separate set of gaps.
    if "MN" in policies:
        if unit.itemized is not None:
            issues.append(CoverageIssue(
                code="mn-itemized-deductions-unmodeled",
                detail=(
                    "Minnesota itemized deductions (Schedule M1SA) are not "
                    "modeled. The MN standard deduction is used even when "
                    "federal deductions are itemized."
                ),
                severity="warning",
            ))

        if income.taxable_social_security:
            issues.append(CoverageIssue(
                code="mn-social-security-subtraction-unmodeled",
                detail=(
                    "the Minnesota subtraction for Social Security benefits is "
                    "not modeled; all federally taxable Social Security is "
                    "included in Minnesota taxable income."
                ),
                severity="warning",
            ))

        if income.tax_exempt_interest or income.private_activity_bond_interest:
            issues.append(CoverageIssue(
                code="mn-additions-unmodeled",
                detail=(
                    "Minnesota additions, such as interest on bonds of another "
                    "state, are not modeled. tax_exempt_interest is left out "
                    "of Minnesota taxable income."
                ),
                severity="warning",
            ))

        if (
            unit.itemized is not None
            or income.other_sched_1
            or income.tax_exempt_interest
            or income.private_activity_bond_interest
        ):
            issues.append(CoverageIssue(
                code="mn-amt-unmodeled",
                detail=(
                    "the Minnesota alternative minimum tax is not modeled, and "
                    "neither are Minnesota nonrefundable credits. Inputs that "
                    "often create AMT adjustments are present."
                ),
                severity="warning",
            ))

    taxpayers = [unit.primary]
    if unit.spouse is not None:
        taxpayers.append(unit.spouse)

    if any(person.age >= 65 for person in taxpayers):
        issues.append(CoverageIssue(
            code="age-65-additional-deduction-unmodeled",
            detail=(
                "a taxpayer is 65 or older. The additional standard deduction "
                "for age 65+ is not modeled."
            ),
            severity="error",
        ))

    if any(person.blind for person in taxpayers):
        issues.append(CoverageIssue(
            code="blind-additional-deduction-unmodeled",
            detail=(
                "a taxpayer is blind. The additional standard deduction for "
                "blindness is not modeled."
            ),
            severity="error",
        ))

    if any(person.full_time_student for person in unit.dependents):
        issues.append(CoverageIssue(
            code="education-credits-unmodeled",
            detail=(
                "a dependent is a full-time student. Education credits are "
                "not modeled."
            ),
            severity="warning",
        ))

    if any(person.disabled for person in taxpayers):
        issues.append(CoverageIssue(
            code="disability-credits-unmodeled",
            detail=(
                "a taxpayer is disabled. Disability-related credits are not "
                "modeled."
            ),
            severity="warning",
        ))

    return issues


def check_result_coverage(
    unit: TaxUnit,
    policy: Policy,
    result: TaxResult,
) -> List[CoverageIssue]:
    """Return caveats that depend on a computed income-tax result."""
    issues: List[CoverageIssue] = []

    credits = result.credits
    if credits is None or credits.qualifying_children == 0:
        return issues

    # If the family credit exceeds the tax after the other nonrefundable
    # credits, some of the child credit could be refundable as the additional
    # child tax credit.  Model only the nonrefundable piece.
    available_tax = max(
        0.0, result.pre_credit_tax - credits.foreign_tax_credit
    )
    if credits.family_credit > available_tax:
        issues.append(CoverageIssue(
            code="refundable-ctc-unmodeled",
            detail=(
                "the child tax credit is limited to the available pre-credit "
                "tax. The refundable additional child tax credit is not "
                "modeled."
            ),
            severity="warning",
        ))

    return issues
