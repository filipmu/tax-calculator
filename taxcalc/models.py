"""
Data models for tax calculations.

This module defines all data structures used throughout the tax calculator,
including taxpayer information, income sources, deductions, and results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple


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
    """ All income sources"""
    # Wage and salary income
    wages_w2: float = 0.0

    # Investment income
    interest: float = 0.0
    qualified_dividends: float = 0.0   # Subset of ordinary_dividends
    ordinary_dividends: float = 0.0    # Includes qualified_dividends

    # Capital gains
    short_term_capital_gains: float = 0.0
    long_term_capital_gains: float = 0.0

    # Business and other income
    self_employment: float = 0.0
    rental: float = 0.0
    other: float = 0.0

    # Income adjustments
    ira_deduction: float = 0.0
    student_loan_interest_deduction: float = 0.0


    # Tax-exempt interest (affects AMT)
    tax_exempt_interest: float = 0.0
    private_activity_bond_interest: float = 0.0

@dataclass
class TaxUnit:
    """Basic taxpayer unit information"""
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







@dataclass
class Policy:
    year: int
    jurisdiction: str  # e.g., "federal", "MN"

    # Standard deduction by filing status
    standard_deduction: Dict[FilingStatus, float]

    # Brackets: list of (rate, threshold)
    # Example: [(0.10, 11000), (0.12, 44725), ...]
    brackets: Dict[FilingStatus, List[Tuple[float, float]]]

    # Placeholder for credits (we’ll expand later)
    child_credit_amount: float = 0.0






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
    All brackets are tuples of (upper_limit, rate) for each filing status.

    Example:
        # Create custom config for 2025
        config_2025 = TaxConfig(
            tax_year=2025,
            federal_brackets={
                FilingStatus.SINGLE: [
                    (11925, 0.10),
                    (48475, 0.12),
                    # ... etc
                ]
            }
        )
    """
    # Metadata
    tax_year: int = 2024

    # Federal tax brackets: {FilingStatus: [(upper_limit, rate), ...]}
    federal_brackets: dict = field(default_factory=dict)

    # Federal standard deductions: {FilingStatus: amount}
    standard_deductions: dict = field(default_factory=dict)
    additional_deduction_married: float = 1550
    additional_deduction_unmarried: float = 1950

    # Long-term capital gains brackets: {FilingStatus: [(upper_limit, rate), ...]}
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

    # California state tax brackets: {FilingStatus: [(upper_limit, rate), ...]}
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

@dataclass
class TaxResult:
    """Core calculation results"""
    agi: float
    taxable_income: float
    pre_credit_tax: float
    total_credits: float
    net_tax: float

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
