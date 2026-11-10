# Private law pack example

This directory is a template for keeping your parameters and rule wiring
outside the public `taxcalc` package.

It is **illustrative and not authoritative**. The values are the example
values, not reviewed tax law. The pack is deliberately marked
`authoritative=False`, so using it emits a warning.

## Layout

```
private_law/
  __init__.py     # makes this directory a package
  params.py       # your parameter catalog
  rules.py        # your RuleSet wiring
  pack.py         # PACK = LawPack(...)
```

`pack.py` is the only entry point. Its module-level `PACK` is what
`taxcalc.load_pack` looks for; there is no registry and no `register()` call.

## Run the demo

From the repository root:

```bash
python examples/private_law_demo.py
```

The demo loads `private_law.pack`, builds 2024 income and NIIT policies, runs
`compute_return`, and prints the pack identity, AGI, and tax parts. It also
prints the expected non-authoritative warning.

## Use it from a notebook

Put the parent directory on `sys.path`, then load by dotted path:

```python
import sys
sys.path.insert(0, "/path/to/examples")

from taxcalc import build_policy, compute_return, load_pack

pack = load_pack("private_law.pack")
policies = {
    "income": build_policy("federal", "income", 2024, pack=pack),
    "niit": build_policy("federal", "niit", 2024, pack=pack),
}
result = compute_return(unit, policies, pack=pack)
```

Every entry point takes `pack=` explicitly. The pack you pass is the only law
used for that call; the package never falls back to the example pack.

## Make it genuinely private

This copy is in the public repo as a template. For your real data:

1. Copy `private_law/` to a directory outside the repository, for example
   `~/taxlaw/private_law/`.
2. Keep that directory out of version control. If you ever place it inside the
   repo, add it to `.gitignore`.
3. Put its parent directory on `PYTHONPATH`, or add it to `sys.path` in your
   notebook.
4. Load it with `load_pack("private_law.pack")`.

Nothing about your income or assumptions needs to enter the public package.

## Checklist before setting `authoritative=True`

- [ ] Replace the illustrative values in `params.py` with reviewed figures.
- [ ] Add every filing-status selector you actually use.
- [ ] Add every parameter the selected rules read (missing ones raise
      `MissingParameterError`).
- [ ] Update `RULE_SETS` so its effective range covers the year(s) you compute.
      Add a new rule set instead of editing an old one when the logic changes.
- [ ] Set `provenance` to the sources and review date.
- [ ] Change `authoritative=False` to `authoritative=True`.

The `authoritative` flag is a promise, not an automatic check. Only set it
after the values have actually been reviewed.
