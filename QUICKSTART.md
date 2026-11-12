# Quick Start Guide

## Installation

1. **Navigate to the project directory:**
   ```bash
   cd /home/azhar/tax-calculator
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install additional dependencies (for Jupyter):**
   ```bash
   pip install jupyter pandas matplotlib
   ```

## Usage in Jupyter Lab

### Start Jupyter Lab:
```bash
cd /home/azhar/tax-calculator
source venv/bin/activate
jupyter lab
```

Then open the example notebook: `examples/tax_analysis_example.ipynb`

### Quick Example in Jupyter:

```python
from taxcalc import (
    FilingStatus,
    Person,
    TaxUnit,
    Income,
    ItemizedDeductions,
    TaxCalculator2024
)

# Define your tax scenario
taxpayer = TaxUnit(
    filing_status=FilingStatus.MARRIED_JOINT,
    primary=Person(age=45),
    spouse=Person(age=43),
    income=Income(
        wages_w2=400000,
        long_term_capital_gain_loss=100000,
        ordinary_dividends=15000,
        qualified_dividends=15000
    )
)

itemized = ItemizedDeductions(
    state_local_income_taxes=25000,
    mortgage_interest=35000,
    cash_contributions_50pct_orgs=40000
)

# Calculate taxes
calc = TaxCalculator2024(taxpayer, itemized)
results = calc.calculate_all_taxes()

# View results
print(calc.generate_summary_report(results))
```

## Usage in Python Scripts

### Run the example script:
```bash
cd /home/azhar/tax-calculator
source venv/bin/activate
python examples/simple_example.py
```

### Create your own script:

```python
# my_tax_calculation.py
from taxcalc import *

# Your tax data here
taxpayer = TaxUnit(
    filing_status=FilingStatus.SINGLE,
    primary=Person(age=30),
    income=Income(wages_w2=150000)
)
itemized = ItemizedDeductions()

calc = TaxCalculator2024(taxpayer, itemized)
results = calc.calculate_all_taxes()

print(f"Total Tax: ${results.total_tax_liability:,.2f}")
print(f"Effective Rate: {results.effective_total_rate*100:.2f}%")
```

Then run:
```bash
source venv/bin/activate
python my_tax_calculation.py
```

## Key Features to Try

1. **Compare Standard vs Itemized Deductions**
   - Create two calculations with same income
   - One with empty ItemizedDeductions()
   - One with your itemized amounts
   - Compare total_tax_liability

2. **Analyze Capital Gains Impact**
   - Add long_term_capital_gain_loss to `Income`
   - Note preferential tax treatment (0%, 15%, 20%)

3. **Check AMT Exposure**
   - Add AMTAdjustments with iso_bargain_element
   - Review results.amt_owed in output

4. **Charitable Giving Analysis**
   - Vary cash_contributions_50pct_orgs amounts
   - Calculate tax savings per dollar donated

## Common Scenarios

### Scenario 1: Basic W-2 Employee
```python
taxpayer = TaxUnit(
    filing_status=FilingStatus.SINGLE,
    primary=Person(age=30),
    income=Income(wages_w2=150000)
)
itemized = ItemizedDeductions()
```

### Scenario 2: High-Income with Investments
```python
taxpayer = TaxUnit(
    filing_status=FilingStatus.MARRIED_JOINT,
    primary=Person(age=45),
    spouse=Person(age=43),
    income=Income(
        wages_w2=400000,
        long_term_capital_gain_loss=100000,
        ordinary_dividends=20000,
        qualified_dividends=20000
    )
)
itemized = ItemizedDeductions(
    state_local_income_taxes=25000,
    mortgage_interest=35000
)
```

### Scenario 3: ISO Exercise (AMT)
```python
taxpayer = TaxUnit(
    filing_status=FilingStatus.SINGLE,
    primary=Person(age=35),
    income=Income(wages_w2=250000)
)
itemized = ItemizedDeductions(state_local_income_taxes=30000)
amt_adj = AMTAdjustments(iso_bargain_element=200000)
calc = TaxCalculator2024(taxpayer, itemized, amt_adj)
```

## Understanding the Results

The `TaxResults` object contains all calculations:

- `gross_income` - Total income
- `agi` - Adjusted Gross Income
- `taxable_income` - Income after deductions
- `federal_income_tax` - Regular federal tax on ordinary income
- `capital_gains_tax` - Federal tax on LTCG and qualified dividends
- `amt_owed` - Alternative Minimum Tax (if applicable)
- `niit_owed` - Net Investment Income Tax (3.8%)
- `california_income_tax` - California state income tax
- `total_tax_liability` - Combined federal and California taxes
- `effective_total_rate` - Overall effective tax rate

## Tips

1. **Pre-tax contributions**: Add up Schedule 1 adjustments (for example, IRA and student loan interest) and enter the total in `Income.adjustments_sched_1`; subtract 401(k) and HSA contributions from wages_w2 before input
2. **SALT cap**: Federal SALT deduction automatically capped at $10,000
3. **Charitable limits**: Cash contributions limited to 60% of AGI, property to 30%
4. **Medical expenses**: Only amount exceeding 7.5% of AGI is deductible
5. **California differences**: CA taxes capital gains as ordinary income, has lower standard deduction

## Next Steps

1. Open `examples/tax_analysis_example.ipynb` for detailed examples
2. Review `README.md` for complete API documentation
3. Modify examples to match your specific tax situation
4. Use visualizations to understand tax breakdown

## Getting Help

- Check the examples directory for common use cases
- Review the README.md for detailed documentation
- All calculations show line-by-line breakdowns in the summary report
