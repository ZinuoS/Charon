# Proposed README corrections

README §11 reserves edits to the author. **Nothing in this file has been applied.** Each
correction below gives the current text, the proposed replacement, the evidence, and —
the part that matters for deciding — **what breaks if you decline**.

Six corrections. Two are factual (the constitution asserts something no longer true),
two are scope (an assumption is confirmed or reframed), one is an upgrade (a better
source exists than the one assumed), and one is a measurement definition (§2's close
price, which propagates into every premium observation).

Status legend: **[V]** verified by primary source or live probe · **[U]** unverified.

---

## 1. §4 D1(b) and §5 H2 — the Eurex night session no longer exists

**Severity: factual error. Highest blast radius in this document.**

### Current text

> **D1** … (b) **synthetic contemporaneous** π using the KRW NDF and the **Eurex–KRX
> night-session KOSPI200 futures overlap** to proxy the local leg during US hours.

> **H2 — Construction:** … offshore "cheap local Hynix" demand can only express through
> KOSPI200 futures (**incl. Eurex night session**) or long-KOSPI200 / short ex-Hynix
> baskets.

### Proposed replacement

```diff
- (b) synthetic contemporaneous π using the KRW NDF and the Eurex–KRX night-session
-     KOSPI200 futures overlap to proxy the local leg during US hours.
+ (b) synthetic contemporaneous π using a USD/KRW forward proxy and the KRX
+     night-session KOSPI200 futures overlap to proxy the local leg during US hours.
+     KRX has run its own night session since 2025-06-09 (18:00–06:00 KST), which
+     fully covers the US cash session; the Eurex–KRX Link that previously supplied
+     this leg was terminated 2025-06-06. Two constraints follow: night-session
+     history begins 2025-06-09 (~14 months as of writing), and D1(b) is declared
+     constructible only after the day/night bar separability test passes (S2 gate).
```

```diff
- KOSPI200 futures (incl. Eurex night session)
+ KOSPI200 futures (incl. the KRX night session, 18:00–06:00 KST since 2025-06-09)
```

### Evidence

