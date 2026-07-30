# Research notes — cited factual spine

**All URLs accessed 2026-07-28.** Every claim carries a marker: **[P]** primary (SEC
filings, regulator/exchange releases, deposit agreements), **[S]** secondary (reputable
financial press), **[U]** unsourced. Documented fact and interpretation are separated
throughout; anything marked *Interpretation* is mine and is not evidence.

**57 distinct sources: 40 primary, 17 secondary.**

---

# ⚠️ Three corrections that change the repo's framing

These emerged from reading the actual prospectus rather than inheriting the market
narrative. Each is a proposed README correction (see `docs/proposed_readme_patch.md`
items 7–9); none has been applied.

## C-A. The 2.5% is **not** a conversion cap. It is a primary-issuance cap driven by Korean competition law.

README §2 currently reads: *"Conversion cap: local→ADR conversion capped at 2.5% of
shares outstanding, fully exhausted at the offering."*

**[P] SK hynix 424B4, "The Offering," verbatim:**

> "On June 24, 2026, our board of directors resolved that the maximum number of new
> common shares to be issued in connection with this offering is 17,790,000 shares,
> representing approximately 2.50% of our total issued common shares of 712,702,365
> shares as of the date of such resolution. **The maximum offering size was determined
> taking into account the requirement under the Monopoly Regulation and Fair Trade Act
> that SK square Co., Ltd. ("SK square"), our largest shareholder, maintain ownership of
> at least 20% of our issued common shares.**"

*Interpretation (arithmetic from primary):* SK square held 20.50% of 712,702,365 =
146,103,985 shares. Post-issuance total 730,492,365. 146,103,985 / 730,492,365 =
**20.0008%**. The 2.5% was calibrated to land SK square on the 20% floor almost exactly
to the basis point.

**Why this matters rather than being pedantry.** It changes what would have to happen for
the barrier to lift. A depositary or regulatory conversion cap could be raised by
application. This one cannot: expanding the ADR programme by primary issuance dilutes SK
square below a **statutory** 20% floor. Relief requires SK square to buy shares, a
structural change, or a secondary rather than primary route. The constraint is harder
than the repo has been treating it.

## C-B. No numeric deposit cap exists in **any** SEC filing.

**[P] 424B4, "Issuance of ADSs upon Deposit of Common Shares," verbatim:**

> "…the depositary is required to obtain our prior consent to any such deposit if, after
> giving effect to such deposit, the total number of our common shares represented by ADSs
> exceeds the limits imposed by applicable laws and regulations or our articles of
> incorporation, **or otherwise exceeds a specified maximum that we may establish from
> time to time**…"

**[P] Deposit Agreement (F-6 Ex. 99(a)), verbatim:**

> "Each of the Depositary and the Custodian shall refuse to accept Shares for deposit
> whenever it has been notified… that **such deposit would cause the total number of
> Shares deposited to exceed a level from time to time determined by the Company.**"

**The string "2.5%" appears nowhere outside "The Offering."** The deposit-side instrument
is a *discretionary, issuer-set level plus a consent gate* — legally binding but with no
published number. That the operative level is 2.5% rests **entirely on KSD statements
relayed in press [S]**, never in a filing.

**[P] Risk factor**, headed *"If you surrender your ADSs in order to withdraw the
underlying common shares, you may not be allowed to deposit the common shares again":*

> "**It is possible that we may not give such consent** or make such securities
> registration statement or other filing."

*Interpretation:* the barrier is real but its height is **undisclosed and revisable by the
issuer**. Anything this repo says about headroom must be phrased against an
issuer-discretionary level, not a published quota.

## C-C. The "25%" is the F-6 registration and is ~90% **unused** — it is not the constraint.

**[P] Form F-6** registers **1,780,000,000 ADSs** (Reg. 333-297185).
*Interpretation (arithmetic):* = 178,000,000 common shares = **24.98%** of pre-offering
shares, and **10.01×** the 177,900,000 actually issued.

**[P] SEC Form F-6 General Instruction II, verbatim:** *"The registration statement
relates to Depositary Shares, not the number of physical certificates issued… 75,000
(100,000 minus 25,000) Depositary Shares… remain available for distribution."* So the
registered count is a **consumable capacity ceiling**, drawn down one-for-one.

README §2 calls the 25% "a technical reserve," which is directionally right. The precise
statement: ~90% of US registration is unused, so **the SEC registration is not binding**.

---

# 1. Deal facts — all [P], from 424B4 unless noted

