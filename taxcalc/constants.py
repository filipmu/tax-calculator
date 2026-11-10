"""
Tax constants for tax year 2024 and helper functions for creating tax configurations.

All rates, brackets, and thresholds based on:
- IRS Revenue Procedure 2023-34 (official 2024 inflation adjustments)
- California Franchise Tax Board official 2024 guidance
"""

from .models import FilingStatus, TaxConfig

# ============================================================================
# FEDERAL TAX BRACKETS 2024
# Tuples are (rate, upper_limit); the top bracket has no upper limit.
# ============================================================================

FEDERAL_TAX_BRACKETS = {
    FilingStatus.SINGLE: [
        (0.10, 11600),
        (0.12, 47150),
        (0.22, 100525),
        (0.24, 191950),
        (0.32, 243725),
        (0.35, 609350),
        (0.37, float('inf'))
    ],
    FilingStatus.MARRIED_JOINT: [
        (0.10, 23200),
        (0.12, 94300),
        (0.22, 201050),
        (0.24, 383900),
        (0.32, 487450),
        (0.35, 731200),
        (0.37, float('inf'))
    ],
    FilingStatus.MARRIED_SEPARATE: [
        (0.10, 11600),
        (0.12, 47150),
        (0.22, 100525),
        (0.24, 191950),
        (0.32, 243725),
        (0.35, 365600),
        (0.37, float('inf'))
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (0.10, 16550),
        (0.12, 63100),
        (0.22, 100500),
        (0.24, 191950),
        (0.32, 243700),
        (0.35, 609350),
        (0.37, float('inf'))
    ],
    FilingStatus.QUALIFYING_WIDOW: [
        (0.10, 23200),
        (0.12, 94300),
        (0.22, 201050),
        (0.24, 383900),
        (0.32, 487450),
        (0.35, 731200),
        (0.37, float('inf'))
    ]
}

# ============================================================================
# FEDERAL STANDARD DEDUCTIONS 2024
# ============================================================================

STANDARD_DEDUCTION = {
    FilingStatus.SINGLE: 14600,
    FilingStatus.MARRIED_JOINT: 29200,
    FilingStatus.MARRIED_SEPARATE: 14600,
    FilingStatus.HEAD_OF_HOUSEHOLD: 21900,
    FilingStatus.QUALIFYING_WIDOW: 29200
}

# Additional standard deduction for age 65+ or blind
ADDITIONAL_DEDUCTION_MARRIED = 1550  # Per person for married taxpayers
ADDITIONAL_DEDUCTION_UNMARRIED = 1950  # Per person for unmarried taxpayers

# ============================================================================
# LONG-TERM CAPITAL GAINS TAX RATES 2024
# Tuples are (rate, upper_limit); the top bracket has no upper limit.
# ============================================================================

LTCG_BRACKETS = {
    FilingStatus.SINGLE: [
        (0.00, 47025),
        (0.15, 518900),
        (0.20, float('inf'))
    ],
    FilingStatus.MARRIED_JOINT: [
        (0.00, 94050),
        (0.15, 583750),
        (0.20, float('inf'))
    ],
    FilingStatus.MARRIED_SEPARATE: [
        (0.00, 47025),
        (0.15, 291850),
        (0.20, float('inf'))
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (0.00, 63000),
        (0.15, 551350),
        (0.20, float('inf'))
    ],
    FilingStatus.QUALIFYING_WIDOW: [
        (0.00, 94050),
        (0.15, 583750),
        (0.20, float('inf'))
    ]
}

# ============================================================================
# AMT (ALTERNATIVE MINIMUM TAX) 2024
# ============================================================================

AMT_EXEMPTION = {
    FilingStatus.SINGLE: 85700,
    FilingStatus.MARRIED_JOINT: 133300,
    FilingStatus.MARRIED_SEPARATE: 66650,
    FilingStatus.HEAD_OF_HOUSEHOLD: 85700,
    FilingStatus.QUALIFYING_WIDOW: 133300
}

AMT_EXEMPTION_PHASEOUT_START = {
    FilingStatus.SINGLE: 609350,
    FilingStatus.MARRIED_JOINT: 1218700,
    FilingStatus.MARRIED_SEPARATE: 609350,
    FilingStatus.HEAD_OF_HOUSEHOLD: 609350,
    FilingStatus.QUALIFYING_WIDOW: 1218700
}