**[V]** The Eurex–KRX Link was terminated effective **2025-06-06** — last trading day
2025-06-04, decommissioned 2025-06-05 ([Eurex circular
4260544](https://www.eurex.com/ex-en/find/circulars/circular-4260544)). Eurex's stated
reason: *"The Korea Exchange (KRX) will offer extended trading hours on their platform as
of 9 June 2025."* All current-market KOSPI product pages return 404; only an archive page
survives. Eurex never listed a plain KOSPI 200 future — the products (OKS2, FBK2, FMK2,
weeklies, FCUW) were *"Daily Futures on…"* wrappers cash-settled into KRX's own daily
settlement price.

**[V]** KRX launched its night session **2025-06-09**, 18:00–06:00 KST, covering 10
products including KOSPI 200 futures, mini futures, options, and **USD futures**.

**The mechanism survives; the venue moved.** 18:00–06:00 KST fully contains the US cash
session (22:30–05:00 KST under EDT). Arguably an improvement: the index leg and a USD/KRW
leg now trade on the *same* venue in the *same* session, where the Eurex construction
spliced two.

**[V]** Eurex-era night-session prices are effectively unrecoverable: free Eurex daily
statistics are volume and open interest only — no OHLC, no settlement — and historical
data is paid (File Service retains 20 days).

### Two flagged risks

1. **History truncates at ~14 months.** Anything needing a long overlap sample must
   either splice Eurex-era history (which is not freely available) or accept the short
   sample.
2. **⚠️ [U] Day/night bar separability is unverified.** KRX instrument names carry a
   `(주간)` day-session suffix, implying the two are distinguishable, but the selecting
   parameter was not identified and no library supports it. **If day and night bars
   cannot be separated in the data as served, D1(b) is not constructible from KRX daily
   endpoints at all**, and H2's night-session leg goes with it. This must be tested
   empirically before D1(b) is declared constructible.

### If you decline

README continues to specify a venue that has not existed for 14 months. Any session
reading §4 D1 as written will attempt to source a delisted product, fail, and either
waste the session or silently substitute — the exact failure the constitution exists to
prevent. H2's construction would remain unbuildable as specified.

---

## 2. §4 D5 — the observable is headroom, not DR outstanding

**Severity: reframing. Arguably makes the repo's central claim easier, not harder.**

### Current text

> **D5** | Conversion plumbing | **DR outstanding from depositary reporting**; KSD
> notices | Post-07-29 this becomes the barrier-state variable: cancellations (supply
> destroyed, headroom freed) vs. creations (headroom consumed).

### Proposed replacement

```diff
- D5 | Conversion plumbing | DR outstanding from depositary reporting; KSD notices |
-    Post-07-29 this becomes the barrier-state variable: cancellations (supply
-    destroyed, headroom freed) vs. creations (headroom consumed).
+ D5 | Conversion plumbing | KSD/SEIBro `DR전환가능주식수량` (remaining conversion
+    capacity), daily per-ISIN, free, back to 2010; KSD notices | The freely available
+    observable is HEADROOM, not DR outstanding: no depositary publishes outstanding
+    without entitlement. Level = barrier state (M2); first difference = net creation
+    (headroom consumed) or cancellation (headroom freed), the H5 flow signal.
+    OPEN EMPIRICAL QUESTION: KSD ties this capacity to the FOREIGN OWNERSHIP LIMIT,
+    whereas SKHY's binding constraint is the 2.5% deal cap. Which constraint the
+    series reflects — the ownership limit, the deal cap, or the tighter of the two —
+    cannot be settled from documentation and is decided only by the first
+    post-2026-07-29 observations. Until it is, D5 is a candidate barrier-state
+    variable, not a confirmed one.
```

### Evidence

**[V]** KSD/SEIBro serves a daily per-ISIN series, free, no login, server-rendered HTML,
verified twice independently. Samsung Electronics (`US7960508882`) returns **3,052 daily
rows, 2010-03-31 → 2026-07-28**.

**[V]** KSD's own footnote defines `DR전환가능주식수량` as remaining capacity to convert
ordinary shares *into* DRs — issuance ceiling minus DRs outstanding, constrained by the
foreign ownership limit. Woori's figure exceeding its total shares outstanding confirms
the reading.

**[V]** No depositary publishes DR outstanding freely: BNY (`adrbny.com`, not
`adrbnymellon.com`) has no outstanding field; Deutsche Bank's fields render empty without
login and its `robots.txt` is `Disallow: /`; Citi — **SKHY's actual depositary** — is
JS-driven and bot-managed **[U]**.

**Why this is good news.** README §3.3 already says the barrier state is "observable via
quota headroom (§4 D5), which makes regime modelling a data problem rather than a
latent-variable guess." A headroom series *is* that variable. §4 asked for the wrong
quantity; §3 asked for the right one.

### If you decline

D5 remains specified as a quantity that cannot be freely obtained, and H5 — the
connective tissue of M2 per README §5 — has no data source. The honest alternative is to
mark H5 untestable, which is a legitimate pre-registered outcome but a worse one than
using the series that exists.

---

## 3. §4 D3 — KRX is login-mandatory and bars automated collection

**Severity: access + compliance. Needs a choice, not just a correction.**

### Current text

> **D3** | Borrow/financing | **KRX daily short-sale balance and securities-lending data
> (public)**; indicative ADR borrow where publicly observable

### Evidence

**[V]** On **2025-12-27** `data.krx.co.kr` became "KRX Data Marketplace" and login became
mandatory. Verified live: the anonymous `getJsonData.cmd` path returns the literal string
`LOGOUT`, confirmed against both derivatives and equities `bld` identifiers — an
authentication wall, not a wrong-parameter problem.

**[V]** There is **no `robots.txt`**, but terms Art. 10(2) prohibits *automated
collection, copying or distribution*, and Art. 12(2) bars copying site information
without prior permission. **Scraping is terms-prohibited where robots.txt is silent.**

**[V]** The sanctioned KRX Open API has **no short-selling endpoint** (verified against
the full 31-endpoint service list). It is also non-commercial-only, 10,000 req/day, and
bars redistribution.

**[V]** `pykrx` — the only library with real short-selling coverage — now requires
`KRX_ID`/`KRX_PW` credentials **and ships no LICENSE file**, which independently fails
README §8's Apache-2.0-compatible-dependencies rule.

### Four options

| Option | Gets the data? | Cost |
|---|---|---|
| **A. Register for KRX Open API** | ❌ No short-selling endpoint | Free but useless for D3; still worth it for derivatives/ETP |
| **B. Credentialed `pykrx`** | ✅ Yes | Runs **against KRX ToS Art. 10(2)**; unlicensed dependency; needs your credentials in the pipeline |
| **C. KOFIA 대차거래 + KSFC** | 🟡 Lending only, no short-sale balance | KOFIA is an SPA whose XHR format is unverified **[U]**; KSFC was unreachable **[U]** |
| **D. Drop D3** | ❌ | H5 loses the borrow-availability regime input; §7 execution module loses its financing table |

**Recommendation: C, falling back to D, and explicitly not B.** This repo is portfolio
material with your name on it (README §0 contemplates publication). A scraper
contravening an exchange's stated terms is a bad artifact regardless of enforcement
likelihood, and "the data was convenient" is not a defence you would want to give on a
desk. Option C's blockers are engineering unknowns, which are cheaper to resolve than a
compliance position.

### If you decline (i.e. keep §4 D3 as written)

§4 describes as "public" a dataset that requires an account and whose automated
collection is prohibited. M2's regime definition (README §6) lists borrow availability as
a regime input; if D3 yields nothing, that input is absent and the regime model is
defined on quota headroom and short-sale *regulatory state* alone. That is workable, but
it should be a stated design decision, not a discovery made in S4.

---

## 4. §4 D4 — premise confirmed, and better than assumed

**Severity: upgrade + a new risk to register.**

### Current text

> **D4** | LETF flow proxies | AUM + daily NAV for Korean 2× single-stock ETFs on SK
> Hynix; US 2× SKHY products

### Proposed addition

```diff
  D4 | LETF flow proxies | AUM + daily NAV for Korean 2× single-stock ETFs on SK
     Hynix; US 2× SKHY products | Estimated close rebalance notional ≈ 2 × AUM ×
     daily return, per market, per close. Hard gate: missing AUM ⇒ observation
     weight 0, never imputed.
+    CONFIRMED 2026-07-29: Korean 2× single-stock ETFs exist — 16 ETFs + 2 ETNs
+    listed 2026-05-27 under an FSC rule revision effective 2026-04-28. Eligibility
+    (≥10% of benchmark market cap and ≥5% of trading volume, trailing 3 months) is
+    met by ONLY Samsung Electronics and SK hynix, which supplies H3's Samsung
+    control by construction. REGULATORY RISK: as of 2026-07-08 the ruling party is
+    reviewing curbs, with new listings reported "effectively off the table" and
+    delisting under discussion — a live threat to the H3 sample, tracked in
+    data/raw/events/events.yaml as `kr_2x_etf_curb_review`.
```

### Evidence

**[V]** FSC rule revision approved by Cabinet 2026-04-16, effective 2026-04-28; **2×
only** (3× not permitted); 18 products listed 2026-05-27. **[V]** Eligibility rules admit
only Samsung and SK hynix. **[V]** Naver Finance serves NAV and AUM for all of them free
with no auth; combined AUM was ₩7.13tn at probe, down from ₩13.02tn on 2026-07-08.

**⚠️ [U] Whether AUM *history* is retrievable, or only a live snapshot.** If the latter,
the D4 series can only be built forward from the day capture begins.

### If you decline

No correctness cost — §4 D4 as written is not wrong, merely tentative where it could be
definite. But the regulatory-curb risk would remain unregistered, and H3's sample could
terminate mid-study with no prior record that the risk was known.

---

## 5. §4 D2 — solved via SGX, with two caveats that belong in the constitution

**Severity: upgrade. The caveats are the reason this belongs in README and not only in
`data_sources.md`.**

### Current text

> **D2** | FX | USDKRW spot, forwards/NDF curve | Forward points feed carry legs in H1
> and the hedge-cost table in §7.

### Proposed replacement

```diff
- D2 | FX | USDKRW spot, forwards/NDF curve | Forward points feed carry legs in H1
-    and the hedge-cost table in §7.
+ D2 | FX | USDKRW spot; forward curve via SGX USD/KRW futures settlements | Forward
+    points feed carry legs in H1 and the hedge-cost table in §7. SGX publishes a free,
+    keyless, loginless daily ZIP with a 12-month curve back to at least 2020, settling
+    against the SMBS USD/KRW fixing. TWO BINDING CAVEATS: (a) only the front two
+    months trade — months 3–12 carry zero volume and zero open interest and are
+    EXCHANGE-MARKED, never to be described as traded or market-observed prices;
+    (b) the URL path integer is a sequential business-day counter, not a date, so
+    every pull must probe and verify against the file's own DATE column. Neither
+    ECOS nor FRED carries any FX forward series (verified by exhaustion).
```

### Evidence

**[V]** `https://links.sgx.com/1.0.0/derivatives-daily/{id}/FUTURE.zip` — HTTP 200, no
key, no login. A complete 12-month curve was retrieved for 2026-07-24. Full-size ticker
`KRW` (125,000,000 KRW, cash settled USD, 12 monthly maturities); mini `KU` carries the
liquidity.

**[V]** Months 3–12: volume 0, open interest 0. Exchange-marked off the OTC forward
curve — arguably a *feature* for a forward proxy, since they track NDF pricing, but they
are not executable.

**[V]** Independent corroboration: SMBS 1Y mid −12.10 won vs. SGX 11M −10.59 won. Same
sign, same order of magnitude, two independent free sources.

**[V]** ECOS has **no** forward/swap/NDF table (verified three ways: full catalog
enumeration, term scan over 935 nodes, full-text search returning 0 for 선물환/스왑/NDF).
FRED has **no** FX forward series for *any* currency (H.10 is 66 spot series).

**⚠️ [U] One open compliance item: SGX's own terms of use were not reviewed** for
automated-access restrictions. This is the single unresolved question on the otherwise
best D2 source, and it should be settled before `sgx_krw_futures` is approved.

### If you decline

§4 D2 continues to name a "forwards/NDF curve" without a source. H1's `FX_fwd(T)` leg and
§7's hedge-cost table remain unbuildable. The alternatives all have worse terms — SMBS
explicitly bans crawlers, investing.com returns 403 to scripts and bars redistribution —
so declining SGX in practice means declining D2.

---

# Summary of decisions

| # | Section | Decision | If declined |
|---|---|---|---|
| 1 | §4 D1(b), §5 H2 | Replace Eurex with KRX night session | README specifies a venue delisted 14 months ago; D1(b) and H2 unbuildable |
| 2 | §4 D5 | Reframe as headroom + open empirical question | H5 has no data source; must be marked untestable |
| 3 | §4 D3 | Choose option A/B/C/D | §4 calls "public" a dataset needing an account whose scraping is barred |
| 4 | §4 D4 | Confirm premise; register curb risk | No correctness cost; risk stays unregistered |
| 5 | §4 D2 | Adopt SGX with both caveats | H1's FX_fwd leg and §7's hedge table unbuildable |

**Correction 1 is the one with a deadline attached**, because the separability test it
depends on is S2 work and S2 is the next gate.

---

## 6. §2 — the 2026-07-28 close, and what "the close" means for π

**Severity: measurement definition. Small number, wide blast radius.**

### The discrepancy

README §2 records: *"~22% on 07-28 (ADR −8.76% to **$130.49**)"*. Two independent
providers disagree:

| Source | 2026-07-28 close | Implied return vs 143.02 |
|---|---|---|
| **Nasdaq** (listing exchange) | **$130.17** | −8.985% |
| Yahoo chart API | **$130.17** | −8.985% |
| README §2 | $130.49 | −8.761% |

### It is not a typo

README's figure is **internally consistent**: 130.49 / 143.02 − 1 = **−8.761%**, matching
the −8.76% stated alongside it. So §2's pair came from a source using a *different close
print of the same session*, not from a transcription slip. The gap is **+24.6bp**.

### Leading hypothesis

**Consolidated tape vs. primary-listing official close.** +25bp is the right order of
magnitude for that spread, and it explains why two providers agree with each other and
differ from a third figure. The alternatives — a late print, or an intraday quote
mistaken for a close — are not excluded, but both providers here agree, and one of them
*is* the listing exchange.

### Why this matters more than 32 cents

π is a **ratio of two closes**. A 25bp ambiguity in the ADR close is a 25bp ambiguity in
every premium observation, which sits directly on top of the effects this repo measures —
the ECB-vs-noon-NY FX fix gap measured today has p95 of 51bp, the same order. A premium
series built from mixed close definitions has a noise floor nobody can later decompose.

### Proposed

```diff
- **Premium path to date:** peak ~51–52% post-offering → ~19% on 07-16 → ~33% around
-   07-23 → **~22% on 07-28** (ADR −8.76% to $130.49 amid broad Korea weakness).
+ **Premium path to date:** peak ~51–52% post-offering → ~19% on 07-16 → ~33% around
+   07-23 → **~22% on 07-28** (ADR ~−9% amid broad Korea weakness). CLOSE DEFINITION:
+   this repo takes the **primary-listing official close** as canonical for both legs of
+   π — Nasdaq's own print for SKHY ($130.17 on 07-28), TWSE's for 2330. The $130.49
+   originally recorded here is a consolidated-tape figure; the two differ by ~25bp,
+   which is material because π is a ratio of closes and 25bp of definitional ambiguity
+   propagates into every observation. Provider figures are reconciled rather than
+   averaged (`pipeline/ingest/reconcile.py`).
```

**TODO(ash: ratify)** — the canonical-close choice is a measurement decision reserved to
you. The recommendation is primary-listing official close, because it is the exchange's
own print, it is what the reconciliation module can verify against a second provider, and
it is the definition an execution desk would recognise.

### If you decline

π carries an unresolved ~25bp definitional ambiguity that cannot be separated from real
premium moves after the fact, and the notebook cannot state which close it used.
