# Adding a New Tax Year to the Proto2 Tax Calculator

This guide is for the `proto2` prototype. It walks through adding a new tax
year when **some parameters change and a rule also changes**, using 2025 as the
worked example. No deep OO knowledge is assumed.

---

## The mental model (read this once)

There are two kinds of things in the prototype, and they are versioned
separately:

| Kind | What it is | Example | Where it lives |
|---|---|---|---|
| **Parameter** | A number from the tax code | standard deduction, brackets | `taxcalc/params.py` |
| **Rule** | The logic that uses numbers | how taxable income is computed | `taxcalc/rules/rulesets.py` |
| **Policy** | One tax for one year, with resolved numbers | federal income 2025 | built by `build_policy(...)` |
| **Pipeline** | Runs each tax and combines them | income + NIIT | `taxcalc/pipeline.py` |

Every parameter version and every rule set has an **effective date range**:
`(start, end)`. A version applies to tax year `Y` if its range contains
**31 December of `Y`**.

There is **no fallback**. If no version is effective, or two versions overlap,
you get an error. That is deliberate: it is better to stop than to compute with
the wrong year's law.

Two useful conventions:

- `yearly(2025, {...})` = effective only for 2025.
- `since(2025, {...})` = effective from 2025 until amended.

---

## Where the law data lives (law packs)

The package ships one **law pack**, `EXAMPLE_PACK` in
`taxcalc/example_pack.py`. Its numbers are in `taxcalc/params.py` and its rule
wiring is in `taxcalc/rules/rulesets.py`. It is illustrative and **not
authoritative**; using it emits a warning.

Private parameters and rules live in a separate module outside the package:

```python
# my_private_law/pack.py
from taxcalc import LawPack
from taxcalc.pipeline import federal_combine
from taxcalc.rules.niit_rules import compute_niit

from .params import PARAMETERS      # your own catalog
from .rules import RULE_SETS        # your own rule wiring

PACK = LawPack(
    name="my-private-law",
    authoritative=True,
    provenance="My reviewed assumptions, 2026-11-10.",
    catalog=PARAMETERS,
    rule_sets=RULE_SETS,
    addon_taxes={"niit": compute_niit},
    combiners={"federal": federal_combine},
)
```

Then pass it explicitly at every entry point:

```python
from taxcalc import build_policy, compute_return, load_pack

pack = load_pack("my_private_law.pack")
policy = build_policy("federal", "income", 2025, pack=pack)
result = compute_return(unit, {"income": policy}, pack=pack)
```

There is no global active pack and no fallback: the pack you pass is the only
law used for that call. This guide edits `taxcalc/params.py` and
`taxcalc/rules/` because that is where the example pack lives; with a private
pack, make the same edits in your own modules.

---

## Step 1 — Decide what changed

Ask two questions:

1. **Did a number change?** → edit `taxcalc/params.py` (Step 2).
2. **Did the logic change?** → edit `taxcalc/rules/` and `rulesets.py` (Step 3).

If only numbers changed, stop after Step 2. If only logic changed, skip Step 2.
If both changed, do both.

The 2025 example below does both:

- **Numbers:** the 2025 standard deduction and brackets differ from 2024.
- **New parameters:** a standard-deduction phase-out starts in 2025.
- **Rule change:** starting in 2025, the standard deduction is reduced for
  high-AGI taxpayers.

> The 2025 values below are **illustrative**. Replace them with the official
> IRS Revenue Procedure (and FTB guidance for California) before relying on
> them.

---

## Step 2 — Update the parameter catalog

File: `taxcalc/params.py`

The catalog is one big dictionary. Each key is
`(jurisdiction, tax, parameter name)` and each value is a **list of versions**:

```python
PARAMETERS = {
    ("federal", "income", "standard_deduction"): [
        yearly(2023, {...}),
        yearly(2024, {...}),
    ],
    ...
}
```

### 2a. Add a version for every `yearly` parameter

Look at every `yearly(...)` entry for the tax you are updating. Each one needs a
new version for 2025, because its range currently ends on 2024-12-31.

**Standard deduction** — add the 2025 entry to the existing list:

