"""
Tax Calculator Package for Federal and California Taxes

A comprehensive tax calculation package for analyzing tax scenarios.
Includes support for itemized deductions, capital gains, AMT, and California state taxes.
Supports custom tax configurations for different years or hypothetical scenarios.

Author: Tax Calculator
Last Updated: October 2025
"""

from .models import (
    FilingStatus,
    Person,
    TaxUnit,
    Income,
    IncomeData,
    ItemizedDeductions,
    AMTAdjustments,
    TaxResult,
    TaxResults,
    Policy,
    TaxConfig
)

from .calculator import TaxCalculator, TaxCalculator2024

from .pipeline import compute_tax

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
    "IncomeData",
    "Income",
    "ItemizedDeductions",
    "AMTAdjustments",
    "TaxResults",
    "TaxResult",
    "Policy",
    "TaxConfig",
    # Calculators
    "compute_tax",
    "TaxCalculator",
    "TaxCalculator2024",
    # Config helpers
    "get_tax_config_2024",
    "get_tax_config_2025",
    "DEFAULT_TAX_CONFIG"
]