CIK **0002120882**, Nasdaq **SKHY**, 17 filings 2026-03-24 → 07-22. **No 20-F yet.**

| Fact | Value |
|---|---|
| ADSs offered | **177,900,000** (= 17,790,000 common shares) |
| Price | **US$149.00** per ADS |
| Gross / net | US$26,507,100,000 / US$26,249,554,170 |
| Ratio | **1 ADS = 1/10 common share** (10 ADSs = 1 share) |
| Prospectus date / settlement | 2026-07-09 / **2026-07-14** (DTC) |
| Over-allotment | **None granted** |
| Depositary / Custodian | **Citibank, N.A.** / **Korea Securities Depository**, Busan |
| Lock-up | 90 days from prospectus (~2026-10-07) |
| KOSPI close 2026-07-09 | **KRW 2,186,000** at KRW 1,538.05/US$ = US$1,421.28 |
| Fees | **US$5.00 per 100 ADSs issued** and **per 100 cancelled** (= $0.05/ADS, symmetric) |

*Interpretation (arithmetic from primary):* US$149.00 × 10 = **US$1,490.00** per
common-share equivalent vs US$1,421.28 local close → **the deal priced at a ~4.84%
premium to the local market.**

**[P] 6-K, 2026-07-15, verbatim:** *"All of the newly issued common shares were issued to
Citibank, N.A. (the 'Depositary'), an overseas depositary institution, **through a
third-party allotment**."*

*Interpretation:* the ADR shares were **newly issued primary stock**, not existing local
shares converted. At inception nothing was converted — which is why the deposit-side
mechanism had never been exercised before the books opened.

**Key URLs [P]:**
- 424B4 — https://www.sec.gov/Archives/edgar/data/2120882/000119312526299963/d32785d424b4.htm
- F-6 — https://www.sec.gov/Archives/edgar/data/2120882/000119380526000898/e665622_f6-skhynix.htm
- Deposit Agreement — https://www.sec.gov/Archives/edgar/data/2120882/000119380526000898/e665622_ex99-a.htm
- 6-K capital increase — https://www.sec.gov/Archives/edgar/data/2120882/000119312526303972/d143606d6k.htm
- Submissions API — https://data.sec.gov/submissions/CIK0002120882.json

## The arbitrage risk factor — [P], and notable for what it omits

> "Investors could seek to sell or buy our common shares or ADSs to take advantage of any
> price differences between the markets through a practice referred to as arbitrage…
> holders of ADSs cannot immediately surrender their ADSs and withdraw the underlying
> common shares… This could result in time delays and additional cost."

**Documented gap:** the prospectus contains **no risk factor addressing a sustained ADS
premium or discount.**

## The July 29 reopening — **[S] only**

**[S] Bloomberg (Lee, Yang), 2026-07-23**, via Yahoo syndication —
https://finance.yahoo.com/markets/stocks/articles/sk-hynix-51-arbitrage-trade-073703063.html

> "The ADR books are closed for issuance and cancellation until July 29, as newly issued
> common shares in Korea are not transferable until they are listed on the Korea Exchange."

Same article, KSD CEO Rhee Yunsu: conversion capped at 2.5%; *"The limit is already fully
used up."* **[S] Seoul Economic Daily, 2026-07-23** — the 25% *"is merely a buffer volume…
KSD and Citibank cannot unilaterally expand it."*

**Documented gap:** no SEC filing states a July 29 KOSPI additional-listing date or a
two-way conversion opening. **The reason for the closure is not a lock-up** — it is that
newly issued Korean shares are not transferable until listed on KRX.

**Sourced premium datapoints [S]:** ~24.60% on 2026-07-17 (SKHY US$154.03); ~28.65% as of
2026-07-24; range 16–51% over two weeks.

---

# 2. The mechanism — the best-supported version

Assembled from primary sources; the loop itself is *Interpretation*.

1. **[P]** ADR→local withdrawal is a **holder right** — 17 CFR §239.36(a) requires the
   holder be *"entitled to withdraw the deposited securities at any time"*, subject only
   to transfer-book closures, fees and law. A programme cannot use Form F-6 without it.
2. **[P]** local→ADR deposit requires **issuer consent** and sits under an
   **issuer-determined level** (C-B above).
3. **[P]** Additionally, issuing shares to the depositary is an "offering" under the FSCMA
   requiring an effective **Korean-language securities registration statement** with the
   FSC; and under the Foreign Exchange Transaction Laws, ADS issuance above **US$50m**
   requires a report to MOFE via a designated FX bank.
