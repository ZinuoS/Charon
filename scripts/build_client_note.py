"""Generate notebooks/01_client_note.ipynb. uv run python -m scripts.build_client_note"""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "01_client_note.ipynb"
cells=[]
md=lambda s: cells.append({"cell_type":"markdown","metadata":{},"source":s.strip().splitlines(True)})
code=lambda s: cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.strip().splitlines(True)})

md(r"""
# SK Hynix ADR premium — access, financing, execution and monitoring

**A prime-finance note.** What the constraint is, how exposure to it can be expressed and
hedged, what it costs, what it risks, and what a desk would watch on a client's behalf.

---

> **Informational only.** This note is not investment advice, not a recommendation, and not
> a solicitation. It describes structures and their mechanics; it does not advise taking
> any position. All figures derive from public data or cited public sources. Levels marked
> *desk quotes live* are not published and would be quoted on request. Nothing here
> forecasts the premium beyond what a registered research call states, and those calls are
> named with their class and resolution date.

---

## Executive summary

**The situation, in four sentences.** SK Hynix listed ADRs on Nasdaq on 2026-07-10 at
US$149.00 (177.9m ADSs, 10 ADSs = 1 common share), and the ADR has traded persistently above
the underlying since — 15.98% to 51.60% in the first three weeks, 22.6% most recently. The
usual arbitrage does not close it, because the supply valve is asymmetric: **ADR→local
cancellation is a holder right, while local→ADR issuance requires the Company's prior
consent against a level it sets and does not disclose** (Deposit Agreement, F-6 Ex. 99(a)).
The board's 2.50% figure widely described as a "conversion quota" is in fact a cap on
*primary issuance*, sized so the controlling shareholder stays above a 20% statutory floor
under the Monopoly Regulation and Fair Trade Act. So the upper barrier is a corporate
decision entangled with a regulatory position — harder to lift than a quota.

**Expressions menu** — one live, four contingent on data this programme has not yet sourced.

| | Expression | Readiness | What it monetizes |
|---|---|---|---|
| 1 | Convergence RV (short ADR / long local, FX-hedged) | **live** | premium compression toward the conversion floor |
| 2 | Local-access substitute (index synthetic) | contingent | offshore demand for constrained local exposure |
| 3 | Term-structure RV | contingent | mispriced convergence *speed* |
| 4 | Volatility RV | contingent | ADR implied vol over the local+FX stack |
| 5 | Flow-aware execution overlay | contingent | slippage against mechanical rebalance flow |

**Cost.** The documented crossing cost is trivial — US$0.05 per ADS each way, **~0.07% of
price**. Borrow, funding and hedge points are not publicly documented and would be quoted
live. Cost is emphatically *not* what sustains this premium.

**Risk, in one sentence.** Every short-premium expression is short a barrier that exists on
only one side: gain is bounded by the conversion floor, loss is unbounded, and the premium
ran **from 15.98% to 51.60% in week one** — roughly 36 points against such a position
before any convergence.

**Monitoring.** The desk tracks the barrier-state observable daily (KSD headroom on the
capped programme), the premium under both measurement definitions, and a regulatory event
register. Current headroom reading appears in §5.
""")

code(r'''
%matplotlib inline
import sys, pathlib, subprocess, yaml
ROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == "notebooks" else pathlib.Path.cwd()
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from pipeline.viz import theme
from pipeline.measurement.premium import build_all_variants
theme.apply()

calls = yaml.safe_load((ROOT/"preregistration"/"calls.yaml").read_text())
frozen = calls.get("frozen_at")
print(f"Research ledger: FROZEN {frozen}" if frozen else "Research ledger: NOT FROZEN")
for h, v in calls.items():
    if isinstance(v, dict) and "freeze_class" in v:
        print(f"  {h:22s} class {v['freeze_class']}  status {v['status']}")
print("\nOnly Class C/P calls are registered. Class X are exploratory and are not")
print("presented as pre-registered forward tests anywhere in this note.")

sk = build_all_variants("skhy")[0]
theme.sparkline_header(sk.series, highlight=("2026-07-10","2026-07-28"),
                       label="SKHY premium since listing  ·  this note: access, cost, risk, monitoring");
''')

md(r"""
---

# §1 Situation

## 1.1 What the constraint actually is

Two documented facts define the asymmetry, and they are of different kinds.

**Downward — a right.** A holder may surrender ADSs and withdraw the underlying shares at
any time, subject only to transfer books, fees and law (17 CFR §239.36(a)). A programme
cannot use Form F-6 without granting it.

**Upward — a permission.** The deposit agreement requires the depositary to refuse shares
whenever a deposit *"would cause the total number of Shares deposited to exceed a level from
time to time determined by the Company"*, and the prospectus adds that the Company's prior
consent is required, noting plainly: *"It is possible that we may not give such consent."*

**No numeric deposit cap appears in any SEC filing.** The widely-quoted 2.50% is the board's
authorization for *primary issuance* — 17,790,000 shares — sized against the MRFTA
requirement that the controlling shareholder hold ≥20%; post-issuance it sits at 20.0008%.
Expanding the programme by primary issuance would dilute below a statutory floor.

*Interpretation.* Headroom on the deposit side is created only by prior cancellations. While
the ADR trades at a premium, no rational holder cancels — so no headroom appears — so the
premium is not arbitraged away. The premium removes the incentive to create the capacity
that would compress it.
""")

