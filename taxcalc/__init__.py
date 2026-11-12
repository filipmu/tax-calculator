"""
Tax Calculator Package for Federal and California Taxes

A comprehensive tax calculation package for analyzing tax scenarios.
Includes support for itemized deductions, capital gains, AMT, and California state taxes.
Supports custom tax configurations for different years or hypothetical scenarios.

The package ships only an *illustrative* law pack (``EXAMPLE_PACK``). It is not
authoritative and is not tax advice. Pass your own ``LawPack`` (see
``taxcalc.load_pack``) to compute with real parameters and rules.

Author: Tax Calculator
Last Updated: October 2025
"""

from .models import (
    FilingStatus,
    Person,
    TaxUnit,
    Income,
    ItemizedDeductions,
    AMTAdjustments,
    CapitalGainDetail,
    PreCreditTax,
    DeductionDetail,
    TaxableIncome,
    CoverageIssue,
    TaxResult,
    TaxResults,
    ReturnResult,
    Policy,
    Parameter,
    TaxConfig
)

from .params import (
    PARAMETERS,
    AmbiguousVersionError,
    AvailabilityError,
    MissingParameterError,
    NoEffectiveVersionError,
    build_policy,
    optional_param,
    param,
    resolve,
    since,
    yearly,
)

from .rules.rulesets import get_ruleset
from .rules.capital_gain_rules import compute_capital_gains
from .rules.deduction_rules import compute_deductions

from .calculator import TaxCalculator, TaxCalculator2024

from .pipeline import compute_tax, compute_return

from .coverage import UnsupportedInputError, check_coverage

from .pack import LawPack, load_pack
from .example_pack import EXAMPLE_PACK

from .constants import (
    get_tax_config_2024,
    get_tax_config_2025,
    DEFAULT_TAX_CONFIG
)

__version__ = "1.1.0"
__all__ = [
    # Models
    "FilingStatus",
    "Person",
    "TaxUnit",
    "Income",
    "ItemizedDeductions",
    "AMTAdjustments",
    "CapitalGainDetail",
    "PreCreditTax",
    "DeductionDetail",
    "TaxableIncome",
    "CoverageIssue",
    "TaxResults",
    "TaxResult",
    "ReturnResult",
    "Policy",
    "Parameter",
    "TaxConfig",
    # Parameters
    "PARAMETERS",
    "build_policy",
    "param",
    "optional_param",
    "resolve",
    "yearly",
    "since",
    "NoEffectiveVersionError",
    "AmbiguousVersionError",
    "MissingParameterError",
    "AvailabilityError",
    # Rules
    "get_ruleset",
    "compute_capital_gains",
    "compute_deductions",
    # Law packs
    "LawPack",
    "load_pack",
    "EXAMPLE_PACK",
    # Calculators
    "compute_tax",
    "compute_return",
    "check_coverage",
    "UnsupportedInputError",
    "TaxCalculator",
    "TaxCalculator2024",
    # Config helpers
    "get_tax_config_2024",
    "get_tax_config_2025",
    "DEFAULT_TAX_CONFIG"
]
