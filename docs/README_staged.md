# charon

**Pricing a one-sided arbitrage barrier: the SK Hynix (SKHY) ADR premium as a reflected process.**

> *Charon ferries in one direction, and the crossing costs an obol.* The SKHY conversion channel is a one-way crossing: ADR → local cancellation is a holder right; local → ADR issuance requires the Company's consent against a level it sets and does not disclose. This repository studies what a Law-of-One-Price violation does when the arbitrage that should kill it can only push from one side.

Built as a standing research program in constrained cross-listing relative value, covering deal structure, trading insights and execution.

---

## Reading the research

Start with **[`notebooks/00_executive_pitch.ipynb`](notebooks/00_executive_pitch.ipynb)** —
the full argument, chart-led, every number traceable. Continue into
**[`notebooks/02_premium_anatomy.ipynb`](notebooks/02_premium_anatomy.ipynb)** for the
measurement layer. [`notebooks/README.md`](notebooks/README.md) is the reading guide, and
carries nbviewer links (GitHub truncates figure-heavy notebooks).

Key documents: [`docs/research_notes.md`](docs/research_notes.md) — 57 cited sources, 40
primary · [`docs/data_sources.md`](docs/data_sources.md) — every source evaluated, with its
terms posture · [`docs/gate_reports/`](docs/gate_reports/) — what each stage established
and what it could not.

---

## 0. Status, scope, and compliance

- **Status:** Stage 0 (pre-registration freeze). See §9 stage gates.
- **Data policy:** public data only, personal hardware only, deterministic runtime. No firm data, firm code, client information, or internal communications enter this repository under any circumstances. The internal pitch deliverable (memo + deck) lives on firm systems and is out of scope here; this repo contains only the public-data research layer.
<!-- ===================== §0 VISIBILITY — AUTHOR RULING PENDING =====================
     Two variants below. Delete the one you do not want, delete these comment markers,
     then `cp docs/README_staged.md README.md` and commit. Nothing else in this file
     needs your attention.

     VARIANT A — PUBLIC (current live text; ratified by your 2026-07-28 override):
     - **Visibility:** **public.** This repository is the public-data research layer only. No firm data, firm code, client information or internal communications enter it under any circumstances; desk and firm names are excluded from all committed files. Any internal deliverable lives on firm systems and is out of scope here.

     VARIANT B — PRIVATE-UNTIL-CLEARED (the original §0 rule, if you reverse the override):
     - **Visibility:** **private** until the rotation concludes or compliance clears
       publication, whichever is later. No firm data, firm code, client information or
       internal communications enter this repository under any circumstances; desk and
       firm names are excluded from all committed files.
     ================================================================================ -->
- **Visibility:** **public.** This repository is the public-data research layer only. No firm data, firm code, client information or internal communications enter it under any circumstances; desk and firm names are excluded from all committed files. Any internal deliverable lives on firm systems and is out of scope here.
- **No LLM calls in pipeline code.** Feature extraction is deterministic end to end (doctrine rule; see §8).

---

## 1. Motivation and prompt mapping

The desk prompt has three parts. This project answers each with a quantitative artifact rather than prose alone:

| Desk ask | This repo's answer |
|---|---|
| **Part 1 — Background:** why the IPO opened above offer and trades at a premium to the underlying | The reflected-process framework (§3): US liquidity preference + AI scarcity demand + supply gated by a *discretionary* issuance decision (§2) ⇒ premium bounded below, unbounded above. Comparator evidence from TSMC's structurally identical regime. |
| **Part 2 — Trading insights:** can it be arbitraged; long/short convergence trades; limits on size and frequency | Classic create-to-arb is unavailable — the deposit side requires the Company's consent against an undisclosed level (§2). Five testable relative-value channels replace it (§5, H1–H5), each with a pre-registered direction and validation design. Honest framing: these are RV trades against a one-sided barrier, never "arbitrage." |
| **Part 3 — Execution:** long/short exposure mechanics, borrow and financing, margin, risk factors | Execution module (§7): borrow/financing cost table, margin stress under the 22%→51%→22% premium round trip, FX hedge mechanics, conversion plumbing timeline. |

---

