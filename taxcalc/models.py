"""
Data models for tax calculations.

This module defines all data structures used throughout the tax calculator,
including taxpayer information, income sources, deductions, and results.
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, List, Dict, Mapping, Tuple


class FilingStatus(Enum):
    """Tax filing status options"""
    SINGLE = "single"
    MARRIED_JOINT = "married_joint"
    MARRIED_SEPARATE = "married_separate"
    HEAD_OF_HOUSEHOLD = "head_of_household"
    QUALIFYING_WIDOW = "qualifying_widow"

@dataclass
class Person:
    age: int
    blind: bool = False
    disabled: bool = False
    full_time_student: bool = False
    relationship: str | None = None   # e.g., "child", "spouse", "parent"


@dataclass
class Income:
    """Income sources, grouped to follow Form 1040."""

    # Form 1040, line 1a
    wages_w2: float = 0.0

    # Form 1040, line 2b
    taxable_interest: float = 0.0   # e.g., taxable interest from Form 1099-INT

    # Form 1040, line 3b
    qualified_dividends: float = 0.0   # Subset of ordinary_dividends
    ordinary_dividends: float = 0.0    # Includes qualified_dividends

    # Form 1040, lines 4b, 5b, and 6b
    taxable_ira: float = 0.0
    taxable_pensions_annuities: float = 0.0
    taxable_social_security: float = 0.0

    # Form 1040, line 7 (from Schedule D)
    short_term_capital_gain_loss: float = 0.0
    long_term_capital_gain_loss: float = 0.0

    # Schedule D carry-in: losses disallowed in earlier years, entered as
    # positive amounts.  These are input facts, not calculator state: the
    # caller decides what to carry forward from CapitalGainDetail.
    short_term_capital_loss_carryforward: float = 0.0
    long_term_capital_loss_carryforward: float = 0.0

    # Form 1040, line 8 (Schedule 1, line 10).  Net business, rental,
    # unemployment, and other Schedule 1 income.
    other_sched_1: float = 0.0

    # Income adjustments (Schedule 1, Part II; Form 1040, line 10).
    # Enter the total of all adjustments; the prototype does not itemize them.
    adjustments_sched_1: float = 0.0

    # Tax-exempt interest (affects AMT)
    tax_exempt_interest: float = 0.0
    private_activity_bond_interest: float = 0.0

    def __post_init__(self) -> None:
        if self.qualified_dividends > self.ordinary_dividends:
            raise ValueError(
                "qualified_dividends cannot exceed ordinary_dividends: "
                f"{self.qualified_dividends} > {self.ordinary_dividends}"
            )
        if self.short_term_capital_loss_carryforward < 0:
            raise ValueError(
                "short_term_capital_loss_carryforward must be a positive "
                "loss amount; enter gains in "
                "short_term_capital_gain_loss instead"
            )
        if self.long_term_capital_loss_carryforward < 0:
            raise ValueError(
                "long_term_capital_loss_carryforward must be a positive "
                "loss amount; enter gains in long_term_capital_gain_loss "
                "instead"
            )

@dataclass
class TaxUnit:
    """Taxpayer unit information - defines 'who' provides input and is taxed"""
    filing_status: FilingStatus
    primary: Person
    income: Income 
    spouse: Person | None = None
    dependents: List[Person] = field(default_factory=list)




    #dependent_ages: List[int] = field(default_factory=list)

    @property
    def num_dependents(self) -> int:
        return len(self.dependents)

    @property
    def is_married(self) -> bool:
        return self.filing_status in {
            FilingStatus.MARRIED_JOINT,
            FilingStatus.MARRIED_SEPARATE
        }
    
    def __post_init__(self):
        # Filing status checks
        if self.filing_status in {
            FilingStatus.MARRIED_JOINT,
            FilingStatus.MARRIED_SEPARATE
        } and self.spouse is None:
            raise ValueError("Married filing statuses require a spouse")

        if self.filing_status is FilingStatus.SINGLE and self.spouse is not None:
            raise ValueError("Single filers cannot have a spouse")

        # Age sanity checks
        if self.primary.age < 0:
            raise ValueError("Primary age cannot be negative")

        if self.spouse is not None and self.spouse.age < 0:
            raise ValueError("Spouse age cannot be negative")

        for dep in self.dependents:
            if dep.age < 0:
                raise ValueError("Dependent ages must be non-negative")


@dataclass(frozen=True)
class Parameter:
    """One version of a tax law parameter, valid over an effective date range.

    `value` is a dict of lists: each key selects a variant of the parameter
    (e.g., a filing status), and each list holds the parameter's values for
    that key. Brackets are lists of (rate, upper_limit) tuples, rate first
    (matching IRS table order), with the top bracket's upper_limit being
    float('inf'). Single-value parameters use the key "default" with a
    one-element list. Other multi-value parameters (e.g., phase-out steps)
    can hold any list items.

    The parameter's name is its key in the catalog (see ``params.PARAMETERS``),
    so it is not repeated here. Versions are resolved to plain values by
    ``params.resolve``; rules never see ``Parameter`` objects.

    Example:
        Parameter(
            effective=(date(2024, 1, 1), date(2024, 12, 31)),
            value={
                "single": [(0.0, 47025), (0.15, 518900), (0.20, float('inf'))],
                "married_joint": [(0.0, 94050), (0.15, 583750), (0.20, float('inf'))],
            },
        )
        Parameter(
            effective=(date(2024, 1, 1), date.max),   # still in effect
            value={"single": [14600], "married_joint": [29200]},
        )
    """
    effective: Tuple[date, date]  # (start_date, end_date), inclusive; date.max = open-ended
    value: Dict[str, List[Any]]  # {selector key: [values]}, e.g. {"single": [(rate, upper_limit), ...]}

    def __post_init__(self):
        start, end = self.effective
        if start > end:
            raise ValueError("Parameter effective start date is after end date")


@dataclass(frozen=True)
class Policy:
    """One tax for one jurisdiction and tax year, with resolved parameters.

    A policy is a single tax (e.g. "income", "niit"), not a whole tax return.
    ``parameters`` holds plain, resolved values for the tax year - never
    ``Parameter`` objects - so rules can read them directly.
    """
    year: int
    jurisdiction: str  # e.g. "federal", "MN"
    tax: str           # e.g. "income", "niit"

    # Resolved parameter values for this tax year, keyed by parameter name.
    parameters: Mapping[str, Any] = field(default_factory=dict)






@dataclass
class ItemizedDeductions:
    """Itemized deduction categories for Schedule A"""
    # Medical and dental expenses (only amounts exceeding 7.5% of AGI are deductible)
    medical_dental_expenses: float = 0.0

    # State and local taxes (SALT) - subject to $10,000 cap
    state_local_income_taxes: float = 0.0
    real_estate_taxes: float = 0.0
    personal_property_taxes: float = 0.0

    # Home mortgage interest
    mortgage_interest: float = 0.0
    mortgage_points: float = 0.0

    # Charitable contributions
    cash_contributions_50pct_orgs: float = 0.0
    cash_contributions_other: float = 0.0
    noncash_contributions: float = 0.0
    donor_advised_fund_contributions: float = 0.0  # Included in cash/noncash limits

    # Other deductions
    casualty_theft_losses: float = 0.0
    gambling_losses: float = 0.0  # Limited to gambling winnings


@dataclass
class AMTAdjustments:
    """AMT-specific adjustments and preference items"""
    # ISO exercise bargain element
    iso_bargain_element: float = 0.0

    # Depreciation adjustments
    depreciation_adjustment: float = 0.0

    # Miscellaneous adjustments
    tax_refunds: float = 0.0
    investment_interest_adjustment: float = 0.0
    passive_activity_adjustment: float = 0.0


@dataclass
class TaxConfig:
    """
    Tax configuration containing all rates, brackets, and thresholds.

    This allows you to customize tax calculations for different years or scenarios.
    All brackets are tuples of (rate, upper_limit) for each filing status.

    Example:
        # Create custom config for 2025
        config_2025 = TaxConfig(
            tax_year=2025,
            federal_brackets={
                FilingStatus.SINGLE: [
                    (0.10, 11925),
                    (0.12, 48475),
                    # ... etc
                ]
            }
        )
    """
    # Metadata
    tax_year: int = 2024

    # Federal tax brackets: {FilingStatus: [(rate, upper_limit), ...]}
    federal_brackets: dict = field(default_factory=dict)

    # Federal standard deductions: {FilingStatus: amount}
    standard_deductions: dict = field(default_factory=dict)
    additional_deduction_married: float = 1550
    additional_deduction_unmarried: float = 1950

    # Long-term capital gains brackets: {FilingStatus: [(rate, upper_limit), ...]}
    ltcg_brackets: dict = field(default_factory=dict)

    # AMT parameters
    amt_exemption: dict = field(default_factory=dict)
    amt_phaseout_start: dict = field(default_factory=dict)
    amt_phaseout_rate: float = 0.25
    amt_rate_threshold: dict = field(default_factory=dict)
    amt_rate_low: float = 0.26
    amt_rate_high: float = 0.28

    # NIIT and Medicare
    niit_rate: float = 0.038
    niit_threshold: dict = field(default_factory=dict)
    medicare_additional_rate: float = 0.009
    medicare_threshold: dict = field(default_factory=dict)

    # California state tax brackets: {FilingStatus: [(rate, upper_limit), ...]}
    ca_brackets: dict = field(default_factory=dict)
    ca_standard_deductions: dict = field(default_factory=dict)
    ca_mental_health_threshold: float = 1000000
    ca_mental_health_rate: float = 0.01
    ca_sdi_rate: float = 0.011

    # Deduction limits
    salt_cap: float = 10000
    salt_cap_mfs: float = 5000
    medical_expense_floor: float = 0.075
    charitable_cash_limit: float = 0.60
    charitable_noncash_limit: float = 0.30
    capital_loss_limit: float = 3000
    capital_loss_limit_mfs: float = 1500

@dataclass(frozen=True)
class CapitalGainDetail:
    """One year's Schedule D netting result.

    The calculator keeps no carryforward state.  Disallowed losses are
    reported here so the caller (a notebook, a spreadsheet) can feed them
    back in as ``Income`` carry-in fields next year.
    """
    net_short_term: float = 0.0
    net_long_term: float = 0.0
    ordinary_capital_gain: float = 0.0   # taxed at ordinary rates
    preferential_income: float = 0.0     # net long-term gain + qualified dividends
    allowed_loss: float = 0.0            # deducted against other income
    carryforward_short_term: float = 0.0
    carryforward_long_term: float = 0.0

    @property
    def agi_amount(self) -> float:
        """Net capital amount added to AGI (gains less the allowed loss)."""
        return (
            self.ordinary_capital_gain
            + max(0.0, self.net_long_term)
            - self.allowed_loss
        )


@dataclass(frozen=True)
class PreCreditTax:
    """Pre-credit income tax split into ordinary and preferential parts."""
    ordinary_taxable_income: float = 0.0
    preferential_taxable_income: float = 0.0
    ordinary_tax: float = 0.0
    preferential_tax: float = 0.0

    @property
    def total(self) -> float:
        return self.ordinary_tax + self.preferential_tax


@dataclass(frozen=True)
class CoverageIssue:
    """One input or result the active rules do not fully model.

    ``severity`` is "error" when an input is ignored entirely and "warning"
    when it is included but only partially modeled.
    """
    code: str
    detail: str
    severity: str = "warning"


@dataclass
class TaxResult:
    """Core calculation results"""
    agi: float
    taxable_income: float
    pre_credit_tax: float
    total_credits: float
    net_tax: float
    ordinary_taxable_income: float = 0.0
    preferential_taxable_income: float = 0.0
    ordinary_tax: float = 0.0
    preferential_tax: float = 0.0
    capital_gains: CapitalGainDetail | None = None

@dataclass
class ReturnResult:
    """Result of combining several tax policies for one return."""
    agi: float
    parts: Dict[str, float]   # tax name -> tax amount on a comparable base
    detail: Dict[str, Any]    # tax name -> detailed result (e.g. TaxResult)
    total_tax: float
    # Which law produced this result: the pack's identity travels with the
    # number so illustrative output cannot be mistaken for filing-grade work.
    pack_name: str = ""
    authoritative: bool = True
    provenance: str = ""
    # Inputs that the active rules do not fully model.  Empty when the
    # calculation covers everything that was entered.
    coverage: Tuple["CoverageIssue", ...] = ()

@dataclass
class TaxResults:
    """Comprehensive tax calculation results"""
    # Income calculations
    gross_income: float = 0.0
    agi: float = 0.0
    taxable_income: float = 0.0

    # Deductions
    standard_deduction: float = 0.0
    itemized_deductions: float = 0.0
    deduction_used: float = 0.0
    used_itemized: bool = False

    # Federal taxes
    federal_income_tax: float = 0.0
    capital_gains_tax: float = 0.0
    total_federal_regular_tax: float = 0.0

    # Special federal taxes
    amt_taxable_income: float = 0.0
    tentative_minimum_tax: float = 0.0
    amt_owed: float = 0.0
    niit_owed: float = 0.0
    additional_medicare_tax: float = 0.0

    # California taxes
    california_income_tax: float = 0.0
    california_sdi: float = 0.0
    california_mental_health_tax: float = 0.0

    # Totals
    total_federal_tax: float = 0.0
    total_california_tax: float = 0.0
    total_tax_liability: float = 0.0

    # Effective rates
    effective_federal_rate: float = 0.0
    effective_california_rate: float = 0.0
    effective_total_rate: float = 0.0
