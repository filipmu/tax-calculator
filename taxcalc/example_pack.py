"""The illustrative law pack shipped with the package.

This is the only tax-law data included in the public package.  The values are
simplified and reviewed only enough to demonstrate the mechanics.  They are
**not authoritative, not tax advice, and not suitable for filing**.

Use it as a template for a private pack: create a module outside this package
that builds a ``LawPack`` (its own ``PARAMETERS``, rule sets, add-on taxes and
combiners) and exposes it as ``PACK``.  Then load it with
``taxcalc.load_pack("your.module")``.
"""

from .pack import LawPack
from .params import PARAMETERS
from .pipeline import COMBINERS
from .rules.mn_rules import compute_mn_tax
from .rules.niit_rules import compute_niit
from .rules.rulesets import RULE_SETS

EXAMPLE_PACK = LawPack(
    name="example-illustrative",
    authoritative=False,
    provenance=(
        "Illustrative prototype values (2023-2024). "
        "Not authoritative, not tax advice, not for filing."
    ),
    catalog=PARAMETERS,
    rule_sets=RULE_SETS,
    addon_taxes={"niit": compute_niit, "MN": compute_mn_tax},
    combiners=COMBINERS,
)

# The module-level name required by taxcalc.load_pack().
PACK = EXAMPLE_PACK
