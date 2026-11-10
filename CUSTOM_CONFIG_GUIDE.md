# Custom Tax Configuration Guide

## Overview

The tax calculator now supports flexible tax configurations, allowing you to:
- Use built-in 2024 and 2025 tax year data
- Modify specific parameters for what-if analysis
- Create completely custom tax systems
- Compare different scenarios side-by-side

## Quick Start

### Using Built-in Configurations

```python
from taxcalc import (
    FilingStatus, Person, TaxUnit, Income, ItemizedDeductions,
    TaxCalculator, get_tax_config_2024, get_tax_config_2025
)

# Define your scenario
taxpayer = TaxUnit(
    filing_status=FilingStatus.SINGLE,
    primary=Person(age=30),
    income=Income(wages_w2=150000)
)
itemized = ItemizedDeductions()

# Use 2024 tax rules (default)
calc_2024 = TaxCalculator(taxpayer, itemized)
results_2024 = calc_2024.calculate_all_taxes()

# Use 2025 tax rules
calc_2025 = TaxCalculator(taxpayer, itemized, config=get_tax_config_2025())
results_2025 = calc_2025.calculate_all_taxes()

# Compare
print(f"2024 tax: ${results_2024.total_tax_liability:,.2f}")
print(f"2025 tax: ${results_2025.total_tax_liability:,.2f}")
```

### Modifying Specific Parameters

```python
# Start with a base configuration
config = get_tax_config_2024()

# Modify specific parameters
config.salt_cap = 15000  # Increase SALT cap from $10K to $15K
config.ca_sdi_rate = 0.015  # Increase CA SDI rate to 1.5%

# Use the modified config
calc = TaxCalculator(taxpayer, itemized, config=config)
results = calc.calculate_all_taxes()
```

### Creating a Custom Configuration

```python
from taxcalc import TaxConfig, FilingStatus

# Build a completely custom configuration
custom_config = TaxConfig(
    tax_year=2026,

    # Federal brackets: {FilingStatus: [(rate, upper_limit), ...]}
    federal_brackets={
        FilingStatus.SINGLE: [
            (0.10, 12000),
            (0.12, 50000),
            (0.22, 100000),
            (0.24, 200000),
            (0.35, float('inf'))
        ],
        FilingStatus.MARRIED_JOINT: [
            (0.10, 24000),
            (0.12, 100000),
            (0.22, 200000),
            (0.24, 400000),
            (0.35, float('inf'))
        ],
        # ... other filing statuses
    },

    # Standard deductions
    standard_deductions={
        FilingStatus.SINGLE: 15000,
        FilingStatus.MARRIED_JOINT: 30000,
        # ... other filing statuses
    },

    # Other parameters...
    salt_cap=20000,
    ca_sdi_rate=0.012,
    # ... etc
)

calc = TaxCalculator(taxpayer, itemized, config=custom_config)
```

## TaxConfig Parameters

### Federal Income Tax
- `federal_brackets`: Progressive tax brackets by filing status, as (rate, upper_limit) tuples
- `standard_deductions`: Standard deduction amounts by filing status
- `additional_deduction_married`: Additional deduction for age/blindness (married)
- `additional_deduction_unmarried`: Additional deduction for age/blindness (unmarried)

### Capital Gains
- `ltcg_brackets`: Long-term capital gains brackets (0%, 15%, 20%)

### Alternative Minimum Tax (AMT)
- `amt_exemption`: AMT exemption amounts by filing status
- `amt_phaseout_start`: Income level where AMT exemption begins phasing out
- `amt_phaseout_rate`: Rate at which AMT exemption phases out (typically 0.25)
- `amt_rate_threshold`: Threshold for AMT rates
- `amt_rate_low`: Lower AMT rate (typically 0.26)
- `amt_rate_high`: Higher AMT rate (typically 0.28)

### Net Investment Income Tax (NIIT)
- `niit_rate`: NIIT rate (typically 0.038 = 3.8%)
- `niit_threshold`: Income thresholds for NIIT by filing status

### Additional Medicare Tax
- `medicare_additional_rate`: Additional Medicare tax rate (typically 0.009 = 0.9%)
- `medicare_threshold`: Income thresholds by filing status

### California State Tax
- `ca_brackets`: California progressive tax brackets
- `ca_standard_deductions`: California standard deductions
- `ca_mental_health_threshold`: Threshold for Mental Health Services Tax ($1M)
- `ca_mental_health_rate`: Mental Health Services Tax rate (1%)
- `ca_sdi_rate`: State Disability Insurance rate