```python
    ("federal", "income", "standard_deduction"): [
        yearly(2023, {
            "single": [13850],
            "married_joint": [27700],
            "married_separate": [13850],
            "head_of_household": [20800],
            "qualifying_widow": [27700],
        }),
        yearly(2024, {
            "single": [14600],
            "married_joint": [29200],
            "married_separate": [14600],
            "head_of_household": [21900],
            "qualifying_widow": [29200],
        }),
        yearly(2025, {                      # <-- ADD THIS
            "single": [15000],
            "married_joint": [30000],
            "married_separate": [15000],
            "head_of_household": [22500],
            "qualifying_widow": [30000],
        }),
    ],
```

**Brackets** — same idea. Brackets are lists of `(rate, upper_limit)` tuples,
rate first. Add a 2025 list for every filing status:

```python
    ("federal", "income", "brackets"): [
        yearly(2023, {...}),
        yearly(2024, {...}),
        yearly(2025, {                      # <-- ADD THIS
            "single": [
                (0.10, 11925),
                (0.12, 48475),
                (0.22, 103350),
                (0.24, 197300),
                (0.32, 250525),
                (0.35, 626350),
                (0.37, float("inf")),
            ],
            "married_joint": [
                (0.10, 23850),
                (0.12, 96950),
                (0.22, 206700),
                (0.24, 394600),
                (0.32, 501050),
                (0.35, 751600),
                (0.37, float("inf")),
            ],
            "married_separate": [
                (0.10, 11925),
                (0.12, 48475),
                (0.22, 103350),
                (0.24, 197300),
                (0.32, 250525),
                (0.35, 375800),
                (0.37, float("inf")),
            ],
            "head_of_household": [
                (0.10, 17000),
                (0.12, 64850),
                (0.22, 103350),
                (0.24, 197300),
                (0.32, 250500),
                (0.35, 626350),
                (0.37, float("inf")),
            ],
            "qualifying_widow": [
                (0.10, 23850),
                (0.12, 96950),
                (0.22, 206700),
                (0.24, 394600),
                (0.32, 501050),
                (0.35, 751600),
                (0.37, float("inf")),
            ],
        }),
    ],
```

### 2b. Parameters that do not change

You do **not** add a new version for `since(...)` parameters. For example:

```python
    ("federal", "income", "child_credit_amount"): [
        since(2023, {"default": [2000]}),      # still in force in 2025
    ],
    ("federal", "niit", "niit_rate"): [
        since(2013, {"default": [0.038]}),     # still in force in 2025
    ],
```

They already cover 2025.

**But** if a value used to be `yearly(2024)` and is unchanged in 2025, you still
need a `yearly(2025)` entry. `yearly` means *only this year*; a missing year is
an error, not a carry-forward.

### 2c. Add the new parameters for the rule change

The 2025 rule needs two numbers that did not exist before. Add them as new keys
at the end of `PARAMETERS`:

```python
    # Standard deduction phase-out (new in 2025)
    ("federal", "income", "standard_deduction_phaseout_start"): [
        since(2025, {"default": [500000]}),
    ],
    ("federal", "income", "standard_deduction_phaseout_rate"): [
        since(2025, {"default": [0.25]}),
    ],
```

Use `{"default": [...]}` for a value that is the same for every filing status.
Use a filing-status key (e.g. `"married_joint": [...]`) when the value differs.

**What happens in earlier years?** The new keys start in 2025, so a 2024 policy
simply does not contain them. It does not fail. Any rule that asks for them in
2024 would fail loudly with `MissingParameterError`, which is what you want.

### 2d. If a parameter is repealed

End its last range at the last year it applies:

```python
        yearly(2024, {...}),   # last year; do NOT add 2025
```

If the last version used `since(...)`, replace it with an explicit end date:

```python
    ("federal", "income", "some_repealed_parameter"): [
        Parameter(
            effective=(date(2013, 1, 1), date(2024, 12, 31)),
            value={...},
        ),
    ],
```

Make sure no 2025 rule still reads it, or you will get `MissingParameterError`.

### 2e. Check the catalog resolves

```python
from taxcalc import build_policy, param

policy_2025 = build_policy("federal", "income", 2025)
print(param(policy_2025, "standard_deduction", "married_joint"))  # 30000
print(param(policy_2025, "brackets", "married_joint"))
print(param(policy_2025, "standard_deduction_phaseout_start"))    # 500000
```