# AMT exemption phases out at 25 cents per dollar of AMTI above threshold
AMT_EXEMPTION_PHASEOUT_RATE = 0.25

# AMT tax rates: 26% on first threshold amount, 28% above
AMT_RATE_THRESHOLD = {
    FilingStatus.SINGLE: 232600,
    FilingStatus.MARRIED_JOINT: 232600,
    FilingStatus.MARRIED_SEPARATE: 116300,
    FilingStatus.HEAD_OF_HOUSEHOLD: 232600,
    FilingStatus.QUALIFYING_WIDOW: 232600
}
AMT_RATE_LOW = 0.26
AMT_RATE_HIGH = 0.28

# ============================================================================
# NET INVESTMENT INCOME TAX (NIIT) 2024
# ============================================================================

NIIT_RATE = 0.038  # 3.8%
NIIT_THRESHOLD = {
    FilingStatus.SINGLE: 200000,
    FilingStatus.MARRIED_JOINT: 250000,
    FilingStatus.MARRIED_SEPARATE: 125000,
    FilingStatus.HEAD_OF_HOUSEHOLD: 200000,
    FilingStatus.QUALIFYING_WIDOW: 250000
}

# ============================================================================
# ADDITIONAL MEDICARE TAX 2024
# ============================================================================

MEDICARE_ADDITIONAL_RATE = 0.009  # 0.9%
MEDICARE_THRESHOLD = {
    FilingStatus.SINGLE: 200000,
    FilingStatus.MARRIED_JOINT: 250000,
    FilingStatus.MARRIED_SEPARATE: 125000,
    FilingStatus.HEAD_OF_HOUSEHOLD: 200000,
    FilingStatus.QUALIFYING_WIDOW: 250000
}

# ============================================================================
# CALIFORNIA TAX BRACKETS 2024
# Tuples are (rate, upper_limit); the top bracket has no upper limit.
# ============================================================================

CA_TAX_BRACKETS = {
    FilingStatus.SINGLE: [
        (0.01, 10756),
        (0.02, 25499),
        (0.04, 40245),
        (0.06, 55866),
        (0.08, 70606),
        (0.093, 360659),
        (0.103, 432787),
        (0.113, 721314),
        (0.123, float('inf'))
    ],
    FilingStatus.MARRIED_JOINT: [
        (0.01, 21512),
        (0.02, 50998),
        (0.04, 80490),
        (0.06, 111732),
        (0.08, 141212),
        (0.093, 721318),
        (0.103, 865574),
        (0.113, 1442628),
        (0.123, float('inf'))
    ],
    FilingStatus.MARRIED_SEPARATE: [
        (0.01, 10756),
        (0.02, 25499),
        (0.04, 40245),
        (0.06, 55866),
        (0.08, 70606),
        (0.093, 360659),
        (0.103, 432787),
        (0.113, 721314),
        (0.123, float('inf'))
    ],
    FilingStatus.HEAD_OF_HOUSEHOLD: [
        (0.01, 21527),
        (0.02, 51000),
        (0.04, 65744),
        (0.06, 81364),
        (0.08, 96107),
        (0.093, 490493),
        (0.103, 588593),
        (0.113, 980987),
        (0.123, float('inf'))
    ],
    FilingStatus.QUALIFYING_WIDOW: [
        (0.01, 21512),
        (0.02, 50998),
        (0.04, 80490),
        (0.06, 111732),
        (0.08, 141212),
        (0.093, 721318),
        (0.103, 865574),
        (0.113, 1442628),
        (0.123, float('inf'))
    ]
}

# California Mental Health Services Tax (additional 1% on income over $1 million)
CA_MENTAL_HEALTH_THRESHOLD = 1000000
CA_MENTAL_HEALTH_RATE = 0.01

# ============================================================================
# CALIFORNIA STANDARD DEDUCTIONS 2024
# ============================================================================

CA_STANDARD_DEDUCTION = {
    FilingStatus.SINGLE: 5540,
    FilingStatus.MARRIED_JOINT: 11080,
    FilingStatus.MARRIED_SEPARATE: 5540,
    FilingStatus.HEAD_OF_HOUSEHOLD: 11080,
    FilingStatus.QUALIFYING_WIDOW: 11080
}

# ============================================================================
# CALIFORNIA SDI/PFL 2024/2025
# ============================================================================