4. **[P]** Fees are symmetric and trivial: $0.05/ADS each way ≈ **0.07% of the $149 ADS
   price**. *Interpretation:* **fees are not what sustains the premium.**

*Interpretation — the self-reinforcing loop:* headroom on the deposit side can only be
created by prior cancellations. While ADRs trade at a large premium, no rational holder
cancels — so no headroom appears — so the premium is not arbitraged away. The asymmetry is
not merely that one direction is capped; it is that **the capped direction's capacity is
manufactured only by the uncapped direction being used, and the premium itself removes the
incentive to use it.**

---

# 3. TSMC — the precedent is weaker than assumed

## ⚠️ The 12.6% five-year average is **[U] at origin** — do not use it as a fair-value anchor

Traceable only to *"data compiled by Bloomberg"* relayed in the 2026-07-23 article. **No
published methodology** — price snapshot, FX rate, arithmetic vs time-weighted all
unstated. Not independently reproducible. Bloomberg's own pages returned HTTP 403.

**Contradicted by the same provider [S]:** Taipei Times, 2025-02-25 —
https://www.taipeitimes.com/News/biz/archives/2025/02/25/2003832441 — Bloomberg-sourced,
*"about **10 percent** for the five-year average."* And Yahoo/Bloomberg 2026-06-01:
**13.7%** average in May 2026, down from **26%** in December.

*Interpretation:* a Bloomberg "five-year average" was **~10% in Feb 2025** and **12.6% in
Jul 2026**. Both can be true — the trailing window rolled through a 26% episode. **12.6%
is a rolling-window artifact, not an equilibrium anchor.**

**This repo has an independent, reproducible alternative:** its own TSM series, computed
from primary-exchange data with a published formula — mean **+6.24%** over 5,064 days (2005-01-03 onward; was +8.88% over 2,328 days when the ADR leg's provider chain truncated it at 2016 — see docs/gate_reports/S25.md)
(2016–2026). Cite that, not the press figure.

## TSMC's facility is **revolving**, not closed — [P]

**20-F FY2025, Item 10, verbatim:**

> "We, or the foreign depositary bank, may not increase the number of depositary receipts…
> **without specific R.O.C. FSC approval**… **Issuances of additional depositary
> receipts… will be permitted to the extent that previously issued depositary receipts
> have been cancelled and the underlying shares have been withdrawn.**"

**[P] ADS count essentially frozen** across four 20-Fs: 1,063,805,907 (2023-02-28) →
1,062,690,167 (2026-02-28) — **−0.105% over three years**, through premium swings of ~1%
to 26%. **[P]** 1 ADS = 5 common shares; depositary Citibank; fees up to $0.05/ADS each
way.

**⚠️ [U] That TSMC's cap is *exhausted* is unsourced.** No TSMC filing, IR page, FSC or
TWSE notice states the FSC-approved deposited-share number or remaining headroom. **The
"structural precedent" argument rests on an unverifiable premise.**

*Interpretation:* the near-frozen ADS count through a 26% premium is *consistent* with a
binding ceiling — but equally consistent with two-way flow netting to zero. **Public data
cannot distinguish these.** Note also **[S]** Goldman Sachs (via Taipei Times, 2025-02-25)
attributed the premium *"largely due to the difference in investor bases"* — putting
segmentation ahead of any hard cap.

---

# 4. Korean market access

**[P] FSC 2023-01-25** — https://fsc.go.kr/eng/pr010101/79346 — abolish foreign investor
registration in favour of LEIs / passport numbers; abolish end-investor reporting for
omnibus accounts. **[P] FSC 2024-06-21** — https://www.fsc.go.kr/eng/pr010101/82511 — IRC
abolition **effective 2023-12-14**; 1,432 new foreign accounts in six months vs ~105
monthly IRC issuances in 2023. **[P] Corroborated in the 424B4 itself.**

**[S] Clearstream** — legacy IRC holders must keep using the IRC; *"cannot use both an IRC
and an LEI at the same time."* *Interpretation:* the reform removed a pre-registration
*gate*, not identification; two identifier regimes run in parallel.

**Short selling [P]:** FSC 2025-03-24 — https://www.fsc.go.kr/eng/pr010101/84220 — **short
selling resumed on all listed stocks 2025-03-31**, first time in ~5 years; NSDS blocks
naked positions pre-submission. FSC 2024-11-21 — disclosure threshold 0.01% or KRW 1bn.

**⚠️ [U] Current July 2026 status is inference from negative evidence only** — confirmed
operating Feb 2026 **[S]**, and no short-selling item on the FSC English press index as of
2026-07-28. **This matters:** the Kospi is in a severe drawdown and Korea has twice
responded to sharp declines with bans. **Verify directly before relying on it.**

**[S] Clearstream** is the only source found on DR conversion generally: *"No restriction
is applied to the conversion of DRs to ordinary shares."* **⚠️ No KRX rulebook or FSC
regulation text on DR conversion was located** — `global.krx.co.kr` is JS-rendered and
yielded nothing. **Do not describe SK hynix's cap as a KRX or FSC rule.**

---

# 5. Korean 2× single-stock ETFs — permitted, then curbed inside three months

**[P] FSC 2026-04-21** — https://fsc.go.kr/eng/pr010101/86752 — effective **2026-04-28**;
**max 200%**; eligibility ≥10% market-cap ratio and ≥5% trading volume; KRW 10m deposit;
two hours prior learning. **[S] Korea Herald** — **only Samsung Electronics and SK hynix
qualify.**

**[S] Korea JoongAng Daily 2026-07-16** — 16 products launched **2026-05-27**; **Kospi fell
6.37% on 2026-07-16**. **[P] FSC 2026-07-16** — https://www.fsc.go.kr/eng/pr010101/87354 —
**new listings suspended**, marketing banned, deposit to KRW 30m, learning to 3 hours.
**[P] FSC 2026-07-24** — https://www.fsc.go.kr/eng/pr010101/87405 — deposit increase
accelerated to **2026-07-31**, **cash only**.

*Interpretation:* Korea went prohibition → permission → retrenchment in under three
months, and the ≥10% criterion mechanically restricted the universe to the two
semiconductor names — a concentrated bet on the most volatile sector as volatility spiked.
**Directly relevant to the premium:** leveraged retail demand for SK hynix exposure was
being throttled *in Korea* in the same fortnight the ADR premium hit 51%.

---

# 6. DR mechanics — [P]

**SEC Investor Bulletin** — https://www.sec.gov/files/adr-bulletin.pdf · **Form F-6** —
https://www.sec.gov/files/formf-6.pdf · **17 CFR §239.36(a)** · **BNY DR Basics** —
https://www.adrbny.com/resources/dr-basics.html (note: `adrbny.com`, **not**
adrbnymellon.com) · **Citi ADR primer** —
https://depositaryreceipts.citi.com/adr/common/file.aspx?idf=1248 · **SEC PR 2018-285** on
pre-release — https://www.sec.gov/newsroom/press-releases/2018-285

