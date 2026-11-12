"""Schedule D netting and the capital-loss limit.

The calculator holds **no carryforward state**.  Losses disallowed in earlier
years are input facts on ``Income`` and the losses that remain at the end of the
year travel back out on ``CapitalGainDetail`` for the caller to use next year.

Netting follows the Schedule D / Capital Loss Carryover Worksheet order:

1. Add each character's carry-in to its current-year amount.
2. Offset short-term against long-term when the signs differ.
3. Deduct a net loss up to the annual limit (``$3,000``, ``$1,500`` MFS).
4. Carry the remainder forward, preserving its character.
"""

from ..models import CapitalGainDetail, Policy, TaxUnit
from ..params import param


def capital_loss_limit(unit: TaxUnit, policy: Policy) -> float:
    """Annual limit on the net capital loss deducted against other income."""
    return param(policy, "capital_loss_limit", unit.filing_status.value)


def compute_capital_gains(unit: TaxUnit, policy: Policy) -> CapitalGainDetail:
    """Net current-year gains against carry-in losses.

    ``unit.income`` holds signed current-year gains and positive carry-in
    loss amounts.  Nothing is written back to the unit.
    """
    income = unit.income

    net_short = (
        income.short_term_capital_gain_loss
        - income.short_term_capital_loss_carryforward
    )
    net_long = (
        income.long_term_capital_gain_loss
        - income.long_term_capital_loss_carryforward
    )

    # Step 2: offset opposite signs.  Afterwards at most one character is
    # negative, and the other is zero or positive.
    if net_short > 0 and net_long < 0:
        offset = min(net_short, -net_long)
        net_short -= offset
        net_long += offset
    elif net_long > 0 and net_short < 0:
        offset = min(net_long, -net_short)
        net_long -= offset
        net_short += offset

    ordinary_gain = max(0.0, net_short)
    long_term_gain = max(0.0, net_long)

    allowed_loss = 0.0
    carryforward_short = 0.0
    carryforward_long = 0.0

    total = net_short + net_long
    if total < 0:
        short_loss = max(0.0, -net_short)
        long_loss = max(0.0, -net_long)
        allowed_loss = min(
            short_loss + long_loss, capital_loss_limit(unit, policy)
        )
        remaining = max(0.0, short_loss + long_loss - allowed_loss)

        # Capital Loss Carryover Worksheet: the short-term carryover is
        # min(short-term loss, remaining), so the allowed deduction is applied
        # to the long-term loss first and short-term losses are preserved.
        carryforward_short = min(short_loss, remaining)
        carryforward_long = remaining - carryforward_short

    return CapitalGainDetail(
        net_short_term=net_short,
        net_long_term=net_long,
        ordinary_capital_gain=ordinary_gain,
        preferential_income=long_term_gain + income.qualified_dividends,
        allowed_loss=allowed_loss,
        carryforward_short_term=carryforward_short,
        carryforward_long_term=carryforward_long,
    )