code(r'''
from pipeline.viz import figures
fig, ax = figures.g1_barrier_anatomy(sk.series, theme.events_for(markets=["US","KR"]))
fig;
''')
code(r'''
fig, ax = figures.g2_plumbing_map()
fig;
''')

md(r"""
## 1.2 The comparator, and what it does not tell you

TSMC's ADR operates a structurally similar asymmetry, and its premium has persisted for a
decade — but its facility is explicitly **revolving**: its 20-F states issuance is
*"permitted to the extent that previously issued depositary receipts have been cancelled."*
That makes it a weaker analogue for a discretionary-consent barrier, while simultaneously
*strengthening* the persistence case: a premium that survives a working refill valve is more
evidence of durability, not less.

The 12.6% "five-year average" in circulation is untraceable to a primary source and is
contradicted by ~10% from the same provider a year earlier. This note does not use it. It
uses this programme's own reproducible measurement instead.
""")

md(r"""
---

# §2 Expressions menu

Each sheet below states structure, hedge, residual exposures, cost, stress, constraints,
risk and the observable that monitors it.

**On the holding period, which every cost line accrues against.** The research programme now
measures it rather than extrapolating it, and the measurement has an unusual shape: the
premium's half-life has a **floor of about 143 trading days (~7 months) at 95%, and no upper
bound.** The upper edge of the confidence band never reaches half-decay at any horizon the
data can estimate — so these data do not reject a premium that never halves. Financing cost
is linear in holding period. **It is therefore quoted as a floor, never as a point**, and a
financing line that can be withdrawn inside that floor is the binding risk on any convergence
expression. §6 sets out what remains genuinely unquantified.
""")

code(r'''
from pipeline.hedging.sheets import all_sheets
from pipeline.hedging.ratios import HedgeLegs, fx_hedge, fx_sensitivity
from pipeline.ingest._common import latest_raw_file
import pandas as pd

adr = pd.read_csv(latest_raw_file("d1_prices","skhy_adr_daily.csv")).iloc[-1]
loc = pd.read_csv(latest_raw_file("d1_prices","skhynix_local_daily.csv")).iloc[-1]
fxr = pd.read_csv(latest_raw_file("d1_prices","usdkrw_spot_daily.csv")).iloc[-1]
legs = HedgeLegs(float(adr.close), float(loc.close), float(fxr.close))

from hypotheses.h5_quota_ledger.monitor import ledger
cap = ledger()["capped"]
reading = f"headroom {cap.level:,} on {cap.isin} (obs {cap.n_obs}, last {cap.last_obs})"

sheets = all_sheets(legs.premium, reading)
print(sheets[0].render())
''')

md(r"""
### The hedge detail that matters most

A convergence position is **not FX-neutral even when the local leg is fully FX-hedged.** The
premium is itself a currency-exposed notional — the excess of ADR notional over local
notional — and it is the part a local-leg hedge does not cover.
""")

code(r'''
h = fx_hedge(legs)
s = fx_sensitivity(legs.premium)
print(f"ADR leg notional            ${h['adr_leg_usd_notional']:,.2f}")
print(f"local leg (USD equivalent)  ${h['local_leg_usd_equivalent']:,.2f}")
print(f"RESIDUAL premium notional   ${h['residual_premium_notional_usd']:,.2f}"
      f"   = {h['residual_as_pct_of_adr_leg']:.1%} of the ADR leg, unhedged by a local-leg hedge")
print()
print(f"1% KRW depreciation widens the premium by:")
print(f"   analytic   {s['analytic_premium_change_pct_pts']}pp   (ceteris paribus)")
print(f"   empirical  {s['empirical_central_pct_pts']}pp   range {s['empirical_range_pct_pts']} (95% CI)")
print(f"   FX share of daily premium variance: {s['fx_share_of_daily_premium_variance']:.1%}")
print()
print("READ THIS CAREFULLY:", s['caveat'])
''')

md(r"""
**Two readings, and the second qualifies the first.** The mechanical link is real and
correctly signed — a short-premium position is structurally short KRW weakness, and a hedge
sized off the local leg alone leaves it uncovered. But empirically the coefficient is 0.805
(95% CI 0.51–1.10, so theory is not rejected but is imprecisely pinned), because both equity
legs carry strong negative FX betas that partly offset it. And **FX explains only ~1.2% of
daily premium variation** — hedging the currency does not turn this into a low-variance
position. It removes a real but secondary risk.

### Contingent expressions

The remaining four are shown with their contingency stated rather than omitted — a desk
that shows a client what it cannot yet price earns more trust than one that quietly drops it.
""")

code(r'''
for sh in sheets[1:]:
    print(sh.render())
    print()
''')

