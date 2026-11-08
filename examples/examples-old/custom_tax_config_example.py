#!/usr/bin/env python3
"""
Example: Using Custom Tax Configurations

This example demonstrates how to:
1. Use built-in 2024 and 2025 configurations
2. Create custom tax configurations for hypothetical scenarios
3. Compare different tax scenarios side-by-side
"""

from taxcalc import (
    FilingStatus,
    Person,
    TaxUnit,
    Income,
    ItemizedDeductions,
    TaxCalculator,
    TaxConfig,
    get_tax_config_2024,
    get_tax_config_2025
)


def example_1_compare_2024_vs_2025():
    """Compare 2024 vs 2025 tax treatment for the same scenario."""
    print("="*80)
    print("EXAMPLE 1: Comparing 2024 vs 2025 Tax Year")
    print("="*80)

    # Define taxpayer
    taxpayer = TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary=Person(age=45),
        spouse=Person(age=43),
        income=Income(
            wages_w2=400000,
            long_term_capital_gains=100000,
            ordinary_dividends=15000,
            qualified_dividends=15000
        )
    )

    # Define deductions
    itemized = ItemizedDeductions(
        state_local_income_taxes=25000,
        mortgage_interest=35000,
        cash_contributions_50pct_orgs=40000
    )

    # Calculate for 2024
    config_2024 = get_tax_config_2024()
    calc_2024 = TaxCalculator(taxpayer, itemized, config=config_2024)
    results_2024 = calc_2024.calculate_all_taxes()

    # Calculate for 2025
    config_2025 = get_tax_config_2025()
    calc_2025 = TaxCalculator(taxpayer, itemized, config=config_2025)
    results_2025 = calc_2025.calculate_all_taxes()

    # Compare results
    print(f"\nScenario: Married filing jointly, $400K wages + $100K LTCG + $15K dividends")
    print(f"\n{'Metric':<40} {'2024':>15} {'2025':>15} {'Difference':>15}")
    print("-" * 90)
    print(f"{'Total Tax Liability':<40} ${results_2024.total_tax_liability:>14,.2f} ${results_2025.total_tax_liability:>14,.2f} ${results_2025.total_tax_liability - results_2024.total_tax_liability:>14,.2f}")
    print(f"{'Federal Tax':<40} ${results_2024.total_federal_tax:>14,.2f} ${results_2025.total_federal_tax:>14,.2f} ${results_2025.total_federal_tax - results_2024.total_federal_tax:>14,.2f}")
    print(f"{'California Tax':<40} ${results_2024.total_california_tax:>14,.2f} ${results_2025.total_california_tax:>14,.2f} ${results_2025.total_california_tax - results_2024.total_california_tax:>14,.2f}")
    print(f"{'CA SDI (rate)':<40} {results_2024.california_sdi:>13,.2f} {results_2025.california_sdi:>14,.2f} {results_2025.california_sdi - results_2024.california_sdi:>14,.2f}")
    print(f"{'   (1.1% vs 1.2%)':<40}")
    print(f"{'Effective Total Rate':<40} {results_2024.effective_total_rate*100:>13,.2f}% {results_2025.effective_total_rate*100:>13,.2f}% {(results_2025.effective_total_rate - results_2024.effective_total_rate)*100:>13,.2f}%")