## 2. Market facts (frozen as of 2026-07-28)

Recorded here so later analysis is checked against what was knowable at freeze time, not hindsight.

- SK Hynix listed ADRs on Nasdaq (ticker **SKHY**) on **2026-07-10**: 177.9M ADRs priced at **$149**, raising ~**$26.5B** — the largest US listing by a foreign company on record. Ratio: **10 ADRs = 1 Korean common share (000660.KS)**. Priced at a ~3% markup to the Seoul close; opened ~$170, closed day one at $168.01 (+13%).
- **The barrier — corrected 2026-07-29 from the primary documents.** The widely-quoted "2.5% conversion quota" is **not** a conversion cap. The 424B4 states the board resolved a maximum *primary issuance* of 17,790,000 shares (2.50%), sized so that SK square remains above the **20% floor required by the Monopoly Regulation and Fair Trade Act** (post-issuance: 20.0008%). Separately, **no numeric deposit cap appears in any SEC filing**: the deposit agreement refuses deposits that would exceed "a level from time to time determined by the Company," subject to the Company's prior consent. The 1.78bn-ADS Form F-6 registration is ~90% unused and is not the binding constraint. **So the upper barrier is a corporate decision entangled with a controlling shareholder's regulatory position — harder to lift than a quota, since expanding by primary issuance dilutes SK square below a statutory floor. ADR→local cancellation is uncapped and is a holder right (17 CFR §239.36(a)).** See `docs/research_notes.md`.
- **Two-way conversion opens 2026-07-29** — the same day as Q2 earnings (confounded event; treated as such, §5 H-notes). Depositary: Citibank; issuance/cancellation overseen by the Korea Securities Depository (KSD).
- **Premium path to date:** peak ~51–52% post-offering → ~19% on 07-16 (front-running of conversion expectations) → ~33% around 07-23 → **~22% on 07-28** (ADR −8.76% to $130.49 amid broad Korea weakness).
- **Structural comparator:** TSMC ADR/2330.TW operates an asymmetric regime, but a *revolving* one — its 20-F states issuance is "permitted to the extent that previously issued depositary receipts have been cancelled." The widely-quoted **12.6% five-year average is untraceable at origin** and is contradicted by ~10% from the same provider in Feb 2025; it is a rolling-window artifact, not an equilibrium anchor, and is **not used**. This repo measures its own: **mean +6.24% over 5,064 days** (2005-2026). That TSMC's ceiling is *exhausted* is unsourced. Note the analogy cuts both ways: a working refill valve makes TSMC a weaker analogue for a discretionary barrier, yet its premium persists anyway — which strengthens the persistence prior.

---

## 3. Core framework: the premium as a reflected process

Define the premium

`π_t = P_ADR,t / (P_local,t × FX_t / 10) − 1`.

The conversion asymmetry implies:

- **Lower barrier (active):** if π < ~0 (net of costs), buy ADR → cancel → sell local. Uncapped, fast. The premium is *reflected* near conversion cost from below.
- **Upper barrier (discretionary):** local → ADR creation requires issuer consent against a level the Company sets and does not disclose. With the board authorization consumed and headroom = 0, nothing structurally caps π from above; compression can only come from (a) demand rotation into the local line, (b) local-share appreciation closing the gap from below (the Shinhan/TSMC observation), or (c) quota recycling (§5 H5).

Consequences the whole project hangs on:

1. π is **not** a mean-reverting spread. Modeling it as an OU process is misspecified; the correct null is a process with one-sided reflection and a state-dependent upper drift.
2. Any short-premium expression is **short a barrier that doesn't exist** — negatively skewed by construction. This is stated plainly in every trading section.
3. The barrier's "on/off/partial" state is **observable** via quota headroom (§4 D5), which makes regime modeling a data problem rather than a latent-variable guess.

---

## 4. Data stack

All series versioned as pulled, with pull timestamps; raw immutable under `data/raw/`, derived under `data/derived/` regenerated only by pipeline code.

