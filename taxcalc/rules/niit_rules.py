from ..models import TaxUnit, Policy
from ..params import param


def compute_niit(unit: TaxUnit, policy: Policy, agi: float) -> float:
    """Net Investment Income Tax.

    3.8% of the lesser of net investment income and MAGI above the threshold.
    """
    rate = param(policy, "niit_rate")
    threshold = param(policy, "niit_threshold", unit.filing_status.value)

    # Qualified dividends are included in ordinary dividends, so they are not
    # added separately.
    net_investment_income = (
        unit.income.interest
        + unit.income.ordinary_dividends
        + unit.income.short_term_capital_gains
        + unit.income.long_term_capital_gains
        + unit.income.rental  # passive rental income
    )

    magi = agi  # MAGI equals AGI for this prototype

    if magi <= threshold:
        return 0.0

    return min(net_investment_income, magi - threshold) * rate
