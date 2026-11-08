# Tax Calculator Project

**Location:** `/home/azhar/tax-calculator`

## Project Overview

A comprehensive Python package for calculating Federal and California state taxes for tax year 2024/2025. Designed for easy use in Jupyter Lab notebooks for tax analysis and planning.

## What's Included

### Package Structure
```
tax-calculator/
├── taxcalc/                    # Main package
│   ├── __init__.py            # Package exports
│   ├── models.py              # Data models
│   ├── constants.py           # Tax rates and brackets
│   └── calculator.py          # Main calculator
├── examples/                   # Examples
│   ├── simple_example.py      # Python script examples
│   └── tax_analysis_example.ipynb  # Jupyter notebook
├── tests/                      # Unit tests (future)
├── venv/                       # Virtual environment
├── setup.py                    # Package installation
├── requirements.txt            # Dependencies
├── README.md                   # Full documentation
├── QUICKSTART.md              # Quick start guide
└── .gitignore                 # Git ignore file
```

### Features Implemented

1. **Federal Taxes**
   - Regular income tax (progressive brackets)
   - Capital gains tax (0%, 15%, 20%)
   - Alternative Minimum Tax (AMT)
   - Net Investment Income Tax (NIIT - 3.8%)
   - Additional Medicare Tax (0.9%)

2. **California Taxes**
   - State income tax (1% to 12.3%)
   - Mental Health Services Tax (1% over $1M)
   - State Disability Insurance (SDI)

3. **Deductions**
   - Standard vs Itemized comparison
   - Medical expenses (7.5% AGI floor)
   - SALT deduction ($10,000 cap)
   - Mortgage interest
   - Charitable contributions (with AGI limits)
   - Donor-Advised Fund support

4. **Special Scenarios**
   - ISO exercise (AMT calculation)
   - Multiple income sources
   - Investment income
   - Rental income

## Quick Start

### 1. Activate the virtual environment:
```bash
cd /home/azhar/tax-calculator
source venv/bin/activate
```

### 2. For Jupyter Lab:
```bash
# Install Jupyter if not already installed
pip install jupyter pandas matplotlib

# Launch Jupyter Lab
jupyter lab
```

Then open: `examples/tax_analysis_example.ipynb`

### 3. For Python scripts:
```bash
# Run the example
python examples/simple_example.py

# Or create your own script
python your_tax_script.py
```

## Example Usage

```python
from taxcalc import (
    FilingStatus,
    Person,
    TaxUnit,
    Income,
    ItemizedDeductions,
    TaxCalculator2024
)

# Define taxpayer
taxpayer = TaxUnit(
    filing_status=FilingStatus.MARRIED_JOINT,
    primary=Person(age=45),
    spouse=Person(age=43),
    income=Income(
        wages_w2=400000,
        long_term_capital_gains=100000
    )
)

# Define deductions
itemized = ItemizedDeductions(
    state_local_income_taxes=25000,
    mortgage_interest=35000,
    cash_contributions_50pct_orgs=40000
)

# Calculate
calc = TaxCalculator2024(taxpayer, itemized)
results = calc.calculate_all_taxes()

# View results
print(calc.generate_summary_report(results))
print(f"Total Tax: ${results.total_tax_liability:,.2f}")
print(f"Effective Rate: {results.effective_total_rate*100:.2f}%")
```

## Files to Check Out

1. **QUICKSTART.md** - Quick start guide with common scenarios
2. **README.md** - Complete API documentation
3. **examples/tax_analysis_example.ipynb** - Comprehensive Jupyter notebook with:
   - Multiple calculation examples
   - Comparison analyses
   - Visualization examples
   - Custom analysis functions
4. **examples/simple_example.py** - Python script with 4 example scenarios

## Tax Year 2024 Rates (Built-in)

### Federal
- Brackets: 10%, 12%, 22%, 24%, 32%, 35%, 37%
- Standard Deduction: $29,200 (Married Joint), $14,600 (Single)
- Long-term Capital Gains: 0%, 15%, 20%
- SALT Cap: $10,000
- AMT Exemption: $133,300 (Married Joint), $85,700 (Single)

### California
- Brackets: 1% to 12.3%
- Standard Deduction: $11,080 (Married Joint), $5,540 (Single)
- Mental Health Tax: 1% over $1,000,000
- SDI Rate: 1.1% (2024), 1.2% (2025)

## Common Use Cases

### 1. Tax Planning
- Compare different income scenarios
- Evaluate charitable giving strategies
- Assess capital gains realization timing
- Calculate marginal vs effective tax rates

### 2. What-If Analysis
- Standard vs itemized deduction comparison
- Impact of additional income
- Tax-loss harvesting evaluation
- Donor-Advised Fund contribution planning

### 3. AMT Analysis
- ISO exercise impact
- High SALT deduction scenarios
- Large capital gains with high state taxes

### 4. Comparative Analysis
- Multiple scenarios side-by-side
- Visualization of tax breakdown
- Effective rate comparisons

## Important Notes

1. **Above-the-line deductions**: Traditional IRA and student loan interest are set on `Income`; subtract 401(k)/HSA workplace contributions from `wages_w2` before input
2. **Accuracy**: Based on official IRS and CA FTB 2024 guidance
3. **Limitations**: Does not include self-employment tax calculation
4. **Use**: For planning purposes only - consult tax professional for filing

## Package Installation

The package is installed in editable mode (`-e`), so you can modify the source code and changes will be immediately available without reinstalling.

To reinstall or update:
```bash
cd /home/azhar/tax-calculator
source venv/bin/activate
pip install -e .
```

## Dependencies

Core package: **None** (uses only Python standard library)

Optional (for examples):
- jupyter
- pandas
- matplotlib

## Next Steps

1. ✅ Package is installed and tested
2. 📊 Open Jupyter Lab and explore the example notebook
3. 🧮 Create your own tax scenarios
4. 📈 Use visualizations to understand tax breakdown
5. 💡 Experiment with different income and deduction combinations

## Support & Documentation

- **Full Documentation**: See README.md
- **Quick Start**: See QUICKSTART.md
- **Examples**: Check examples/ directory
- **Code**: Well-documented source in taxcalc/

## Testing

Run the simple example to verify everything works:
```bash
cd /home/azhar/tax-calculator
source venv/bin/activate
python examples/simple_example.py
```

You should see detailed tax calculations for 4 different scenarios.

---

**Project Created:** October 2025
**Python Version:** 3.7+
**Status:** Ready for use in Jupyter Lab analysis
