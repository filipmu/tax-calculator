"""Law packs: the boundary between the calculator and a set of tax law.

The package contains the machinery (parameters, rules, pipeline) and one
*example* pack with illustrative values.  A law pack is the container that
supplies the actual numbers and rule wiring.

A pack is deliberately a plain, explicit object: pass it where you need it.

    from taxcalc import build_policy, compute_return, load_pack

    my_pack = load_pack("my_private_tax_law.pack")
    policy = build_policy("federal", "income", 2025, pack=my_pack)
    result = compute_return(unit, {"income": policy}, pack=my_pack)

There is no global "active pack" and no fallback between packs: a pack you
pass is the only law used for that call.

.. warning::
   The example pack shipped with this package is **illustrative only**.  It is
   not authoritative, is not tax advice, and must not be used to file a return.
   Any pack that is not marked ``authoritative`` triggers a warning when used.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Mapping, Tuple

from .models import Policy, TaxResult, TaxUnit

# Catalog keys and rule keys, kept here so the pack does not import the
# registries (which would create an import cycle).
ParamKey = Tuple[str, str, str]   # (jurisdiction, tax, parameter name)
RuleKey = Tuple[str, str]         # (jurisdiction, tax)

AddonTax = Callable[[TaxUnit, Policy, TaxResult], float]
Combiner = Callable[[Mapping[str, float]], float]


@dataclass(frozen=True)
class LawPack:
    """One self-contained set of tax parameters and rules.

    ``catalog`` and ``rule_sets`` use the same shapes as ``params.PARAMETERS``
    and ``rules.rulesets.RULE_SETS``.  They are typed loosely on purpose so a
    private pack can define its own data without importing package internals.
    """

    name: str
    authoritative: bool
    provenance: str
    catalog: Mapping[ParamKey, Any]
    rule_sets: Mapping[RuleKey, Any]
    addon_taxes: Mapping[str, AddonTax]
    combiners: Mapping[str, Combiner]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("LawPack.name must be a non-empty string")
        if not isinstance(self.authoritative, bool):
            raise TypeError("LawPack.authoritative must be a bool")
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise ValueError("LawPack.provenance must be a non-empty string")

        for attribute in ("catalog", "rule_sets", "addon_taxes", "combiners"):
            if not isinstance(getattr(self, attribute), Mapping):
                raise TypeError(f"LawPack.{attribute} must be a mapping")

        for tax, function in self.addon_taxes.items():
            if not callable(function):
                raise TypeError(
                    f"LawPack.addon_taxes[{tax!r}] must be callable"
                )
        for jurisdiction, function in self.combiners.items():
            if not callable(function):
                raise TypeError(
                    f"LawPack.combiners[{jurisdiction!r}] must be callable"
                )


def load_pack(dotted_path: str) -> LawPack:
    """Import ``dotted_path`` and return its module-level ``PACK``.

    This is how a private pack that lives outside the package is reached:

        PACK = LawPack(...)   # in my_private_tax_law/pack.py

    The module is imported normally, so it can import ``taxcalc``.
    """
    module = import_module(dotted_path)
    pack = getattr(module, "PACK", None)
    if pack is None:
        raise AttributeError(
            f"module {dotted_path!r} does not define a module-level PACK"
        )
    if not isinstance(pack, LawPack):
        raise TypeError(
            f"{dotted_path}.PACK must be a LawPack, got "
            f"{type(pack).__name__}"
        )
    return pack


def default_pack() -> LawPack:
    """Return the illustrative pack shipped with the package.

    Imported lazily because the example pack itself imports the rules and
    pipeline modules.
    """
    from .example_pack import EXAMPLE_PACK

    return EXAMPLE_PACK
