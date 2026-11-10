"""Run the example private pack.

    python examples/private_law_demo.py

The pack is a template and is marked non-authoritative, so the guard emits a
warning.  The demo captures and prints it instead of letting it go to stderr.
"""

import sys
import warnings
from pathlib import Path

# Make the "private_law" package importable when this script is run directly,
# and make the repo root importable when taxcalc is not installed.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

from taxcalc import (
    FilingStatus,
    Income,
    Person,
    TaxUnit,
    build_policy,
    compute_return,
    load_pack,
)


def main() -> None:
    pack = load_pack("private_law.pack")

    unit = TaxUnit(
        filing_status=FilingStatus.SINGLE,
        primary=Person(age=40),
        income=Income(
            wages_w2=250_000,
            interest=10_000,
            long_term_capital_gains=50_000,
        ),
    )

    policies = {
        "income": build_policy("federal", "income", 2024, pack=pack),
        "niit": build_policy("federal", "niit", 2024, pack=pack),
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = compute_return(unit, policies, pack=pack)

    for item in caught:
        print(f"expected guard warning: {item.message}")

    print()
    print(f"pack:         {result.pack_name}")
    print(f"authoritative: {result.authoritative}")
    print(f"AGI:          {result.agi:,.2f}")
    print(f"income tax:   {result.parts['income']:,.2f}")
    print(f"NIIT:         {result.parts['niit']:,.2f}")
    print(f"total:        {result.total_tax:,.2f}")


if __name__ == "__main__":
    main()
