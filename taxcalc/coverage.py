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
from .params import param


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
                "tax, the QBI/section 199A deduction, and rental passive-loss "
                "limits are not modeled."
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

    older_dependents = [d for d in unit.dependents if d.age >= 17]
    if older_dependents:
        issues.append(CoverageIssue(
            code="dependent-credit-unmodeled",
            detail=(
                f"{len(older_dependents)} dependent(s) are 17 or older. Only "
                "the child tax credit for children under 17 is modeled; the "
                "credit for other dependents is not."
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

    qualifying_children = sum(1 for d in unit.dependents if d.age < 17)
    raw_credit = qualifying_children * param(policy, "child_credit_amount")

    if raw_credit > result.pre_credit_tax:
        issues.append(CoverageIssue(
            code="refundable-ctc-unmodeled",
            detail=(
                "the child tax credit is limited to the pre-credit tax. The "
                "refundable additional child tax credit is not modeled."
            ),
            severity="warning",
        ))

    return issues
