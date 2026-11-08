"""
Main tax calculator implementation for Federal and California taxes.

This module contains the TaxCalculator2024 class which performs all tax calculations
including regular income tax, capital gains, AMT, NIIT, and California state taxes.
"""

from .models import (
    FilingStatus,
    TaxUnit,
    ItemizedDeductions,
    AMTAdjustments,
    TaxResults,
    TaxConfig
)
from . import constants as const


class TaxCalculator:
    """
    Comprehensive tax calculator for Federal and California taxes.

    Supports custom tax configurations for different years or scenarios.
    Default configuration uses 2024 tax year parameters.
    """

    def __init__(self, taxpayer_info: TaxUnit,
                 itemized_deductions: ItemizedDeductions, amt_adjustments: AMTAdjustments = None,
                 config: TaxConfig = None):
        """
        Initialize tax calculator with taxpayer information and deduction data.

        Args:
            taxpayer_info: TaxUnit containing filing status, people, and income
            itemized_deductions: Itemized deduction amounts by category
            amt_adjustments: AMT-specific adjustments (optional)
            config: Tax configuration (optional, defaults to 2024)

        Example:
            # Use default 2024 config
            calc = TaxCalculator(taxpayer, itemized)

            # Use 2025 config
            from taxcalc import get_tax_config_2025
            calc = TaxCalculator(taxpayer, itemized, config=get_tax_config_2025())

            # Use custom config
            custom_config = TaxConfig(tax_year=2026, federal_brackets={...})
            calc = TaxCalculator(taxpayer, itemized, config=custom_config)
        """
        self.taxpayer = taxpayer_info
        self.income = taxpayer_info.income
        self.itemized = itemized_deductions
        self.amt_adj = amt_adjustments or AMTAdjustments()
        self.config = config or const.DEFAULT_TAX_CONFIG

    def calculate_all_taxes(self) -> TaxResults:
        """
        Calculate all federal and California taxes.

        Returns:
            TaxResults object containing all tax calculations
        """
        results = TaxResults()

        # Step 1: Calculate Adjusted Gross Income (AGI)
        results.gross_income = self._calculate_gross_income()
        results.agi = self._calculate_agi(results.gross_income)

        # Step 2: Calculate deductions (standard vs itemized)
        results.standard_deduction = self._calculate_standard_deduction()
        results.itemized_deductions = self._calculate_itemized_deductions(results.agi)
        results.used_itemized = results.itemized_deductions > results.standard_deduction
        results.deduction_used = max(results.standard_deduction, results.itemized_deductions)

        # Step 3: Calculate taxable income
        results.taxable_income = max(0, results.agi - results.deduction_used)

        # Step 4: Calculate federal regular income tax
        # Separate ordinary income from capital gains for proper tax treatment
        ordinary_income = results.taxable_income - self.income.long_term_capital_gains - self.income.qualified_dividends
        ordinary_income = max(0, ordinary_income)

        results.federal_income_tax = self._calculate_federal_tax(ordinary_income)
        results.capital_gains_tax = self._calculate_capital_gains_tax(
            results.taxable_income,
            self.income.long_term_capital_gains,
            self.income.qualified_dividends
        )
        results.total_federal_regular_tax = results.federal_income_tax + results.capital_gains_tax

        # Step 5: Calculate Alternative Minimum Tax (AMT)
        results.amt_taxable_income = self._calculate_amt_income(results.agi)
        results.tentative_minimum_tax = self._calculate_tentative_minimum_tax(results.amt_taxable_income)
        results.amt_owed = max(0, results.tentative_minimum_tax - results.total_federal_regular_tax)

        # Step 6: Calculate Net Investment Income Tax (NIIT)
        results.niit_owed = self._calculate_niit(results.agi)

        # Step 7: Calculate Additional Medicare Tax
        results.additional_medicare_tax = self._calculate_additional_medicare_tax()

        # Step 8: Calculate total federal tax
        results.total_federal_tax = (
            results.total_federal_regular_tax +
            results.amt_owed +
            results.niit_owed +
            results.additional_medicare_tax
        )

        # Step 9: Calculate California taxes
        # California taxes all income (including capital gains) as ordinary income
        ca_taxable_income = self._calculate_california_taxable_income(results.agi)
        results.california_income_tax = self._calculate_california_tax(ca_taxable_income)

        # California Mental Health Services Tax (1% on income over $1 million)
        if results.agi > self.config.ca_mental_health_threshold:
            results.california_mental_health_tax = (
                (results.agi - self.config.ca_mental_health_threshold) * self.config.ca_mental_health_rate
            )

        # California SDI (State Disability Insurance)
        results.california_sdi = self._calculate_california_sdi()

        results.total_california_tax = (
            results.california_income_tax +
            results.california_mental_health_tax +
            results.california_sdi
        )

        # Step 10: Calculate total tax liability and effective rates
        results.total_tax_liability = results.total_federal_tax + results.total_california_tax

        if results.gross_income > 0:
            results.effective_federal_rate = results.total_federal_tax / results.gross_income
            results.effective_california_rate = results.total_california_tax / results.gross_income
            results.effective_total_rate = results.total_tax_liability / results.gross_income

        return results

    def _calculate_gross_income(self) -> float:
        """Calculate total gross income from all sources.

        Qualified dividends are a subset of ordinary dividends and are therefore
        not added separately.
        """
        return (
            self.income.wages_w2 +
            self.income.interest +
            self.income.ordinary_dividends +
            self.income.short_term_capital_gains +
            self.income.long_term_capital_gains +
            self.income.self_employment +
            self.income.rental +
            self.income.other
        )

    def _calculate_agi(self, gross_income: float) -> float:
        """
        Calculate Adjusted Gross Income (AGI).

        Subtracts above-the-line adjustments (IRA deduction and student loan
        interest) from gross income.
        """
        adjustments = (
            self.income.ira_deduction +
            self.income.student_loan_interest_deduction
        )
        return max(0.0, gross_income - adjustments)

    def _calculate_standard_deduction(self) -> float:
        """
        Calculate standard deduction including additional amounts for age and blindness.
        """
        base_deduction = self.config.standard_deductions[self.taxpayer.filing_status]

        # Additional deduction for age 65+ and/or blind
        additional = 0
        is_married = self.taxpayer.filing_status in [FilingStatus.MARRIED_JOINT, FilingStatus.MARRIED_SEPARATE]
        per_person_amount = self.config.additional_deduction_married if is_married else self.config.additional_deduction_unmarried

        # Primary taxpayer
        if self.taxpayer.primary.age >= 65:
            additional += per_person_amount
        if self.taxpayer.primary.blind:
            additional += per_person_amount

        # Spouse (if married, including married filing separately)
        if is_married and self.taxpayer.spouse is not None:
            if self.taxpayer.spouse.age >= 65:
                additional += per_person_amount
            if self.taxpayer.spouse.blind:
                additional += per_person_amount

        return base_deduction + additional

    def _calculate_itemized_deductions(self, agi: float) -> float:
        """
        Calculate total itemized deductions with all applicable limits.

        Applies:
        - Medical expense floor (7.5% of AGI)
        - SALT cap ($10,000 or $5,000 for MFS)
        - Charitable contribution limits (60% of AGI for cash, 30% for property)
        """
        total_itemized = 0.0

        # 1. Medical and dental expenses (only amount exceeding 7.5% of AGI)
        medical_floor = agi * self.config.medical_expense_floor
        deductible_medical = max(0, self.itemized.medical_dental_expenses - medical_floor)
        total_itemized += deductible_medical

        # 2. State and local taxes (SALT) - subject to $10,000 cap
        salt_total = (
            self.itemized.state_local_income_taxes +
            self.itemized.real_estate_taxes +
            self.itemized.personal_property_taxes
        )
        salt_cap = self.config.salt_cap_mfs if self.taxpayer.filing_status == FilingStatus.MARRIED_SEPARATE else self.config.salt_cap
        deductible_salt = min(salt_total, salt_cap)
        total_itemized += deductible_salt

        # 3. Home mortgage interest and points
        total_itemized += self.itemized.mortgage_interest
        total_itemized += self.itemized.mortgage_points

        # 4. Charitable contributions with AGI limits
        # Cash contributions to 50% organizations: up to 60% of AGI
        cash_limit = agi * self.config.charitable_cash_limit
        cash_contributions = (
            self.itemized.cash_contributions_50pct_orgs +
            self.itemized.cash_contributions_other +
            self.itemized.donor_advised_fund_contributions  # DAF contributions count as cash
        )
        deductible_cash = min(cash_contributions, cash_limit)
        total_itemized += deductible_cash

        # Noncash contributions (appreciated property): up to 30% of AGI
        noncash_limit = agi * self.config.charitable_noncash_limit
        deductible_noncash = min(self.itemized.noncash_contributions, noncash_limit)
        total_itemized += deductible_noncash

        # 5. Other itemized deductions
        total_itemized += self.itemized.casualty_theft_losses
        total_itemized += self.itemized.gambling_losses

        return total_itemized

    def _calculate_federal_tax(self, ordinary_taxable_income: float) -> float:
        """
        Calculate federal income tax on ordinary income using marginal tax brackets.

        Args:
            ordinary_taxable_income: Taxable income excluding long-term capital gains
                                    and qualified dividends (which are taxed separately)
        """
        brackets = self.config.federal_brackets[self.taxpayer.filing_status]
        tax = 0.0
        previous_bracket = 0

        for bracket_top, rate in brackets:
            if ordinary_taxable_income <= previous_bracket:
                break

            taxable_in_bracket = min(ordinary_taxable_income, bracket_top) - previous_bracket
            tax += taxable_in_bracket * rate
            previous_bracket = bracket_top

        return tax

    def _calculate_capital_gains_tax(self, total_taxable_income: float,
                                    ltcg: float, qualified_div: float) -> float:
        """
        Calculate tax on long-term capital gains and qualified dividends.

        Uses preferential rates (0%, 15%, 20%) based on total taxable income.
        Short-term capital gains are taxed as ordinary income (already included).

        Args:
            total_taxable_income: Total taxable income including LTCG and qualified dividends
            ltcg: Long-term capital gains amount
            qualified_div: Qualified dividends amount
        """
        preferential_income = ltcg + qualified_div
        if preferential_income == 0:
            return 0.0

        brackets = self.config.ltcg_brackets[self.taxpayer.filing_status]
        tax = 0.0

        # The key is that LTCG/qualified dividends are taxed based on where they
        # fall in the overall income stack
        ordinary_income = total_taxable_income - preferential_income

        # Calculate tax on preferential income using the stacking method
        income_so_far = ordinary_income
        remaining_preferential = preferential_income

        previous_bracket = 0
        for bracket_top, rate in brackets:
            if remaining_preferential <= 0:
                break

            # How much room is left in this bracket?
            if income_so_far >= bracket_top:
                previous_bracket = bracket_top
                continue

            # Amount of preferential income that falls in this bracket
            room_in_bracket = bracket_top - income_so_far
            amount_in_bracket = min(remaining_preferential, room_in_bracket)

            tax += amount_in_bracket * rate
            income_so_far += amount_in_bracket
            remaining_preferential -= amount_in_bracket
            previous_bracket = bracket_top

        return tax

    def _calculate_amt_income(self, agi: float) -> float:
        """
        Calculate Alternative Minimum Taxable Income (AMTI).

        Start with AGI and add back:
        - State and local taxes deducted
        - Certain other adjustments and preferences
        - ISO exercise bargain element
        - Private activity bond interest
        """
        amti = agi

        # Add back state and local taxes if itemizing
        if self._calculate_itemized_deductions(agi) > self._calculate_standard_deduction():
            # Add back SALT deduction
            salt_total = (
                self.itemized.state_local_income_taxes +
                self.itemized.real_estate_taxes +
                self.itemized.personal_property_taxes
            )
            salt_cap = self.config.salt_cap_mfs if self.taxpayer.filing_status == FilingStatus.MARRIED_SEPARATE else self.config.salt_cap
            amti += min(salt_total, salt_cap)

        # Add AMT preference items
        amti += self.amt_adj.iso_bargain_element
        amti += self.income.private_activity_bond_interest

        # Add other AMT adjustments
        amti += self.amt_adj.depreciation_adjustment
        amti += self.amt_adj.investment_interest_adjustment
        amti += self.amt_adj.passive_activity_adjustment

        # Subtract tax refunds (negative adjustment)
        amti -= self.amt_adj.tax_refunds

        return max(0, amti)

    def _calculate_tentative_minimum_tax(self, amti: float) -> float:
        """
        Calculate tentative minimum tax.

        Formula:
        1. Calculate AMT exemption (with phase-out)
        2. Subtract exemption from AMTI to get taxable excess
        3. Apply AMT rates (26% up to threshold, 28% above)
        """
        # Calculate AMT exemption with phase-out
        base_exemption = self.config.amt_exemption[self.taxpayer.filing_status]
        phaseout_start = self.config.amt_phaseout_start[self.taxpayer.filing_status]

        if amti > phaseout_start:
            phaseout_amount = (amti - phaseout_start) * self.config.amt_phaseout_rate
            exemption = max(0, base_exemption - phaseout_amount)
        else:
            exemption = base_exemption

        # Calculate taxable excess
        taxable_excess = max(0, amti - exemption)

        # Apply AMT rates
        rate_threshold = self.config.amt_rate_threshold[self.taxpayer.filing_status]

        if taxable_excess <= rate_threshold:
            amt_tax = taxable_excess * self.config.amt_rate_low
        else:
            amt_tax = (rate_threshold * self.config.amt_rate_low +
                      (taxable_excess - rate_threshold) * self.config.amt_rate_high)

        return amt_tax

    def _calculate_niit(self, agi: float) -> float:
        """
        Calculate Net Investment Income Tax (NIIT).

        3.8% tax on the lesser of:
        1. Net investment income, OR
        2. MAGI in excess of threshold
        """
        threshold = self.config.niit_threshold[self.taxpayer.filing_status]

        # Calculate net investment income. Qualified dividends are already
        # included in ordinary dividends, so they are not added separately.
        net_investment_income = (
            self.income.interest +
            self.income.ordinary_dividends +
            self.income.short_term_capital_gains +
            self.income.long_term_capital_gains +
            self.income.rental  # Passive rental income
        )

        # MAGI for most taxpayers equals AGI
        magi = agi

        # Calculate NIIT
        if magi <= threshold:
            return 0.0

        excess_magi = magi - threshold
        niit_base = min(net_investment_income, excess_magi)

        return niit_base * self.config.niit_rate

    def _calculate_additional_medicare_tax(self) -> float:
        """
        Calculate Additional Medicare Tax (0.9% on wages/SE income above threshold).
        """
        threshold = self.config.medicare_threshold[self.taxpayer.filing_status]

        # Calculate wages and self-employment income subject to Medicare tax
        medicare_income = self.income.wages_w2 + self.income.self_employment * 0.9235

        if medicare_income <= threshold:
            return 0.0

        excess_income = medicare_income - threshold
        return excess_income * self.config.medicare_additional_rate

    def _calculate_california_taxable_income(self, agi: float) -> float:
        """
        Calculate California taxable income.

        California standard deduction is lower than federal.
        California does not allow SALT deduction.
        """
        ca_standard = self.config.ca_standard_deductions[self.taxpayer.filing_status]

        # Recalculate itemized deductions for California (excluding SALT)
        ca_itemized = 0.0

        # Medical expenses (same floor as federal)
        medical_floor = agi * self.config.medical_expense_floor
        ca_itemized += max(0, self.itemized.medical_dental_expenses - medical_floor)

        # Mortgage interest
        ca_itemized += self.itemized.mortgage_interest
        ca_itemized += self.itemized.mortgage_points

        # Charitable contributions (same limits as federal)
        cash_limit = agi * self.config.charitable_cash_limit
        cash_total = (
            self.itemized.cash_contributions_50pct_orgs +
            self.itemized.cash_contributions_other +
            self.itemized.donor_advised_fund_contributions
        )
        ca_itemized += min(cash_total, cash_limit)

        noncash_limit = agi * self.config.charitable_noncash_limit
        ca_itemized += min(self.itemized.noncash_contributions, noncash_limit)

        # Other deductions
        ca_itemized += self.itemized.casualty_theft_losses
        ca_itemized += self.itemized.gambling_losses

        # Use larger of standard or itemized deduction
        ca_deduction = max(ca_standard, ca_itemized)

        return max(0, agi - ca_deduction)

    def _calculate_california_tax(self, taxable_income: float) -> float:
        """
        Calculate California state income tax.

        California taxes ALL income (including capital gains) as ordinary income
        at progressive rates from 1% to 12.3%.
        """
        brackets = self.config.ca_brackets[self.taxpayer.filing_status]
        tax = 0.0
        previous_bracket = 0

        for bracket_top, rate in brackets:
            if taxable_income <= previous_bracket:
                break

            taxable_in_bracket = min(taxable_income, bracket_top) - previous_bracket
            tax += taxable_in_bracket * rate
            previous_bracket = bracket_top

        return tax

    def _calculate_california_sdi(self) -> float:
        """
        Calculate California State Disability Insurance (SDI).

        As of 2024, there is no wage cap - all wages are subject to SDI.
        Rate is configured in TaxConfig (1.1% for 2024, 1.2% for 2025)
        """
        # SDI applies only to W-2 wages, not self-employment income
        return self.income.wages_w2 * self.config.ca_sdi_rate

    def generate_summary_report(self, results: TaxResults) -> str:
        """
        Generate a human-readable summary report of tax calculations.
        """
        filing_status_name = self.taxpayer.filing_status.value.replace('_', ' ').title()

        report = f"""
{'='*80}
TAX CALCULATION SUMMARY - TAX YEAR {self.config.tax_year}
{'='*80}

TAXPAYER INFORMATION:
  Filing Status: {filing_status_name}
  Age: {self.taxpayer.primary.age} (Primary)
  Dependents: {self.taxpayer.num_dependents}

{'='*80}
INCOME SUMMARY
{'='*80}

  Wages (W-2):                               ${self.income.wages_w2:>15,.2f}
  Interest Income:                           ${self.income.interest:>15,.2f}
  Dividends (Qualified):                     ${self.income.qualified_dividends:>15,.2f}
  Dividends (Ordinary):                      ${self.income.ordinary_dividends:>15,.2f}
  Short-Term Capital Gains:                  ${self.income.short_term_capital_gains:>15,.2f}
  Long-Term Capital Gains:                   ${self.income.long_term_capital_gains:>15,.2f}
  Self-Employment Income:                    ${self.income.self_employment:>15,.2f}
  Rental Income:                             ${self.income.rental:>15,.2f}
  Other Income:                              ${self.income.other:>15,.2f}
                                             {'-'*30}
  TOTAL GROSS INCOME:                        ${results.gross_income:>15,.2f}

  Adjusted Gross Income (AGI):               ${results.agi:>15,.2f}

{'='*80}
DEDUCTIONS
{'='*80}

  Standard Deduction:                        ${results.standard_deduction:>15,.2f}
  Itemized Deductions:                       ${results.itemized_deductions:>15,.2f}

  Using: {'ITEMIZED' if results.used_itemized else 'STANDARD'} Deduction
  Deduction Amount:                          ${results.deduction_used:>15,.2f}

  Taxable Income:                            ${results.taxable_income:>15,.2f}

{'='*80}
FEDERAL TAX CALCULATION
{'='*80}

  Regular Income Tax:                        ${results.federal_income_tax:>15,.2f}
  Capital Gains Tax (LTCG + Qual Div):       ${results.capital_gains_tax:>15,.2f}
                                             {'-'*30}
  Total Regular Tax:                         ${results.total_federal_regular_tax:>15,.2f}

  Alternative Minimum Tax (AMT):
    AMT Taxable Income (AMTI):               ${results.amt_taxable_income:>15,.2f}
    Tentative Minimum Tax:                   ${results.tentative_minimum_tax:>15,.2f}
    AMT Owed:                                ${results.amt_owed:>15,.2f}

  Net Investment Income Tax (3.8%):          ${results.niit_owed:>15,.2f}
  Additional Medicare Tax (0.9%):            ${results.additional_medicare_tax:>15,.2f}
                                             {'-'*30}
  TOTAL FEDERAL TAX:                         ${results.total_federal_tax:>15,.2f}

  Effective Federal Rate:                    {results.effective_federal_rate*100:>14,.2f}%

{'='*80}
CALIFORNIA TAX CALCULATION
{'='*80}

  California Income Tax:                     ${results.california_income_tax:>15,.2f}
  Mental Health Services Tax (1%):           ${results.california_mental_health_tax:>15,.2f}
  State Disability Insurance (SDI):          ${results.california_sdi:>15,.2f}
                                             {'-'*30}
  TOTAL CALIFORNIA TAX:                      ${results.total_california_tax:>15,.2f}

  Effective California Rate:                 {results.effective_california_rate*100:>14,.2f}%

{'='*80}
TOTAL TAX LIABILITY
{'='*80}

  Total Federal Tax:                         ${results.total_federal_tax:>15,.2f}
  Total California Tax:                      ${results.total_california_tax:>15,.2f}
                                             {'='*30}
  TOTAL TAX LIABILITY:                       ${results.total_tax_liability:>15,.2f}

  Combined Effective Tax Rate:               {results.effective_total_rate*100:>14,.2f}%

{'='*80}
"""
        return report


# Convenience class: TaxCalculator2024 is a TaxCalculator that defaults to 2024 config
class TaxCalculator2024(TaxCalculator):
    """
    Tax calculator for 2024 tax year.

    This is a convenience wrapper around TaxCalculator that defaults to the
    2024 configuration. For new code, use TaxCalculator directly with an
    optional config parameter.
    """
    def __init__(self, taxpayer_info: TaxUnit,
                 itemized_deductions: ItemizedDeductions, amt_adjustments: AMTAdjustments = None,
                 use_2025_sdi_rate: bool = False):
        """
        Initialize tax calculator for 2024.

        Args:
            taxpayer_info: TaxUnit containing filing status, people, and income
            itemized_deductions: Itemized deduction amounts by category
            amt_adjustments: AMT-specific adjustments (optional)
            use_2025_sdi_rate: Use 2025 California SDI rate (1.2%) instead of 2024 rate (1.1%)
        """
        config = const.get_tax_config_2024()
        if use_2025_sdi_rate:
            config.ca_sdi_rate = const.CA_SDI_RATE_2025

        super().__init__(taxpayer_info, itemized_deductions, amt_adjustments, config)
