"""
Simple example of using the taxcalc package.

This script demonstrates basic usage of the tax calculator
for common scenarios.
"""

from taxcalc import (
    FilingStatus,
    TaxUnit,
    IncomeData,
    ItemizedDeductions,
    AMTAdjustments,
    TaxCalculator2024
)


def example_1_basic():
    """Example 1: Basic single filer with W-2 income only."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Single Filer - W-2 Income Only")
    print("="*80)

    taxpayer = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary_age=30
    )

    income = IncomeData(
        wages_w2=150000
    )

    itemized = ItemizedDeductions()  # Will use standard deduction

    calc = TaxCalculator2024(taxpayer, income, itemized)
    results = calc.calculate_all_taxes()

    print(calc.generate_summary_report(results))


def example_2_married_with_investments():
    """Example 2: Married filing jointly with investments and deductions."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Married Filing Jointly - With Investments")
    print("="*80)

    taxpayer = TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary_age=45,
        spouse_age=43,
        num_dependents=2
    )

    income = IncomeData(
        wages_w2=400000,
        interest_income=5000,
        qualified_dividends=15000,
        long_term_capital_gains=100000,
        rental_income=20000
    )

    itemized = ItemizedDeductions(
        medical_dental_expenses=15000,
        state_local_income_taxes=25000,
        real_estate_taxes=18000,
        mortgage_interest=35000,
        cash_contributions_50pct_orgs=40000,
        donor_advised_fund_contributions=20000
    )

    calc = TaxCalculator2024(taxpayer, income, itemized)
    results = calc.calculate_all_taxes()

    print(calc.generate_summary_report(results))


def example_3_amt_scenario():
    """Example 3: ISO exercise triggering AMT."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Single Filer - ISO Exercise (AMT)")
    print("="*80)

    taxpayer = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary_age=35
    )

    income = IncomeData(
        wages_w2=250000,
        long_term_capital_gains=50000,
        qualified_dividends=10000
    )

    itemized = ItemizedDeductions(
        state_local_income_taxes=30000,
        real_estate_taxes=15000,
        mortgage_interest=20000,
        cash_contributions_50pct_orgs=25000
    )

    # Large ISO exercise triggers AMT
    amt_adj = AMTAdjustments(
        iso_bargain_element=200000
    )

    calc = TaxCalculator2024(taxpayer, income, itemized, amt_adj)
    results = calc.calculate_all_taxes()

    print(calc.generate_summary_report(results))


def quick_comparison():
    """Quick comparison of different filing scenarios."""
    print("\n" + "="*80)
    print("COMPARISON: Standard vs Itemized Deduction")
    print("="*80)

    taxpayer = TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary_age=40,
        spouse_age=38
    )

    income = IncomeData(
        wages_w2=200000,
        long_term_capital_gains=30000
    )

    # Scenario 1: Standard deduction
    calc1 = TaxCalculator2024(taxpayer, income, ItemizedDeductions())
    results1 = calc1.calculate_all_taxes()

    # Scenario 2: With itemized deductions
    itemized = ItemizedDeductions(
        state_local_income_taxes=10000,
        mortgage_interest=20000,
        cash_contributions_50pct_orgs=15000
    )
    calc2 = TaxCalculator2024(taxpayer, income, itemized)
    results2 = calc2.calculate_all_taxes()

    print("\nScenario 1: Standard Deduction")
    print(f"  Deduction Used:     ${results1.deduction_used:>12,.2f}")
    print(f"  Total Tax:          ${results1.total_tax_liability:>12,.2f}")
    print(f"  Effective Rate:     {results1.effective_total_rate*100:>12.2f}%")

    print("\nScenario 2: Itemized Deductions ($45,000 total)")
    print(f"  Deduction Used:     ${results2.deduction_used:>12,.2f}")
    print(f"  Total Tax:          ${results2.total_tax_liability:>12,.2f}")
    print(f"  Effective Rate:     {results2.effective_total_rate*100:>12.2f}%")

    savings = results1.total_tax_liability - results2.total_tax_liability
    print(f"\nTax Savings from Itemizing: ${savings:,.2f}")
    print(f"Used {'ITEMIZED' if results2.used_itemized else 'STANDARD'} deduction")


if __name__ == "__main__":
    # Run all examples
    example_1_basic()
    example_2_married_with_investments()
    example_3_amt_scenario()
    quick_comparison()

    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")