def example_2_custom_brackets():
    """Create a custom configuration with hypothetical tax brackets."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Custom Tax Brackets (Hypothetical 2026 Scenario)")
    print("="*80)

    # Start with 2025 config as a base
    custom_config = get_tax_config_2025()

    # Modify for hypothetical 2026 scenario
    custom_config.tax_year = 2026

    # Hypothetical: Increase standard deduction by 3%
    for status in FilingStatus:
        custom_config.standard_deductions[status] = int(custom_config.standard_deductions[status] * 1.03)

    # Hypothetical: Adjust federal tax brackets (3% inflation adjustment)
    for status in FilingStatus:
        custom_config.federal_brackets[status] = [
            (int(bracket * 1.03) if bracket != float('inf') else float('inf'), rate)
            for bracket, rate in custom_config.federal_brackets[status]
        ]

    # Hypothetical: Increase SALT cap to $15,000
    custom_config.salt_cap = 15000

    print("\nCustom modifications:")
    print("  • Standard deduction increased by 3%")
    print("  • Federal tax brackets adjusted by 3% (inflation)")
    print("  • SALT cap increased from $10,000 to $15,000")

    # Test scenario
    taxpayer = TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary=Person(age=50),
        spouse=Person(age=48),
        income=Income(wages_w2=300000)
    )
    itemized = ItemizedDeductions(
        state_local_income_taxes=25000,  # Benefits from higher SALT cap
        mortgage_interest=30000,
        cash_contributions_50pct_orgs=20000
    )

    # Compare 2025 actual vs 2026 hypothetical
    calc_2025 = TaxCalculator(taxpayer, itemized, config=get_tax_config_2025())
    calc_2026 = TaxCalculator(taxpayer, itemized, config=custom_config)

    results_2025 = calc_2025.calculate_all_taxes()
    results_2026 = calc_2026.calculate_all_taxes()

    print(f"\n{'Metric':<40} {'2025 Actual':>15} {'2026 Hypothetical':>18} {'Difference':>15}")
    print("-" * 93)
    print(f"{'Standard Deduction':<40} ${calc_2025.config.standard_deductions[FilingStatus.MARRIED_JOINT]:>14,} ${calc_2026.config.standard_deductions[FilingStatus.MARRIED_JOINT]:>17,} ${calc_2026.config.standard_deductions[FilingStatus.MARRIED_JOINT] - calc_2025.config.standard_deductions[FilingStatus.MARRIED_JOINT]:>14,}")
    print(f"{'SALT Cap':<40} ${calc_2025.config.salt_cap:>14,} ${calc_2026.config.salt_cap:>17,} ${calc_2026.config.salt_cap - calc_2025.config.salt_cap:>14,}")
    print(f"{'Total Tax Liability':<40} ${results_2025.total_tax_liability:>14,.2f} ${results_2026.total_tax_liability:>17,.2f} ${results_2026.total_tax_liability - results_2025.total_tax_liability:>14,.2f}")
    print(f"{'Tax Savings':<40} {'':>15} {'':>18} ${results_2025.total_tax_liability - results_2026.total_tax_liability:>14,.2f}")


def example_3_what_if_no_salt_cap():
    """Hypothetical: What if there was no SALT cap?"""
    print("\n" + "="*80)
    print("EXAMPLE 3: What-If Analysis - No SALT Cap")
    print("="*80)

    # Create a custom config without SALT cap
    no_salt_cap_config = get_tax_config_2024()
    no_salt_cap_config.salt_cap = float('inf')  # No cap
    no_salt_cap_config.salt_cap_mfs = float('inf')

    # High-tax-state scenario
    taxpayer = TaxUnit(
        filing_status=FilingStatus.MARRIED_JOINT,
        primary=Person(age=55),
        spouse=Person(age=53),
        income=Income(wages_w2=500000, long_term_capital_gains=200000)
    )
    itemized = ItemizedDeductions(
        state_local_income_taxes=75000,  # High state taxes
        real_estate_taxes=25000,
        mortgage_interest=40000,
        cash_contributions_50pct_orgs=50000
    )

    # Calculate with current rules (SALT cap)
    calc_with_cap = TaxCalculator(taxpayer, itemized, config=get_tax_config_2024())
    results_with_cap = calc_with_cap.calculate_all_taxes()

    # Calculate without SALT cap
    calc_no_cap = TaxCalculator(taxpayer, itemized, config=no_salt_cap_config)
    results_no_cap = calc_no_cap.calculate_all_taxes()

    total_salt = itemized.state_local_income_taxes + itemized.real_estate_taxes
    capped_salt = min(total_salt, 10000)

    print(f"\nScenario: $500K wages + $200K LTCG, ${total_salt:,.0f} in state/local taxes")
    print(f"\n{'Metric':<40} {'With $10K Cap':>15} {'No Cap':>15} {'Difference':>15}")
    print("-" * 90)
    print(f"{'SALT Deduction Allowed':<40} ${capped_salt:>14,.2f} ${total_salt:>14,.2f} ${total_salt - capped_salt:>14,.2f}")
    print(f"{'Total Itemized Deductions':<40} ${results_with_cap.itemized_deductions:>14,.2f} ${results_no_cap.itemized_deductions:>14,.2f} ${results_no_cap.itemized_deductions - results_with_cap.itemized_deductions:>14,.2f}")
    print(f"{'Federal Tax':<40} ${results_with_cap.total_federal_tax:>14,.2f} ${results_no_cap.total_federal_tax:>14,.2f} ${results_no_cap.total_federal_tax - results_with_cap.total_federal_tax:>14,.2f}")
    print(f"{'Total Tax Liability':<40} ${results_with_cap.total_tax_liability:>14,.2f} ${results_no_cap.total_tax_liability:>14,.2f} ${results_no_cap.total_tax_liability - results_with_cap.total_tax_liability:>14,.2f}")
    print(f"\nTax benefit from removing SALT cap: ${results_with_cap.total_tax_liability - results_no_cap.total_tax_liability:,.2f}")


def example_4_custom_from_scratch():
    """Build a completely custom tax configuration from scratch."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Creating a Completely Custom Tax Configuration")
    print("="*80)

    print("\nBuilding a simplified flat tax system:")
    print("  • 20% flat federal income tax")
    print("  • 10% flat California tax")
    print("  • $50,000 standard deduction")
    print("  • No SALT cap")
    print("  • No AMT")

    # Build a simple flat tax config
    flat_tax_config = TaxConfig(
        tax_year=2024,
        # Flat 20% federal tax
        federal_brackets={
            FilingStatus.SINGLE: [(float('inf'), 0.20)],
            FilingStatus.MARRIED_JOINT: [(float('inf'), 0.20)],
            FilingStatus.MARRIED_SEPARATE: [(float('inf'), 0.20)],
            FilingStatus.HEAD_OF_HOUSEHOLD: [(float('inf'), 0.20)],
        },
        # $50K standard deduction for everyone
        standard_deductions={
            FilingStatus.SINGLE: 50000,
            FilingStatus.MARRIED_JOINT: 50000,
            FilingStatus.MARRIED_SEPARATE: 50000,
            FilingStatus.HEAD_OF_HOUSEHOLD: 50000,
        },
        # 0% capital gains tax (no preferential treatment)
        ltcg_brackets={
            FilingStatus.SINGLE: [(float('inf'), 0.00)],
            FilingStatus.MARRIED_JOINT: [(float('inf'), 0.00)],
            FilingStatus.MARRIED_SEPARATE: [(float('inf'), 0.00)],
            FilingStatus.HEAD_OF_HOUSEHOLD: [(float('inf'), 0.00)],
        },
        # Zero AMT (simplified)
        amt_exemption={status: 999999999 for status in FilingStatus},
        amt_phaseout_start={status: 999999999 for status in FilingStatus},
        amt_rate_threshold={status: 999999999 for status in FilingStatus},
        # No NIIT or additional Medicare tax
        niit_threshold={status: 999999999 for status in FilingStatus},
        medicare_threshold={status: 999999999 for status in FilingStatus},
        # Flat 10% California tax
        ca_brackets={
            FilingStatus.SINGLE: [(float('inf'), 0.10)],
            FilingStatus.MARRIED_JOINT: [(float('inf'), 0.10)],
            FilingStatus.MARRIED_SEPARATE: [(float('inf'), 0.10)],
            FilingStatus.HEAD_OF_HOUSEHOLD: [(float('inf'), 0.10)],
        },
        ca_standard_deductions={
            FilingStatus.SINGLE: 50000,
            FilingStatus.MARRIED_JOINT: 50000,
            FilingStatus.MARRIED_SEPARATE: 50000,
            FilingStatus.HEAD_OF_HOUSEHOLD: 50000,
        },
        ca_sdi_rate=0.011,
        # No SALT cap
        salt_cap=float('inf'),
        salt_cap_mfs=float('inf'),
    )

    # Test with a simple scenario
    taxpayer = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(wages_w2=200000, long_term_capital_gains=50000)
    )
    itemized = ItemizedDeductions()

    # Compare current system vs flat tax
    calc_current = TaxCalculator(taxpayer, itemized, config=get_tax_config_2024())
    calc_flat = TaxCalculator(taxpayer, itemized, config=flat_tax_config)

    results_current = calc_current.calculate_all_taxes()
    results_flat = calc_flat.calculate_all_taxes()

    print(f"\nScenario: Single filer, $200K wages + $50K LTCG")
    print(f"\n{'Metric':<40} {'Current System':>15} {'Flat Tax':>15} {'Difference':>15}")
    print("-" * 90)
    print(f"{'Taxable Income (Federal)':<40} ${results_current.taxable_income:>14,.2f} ${results_flat.taxable_income:>14,.2f} ${results_flat.taxable_income - results_current.taxable_income:>14,.2f}")
    print(f"{'Federal Tax':<40} ${results_current.total_federal_tax:>14,.2f} ${results_flat.total_federal_tax:>14,.2f} ${results_flat.total_federal_tax - results_current.total_federal_tax:>14,.2f}")
    print(f"{'California Tax':<40} ${results_current.total_california_tax:>14,.2f} ${results_flat.total_california_tax:>14,.2f} ${results_flat.total_california_tax - results_current.total_california_tax:>14,.2f}")
    print(f"{'Total Tax':<40} ${results_current.total_tax_liability:>14,.2f} ${results_flat.total_tax_liability:>14,.2f} ${results_flat.total_tax_liability - results_current.total_tax_liability:>14,.2f}")
    print(f"{'Effective Rate':<40} {results_current.effective_total_rate*100:>13,.2f}% {results_flat.effective_total_rate*100:>13,.2f}% {(results_flat.effective_total_rate - results_current.effective_total_rate)*100:>13,.2f}%")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CUSTOM TAX CONFIGURATION EXAMPLES")
    print("="*80)

    example_1_compare_2024_vs_2025()
    example_2_custom_brackets()
    example_3_what_if_no_salt_cap()
    example_4_custom_from_scratch()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
The TaxConfig class allows you to:
1. Use built-in configurations (2024, 2025)
2. Modify existing configurations for what-if analysis
3. Build completely custom tax systems

Key use cases:
- Year-over-year comparisons
- Policy analysis (e.g., removing SALT cap)
- Hypothetical scenarios (different brackets, rates)
- Tax reform simulations

To create your own custom configuration:
  from taxcalc import TaxConfig, FilingStatus

  custom = TaxConfig(
      tax_year=2026,
      federal_brackets={...},
      standard_deductions={...},
      # ... other parameters
  )

  calc = TaxCalculator(taxpayer, itemized, config=custom)
    """)
    print("="*80)