If you forgot a `yearly(2025)`, you will see something like:

```
NoEffectiveVersionError: federal/income/brackets: no version is effective for
tax year 2025. Available ranges: 2023-01-01..2023-12-31, 2024-01-01..2024-12-31
```

That message tells you exactly which parameter and which year to fix.

---

## Step 3 — Change a rule

Rules are plain functions in `taxcalc/rules/`. A **rule set** groups the four
income-tax functions into one snapshot:

```python
@dataclass(frozen=True)
class RuleSet:
    effective: Tuple[date, date]
    compute_agi: ...
    compute_taxable_income: ...
    compute_pre_credit_tax: ...
    compute_credits: ...
```

### 3a. Never edit an old rule in place

If you change `compute_taxable_income` directly, you silently change 2023 and
2024 results too. Historical years must keep their original logic. Instead:

1. Write a **new function** with a year or era in its name.
2. Put it in a **new RuleSet** whose effective range starts in 2025.
3. **Shorten the old RuleSet's range** so it ends in 2024.

### 3b. Write the new function

File: `taxcalc/rules/base_rules.py`

```python
def compute_taxable_income_2025(
    unit: TaxUnit, policy: Policy, agi: float
) -> float:
    """Standard deduction, reduced above a phase-out threshold."""
    std_ded = param(policy, "standard_deduction", unit.filing_status.value)

    phaseout_start = param(policy, "standard_deduction_phaseout_start")
    phaseout_rate = param(policy, "standard_deduction_phaseout_rate")

    if agi > phaseout_start:
        reduction = (agi - phaseout_start) * phaseout_rate
        std_ded = max(0.0, std_ded - reduction)

    return max(0.0, agi - std_ded)
```

Notice what it does **not** do: it contains no dollar amounts. All numbers come
from `param(...)`. That is what lets the same rule run for every year in its
range.

### 3c. Split the rule registry

File: `taxcalc/rules/rulesets.py`

Before:

```python
RULE_SETS = {
    ("federal", "income"): [
        RuleSet(
            effective=(date(2023, 1, 1), date(2025, 12, 31)),
            compute_agi=base_rules.compute_agi,
            compute_taxable_income=base_rules.compute_taxable_income,
            compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
            compute_credits=base_rules.compute_credits,
        ),
    ],
}
```

After:

```python
RULE_SETS = {
    ("federal", "income"): [
        # 2023-2024: original rules
        RuleSet(
            effective=(date(2023, 1, 1), date(2024, 12, 31)),
            compute_agi=base_rules.compute_agi,
            compute_taxable_income=base_rules.compute_taxable_income,
            compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
            compute_credits=base_rules.compute_credits,
        ),
        # 2025 onwards: same rules except taxable income
        RuleSet(
            effective=(date(2025, 1, 1), date.max),
            compute_agi=base_rules.compute_agi,
            compute_taxable_income=base_rules.compute_taxable_income_2025,
            compute_pre_credit_tax=base_rules.compute_pre_credit_tax,
            compute_credits=base_rules.compute_credits,
        ),
    ],
}
```

Key points:

- **Reuse** unchanged functions by referring to them again. Only the changed one
  is swapped.
- The old range must end `2024-12-31`. If both ranges cover 2025, import fails
  with `AmbiguousVersionError: overlapping effective ranges`.
- `date.max` means "in force until amended". That is an explicit statement, not
  a fallback. If you prefer to review the rule every year, use
  `(date(2025, 1, 1), date(2025, 12, 31))` and add another entry next year.
- A rule set is a **snapshot**: if any of the four functions changes, create a
  new rule set. Do not mix functions from different eras.

### 3d. A note on single-function taxes

NIIT is just one function (`compute_niit`) and does not use a `RuleSet` at all.
A `RuleSet` is only needed for the multi-step income-tax pipeline (AGI →
taxable income → pre-credit tax → credits). If a tax is a single computation,
call it directly from `compute_return`, as `compute_niit` is.

### 3e. If the new rule needs data it does not receive

The four income functions have fixed signatures:

