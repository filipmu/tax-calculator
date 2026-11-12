from ..models import Policy, TaxResult, TaxUnit
from ..params import param


def compute_niit(unit: TaxUnit, policy: Policy, income_result: TaxResult) -> float:
    """Net Investment Income Tax.

    3.8% of the lesser of net investment income and MAGI above the threshold.

    Net investment income uses net capital gains, not the net capital loss
    deducted on the return: a capital loss does not reduce NII (Form 8960
    ignores net capital losses).  Qualified dividends are included in ordinary
    dividends, so they are not added separately.
    """
    rate = param(policy, "niit_rate")
    threshold = param(policy, "niit_threshold", unit.filing_status.value)

    capital = income_result.capital_gains
    if capital is None:
        raise ValueError(
            "compute_niit requires an income result with capital gain detail"
        )

    net_capital_gain = max(0.0, capital.net_short_term) + max(
        0.0, capital.net_long_term
    )

    # Rental income is folded into other_sched_1 and is not separable here.
    net_investment_income = (
        unit.income.taxable_interest
        + unit.income.ordinary_dividends
        + net_capital_gain
    )

    magi = income_result.agi  # MAGI equals AGI for this prototype

    if magi <= threshold:
        return 0.0

    return min(net_investment_income, magi - threshold) * rate