**Fee correction [P]:** EDGAR full-text search for `"for each 100 ADSs (or portion
thereof) issued"` returns **1,034 filings**; `"U.S.$2.00 for each 100 ADSs"` returns
**0 hits**. Where $0.02/ADS appears it is a **cash-distribution** fee, not
issuance/cancellation. SK hynix's schedule matches the industry standard exactly.

**⚠️ [U] "Conversion window"** has no authoritative definition in any primary source —
not in the SEC bulletin, Form F-6, 17 CFR 239.36, the GSK deposit agreement, BNY or Citi.
**Define it explicitly rather than attributing it.**

---

# 7. What could not be sourced — excluded or downgraded, never approximated

**Bearing directly on the thesis:**

1. **The numeric deposit cap in SK hynix's own documents — does not exist.** 2.5%-as-
   deposit-cap rests entirely on press relaying KSD.
2. **No primary source for the 2026-07-29 reopening.** Bloomberg-via-Yahoo only.
3. **The 12.6% TSMC figure's origin.** Contradicted by ~10% from the same provider in 2025.
4. **TSMC's FSC-approved ceiling and whether it is exhausted.**
5. **Any KRX/FSC rule text on DR conversion.**
6. **KSD's published conversion procedures.**

**Secondary:** November 2023 short-sale ban imposition date; affirmative current
short-sale status; omnibus-reporting abolition effective date; reported 2026-01-30 FSC
ETF approval; "conversion window" definition; $0.02 as an issuance fee; current SKHY/TSM
premium levels from a cited source (repo data is used instead).

**Deliberately excluded as unreliable:** ts2.tech, kucoin, mexc, weex, skhypremium.com.
BigGo, TradingKey, Whalesbook and a retail GitHub repo are cited **only** to document the
propagation path of the 12.6% figure, never as evidence for it.

**Fetch failures (not cited):** Bloomberg.com, CNBC, marketscreener (HTTP 403);
`global.krx.co.kr`, ksd.or.kr DR pages (JS-rendered); J.P. Morgan adr.com; Deutsche Bank
DR materials.