### Deduction Limits
- `salt_cap`: Federal SALT deduction cap ($10,000 for 2024)
- `salt_cap_mfs`: SALT cap for married filing separately
- `medical_expense_floor`: AGI percentage floor for medical expenses (0.075 = 7.5%)
- `charitable_cash_limit`: Cash contribution AGI limit (0.60 = 60%)
- `charitable_noncash_limit`: Non-cash contribution AGI limit (0.30 = 30%)
- `capital_loss_limit`: Capital loss deduction limit ($3,000)
- `capital_loss_limit_mfs`: Capital loss limit for MFS

## Common Use Cases

### 1. Year-over-Year Comparison

```python
configs = {
    '2024': get_tax_config_2024(),
    '2025': get_tax_config_2025()
}

results = {}
for year, config in configs.items():
    calc = TaxCalculator(taxpayer, itemized, config=config)
    results[year] = calc.calculate_all_taxes()

for year in results:
    print(f"{year}: ${results[year].total_tax_liability:,.2f}")
```

### 2. What-If Analysis: Policy Changes

```python
# Base case: Current law
base_config = get_tax_config_2024()
base_calc = TaxCalculator(taxpayer, itemized, config=base_config)
base_results = base_calc.calculate_all_taxes()

# Scenario: SALT cap removed
no_salt_cap_config = get_tax_config_2024()
no_salt_cap_config.salt_cap = float('inf')
no_salt_calc = TaxCalculator(taxpayer, itemized, config=no_salt_cap_config)
no_salt_results = no_salt_calc.calculate_all_taxes()

# Compare
tax_savings = base_results.total_tax_liability - no_salt_results.total_tax_liability
print(f"Tax savings from removing SALT cap: ${tax_savings:,.2f}")
```

### 3. Adjusting for Inflation

```python
import copy

# Start with current year
config_2026 = copy.deepcopy(get_tax_config_2025())
config_2026.tax_year = 2026

# Apply 3% inflation adjustment
inflation_rate = 1.03

# Adjust standard deductions
for status in FilingStatus:
    config_2026.standard_deductions[status] = int(
        config_2026.standard_deductions[status] * inflation_rate
    )

# Adjust federal brackets
for status in FilingStatus:
    config_2026.federal_brackets[status] = [
        (rate, int(upper_limit * inflation_rate) if upper_limit != float('inf') else float('inf'))
        for rate, upper_limit in config_2026.federal_brackets[status]
    ]
```

### 4. Comparing Multiple Scenarios

```python
scenarios = {
    'Current Law': get_tax_config_2024(),
    'Raised SALT Cap': ...,  # Modified config
    'Lower Rates': ...,      # Modified config
    'Flat Tax': ...          # Custom config
}

for name, config in scenarios.items():
    calc = TaxCalculator(taxpayer, itemized, config=config)
    results = calc.calculate_all_taxes()
    print(f"{name:20} ${results.total_tax_liability:>12,.2f}")
```

## Backward Compatibility

Existing code continues to work:

```python
# Old way (still works)
from taxcalc import TaxCalculator2024

calc = TaxCalculator2024(taxpayer, itemized)
results = calc.calculate_all_taxes()

# New way (more flexible)
from taxcalc import TaxCalculator

calc = TaxCalculator(taxpayer, itemized)  # Uses 2024 by default
results = calc.calculate_all_taxes()
```

## Examples

See these files for complete examples:
- `examples/custom_tax_config_example.py` - Python script with 4 examples
- `examples/custom_config_notebook_example.ipynb` - Jupyter notebook tutorial

## Tips

1. **Use `copy.deepcopy()` when modifying configs** to avoid changing the original:
   ```python
   import copy
   my_config = copy.deepcopy(get_tax_config_2024())
   my_config.salt_cap = 15000  # Only affects my_config
   ```

2. **Handle infinity carefully** in brackets:
   ```python
   # Brackets are (rate, upper_limit); the last bracket always uses infinity
   federal_brackets = [
       (0.10, 50000),
       (0.20, 100000),
       (0.30, float('inf'))  # "All income above $100K"
   ]
   ```

3. **Use dictionaries for all filing statuses**:
   ```python
   # Quick way to set same value for all statuses
   standard_deductions = {status: 20000 for status in FilingStatus}
   ```

4. **Test your custom configs** with simple scenarios first:
   ```python
   # Simple test scenario
   test_taxpayer = TaxUnit(
       filing_status=FilingStatus.SINGLE,
       primary=Person(age=30),
       income=Income(wages_w2=100000)
   )
   test_itemized = ItemizedDeductions()
   ```

## Next Steps

1. Try the examples: `python examples/custom_tax_config_example.py`
2. Open the Jupyter notebook: `examples/custom_config_notebook_example.ipynb`
3. Create your own scenarios in a notebook
4. Use pandas/matplotlib for analyzing multiple scenarios

## Support

For more information, see:
- `README.md` - Full package documentation
- `QUICKSTART.md` - Quick start guide
- `examples/` - Example scripts and notebooks