```python
compute_agi(unit, policy)
compute_taxable_income(unit, policy, agi)
compute_pre_credit_tax(unit, policy, taxable_income)
compute_credits(unit, policy, pre_credit_tax)
```

`compute_credits` does **not** receive AGI. Adding AGI to the credit rule is a
change to the **shared call contract**, not just to the new function. Two things
are involved:

- **Logic is per-era.** The 2023-2024 `compute_credits` must keep doing exactly
  what it did. You do not rewrite its logic.
- **The call is shared.** `compute_return` calls one signature for every era.
  If that signature gains an argument, every function the pipeline can reach
  must accept it, even if the old ones ignore it.

If you change only the new function and the call, computing a prior year fails
with:

```
TypeError: compute_credits() takes 3 positional arguments but 4 were given
```

You have three options:

**Option 1 - compatibility signature (simplest).** Add `agi` to every
`compute_credits` and ignore it in the old ones. Behavior is unchanged, but you
touched old code:

```python
def compute_credits(unit, policy, pre_credit_tax, agi):
    ...  # 2023-2024 logic; does not use agi
```

**Option 2 - adapter (keeps old functions unchanged).** Leave the 2023-2024
function exactly as it is and add a small wrapper for the old RuleSet:

```python
def compute_credits_2023(unit, policy, pre_credit_tax, agi):
    # AGI is ignored; this preserves the original 2023-2024 behavior.
    return compute_credits(unit, policy, pre_credit_tax)
```

Point the old RuleSet at `compute_credits_2023` and the new one at
`compute_credits_2025`.

**Option 3 - context object (future-proof).** Pass one `context` value to all
four functions instead of individual values:

```python
@dataclass
class RuleContext:
    agi: float
    taxable_income: float
    pre_credit_tax: float

def compute_credits(unit, policy, context):
    ...
```

Adding another derived value later then never changes a signature. This is a
bigger one-time refactor of all four functions and `compute_return`.

Whichever option you choose, also update the `RuleSet` type annotation and the
call in `compute_return`:

```python
# RuleSet
compute_credits: Callable[[TaxUnit, Policy, float, float], float]

# compute_return
total_credits = rules.compute_credits(
    unit, income_policy, pre_credit_tax, agi
)
```

For proto2, **Option 1** is the least machinery. Consider Option 3 only if
signature changes become frequent; at four functions it is a modest refactor,
but not necessary yet.

---

## Step 4 — Add tests

File: `test_proto2.py`

Add tests next to the existing ones, and add each function name to the `tests`
list in `main()`.

```python
def test_income_2025() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2025))
    assert result.taxable_income == 570000.0
    assert result.pre_credit_tax == 138594.5
    assert result.net_tax == 134594.5


def test_2025_does_not_change_2024() -> None:
    result = compute_tax(make_taxpayer(), build_policy("federal", "income", 2024))
    assert result.net_tax == 129529.5


def test_new_parameters_absent_before_2025() -> None:
    p2024 = build_policy("federal", "income", 2024)
    assert "standard_deduction_phaseout_start" not in p2024.parameters
```

The expected numbers above come from the illustrative 2025 data:

- AGI 580,000; standard deduction 30,000
- phase-out: (580,000 − 500,000) × 0.25 = 20,000 → deduction 10,000
- taxable income 570,000 → pre-credit tax 138,594.50
- two children × $2,000 = 4,000 credit → net 134,594.50

**How to get expected values:** run the calculation once with `print(...)`, check
it against the official forms, then pin the value in the test. Do not invent
numbers.

Also keep a test that a year with no data still fails:

```python
def test_year_without_data_still_fails() -> None:
    try:
        build_policy("federal", "income", 2027)
    except NoEffectiveVersionError:
        pass
    else:
        raise AssertionError("expected 2027 to raise")
```

---

## Step 5 — Update the notebook (recommended)

File: `examples/Test policy data changes.ipynb`

Add a cell after the 2024 comparison:

```python
fed_2025 = build_policy("federal", "income", 2025)
print("2025:", compute_tax(taxpayer, fed_2025))

print("2023:", compute_tax(taxpayer, build_policy("federal", "income", 2023)))
print("2024:", compute_tax(taxpayer, build_policy("federal", "income", 2024)))
print("2025:", compute_tax(taxpayer, build_policy("federal", "income", 2025)))
```

