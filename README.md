# charon

**Pricing a one-sided arbitrage barrier: the SK Hynix (SKHY) ADR premium as a reflected process.**

> *Charon ferries in one direction, and the crossing costs an obol.* The SKHY conversion channel is a one-way crossing: ADR → local is unlimited; local → ADR is sealed behind an exhausted 2.5% quota. This repository studies what a Law-of-One-Price violation does when the arbitrage that should kill it can only push from one side.

Built as a standing research program in constrained cross-listing relative value, covering deal structure, trading insights and execution.

---

## 0. Status, scope, and compliance

- **Status:** Stage 0 (pre-registration freeze). See §9 stage gates.
- **Data policy:** public data only, personal hardware only, deterministic runtime. No firm data, firm code, client information, or internal communications enter this repository under any circumstances. The internal pitch deliverable (memo + deck) lives on firm systems and is out of scope here; this repo contains only the public-data research layer.
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
- **Structural comparator:** TSMC ADR/2330.TW operates an asymmetric regime, but a *revolving* one — its 20-F states issuance is "permitted to the extent that previously issued depositary receipts have been cancelled." The widely-quoted **12.6% five-year average is untraceable at origin** and is contradicted by ~10% from the same provider in Feb 2025; it is a rolling-window artifact, not an equilibrium anchor, and is **not used**. This repo measures its own: **mean +8.88% over 2,328 days**. That TSMC's ceiling is *exhausted* is unsourced. Note the analogy cuts both ways: a working refill valve makes TSMC a weaker analogue for a discretionary barrier, yet its premium persists anyway — which strengthens the persistence prior.

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
| **S0** | Pre-registration freeze: `calls.yaml` with H1–H5 directions, frozen thresholds, resolution dates; committed and timestamped **before the 2026-07-29 KRX open** | Commit hash recorded |
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
├── README.md
├── preregistration/
│   ├── calls.yaml            # frozen H1–H5: direction, threshold, resolution date
│   └── amendments/           # dated, append-only
├── data/
│   ├── raw/                  # immutable, timestamped pulls (D1–D7)
│   └── derived/              # pipeline-generated only
├── pipeline/
│   ├── ingest/               # one puller per D-source, logged
│   ├── measurement/          # M1: premium construction, async decomposition
│   ├── regimes/              # M2
│   └── convergence/          # M3
├── hypotheses/
│   ├── h1_term_structure/
│   ├── h2_index_access/
│   ├── h3_letf_loop/
│   ├── h4_vol_decomposition/
│   └── h5_quota_ledger/
├── execution/                # §7 tables + memo source
├── tests/
│   └── golden/
├── dashboard/                # SvelteKit or static; Attic-palette-adjacent theming TBD
└── docs/
    ├── deviations.md
    └── confounds.md
```

---

## 11. Session protocol

Every working session opens by (1) reading this README, (2) checking `preregistration/calls.yaml` for anything now resolvable, and (3) stating which stage gate is active. Curation and threshold decisions are the author's alone; analysis sessions may propose, never ratify.

*Freeze deadline for S0: before the Korea open, 2026-07-29 09:00 KST (2026-07-28 20:00 ET).*
