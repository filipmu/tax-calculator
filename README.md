# taxcalc — prototype

> **Not tax advice.** This is a modelling prototype, not a filing tool. The
> tax-law data shipped with the package is **illustrative and not
> authoritative**. Do not use it to file a return or to make tax decisions.
> Verify every figure against official IRS/state guidance. Results record the
> name of the law pack that produced them; a pack that is not marked
> authoritative is not suitable for filing.

## Credit and provenance

This repository is a fork of
[blackace007-cmd/tax-calculator](https://github.com/blackace007-cmd/tax-calculator),
originally published by Azhar as *Tax Calculator Package v1.1.0*. The legacy
calculator, its constants, and the original examples come from that project.

The versioned parameter/rule engine, the per-tax pipeline, and the law-pack
boundary described below are additions in this fork. The new work lives on the
`proto2` branch.

## What this fork is

The upstream project is a broad federal + California calculator. This fork is a
smaller experiment in **maintainable, year-versioned tax logic**:

- Reusable rules and parameters across tax years.
- No silent carry-forward: a missing year raises an error.
- A clean boundary between the calculator (public) and the tax law (private).
- Partial coverage by design; anything not implemented fails loudly.

## What is different from upstream

### Versioned parameters

Each parameter is a list of dated versions keyed by
`(jurisdiction, tax, parameter_name)`:

```python
yearly(2024, {...})   # effective only for 2024
since(2013, {...})    # effective from 2013 until amended
```

`build_policy("federal", "income", 2024)` resolves the catalog into a `Policy`
of plain values. If no version covers the year, or two overlap, it raises; there
is no fallback.

### Per-tax policies

A `Policy` is one tax for one year (`income`, `niit`, ...), not a whole return.
This keeps parameters, rules, and results aligned with a single tax.

### Effective-dated rule sets

A `RuleSet` is a snapshot of the four income-tax steps — AGI, taxable income,
pre-credit tax, and credits. One rule set can cover several years; changing the
law means adding a new snapshot and ending the old one, never editing history.

### One return pipeline

`compute_return(unit, policies)` computes AGI once, runs each tax, and combines
the parts. `compute_tax(unit, policy)` remains as a single-tax convenience
wrapper.

### Law packs: private law, public engine

A `LawPack` bundles everything year-specific:

- parameter catalog
- rule sets
- add-on taxes (e.g. NIIT)
- combiners

The package ships one **illustrative** pack, `EXAMPLE_PACK`. Your own
parameters and rules can live entirely outside the package and be loaded
explicitly:

```python
from taxcalc import build_policy, compute_tax, load_pack

pack = load_pack("my_private_law.pack")   # module outside this package
policy = build_policy("federal", "income", 2024, pack=pack)
result = compute_tax(unit, policy, pack=pack)
```

There is no global active pack and no fallback between packs: the pack you pass
is the only law used for that call. That keeps private data out of the public
repository and prevents example values from leaking into a real calculation.

Using a non-authoritative pack emits a warning, and `ReturnResult` carries
`pack_name`, `authoritative`, and `provenance` alongside the numbers.

A runnable template lives in
[`examples/private_law/`](examples/private_law/README.md); run
`python examples/private_law_demo.py` to see the whole flow.

## Coverage

The calculator refuses to guess. If a populated input is not fully modeled,
`compute_return` reports it:

- **warning** — the input is included but only partly modeled (for example,
  `other_sched_1` is taxed as ordinary income, but self-employment tax and QBI
  are not computed);
- **error** — the input is ignored entirely. With the default
  `coverage="raise"`, an error stops the calculation.

Issues are also returned on `ReturnResult.coverage`, so a notebook can annotate
each scenario instead of parsing warnings. Pass `coverage="warn"` to compute
despite errors, or `coverage="off"` to suppress the checks in tight loops.

Capital loss carryforwards follow the same rule: they are inputs, not state.
Feed last year's `TaxResult.capital_gains` values back in; nothing is mutated
or remembered.

## Current coverage

| Area | Status |
|---|---|
| Federal income tax | Tax years 2023–2024, illustrative values |
| Capital gains and losses | Short/long-term netting, `$3,000` loss limit (`$1,500` MFS), 0/15/20% rates on gains and qualified dividends |
| Capital loss carryforward | Entered as an input (`Income.*_capital_loss_carryforward`); reported back on `TaxResult.capital_gains`; no state is kept |
| Itemized deductions | `TaxUnit.itemized` adds Schedule A amounts. Medical 7.5%-of-AGI floor, SALT cap (including the 2025+ phase-down), mortgage interest as entered, charitable 60%-of-AGI limit with the 2026+ 0.5% floor, and the 2026+ section 68 2/37 limitation. The larger of standard and itemized is used. |
| Net Investment Income Tax (NIIT) | Parameters since 2013; used with 2023–2024 income |
| Minnesota income tax | Form M1 from federal AGI: MN standard deduction with the high-income limitation, dependent exemptions with phase-out, and the U.S. government interest subtraction. Example values for 2023–2024; a private pack can add later years. MN itemized deductions (M1SA), the Social Security subtraction, additions, AMT, and credits are not modeled and are flagged. |
| Add-on taxes | Pluggable through a law pack (`niit` and `MN` are wired in the example) |
| Coverage checks | Populated inputs that are only partly modeled are listed on `ReturnResult.coverage` and emitted as warnings |
| AMT | Legacy calculator only; future work in the new engine (flagged by a coverage warning) |
| California state tax | Legacy calculator only |
| Missing year / parameter | Raises `NoEffectiveVersionError` or `MissingParameterError` |
| Inputs | Flat dataclasses with defaults (`TaxUnit`, `Income`, `Person`) |

## Quick start

```python
from taxcalc import (
    FilingStatus,
    Income,
    Person,
    TaxUnit,
    build_policy,
    compute_tax,
)

unit = TaxUnit(
    filing_status=FilingStatus.SINGLE,
    primary=Person(age=40),
    income=Income(wages_w2=100_000),
)

result = compute_tax(unit, build_policy("federal", "income", 2024))
print(result.net_tax)
```

Because the example pack is not authoritative, this prints a warning. That is
intentional.

Multiple taxes on one return:

```python
from taxcalc import build_policy, compute_return

policies = {
    "income": build_policy("federal", "income", 2024),
    "niit": build_policy("federal", "niit", 2024),
    "MN": build_policy("MN", "income", 2024),
}
result = compute_return(unit, policies)
print(result.parts["niit"], result.parts["MN"], result.total_tax)
print(result.detail["MN"].mn_taxable_income)
```

Minnesota is an add-on tax keyed by `"MN"` in the policy mapping. Its rule
receives the federal AGI from the income result and reports an `MNResult` in
`ReturnResult.detail["MN"]`.

## Repository layout

```
taxcalc/
  models.py          # TaxUnit, Income, Person, Policy, Parameter, results
  params.py          # parameter catalog, build_policy, resolver, errors
  rules/
    base_rules.py    # AGI -> taxable income -> pre-credit tax -> credits
    capital_gain_rules.py  # Schedule D netting and the capital-loss limit
    deduction_rules.py     # Schedule A: itemized deductions and limits
    mn_rules.py      # Minnesota Form M1 income tax
    niit_rules.py    # Net Investment Income Tax
    rulesets.py      # RuleSet and the example rule registry
  coverage.py        # input coverage checks (warn or stop)
  pipeline.py        # compute_return / compute_tax / combiners
  pack.py            # LawPack and load_pack
  example_pack.py    # EXAMPLE_PACK (illustrative, non-authoritative)
  calculator.py      # legacy calculator (upstream)
  constants.py       # legacy constants and TaxConfig data
examples/
  Test policy data changes.ipynb
  private_law/        # template for a private pack (params, rules, PACK)
  private_law_demo.py # runnable demo of the private pack
  examples-old/       # upstream legacy notebooks and scripts
ADDING_A_TAX_YEAR.md
test_proto2.py
test_installation.py
```

## Legacy calculator

`TaxCalculator`, `TaxCalculator2024`, and `TaxConfig` are kept for
compatibility with the upstream project. They use `constants.py` directly and
do **not** use the new parameter catalog or law packs. The new engine does not
depend on them.

## Tests

```bash
python3 test_proto2.py        # new engine: parameters, rules, packs, pipeline
python3 test_installation.py  # legacy calculator still imports and runs
```

`test_proto2.py` currently covers parameter resolution, missing/overlapping
years, the per-tax pipeline, capital-gain netting and 0/15/20% rates, the
capital-loss limit and carryforward round trip, NIIT, itemized deductions,
Minnesota income tax (including the Treasury subtraction, deduction limitation,
and exemption phase-out), coverage checks, law-pack identity and warnings, pack
replacement (no leakage), pluggable add-on taxes, and `load_pack`.

## Documentation

- [`ADDING_A_TAX_YEAR.md`](ADDING_A_TAX_YEAR.md) — step-by-step guide to adding
  a tax year when parameters and rules change, including where private law data
  lives.
- [`examples/private_law/README.md`](examples/private_law/README.md) — a
  runnable private-pack template and a checklist for making it authoritative.
- Module docstrings in `taxcalc/pack.py` and `taxcalc/example_pack.py` — the
  law-pack contract and the private-pack template.

## Status and next steps

This is a prototype. Deliberately out of scope for now:

- Federal and Minnesota AMT in the new engine.
- Minnesota itemized deductions (Schedule M1SA) and the remaining Schedule M1M
  additions and subtractions.
- Minnesota nonrefundable credits.
- California state tax in the new engine.
- Full tax-code coverage; only what is needed is implemented.
- Versioning the `TaxUnit`/`Income` input schema by year (inputs are facts, not
  law).

Likely next steps: add more tax years and golden per-year regression tests,
extend coverage as needed, and keep the law-pack boundary small.

## License

The upstream project is MIT-licensed. This fork follows the same license; see
the upstream repository for the original terms.