| ID | Dataset | Source | Construction rules / notes |
|---|---|---|---|
| **D1** | Premium/basis series | SKHY (Nasdaq) daily + intraday; 000660.KS daily + intraday; USDKRW spot | Two variants, kept separate: (a) **close-to-close** π (stale: 13.5h gap between closes — a measurement artifact, labeled as such); (b) **synthetic contemporaneous** π using a USD/KRW forward proxy and the **KRX night-session** KOSPI200 futures overlap to proxy the local leg during US hours. The Eurex–KRX Link was terminated 2025-06-06; KRX has run its own night session (18:00–06:00 KST) since 2025-06-09, which fully covers the US cash session. History begins 2025-06-09, and day/night bar separability is unverified. Decompose measured π into true premium + asynchronicity artifact. |
| **D2** | FX | USDKRW spot, forwards/NDF curve | Forward points feed carry legs in H1 and the hedge-cost table in §7. |
| **D3** | Borrow/financing | KRX daily short-sale balance and securities-lending data (public); indicative ADR borrow where publicly observable | Korean short-sale regime notes maintained alongside (regulatory state is a feature, not a footnote). |
| **D4** | LETF flow proxies | AUM + daily NAV for Korean 2× single-stock ETFs on SK Hynix; US 2× SKHY products | Estimated close rebalance notional ≈ 2 × AUM × daily return, per market, per close. **Hard gate:** missing AUM ⇒ observation weight 0, never imputed. |
| **D5** | Conversion plumbing | DR outstanding from depositary reporting; KSD notices | Post-07-29 this becomes the barrier-state variable: cancellations (supply destroyed, headroom freed) vs. creations (headroom consumed). |
| **D6** | Comparator panel | TSM/2330.TW + USDTWD (20y); Indian ADR pairs under conversion caps (e.g., INFY, IBN); BABA HK/US fungible pair (unconstrained control); historical DLCs (Shell A/B, Rio/BHP) as the no-channel limit case | The **training universe**. SKHY itself is forward-test only (§8). |
| **D7** | Event calendar | Earnings dates, KSD/depositary announcements, index reviews, Korean regulatory changes | Drives event-study designs and the confound register. |

**Information-timing rule (transplanted from Inflation_Calc):** every feature carries an explicit availability timestamp; nothing enters a forecast made at time t unless it was publicly observable before t in the relevant timezone. The dual-close structure makes this non-trivial and non-negotiable.

---

## 5. Research hypotheses (H1–H5)

Each hypothesis is frozen with a direction, a validation design, and a resolution criterion **before** SKHY outcome data is examined. Thresholds live in `preregistration/calls.yaml` and are never edited after freeze — only appended with dated amendments.

### H1 — Premium term structure (derivatives-implied convergence)

- **Construction:** implied premium at expiry T from KRX single-stock futures/options on 000660 vs. US-listed SKHY options: `π_impl(T) = F_ADR(T) / (10 × F_local(T) × FX_fwd(T)) − 1`. This is the market's priced convergence schedule, set by two nearly disjoint participant pools.
- **Direction:** US-side pricing embeds too-fast convergence at the front (LOOP intuition vs. the TSMC base rate of multi-year persistence) ⇒ front-end implied π too low relative to model half-life; trade = long ADR forward / short local forward at front expiries, reversed at the back, FX-forwarded. Trades convergence *speed*, not level; requires no conversion.
- **Validation:** identical construction backtested on TSM options vs. TAIFEX 2330 futures over 15+ years, expanding walk-forward; SKHY direction pre-registered as forward test.

### H2 — Synthetic local access via the index

- **Construction:** SK Hynix is the largest KOSPI weight; offshore "cheap local Hynix" demand can only express through KOSPI200 futures (incl. the KRX night session, 18:00–06:00 KST since 2025-06-09) or long-KOSPI200 / short ex-Hynix baskets.
- **Direction:** KOSPI200 futures basis rich to fair value (and implied index correlation elevated) on premium-widening days.
- **Validation:** regress basis innovations on π innovations controlling for standard carry determinants (dividends, funding, FX); the pre-listing period is the natural own-control. Dual use: the night-session futures leg also powers D1(b).

### H3 — LETF cross-market close-imbalance loop