Running side by side is the fastest sanity check that you did not disturb past
years.

---

## Step 6 — Run everything

From the repository root:

```bash
python3 -m py_compile taxcalc/*.py taxcalc/rules/*.py test_proto2.py
python3 test_proto2.py
python3 test_installation.py
```

Then run the notebook top to bottom. `test_installation.py` checks the legacy
`TaxCalculator` path, which proto2 does not modify.

---

## Step 7 — Commit

```bash
git add taxcalc/params.py taxcalc/rules/base_rules.py taxcalc/rules/rulesets.py \
        test_proto2.py "examples/Test policy data changes.ipynb"
git commit -m "Add 2025 tax year parameters and standard deduction phase-out"
```

---

## All edits at a glance

For a year where **numbers and a rule change**:

1. `taxcalc/params.py`
   - Add `yearly(2025, {...})` to every `yearly` parameter for that tax.
   - Leave `since(...)` parameters alone.
   - Add any new parameters with `since(2025, {...})`.
2. `taxcalc/rules/base_rules.py` (or a new module)
   - Add the new rule function. No dollar amounts inside it.
3. `taxcalc/rules/rulesets.py`
   - End the old `RuleSet` range at 2024-12-31.
   - Add a new `RuleSet` from 2025-01-01 with the changed function.
4. `test_proto2.py`
   - Add 2025 tests; keep a 2026-still-fails test.
5. `examples/Test policy data changes.ipynb`
   - Add a 2025 cell.
6. Run the checks and commit.

---

## Checklist

- [ ] Every `yearly` parameter for the tax has a 2025 version.
- [ ] `since` parameters that are unchanged were left alone.
- [ ] New parameters use `since(2025, ...)`.
- [ ] No parameter version ranges overlap (import would fail).
- [ ] A new rule function was added instead of editing the old one.
- [ ] The old RuleSet range was shortened; the new one starts in 2025.
- [ ] Tests cover 2025, 2024 unchanged, and a missing future year.
- [ ] `test_proto2.py` and `test_installation.py` pass.
- [ ] The notebook runs top to bottom.

---

## Error messages and what they mean

| Message | Meaning | Fix |
|---|---|---|
| `NoEffectiveVersionError: federal/income/brackets: no version is effective for tax year 2025` | You forgot a 2025 version for that parameter | Add `yearly(2025, ...)` |
| `NoEffectiveVersionError: ... no parameters are effective for tax year ...` | Nothing in the catalog covers that year | Check the year and the `(jurisdiction, tax)` key |
| `NoEffectiveVersionError: federal/income rules: no version is effective for tax year 2025` | The RuleSet range stops before 2025 | Extend or split the RuleSet |
| `AmbiguousVersionError: overlapping effective ranges` | Two versions cover the same year | End the old range at 2024-12-31 |
| `AmbiguousVersionError: 2 versions are effective for tax year 2025` | Same problem, caught during lookup | Make ranges meet without overlapping |
| `MissingParameterError: ... no parameter 'standard_deduction_phaseout_start'` | A rule asked for a parameter that is not in this year's policy | Add it with `since(2025, ...)`, or fix the rule's year |
| `MissingParameterError: ... has no selector 'married_joint'` | The parameter uses different selector keys | Check the catalog keys for typos |
| `ValueError: Parameter effective start date is after end date` | A version's dates are reversed | Fix `(start, end)` |

Validation runs when the package is imported, so most of these errors appear
immediately on `import taxcalc` rather than during a calculation.

---

## Rules of thumb

- **Numbers belong in `params.py`; logic belongs in `rules/`.** Never hard-code a
  dollar amount or rate in a rule function.
- **`yearly` for inflation-adjusted numbers** (brackets, deductions, thresholds
  that change most years).
- **`since` for values that stay put until amended** (e.g. the NIIT rate).
- **One RuleSet per era of logic**, not per year. A rule can cover many years.
- **Never edit a past version.** Add a new one. History must stay reproducible.
- **When in doubt, run it.** The error messages name the tax, year, parameter,
  and available ranges.