md(r"""
---

# §3 Costs and financing
""")
code(r'''
from execution.costs import summary_table, margin_stress
fig, axes = figures.g9_cost_and_skew(summary_table().to_dict("records"), margin_stress())
fig;
''')
md(r"""
The documented segment is the conversion round trip: **US$0.05 per ADS each way, ~0.07% of
price.** Every other segment — local borrow, ADR borrow, FX hedge points, funding
differential — is not publicly documented at usable granularity and is shown hatched. **The
desk quotes these live on request.** They are not zero, and this note does not estimate them.

Margin methodology, in sketch: the premium leg is marked to the observable premium, so the
stress case is the realized excursion in §4 rather than a modelled shock.

---

# §4 Risks
""")
code(r'''
tsm = build_all_variants("tsmc")[0]
fig, axes = figures.g4_asymmetry(tsm.series, sk.series)
fig;
''')
md(r"""
**The skew is structural, not circumstantial.** Gain on a convergence expression is bounded
by the conversion floor; loss is unbounded because there is no numeric ceiling on file. The
left panel shows the comparator's mean reversion is *asymmetric* — the floor reflects far
harder (t = +10.9) than the ceiling pulls (t = −5.0).

**Other risks carried, each with its anchor:**

- **FX gap risk** on the residual premium notional (§2), which a local-leg hedge does not cover.
- **Short-sale regime change.** Korean short selling resumed 2025-03-31; Korea has twice
  responded to sharp declines with bans. Current status is inferred from the absence of a
  contrary notice — verify before relying on it.
- **Leveraged-ETF regulatory review.** New single-stock leveraged listings were suspended
  2026-07-16 and the deposit requirement raised, accelerated to 2026-07-31. Eligibility rules
  admit only two names, so this is concentrated in the underlying.
- **Upper-barrier corporate action.** Because the ceiling is a Company determination, it opens
  by *decision*, disclosable through Korean regulatory filings. This is a monitorable event
  class, not a market variable — and it is the single event that would most change the thesis.
- **Measurement risk.** A quoted premium carries ~25bp of definitional ambiguity depending on
  close definition, and the FX fix choice moves day-over-day changes by ~27bp on average.

---

# §5 Monitoring — what the desk watches

Presented as a service a client would receive: four observables, refreshed daily from public
sources, each with its current reading and its known limitation.
""")
code(r'''
from hypotheses.h5_quota_ledger.monitor import status_report
print(status_report())
''')
md(r"""
**The publication check is the substantive line.** The capped programme has not printed since
2026-07-15, which alone is ambiguous between *the barrier has not moved* and *the feed is
silent*. The legacy programme — a different, unconstrained channel carried purely as a
control — printed through 07-28. So the feed is live and **the barrier is sealed by
observation, not by absence of data.**

**And the scope limit, stated because it changes what the signal means:** this series measures
a programme's issuance-ceiling headroom, **not** the operative consent gate. Headroom can rise
via cancellation while deposits remain blocked by consent never granted. The registered
research call is scoped accordingly, with an explicit indeterminate branch.

Also monitored: the premium under both close definitions and both FX fixes; estimated LETF
rebalance flow (**currently unavailable** — no landed AUM); and the regulatory event register.

---

# §6 Methodology and what is pending

Full research programme: **[00 — executive pitch](00_executive_pitch.ipynb)** ·
**[02 — premium anatomy](02_premium_anatomy.ipynb)** ·
**[05 — hypothesis engines](05_hypothesis_engines.ipynb)**. Sources:
`docs/research_notes.md` (57 sources, 40 primary).

**Pending quantitative fields and what fills them:**

| Field | Fills from | Why not yet |
|---|---|---|
| Upper bound on holding period | — | **none exists at 95%.** ρ's upper band never crosses ½ at any estimable horizon; the floor (~143d) is quoted instead |
| Precise holding period | more constrained pairs, or intraday resolution | first passage sits at ~331d but on ~6 independent spans — observed, not located |
| Financed cost over horizon | linear in the above | inherits the same gate |
| Beta hedge ratio + interval | M5 single-name context layer | M5 not built; no Korea index proxy landed |
| FX hedge points | SGX curve at the horizon tenor | tenor follows the holding period; deferred SGX months are exchange-marked, not executable |
| LETF flow estimate | D4 issuer AUM | issuer pages are JS SPAs; the data-bearing route is terms-withheld |

**What is usable now, and robust:** the persistence contrast. ρ₁ = 0.94 (t-HAC 129) for the
barrier-constrained regime against 0.04 (insignificant) for the fungible control, on 2,328 and
1,593 observations — and, since S17, a **measured floor** under the convergence horizon rather
than an assumption. The premium mean-reverts slowly; it must be financeable for at least seven
months, and possibly indefinitely. That is the fact this note relies on, and it is the fact a
financing conversation should start from.

---

> **Informational only.** Not investment advice, not a recommendation, not a solicitation.
> The desk provides access, financing, execution and monitoring; it does not recommend
> positions. Levels marked *desk quotes live* are quoted on request. Public data throughout;
> figures reproducible from this repository.
""")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}, indent=1)+"\n")
print(f"wrote {OUT.relative_to(ROOT)} ({len(cells)} cells)")