- **Construction:** US 2× SKHY products rebalance at the US close (moves ADR while Korea sleeps); Korean 2× products rebalance at the KRX close (moves local while the US sleeps). Each close mechanically perturbs π in a predictable direction/size with an hours-long response lag.
- **Direction:** π changes over each close window partially revert at the other market's open, scaled by estimated rebalance notional (D4).
- **Validation:** event study with matched controls — Samsung (Korean LETFs, no fresh ADR premium), NVDA/TSLA (US LETF mechanics, no pair) — effect sized per unit of estimated flow; then purged walk-forward on the SKHY pair. Market-neutral to the AI trade itself.

### H4 — Volatility decomposition RV

- **Construction:** Var(ADR) ≈ Var(local) + Var(FX) + Var(π) + covariances. π realized vol has been extreme (51→19→33→22 inside three weeks), so SKHY implied vol should carry a structural premium over [000660 implied + USDKRW implied].
- **Direction:** if US options price SKHY IV off local history or Micron comps, premium-vol is being sold for free ⇒ long SKHY straddles / short 000660 straddles + USDKRW vol, ratio-weighted by the decomposition.
- **Validation:** daily realized variance shares since 07-10 vs. the implied stack; same decomposition run on TSM/2330/USDTWD where the π-vol share is small — the *contrast* between pairs is the evidence.

### H5 — Quota-recycling flow signal (barrier-state monitor)

- **Construction:** post-07-29 the mechanism is a queue: an ADR cancellation frees headroom a local→ADR converter can claim. DR outstanding (D5) makes freed-headroom balance observable.
- **Direction:** premium-compression episodes are preceded by headroom creation, with a lag set by settlement plumbing.
- **Role:** more monitor than trade at research scale, but it is the state variable that switches the model between barrier-off / barrier-partial regimes — the connective tissue of M2 and every H above.

**Confound register:** 07-29 is simultaneously earnings and conversion-open. No design in this repo claims to cleanly separate the two on that date; effects are reported jointly with the confound stated.

---

## 6. Modeling architecture

- **M1 — Premium measurement layer.** D1(a)/(b) construction, asynchronicity decomposition, published as the repo's first artifact (chart + method note).
- **M2 — Barrier-state regime model.** Regimes defined by *arbitrage capacity state* — quota headroom (D5), borrow availability (D3), short-sale regulatory regime — never by narrative labels. Filtered (not smoothed) probabilities for anything predictive. Regimes are feature generators, not deliverables.
- **M3 — Convergence dynamics.** Conditional half-life of π per capacity regime via **Jordà local projections** across h = 1…H with exponential half-life fit, estimated on the D6 comparator panel under expanding walk-forward with purged & embargoed CV (overlapping premium labels ⇒ López de Prado ch. 7; inline PurgedKFold if the package mirror balks). Everything — scalers, regime parameters, feature selection — fits train-only inside every fold.
- **M4 — Hypothesis engines.** One module per H1–H5, each consuming M1–M3 outputs, each with its own golden regression tests before any refactor touches it.
- **Model-capacity rule:** small effective N ⇒ shallow models (regularized linear or RF max_depth≈4, min_samples_leaf≈5); permutation importance only. Mechanism-pinned signs (e.g., headroom creation ⇒ compression) enter as informative shrinkage priors, set by mechanism, never regressed on.

---

## 7. Prime finance / execution module (Part 3 deliverable)

A memo + table set answering the desk's execution questions from public data:

1. **Exposure menu:** how long/short ADR and long/short local are each expressed (cash, swap/TRS, futures, options), with the offshore-access constraints on the local line stated honestly.
2. **Financing table:** local short borrow (D3), indicative ADR borrow, USD vs. KRW funding legs, FX hedge cost from D2 forward points.
3. **Margin stress:** the short-ADR / long-local convergence trade marked through the realized 22%→51% widening — the stress scenario is not hypothetical; it happened in week one. Recall risk and buy-in mechanics for the borrow leg.
4. **Conversion mechanics timeline:** ADR→local cancellation plumbing (depositary → KSD → KRX settlement), fees per crossing (the obol), and the H5 headroom ledger.
5. **Risk factors:** KRW gap risk on the unhedged premium leg, Korean short-sale regime changes, earnings/idiosyncratic HBM-cycle risk, and the structural negative skew of every short-premium expression (§3.2) — flagged in every sizing discussion.

