"""
Tax Calculator Package

A tax calculation package for analyzing tax scenarios.  The versioned engine
supports federal income tax, capital gains and preferential rates, itemized
deductions, NIIT, and Minnesota income tax.  The legacy calculator (kept for
compatibility) also covers AMT and California.

The package ships only an *illustrative* law pack (``EXAMPLE_PACK``). It is not
authoritative and is not tax advice. Pass your own ``LawPack`` (see
``taxcalc.load_pack``) to compute with real parameters and rules.

Author: Tax Calculator
Last Updated: November 2026
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
    AddonTaxResult,
    MNResult,
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
from .rules.mn_rules import compute_mn_return, compute_mn_tax

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
    "AddonTaxResult",
    "MNResult",
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
    "compute_mn_return",
    "compute_mn_tax",
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