CA_SDI_RATE_2024 = 0.011  # 1.1%
CA_SDI_RATE_2025 = 0.012  # 1.2%
# No wage cap - all wages subject to SDI (as of 2024, wage ceiling eliminated)

# ============================================================================
# DEDUCTION LIMITS AND THRESHOLDS
# ============================================================================

SALT_CAP = 10000  # State and Local Tax deduction cap
SALT_CAP_MFS = 5000  # For married filing separately

MEDICAL_EXPENSE_FLOOR = 0.075  # 7.5% of AGI

# Charitable contribution AGI limits
CHARITABLE_CASH_LIMIT = 0.60  # 60% of AGI for cash to public charities
CHARITABLE_NONCASH_LIMIT = 0.30  # 30% of AGI for appreciated property

# Capital loss deduction limit
CAPITAL_LOSS_LIMIT = 3000
CAPITAL_LOSS_LIMIT_MFS = 1500


# ============================================================================
# HELPER FUNCTIONS TO CREATE TAX CONFIGURATIONS
# ============================================================================

def get_tax_config_2024() -> TaxConfig:
    """
    Create a TaxConfig object with all 2024 tax year parameters.

    Returns:
        TaxConfig: Complete 2024 tax configuration

    Example:
        config = get_tax_config_2024()
        calc = TaxCalculator(taxpayer, itemized, config=config)
    """
    return TaxConfig(
        tax_year=2024,
        federal_brackets=FEDERAL_TAX_BRACKETS.copy(),
        standard_deductions=STANDARD_DEDUCTION.copy(),
        additional_deduction_married=ADDITIONAL_DEDUCTION_MARRIED,
        additional_deduction_unmarried=ADDITIONAL_DEDUCTION_UNMARRIED,
        ltcg_brackets=LTCG_BRACKETS.copy(),
        amt_exemption=AMT_EXEMPTION.copy(),
        amt_phaseout_start=AMT_EXEMPTION_PHASEOUT_START.copy(),
        amt_phaseout_rate=AMT_EXEMPTION_PHASEOUT_RATE,
        amt_rate_threshold=AMT_RATE_THRESHOLD.copy(),
        amt_rate_low=AMT_RATE_LOW,
        amt_rate_high=AMT_RATE_HIGH,
        niit_rate=NIIT_RATE,
        niit_threshold=NIIT_THRESHOLD.copy(),
        medicare_additional_rate=MEDICARE_ADDITIONAL_RATE,
        medicare_threshold=MEDICARE_THRESHOLD.copy(),
        ca_brackets=CA_TAX_BRACKETS.copy(),
        ca_standard_deductions=CA_STANDARD_DEDUCTION.copy(),
        ca_mental_health_threshold=CA_MENTAL_HEALTH_THRESHOLD,
        ca_mental_health_rate=CA_MENTAL_HEALTH_RATE,
        ca_sdi_rate=CA_SDI_RATE_2024,
        salt_cap=SALT_CAP,
        salt_cap_mfs=SALT_CAP_MFS,
        medical_expense_floor=MEDICAL_EXPENSE_FLOOR,
        charitable_cash_limit=CHARITABLE_CASH_LIMIT,
        charitable_noncash_limit=CHARITABLE_NONCASH_LIMIT,
        capital_loss_limit=CAPITAL_LOSS_LIMIT,
        capital_loss_limit_mfs=CAPITAL_LOSS_LIMIT_MFS
    )


def get_tax_config_2025() -> TaxConfig:
    """
    Create a TaxConfig object with 2025 tax year parameters.

    Note: Currently uses 2024 values as placeholder. Update with official
    2025 IRS Revenue Procedure when released.

    Returns:
        TaxConfig: Complete 2025 tax configuration

    Example:
        config = get_tax_config_2025()
        calc = TaxCalculator(taxpayer, itemized, config=config)
    """
    # Start with 2024 config
    config = get_tax_config_2024()
    config.tax_year = 2025

    # Update with 2025-specific changes
    config.ca_sdi_rate = CA_SDI_RATE_2025

    # TODO: Update these when official 2025 numbers are released
    # config.federal_brackets = FEDERAL_TAX_BRACKETS_2025
    # config.standard_deductions = STANDARD_DEDUCTION_2025
    # etc.

    return config


# Default configuration (2024)
DEFAULT_TAX_CONFIG = get_tax_config_2024()