---

## 8. Doctrine (binding on all sessions in this repo)

Distilled from `ash-ml-doctrine` and the engineering doctrine; deviations require a dated justification in `docs/deviations.md`.

**Validation.**

- n≈12 SKHY days is not validation. **All backtests live on D6; SKHY is a forward test, full stop.** Never validate a redesign on the observation that motivated it alone.
- Purged & embargoed CV on overlapping labels; expanding walk-forward for one-step forecasts; Jordà LPs for decay questions.
- Forward tests score the same feature/instrument types as training; an OOS point that changes the input distribution is invalid.
- Structural-model temptations (queueing model of the conversion mechanism, etc.): observable-feature approximation + walk-forward ablation first; build structure only if the ablation earns it.

**Reporting.**

- RMSE, R², and sign hit rate side by side, **per regime**, never pooled-only. A signal that helps in the minority regime and hurts in the dominant one nets negative — said plainly.
- A null result is a deliverable: "tested the LETF channel; effect X bps vs. costs Y; here is why" beats a rescued headline number. The diagnosis is the product.
- Failure diagnosis order when a call misses: (1) regime mis-specification → (2) target mis-location → (3) input-distribution shift → (4) only then missing features.

**Engineering.**

- Deterministic pipeline: pinned seeds, pinned package versions, no network calls at analysis runtime (pulls are a separate, logged ingestion step).
- Golden regression tests frozen before any refactor; raw data immutable; derived data regenerated only by code.
- No LLM API calls anywhere in pipeline code.
- Public data, personal hardware, Apache-2.0-compatible dependencies only.

**Language discipline.** Nothing in this repo is called "arbitrage" except the (dead) conversion channel. Everything live is "relative value against a one-sided barrier."

---

## 9. Stage gates

Each stage ends with a written checkpoint; no stage begins before the prior gate is explicitly confirmed.

| Stage | Deliverable | Gate |
|---|---|---|
| **S0** | Pre-registration freeze — **closed 2026-07-29 05:20 UTC.** H5 registered (Class C, four-branch criterion); H1–H4 recorded exploratory (Class X); **Class P empty — no call predated the release on the record.** Partitioned by Amendment 001. | Frozen; commit hash in `docs/gate_reports/S0.md` |
| **S1** | Ingestion: D1–D7 pullers, availability timestamps, raw/derived split | Golden checksums on raw pulls |
| **S2** | M1 measurement layer + asynchronicity decomposition chart/note | Method note reviewed |
| **S3** | D6 comparator panel assembled; TSMC premium history QA'd | Panel coverage report |
| **S4** | M2 regime model + M3 convergence dynamics, walk-forward on panel | Per-regime metrics table |
| **S5** | H1–H4 engines, one at a time, in order of data readiness | Per-H validation report incl. nulls |
| **S6** | H5 headroom ledger live (post-07-29 data permitting) | First ledger snapshot |
| **S7** | Execution module memo + tables (§7) | Memo draft complete |
| **S8** | Pitch assembly: dashboard (NYT-style theming, CLO-Atlas lineage), paper, deck skeleton — pitch materials themselves finalized on firm systems | Dry-run |

---

## 10. Repository layout

```
charon/
├── README.md                     # this file — the constitution (§11: author-only)
├── preregistration/
│   ├── calls.yaml                # FROZEN 2026-07-29; append-only thereafter
│   └── amendments/               # dated, append-only (001 partitions the freeze)
├── data/
│   ├── raw/                      # payloads GITIGNORED; sidecars + pull logs tracked
│   └── derived/                  # pipeline-generated only
├── pipeline/
│   ├── ingest/                   # one puller per D-source; _http.py is the ONLY networked module
│   ├── measurement/              # M1 premium construction, asynchrony decomposition
│   ├── panel/                    # FX conventions, panel assembly
│   ├── convergence/              # M3 Jordà local projections (h→400, half-life interval)
│   ├── validation/               # purged/embargoed CV, forward-test guards
│   ├── hedging/                  # S16 hedge ratios + trade sheets
│   └── viz/                      # theme.py (chrome owner) + figures.py (G-series)
├── hypotheses/                   # h1…h5; h5_quota_ledger is the live barrier-state monitor
├── execution/                    # cost stack, margin stress
├── notebooks/                    # 00 pitch · 01 client note · 02 anatomy · 05 engines
├── scripts/                      # notebook builders, validators, intraday tracker
├── docs/                         # gate reports S0–S19, research notes, regime taxonomy, deviations
└── tests/                        # 430 passing; doctrine is enforced here, not asserted
```

