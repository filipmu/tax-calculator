"""The example private pack.

The module-level ``PACK`` is the only "registration" needed.  Load it with::

    from taxcalc import load_pack
    pack = load_pack("private_law.pack")

This template is deliberately ``authoritative=False``, so using it emits a
warning.  After replacing the values with reviewed figures and confirming the
provenance, set ``authoritative=True``.
"""

from taxcalc import LawPack
from taxcalc.pipeline import federal_combine
from taxcalc.rules.mn_rules import compute_mn_tax
from taxcalc.rules.niit_rules import compute_niit

from .params import PARAMETERS
from .rules import RULE_SETS

PACK = LawPack(
    name="private-law-example",
    authoritative=False,
    provenance=(
        "Example template. Replace these illustrative values with reviewed "
        "figures, then set authoritative=True."
    ),
    catalog=PARAMETERS,
    rule_sets=RULE_SETS,
    addon_taxes={"niit": compute_niit, "MN": compute_mn_tax},
    combiners={"federal": federal_combine},
)