**The display medium is the repository itself.** There is no `dashboard/`: a reader arrives at
GitHub, and the notebooks are the deliverable — committed *with outputs*, so figures and results
render without running anything. Notebook numbering is deliberately sparse (00, 01, 02, 05)
because the gaps are reserved for work that is specified but not landed, and a renumbering that
hid the gaps would misrepresent coverage.

## 11. Session protocol

Every working session opens by (1) reading this README, (2) checking `preregistration/calls.yaml` for anything now resolvable, and (3) stating which stage gate is active. Curation and threshold decisions are the author's alone; analysis sessions may propose, never ratify.

*S0 closed 2026-07-29 05:20 UTC. The pre-release freeze class (P) is **empty**: no call was committed before the 2026-07-10 listing, and Amendment 001 records that rather than backdating one. What is registered is H5 alone; H1–H4 are exploratory and are never presented as pre-registered forward tests. The honest history is the deliverable — see `preregistration/amendments/2026-07-29-partitioned-freeze.md`.*

---

## Research status — the comparator lab (staged for the author's commit, S25)

**The TSMC lab** (`notebooks/09_tsmc_lab.ipynb`) closes the last analysis gap. SK Hynix's ADR
programme is fourteen sessions old, and every question the trade has to answer is a question
about a distribution, so the deepest pair in the same regime family is measured over its full
history and reported as family characterisation. The sample is **5,064 sessions, 2005-01-03 to
2026-07-24** — recovered this session from 2,328 after the ADR leg's provider chain was found
to be resolving to a venue that serves only a rolling ten-year window, and admitted only
because the deeper source agrees with the listing venue bit-for-bit across the whole 2,513-day
overlap. The pre-2005 era is excluded for a documented corporate-action reason, and the
headline number is reported under both the conservative and the cause-based cut: the wider
sample is *less* favourable, so the exclusion is not flattering the result.

What it finds. The gap moved in **137 episodes**, median 7.97 points over 20 sessions, and
**56% of compressions closed through the ADR leg** rather than the local one. Entering at the
90th percentile of the premium's own past and holding a year beat the carry **55.5% / 41.8% /
16.4%** of the time across the low, mid and high cost brackets — so the bracket, not the
signal, decides the trade. The path is the harder finding: the median entry went **11.2 points
against you** first and the worst in 21.6 years went 25.3, while SK Hynix moved **35.6 points
in three sessions**, and no stop distance bounds that loss without also cutting the winners.

What bounds it. TSMC's ADR facility *revolves* — cancelled shares return to a re-issuable pool
— so its premium is arbitraged from both sides and mean-reverts. SK Hynix's issuance requires
Company consent, so its premium is reflected with an open upper tail. Almost every row of the
structural audit leans the same way: this history should understate how persistent the traded
premium can be, and overstate how comparable the two trades are on execution. Every figure in
the notebook carries that caveat in its own caption. **The lab bounds the argument; it does not
make it.**

---

## Staged for S26 — the two registers (author to place in the research-status section)

> **Two registers, one analysis.** This repository is the research register: full
> distributions, the risk analysis, the nulls, and the findings that went against the thesis
> — including a comparator study in which the same entry rule loses more often than it wins
> at mid-bracket financing costs. A pitch deck derived from this work presents the
> opportunity register appropriate to an internal sales document: which panel leads, which of
> three honest paths is featured, and where the qualifier sits. Both draw on identical
> numbers, because every deck figure is rendered by a builder in this repository. What differs
> is emphasis and ordering, never substance — and the deck's build script asserts that it
> quotes no unbracketed cost and claims no convergence force this research disproved.
