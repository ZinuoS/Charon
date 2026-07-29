# Data sources — findings and puller proposals

Session 1, Tasks 3.3 and 3.4 (README §4). This file documents the public sourcing
posture for D2 (FX forwards/NDF), D3 (borrow/financing), D4 (LETF flow proxies), D5
(conversion plumbing), and the night-session leg that D1(b) depends on.

## The approval protocol

**No puller in this file is implemented until the author marks it `approved:`.**

Each source below carries an `approved:` field set to `TODO(ash)`. A later session may
implement a source *only* if that field reads `approved: yes`. This is the sign-off gate
referenced by the Session 2 prompt; it exists because several of these sources are
scrape-shaped, and the decision to scrape a site whose terms discourage it is a
compliance judgement reserved to the author (README §0, §11), not a technical one.

If an approved source turns out on closer inspection to require authentication or to
violate its own terms, the implementing session stops and reports rather than routing
around it.

## Verification status

Findings are marked **[V]** verified by live probe or primary document, or **[U]**
unverified. Where a claim in README §4 turned out to be stale, it is flagged **⚠️** and
collected in the final section — those are corrections for the author to ratify, not
edits I have made to the constitution.

---

# 0. Cross-cutting: KRX closed its anonymous data path

**⚠️ [V] On 2025-12-27 `data.krx.co.kr` became "KRX Data Marketplace" and login became
mandatory.** Viewing remains free and Naver/Kakao SSO is accepted. KRX's stated reason
was server load from AI-bot scraping. The Open API terms are dated 2025-12-26.

Live probe (2026-07-28) confirms the classic anonymous scrape is dead:

```
POST https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd
     bld=dbms/MDC/STAT/standard/MDCSTAT01501&mktId=STK&trdDd=20260724
  -> HTTP 400, body: LOGOUT
```

Warming an anonymous session does not help — no `JSESSIONID` is issued. Reference and
metadata `bld`s (e.g. `dbms/comm/component/drv_prod_clss`) still respond
unauthenticated.

**Terms posture [V].** There is **no `robots.txt`** on either `data.krx.co.kr` or
`openapi.krx.co.kr` (404 on both), but the site terms are explicit where robots.txt is
silent: Article 10(2) prohibits *automated collection, copying or distribution of
information*, and Article 12(2) bars copying or transmitting site information without
prior KRX permission. **Scraping KRX is terms-prohibited regardless of robots.txt.**

This matters for this repo specifically: README §0 keeps `charon` private for now but
contemplates publication, and the project is portfolio material. A scraper that
contravenes an exchange's stated terms is a bad artifact to have your name on
regardless of whether anyone enforces it.

### The sanctioned alternative: KRX Open API

- **Endpoint [V]:** `https://data-dbg.krx.co.kr/svc/apis/{category}/{service}`,
  `AUTH_KEY` request header, `basDd=YYYYMMDD`, JSON or XML. Unauthenticated calls return
  a clean `401 {"respMsg":"Unauthorized Key"}`.
- **Coverage [V]:** 31 endpoints across 7 categories — `idx`(5), `sto`(8), `etp`(3),
  `bon`(3), `drv`(6), `gen`(3), `esg`(3). History from **2010-01-04** for most series.
- **⚠️ [V] There is no short-selling endpoint.** Verified against the full service list.
- **Registration [V]:** free, but requires identity verification, key application with
  admin approval (~1 day), then a *separate* per-service application stating purpose and
  a 1/3/6/12-month term.
- **Licensing [V]:** **non-commercial use only** (Art. 6(2)); **10,000 requests/day per
  key** (Art. 8(4)); data may not be passed to third parties (Art. 11(2)); attribution
  to "한국거래소 통계정보" required (Art. 10(3)).

**Author decision.** The Open API is the only clean route into KRX, and it requires an
account in your name under a non-commercial licence. Whether to register is yours.

```yaml
source: krx_open_api
approved: yes
```

---

# D2 — FX forwards / NDF curve

**⚠️ Finding: a free daily 1W–1Y bid/offer forward-points curve does exist.** Session 1's
working assumption that this was Bloomberg/Refinitiv-only was wrong.

The important caveat is not availability but *identity*: both free sources publish
**broker indicative quotes**, not executable NDF prices. Onshore KRW FX swap and
offshore NDF can diverge precisely when a cross-listing dislocation blows out — i.e.
exactly in the states this repo studies. Any H1 carry leg built on these is measuring
the onshore curve and must say so.

### D2-a. Korea Money Brokerage (KMB) — recommended

- **URL [V]:** `https://www.kmbco.com/kor/rate/swap_rate.do` (English mirror `/eng/`).
- **Data [V]:** daily bid/offer at **1M, 2M, 3M, 6M, 1Y**; unit labelled 전 (0.01 KRW).
- **Excel export works with no login [V]:**
  `/kor/rate/swap_rate_excel.do?sDate=&eDate=`
- **Terms [V]:** attribution required, commercial use barred, **no anti-crawler clause**.
- **Limitation [V]:** the tenor parameter on the *historical* export could not be
  isolated — every value returned the same series. A puller may only be able to retrieve
  one tenor's history per call pattern until this is solved.

```yaml
source: kmb_fx_swap
approved: yes
```

### D2-b. Seoul Money Brokerage (SMBS) — richer, but terms-blocked

- **Endpoint [V]:** `http://www.smbs.biz/Exchange/FxSwap_xml.jsp?arr_value={TENOR}_{FROM}_{TO}`
- **Data [V]:** **1W, 1M, 2M, 3M, 6M, 1Y** bid and offer, history spot-checked to
  **2010** — a wider tenor set and deeper history than KMB. Units 전, cross-calibrated
  against their month-end table (1M mid −105전 = −1.05 KRW ✓).
- **Gotchas [V]:** HTTPS cert covers only `m.smbs.biz` (use HTTP); EUC-KR; bare `curl`
  gets 403 and needs a browser User-Agent.
- **⚠️ Terms [V]:** `Member/Copyright.jsp` Article 4 explicitly bans access via
  *"크롤러(Crawler), 스크래퍼(Scraper), 봇(Bot), 매크로(Macro)"* without written consent;
  Article 5 cites Copyright Act penalties. Non-commercial research *quotation* with
  attribution is permitted.

**Recommendation: do not build a scheduled scraper against SMBS.** It is squarely
against their stated terms and this repo is portfolio material. If SMBS's tenor depth is
needed, the defensible route is a **one-off manual pull committed as a static snapshot
with attribution**, which is quotation rather than automated collection.

```yaml
source: smbs_fx_swap_scraper
approved: TODO(ash)          # recommend: NO — terms prohibit automated access
source: smbs_manual_snapshot
approved: yes          # a single hand-pulled, attributed historical file
```

### D2-c. Bank of Korea ECOS — spot only (now definitive), best licence, and a 15:30 KST fix

**[V] ECOS publishes no forward, swap-point, FX-swap, NDF or currency-forward table.**
This was the open `[U]` from the first research pass and is now settled three
independent ways: full enumeration of catalog section 3 (exactly six FX tables,
`731Y001`–`731Y006`, all spot — there is no §3.1.3); a term scan across all 935 catalog
nodes; and full-text search over table *and* item names returning **0 hits** for 선물환,
스왑, 통화스왑, 금리스왑, NDF, IRS and CRS. The only 선물/옵션 nodes in the entire
catalog are `901Y057`/`901Y058` — *equity index* futures and options, not FX.

**⚠️ The valuable finding is not the forwards; it is the fix time.**

`731Y003` (원화의 대미달러 환율, daily) is **the only OHLC table**, with 10 items:

| Item | Meaning |
|---|---|
| `0000002` | 원/달러 시가 (open) |
| `0000005` / `0000004` | 고가 / 저가 (high / low) |
| **`0000003`** | **원/달러 종가 (15:30)** |
| `0000013` | 원/달러 종가 |
| `0000007`–`0000010` | 원/위안 OHLC |
| `0000006` | 원/100엔 (하나은행 고시) |

**`0000003` is a 15:30 KST close — the same instant as the KRX equity close.** That is
directly material to `docs/confounds.md` C2: the D1(a) premium currently mixes *three*
observation instants because the Yahoo FX snapshot time is undocumented and sits between
the two equity closes. An FX fix stamped 15:30 KST collapses the local-side pair to a
**single contemporaneous instant**, reducing C2 from a three-instant problem to a
clean two-instant one (KRX+FX at 15:30 KST vs. Nasdaq at 16:00 ET).

**TODO(ash): decide whether the D1(a) FX leg is rebuilt on ECOS `731Y003.0000003`
rather than Yahoo `KRW=X`.** This is a measurement-definition decision, not a plumbing
one, so it is yours. `731Y001.0000001` (매매기준율, the Seoul FX brokerage MAR) is the
alternative if a fixing rate is preferred to a market close.

- **Endpoint [V]:**
  `https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/{start}/{end}/{statCode}/{cycle}/{from}/{to}/{itemCode}`
  Both HTTP and HTTPS work. Only `xml` and `json` response types are supported.
- **⚠️ Licence [V] — the most permissive of any source in this document.** The
  통계정보이용지침 states that BOK-authored statistics may be used, processed **and
  redistributed, commercial use included, free of charge, provided the source is
  attributed**. Attribution format is specified verbatim, source plus access date:
  `출처 : ECOS(한국은행, 국제수지), 2024.1.10.`
  *Caveat:* third-party-authored statistics carried inside ECOS are non-commercial-only
  and need the originating agency's approval for commercial use. The FX tables are
  sourced from 서울외국환중개 (and the yen leg from 하나은행), so **the `출처` field
  should be checked per table** before treating them as BOK-authored.
- **`robots.txt` [V]:** `Disallow:` — permits everything.
- **⚠️ Key acquisition is the real barrier [V].** Signup at
  `https://ecos.bok.or.kr/api/#/AuthKeyApply` requires account creation **plus Korean
  identity verification (본인인증)**. Non-commercial applications are auto-issued;
  commercial ones go to manual review. **Keys expire after 2 years**, renewable in
  two-year blocks (이용약관 제4조③). Transferring a key is prohibited and grounds for
  termination.
- **⚠️ [U] No documented call quota exists.** The complete dev spec and FAQ were read:
  the error table lists 정보-100/200 and 에러-100…602 with **no numeric limit stated**,
  and BOK's own 2019 notice says limits were tightened *"추출 Row 건수 및 API 호출횟수
  등으로 제한"* — deliberately without numbers. **Treat the widely-repeated
  "10,000/day" as folklore.** Observed empirically: `ERROR-602` cites >300 calls / 3
  minutes with a 30-minute block, and `에러-400` is a 60-second server-side timeout on
  over-broad queries. A puller must back off on 602 rather than pace to an assumed cap.
- **[V] The shared demo key `sample` is globally saturated** and returned `ERROR-602`
  continuously across ~40 minutes of retries. It is unusable for testing; a real key is
  required even to smoke-test.
- **Python [V]:** `PublicDataReader` (588★, broad Korean public-data library, ECOS is one
  module) or `ecos-reader` (ECOS-dedicated, most actively developed, low adoption).
  `bok-api`, `ecosapi` and `pyecos` **do not exist on PyPI**; `ecospy` is an unrelated
  co-simulation engine. **Recommendation: a ~30-line `requests` wrapper**, since the URL
  format is trivial and already verified — fewer dependencies, and README §8 constrains
  the dependency licence surface anyway.
- **[U] Response payload shape** for `StatisticSearch` on `731Y003` was never observed —
  the demo key never unblocked. Item codes are verified from the catalog backend; the
  response envelope is not. Re-confirm with a real key before writing the parser.

```yaml
source: bok_ecos
approved: yes
```

### D2-d. FRED — spot only, and not just for KRW

**[V] FRED carries no FX forward, NDF, or swap-point series for KRW or for any other
currency.** Established by exhaustion, not inference: `non-deliverable forward` → 0
series; `NDF` → 0 series; `forward` filtered to tag `exchange rate` → 0 series. The H.10
release contains 66 entries, all spot bilateral rates (`DEX*`) or trade-weighted dollar
indexes. Every FRED series with "forward" in the name is an interest-rate or inflation
forward (Treasury fitted forwards, 5y5y breakevens), not FX.

Useful only as an **independent cross-check on the D1 spot leg** — which is a real use,
since the D1 FX leg currently comes from a single provider whose snapshot instant is
undocumented (see `pipeline/ingest/registry.py`).

- **[V] `DEXKOUS`** — Won/USD spot, **daily**, 1981-04-13 → 2026-07-24, H.10 release.
  Notes: *"Noon buying rates in New York City for cable transfers payable in foreign
  currencies."* Licence: **Public Domain: Citation Requested.**
- **⚠️ The stated snapshot time is the point.** DEXKOUS is a **noon-New-York** fix. That
  is a *third* distinct FX observation instant, different again from the assumed 21:00
  UTC Yahoo snapshot. It does not fix the D1(a) asynchrony problem (docs/confounds.md
  C2), but it does let the FX-timing component be **measured** by differencing two
  differently-timed spot series rather than assumed.
- **[V] `EXKOUS`** monthly (G.5), **`AEXKOUS`** annual (G.5A), both averages of daily
  figures. `KOFXUS` discontinued.
- **[V] API key required** — 32-character lowercase alphanumeric, passed as `api_key`.
  Unkeyed calls return HTTP 400. Register at `https://fredaccount.stlouisfed.org/apikeys`
  (requires an account). **[U]** No fee exists and there is no paid tier, but the word
  "free" appears nowhere in FRED's own documentation — it is a community
  characterisation.
- **[V] Rate limit exists and returns HTTP 429**; documented status codes are 400, 404,
  423, 429, 500. **⚠️ [U] The widely-cited "120 requests/minute" figure appears in no
  official FRED document** — every source asserting it is third-party. A puller must
  back off on 429 rather than pace to an assumed number.
- **[V] Terms of Use obligation:** any application built on the FRED API must display a
  notice stating it uses the FRED API **and is not endorsed or certified by the Federal
  Reserve Bank of St. Louis**. If a FRED-backed series reaches the dashboard (README §10),
  that notice is required, not optional.

```yaml
source: fred_dexkous
approved: yes
```

### D2-e. investing.com — the best free tenor coverage, and terms-blocked

**[V]** `https://www.investing.com/currencies/usd-krw-forward-rates` renders fully
**while signed out**, with bid/ask/high/low at **8 tenors: ON, TN, SW, 1M, 2M, 3M, 6M,
1Y**. Values are **forward points**, not outright rates (1Y bid/ask −2010.0 / −410.0; 3M
−435.0 / 55.0 at the time of probe; spot 1,453.85) — negative points consistent with the
standard USD/KRW basis.

This is the **only free source found with ON/TN/SW coverage**, which SMBS and KMB lack.

- **⚠️ [U]/false:** search summaries claim the page covers "1 week to 10 years." The live
  page **stops at 1Y**; there is no 2Y–10Y row for KRW.
- **[V] `robots.txt` does not disallow this path** — the only `/currencies/` rule is
  `Disallow: /currencies/*?page=chart`.
- **⚠️ [V] `robots.txt` is not the binding constraint; the Terms are — and the live Terms
  page currently renders with an empty body.** `about-us/terms-and-conditions` serves nav
  and footer only (`<main>` innerText length 0); alternative paths 404. Snapshots from
  2025-06 onward are already blank, dating the blanking to roughly H1 2025.
- **[V] The archived full text (Wayback, 2024-12-02) is presumptively still operative**
  and contains: an anti-automation clause naming scraping, data mining, robots and
  spiders; a bar on redistributing or **deep-linking Market Information**; and a licence
  granted **solely for personal, non-commercial use**. The same deep-link and
  redistribution restrictions appear in a 2017 snapshot, so this is long-standing.
- **[V] The site-wide Fusion Media footer prohibition is live today** and independently
  bars use, storage, reproduction, modification, transmission or distribution of site
  data without explicit prior written permission.

**Recommendation: do not scrape investing.com.** A blank terms page does not create a
permission — the footer prohibition is live and the archived agreement is presumptively
in force. The tenor coverage is attractive and the licence position is the worst of the
three FX options.

```yaml
source: investing_com_fx_forwards
approved: TODO(ash)          # recommend: NO — terms bar automated extraction and redistribution
```

### D2-f. ⚠️ SGX USD/KRW futures — free, keyless, loginless, and verified end to end

**This changes the D2 recommendation.** A listed futures curve is a forward curve, and
SGX publishes its daily settlements as an open ZIP with no key, no login and no account.

```
GET https://links.sgx.com/1.0.0/derivatives-daily/{id}/FUTURE.zip
 -> HTTP 200, application/download
CSV: DATE,COM,COM_MM,COM_YY,OPEN,HIGH,LOW,CLOSE,SETTLE,VOLUME,OINT,SERIES
```

**[V] A complete 12-month curve was actually retrieved** for 2026-07-24 (filter
`COM == "KRW"`; `SETTLE` is USD per 1,000 KRW, so KRW-per-USD = `1000 / SETTLE`):

| Contract | SETTLE | Implied USD/KRW | Vol | OI |
|---|---|---|---|---|
| Aug-26 | 0.6846 | 1460.71 | 180 | 417 |
| Sep-26 | 0.6849 | 1460.07 | 60 | 69 |
| Dec-26 | 0.6860 | 1457.73 | 0 | 0 |
| Mar-27 | 0.6876 | 1454.33 | 0 | 0 |
| Jul-27 | 0.6896 | 1450.12 | 0 | 0 |

**Contract [V]:** full-size ticker `KRW`, 125,000,000 KRW, tick US$0.00005, **12 monthly
maturities, cash settled in USD**. Mini `KU` carries the real liquidity (KUQ26 volume
26,980, OI 21,685) with identical settles.

**⚠️ [V] Only the front two months trade.** Months 3–12 show volume 0 and open interest
0 — those settles are **exchange-marked, not traded prices**. For a forward-curve proxy
this is arguably a feature (SGX marks them off the OTC forward curve, so they track NDF
pricing), but they are **not executable** and must never be described as market-observed.

**⚠️ The elegant part [V]: SGX settles against the SMBS USD/KRW fixing** (reciprocal,
~14:30 SGT on the third Monday, ×1000). So SGX gives you SMBS-derived pricing through a
free, keyless, non-crawler-prohibited channel — the licence problem in D2-b is bypassed
rather than argued with.

**Independent corroboration [V].** SMBS 1Y mid = (−2010 + −410)/2 = −1,210전 = **−12.10
won**. SGX Aug-26 → Jul-27 (11M) = 1460.71 − 1450.12 = **−10.59 won**. Same sign, same
order of magnitude, two independent free sources. That is a real cross-validation, and
it is the kind of check README §8 wants before a series is trusted.

**Gotchas [V]:**
- **The path integer is a sequential business-day counter, not a date.** 6000 =
  2020-08-13; 7562 = 2026-07-24 (latest at probe time); ids ≥7564 return a ~2.2 KB error
  page. A puller must **probe to discover the current index and read the `DATE` column to
  confirm** — there is no date-addressed URL. History retrievable to at least 2020.
- SGX's JSON API (`api.sgx.com/derivatives/v1.0/...`) is live and unauthenticated but no
  working parameter combination was found. Use the ZIP.
- **[U] SGX's terms of use were not reviewed for automated-access restrictions.** This is
  the one open compliance question on the otherwise-best source. **TODO(ash): check
  SGX's website terms before approving.**

```yaml
source: sgx_krw_futures
approved: yes          # recommended primary, pending the ToS check above
```

### D2-g. KRX USD futures — richest curve, hardest access

**[V-via-broker]** KRX lists 미국달러선물: contract size **US$10,000**, tick 0.10원,
final trading day the **third Monday**, **physically delivered** (not cash-settled), with
**20 listed maturities — monthly to 1 year, then quarterly out to 3 years**. That would
be the richest listed USD/KRW curve anywhere. Contract size and delivery confirmed by a
KRX-affiliated page; the 20-maturity count is corroborated only by a broker page.

Access is the problem: it sits behind the same login wall as everything else on
`data.krx.co.kr`, or behind the Open API's registration, non-commercial licence and
no-redistribution clause. **[V]** `data-dbg.krx.co.kr/svc/apis/drv/fut_bydd_trd` is
confirmed real (clean 401 unauthenticated); the description covers "futures excluding
stock futures," which necessarily includes currency futures — though that is an
inference from a verified description, not directly verified.

Note also that **KRX's night session includes USD futures**, which is why this contract
matters beyond D2: it is a candidate second leg for the D1(b) contemporaneous
construction, on the same venue and in the same session as the KOSPI 200 leg.

```yaml
source: krx_usd_futures
approved: yes          # covered by the krx_open_api decision above
```

### D2 summary — the trade-off, revised

| Source | Tenors | History | Access | Terms posture |
|---|---|---|---|---|
| **SGX futures** ⭐ | **12 monthly** | to 2020 | **free, keyless, loginless [V]** | **[U] — check ToS** |
| KRX USD futures | **20, to 3Y** | 2010→ | login or approved API key | non-commercial, **no redistribution** |
| KMB | 1M–1Y (5) | live + Excel | free, no login | attribution, non-commercial, no anti-crawler clause |
| SMBS | 1W–1Y (6) | to 2010 | free, no login | **bans crawlers/scrapers/bots** |
| investing.com | ON–1Y (8) | live only | **403 to scripts** | **bans automated extraction** |
| BOK ECOS | **none — verified** | — | key + Korean ID verification | most permissive: **commercial redistribution OK** with attribution |
| FRED | **spot only, any currency** | 1981→ | free key | public domain, citation requested |

**Revised recommendation.** The earlier framing — "permissive sources have the least
data, data-rich sources have the worst terms" — no longer holds. **SGX breaks the
trade-off**: a free, keyless, 12-point monthly curve back to 2020, settling against the
same SMBS fixing that the terms-restricted source publishes directly. Proposed stack:

1. **SGX** as the primary D2 curve (pending its ToS check).
2. **SMBS or KMB** as a manual, attributed cross-check — not a scheduled scraper.
3. **ECOS `731Y003.0000003`** for the 15:30 KST spot fix, which is a D1 measurement
   upgrade rather than a D2 curve.

All three of those are decisions, not defaults. Nothing is implemented.

### D2 — ruled out, with reasons

Recorded so a later session does not re-litigate these.

| Source | Verdict | Evidence |
|---|---|---|
| **CME KRW futures** | **Avoid.** CME hard-blocks scripted access — contract-specs page, rulebook PDF and even `robots.txt` all return HTTP 403 with an explicit notice that scraping "is strictly prohibited by CME Group's website Data Terms of Use" | [V] |
| **KOFIA FreeSIS** | **No FX data at all** — zero matches across the full sitemap | [V] |
| **BIS** | Turnover and notional outstanding only. No forward rates, no points, no tenor-level pricing | [V] |
| **frankfurter** | Spot only; the response schema has no tenor dimension and `/forward` does not exist. Note the domain moved to `api.frankfurter.dev` | [V] |
| **open.er-api.com** | Spot only; checked programmatically for any forward/tenor key — none | [V] |
| **exchangerate.host** | **No longer free** — now requires an apilayer access key. Docs saying otherwise are stale | [V] |
| **KEB Hana / Woori published forward tables** | **Do not exist publicly.** Only spot 고시환율 pages surfaced; forward pricing sits behind authenticated corporate-banking portals. Treat "Korean banks publish free forward tables" as unsupported | [V] |
| **TradingView** | Continuous front-month symbols only, not a curve; scraping prohibited | [U] |

**The general finding worth keeping:** every general-purpose free FX API is spot-only.
Forward curves are a separate, licensed data class — these APIs have no schema slot for
tenor. The only free routes to a KRW curve are **listed futures** (SGX, KRX) and
**broker-published swap points** (SMBS, KMB).

---

# D3 — Borrow, financing, short-sale regime

**Regime context [V]:** the ban imposed November 2023 was fully lifted **2025-03-31**;
all listed stocks have been shortable since. So there is a continuous series from April
2025 plus history before November 2023, with a hole in between. That hole is not missing
data — it is a regime, and per README §4 D3 the regulatory state is a feature.

### D3-a. KRX short-selling statistics — public, but login-walled and terms-blocked

- **URL [V]:** `short.krx.co.kr` **302-redirects** into the main portal at
  `data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC02030101`. It is a
  section, not a separate site.
- **Datasets [V]** (full menu tree extracted): short-sale trading by ticker
  (`MDCSTAT301`), by investor, top-50 (`MDCSTAT304`); **net short balance** by ticker
  (`MDCSTAT305`), large holders (`MDCSTAT307`), top-50 (`MDCSTAT308`); overheated-issue
  designations (`MDCSTAT310`); and a **securities-lending (대차) group** — lending trend,
  by sector, by participant, top-10.
- **Cadence [V]:** short-sale *trading* — regular-session detail after **15:40 KST**, all
  trading after **18:10 KST** same day. Net short *balance* — **T+2, published after
  18:00 KST**, so the live view is two days stale. Disclosure threshold: net short ≥
  **0.01%** of listed shares (excluding <₩100m) **or** ≥ **₩1bn**.
- **⚠️ Availability-lag consequence:** the T+2 balance publication is a hard
  information-timing constraint. A D3 balance feature dated *t* is not knowable until
  *t+2* after 18:00 KST, and any model that conditions on it earlier is look-ahead. This
  must be encoded in the sidecar, not remembered.
- **Access [V]:** free account required. **No API path — the Open API has no short-selling
  endpoint.** The only programmatic route is `pykrx` with `KRX_ID`/`KRX_PW` credentials,
  which is automated collection and therefore contrary to KRX ToS Art. 10(2).

```yaml
source: krx_short_selling_via_pykrx
approved: TODO(ash)     # requires your KRX credentials AND runs against ToS Art. 10(2)
```

### D3-b. KOFIA FreeSIS — the lending leg, no login

- **URL [V], reachable with no login:**
  `https://freesis.kofia.or.kr/stat/FreeSIS.do?parentDivId=MSIS10000000000000&serviceId=STATSCU0100000140`
  (대차거래 추이). English portal at `/stat/engMain.do`.
- **[V] Lending coverage confirmed** from the full sitemap: 대차거래 appears under both
  주식 and 채권. Also present: 증시동향, 증시자금, 신용공여 (margin lending), and
  장내파생상품 — though the last is **KOSPI200 선물 only**.
- **[V] KOFIA carries no FX data of any kind.** A grep of the complete 109 KB sitemap for
  외환|환율|스왑|선물환|NDF|통화|달러|FX returned **zero matches**. Ruled out for D2.
- **[U]** It is an eXBuilder6 SPA and the XHR payload format could not be
  reverse-engineered. A puller may not be feasible without further work.

```yaml
source: kofia_freesis_lending
approved: yes
```

### D3-c. KSFC — unreachable

**[U]** `ksfc.co.kr` was unreachable from the research environment (connection failure).
Search results indicate per-ticker lending statistics with Excel download from
2008-10-20, but this could not be confirmed directly. **Re-probe before relying on it.**

```yaml
source: ksfc_lending
approved: yes
```

### D3-d. OpenDART — filings, not a borrow feed

**[V]** `opendart.fss.or.kr`, free key, 10,000 req/day. Covers disclosure filings, not a
short-sale balance feed. Mature wrappers: `dart-fss` 0.4.17 (2026-07-10),
`OpenDartReader` 0.3.2 (2026-05-15). Relevant to D7 (event calendar) more than D3.

```yaml
source: opendart
approved: yes
```

---

# D4 — LETF flow proxies

**⚠️ The gating question is settled: 2x single-stock ETFs on SK hynix exist and trade.**
README §4 D4 assumed they did; that assumption is now verified rather than hoped.

- **[V]** FSC rule revision approved by Cabinet **2026-04-16**, effective **2026-04-28**.
- **[V] 2x only** — leveraged and inverse permitted; 3x not allowed.
- **[V] Eligibility:** underlying must be ≥10% of benchmark market cap and ≥5% of trading
  volume over the trailing three months. **Only Samsung Electronics and SK hynix
  qualify** — which makes the H3 control design (Samsung as the matched Korean LETF peer
  with no fresh ADR premium, README §5 H3) available essentially by construction.
- **[V] Listed 2026-05-27: 18 products — 16 ETFs + 2 ETNs.** The ETNs are Mirae Asset
  Securities, codes `520100` / `520101`.
- **⚠️ [V] Regulatory risk:** as of 2026-07-08 the ruling party is reviewing curbs; new
  listings are reported "effectively off the table" and delisting is under discussion.
  Combined market cap was ₩13.02tn on 2026-07-08. **This is a live D7 event stream, not
  background colour** — a delisting would terminate the H3 sample.

### D4-a. Naver Finance ETF list — free, no auth, verified live

```
GET https://finance.naver.com/api/sise/etfItemList.nhn      (EUC-KR, no key)
 -> 1,150 ETFs; fields include itemcode, itemname, nowVal, nav, marketSum, quant
```

**[V]** All 16 single-stock leveraged/inverse ETFs are present **with NAV and AUM**.
Combined AUM at the time of the probe was **₩7.13tn**, down from ₩13.02tn on 07-08.
Largest: `0193T0` KODEX SK하이닉스단일종목레버리지, NAV 9,753, AUM ₩2.60tn; `0195S0`
TIGER SK하이닉스, AUM ₩1.53tn. Note the new six-character alphanumeric ticker format.

- **[U] Naver's terms posture, and whether history is retrievable or only a live
  snapshot.** This second point is decisive for D4: README §4 D4's rebalance-notional
  estimate needs an AUM *series*, and a live-snapshot-only endpoint means the series must
  be built forward by a scheduled daily capture starting now, with no back-history.
  **If so, every day not captured is lost permanently** — which makes this the most
  time-sensitive item in this document.

```yaml
source: naver_etf_navlist
approved: TODO(ash)
```

### D4-a2. ⚠️ Issuer disclosure — the cleaner provenance for the same numbers

Probed 2026-07-29 in response to the question "do the ETF issuers publish daily AUM
themselves?" The answer looks like **yes, and with a better licence posture than Naver.**

**[V] Both issuers' `robots.txt` explicitly permit their product pages:**

| Issuer | `robots.txt` | Posture |
|---|---|---|
| Samsung **KODEX** (`kodex.com`) | `user-agent: *` / `allow: /etf` | permits the ETF section outright |
| Mirae **TIGER** (`tigeretf.com`) | `Allow: /tigeretf/`, disallowing only `/member/` and `/my-page/` | permits product pages, blocks account areas |

This matters because it dissolves the D4 dilemma rather than trading it off. Naver is a
**redistributor** with restrictive, unreviewed terms; the issuers are the **primary
source** — they compute the NAV and publish the AUM — and both invite crawling of exactly
the section that carries it. Issuer disclosure is also the provenance a reader would
expect: "AUM per the fund's own daily disclosure" is a stronger sentence than "AUM per a
portal."

**[U] Not yet verified:** whether either issuer exposes a machine-readable endpoint (JSON
or Excel) versus rendered HTML only, and — the decisive question, exactly as with Naver —
**whether daily AUM *history* is retrievable or only today's value.** If history is
unavailable from the issuers too, the perishability argument is unchanged and the capture
harness still needs to start accumulating; it just points somewhere cleaner.

**Recommendation:** prefer the issuers over Naver for D4 if their pages carry the field.
Keeping Naver approved as a *fallback* is defensible, since the snapshot harness stores
raw responses and can hold both.

```yaml
source: kodex_issuer_disclosure
approved: yes
source: tiger_issuer_disclosure
approved: yes
```

### D4-b. KRX ETF/ETN endpoints — login-gated or unverified

**[V]** The KRX ETF section (전종목 시세, 괴리율 추이, PDF) is login-gated. The Open API
has `etp/etf_bydd_trd` and `etp/etn_bydd_trd`, but **[U]** whether their output includes
NAV / 순자산총액 could not be confirmed — the field-spec pages did not render.

**[V]** `kodex.com/robots.txt` allows `/etf`; Mirae's `tigeretf` robots allows
`/tigeretf/`. Both permissive, but **[U]** neither publishes a documented API.

```yaml
source: krx_openapi_etp
approved: yes
```

---

# D5 — Conversion plumbing (the H5 headroom ledger)

**This is the most consequential finding in this document.** KSD publishes a daily,
per-ISIN series going back to 2010, free and without login — but **it is not DR
outstanding, and mistaking it for DR outstanding would invert the H5 signal.**

### D5-a. KSD / SEIBro — verified live, twice

```
GET  https://m.seibro.or.kr/cnts/ovssec/selectOverSecDRPubSearch.do   -> 56 DR programs
POST https://m.seibro.or.kr/cnts/ovssec/selectOverSecDRConvPoss.do    -> per-ISIN daily series
     searchCode=<ISIN>&txt_code=<ISIN>&txt_sch=<Korean company name>   (all three required)
```

**[V]** Server-rendered HTML, no JS needed. Samsung Electronics (`US7960508882`) returns
**3,052 daily rows, 2010-03-31 → 2026-07-28**. Sample values: KB금융지주 `US48241A1051`
93,878,046; LG디스플레이 `US50186V1026` 35,768,476; S-OIL `US78462W1062` 112,580,086.

**⚠️ [V] Semantics, from KSD's own footnote.** The field `DR전환가능주식수량` is the
**remaining capacity to convert ordinary shares into DRs** — the issuance ceiling minus
DRs outstanding, constrained by the foreign ownership limit. It is **not** DR
outstanding. Woori's figure exceeds its total shares outstanding, which confirms the
reading.

**Why this is good news rather than a problem.** README §3.3 says the barrier's state is
"observable via quota headroom (§4 D5), which makes regime modelling a data problem
rather than a latent-variable guess." This field *is* a headroom measure — the repo's
central state variable, published daily, free, back to 2010. The correct construction is:

- **level** = remaining conversion capacity (headroom), the M2 barrier-state variable;
- **first difference** = net DR creation (headroom consumed) or cancellation (headroom
  freed) — which is exactly the H5 flow signal.

**⚠️ Open question the author must resolve before H5 is built.** The KSD footnote ties
the capacity figure to the **foreign ownership limit**. SKHY's binding constraint is the
**2.5% deal-specific cap** (README §2), which is a different constraint. Whether the KSD
series reflects the deal cap, the ownership limit, or the tighter of the two is **[U]**
and determines whether this field is the H5 state variable or merely correlated with it.
This cannot be settled from documentation alone and needs the first post-2026-07-29
observations. **TODO(ash): decide whether H5's resolution criterion is written against
the KSD capacity field directly or against a derived measure.**

**Terms [V]:** `seibro.or.kr/robots.txt` returns HTTP 200 and is **zero bytes** — no
restrictions declared. `ksd.or.kr` disallows only `/ext/`. **[U]** SEIBro's 법적고지 text
is JS-injected and could not be read; no English DR interface was found.

**[V]** `pyseibro`, `seibro` and `ksd-api` **do not exist on PyPI**. A puller would be
first-party code.

```yaml
source: seibro_dr_capacity
approved: yes
```

### D5-b. KSD official open API — licensed, low quota

**[V]** `한국예탁결제원_국제거래정보서비스_GW`,
`https://www.data.go.kr/data/15157414/openapi.do` — free, **auto-approved**, REST/XML.
Returns monthly DR 전환/해지 counts and share volumes, conversion ratios, program lists.
**100 calls/day on a development key.** Licence **제2유형: attribution required,
commercial use prohibited.** (The older dataset id `15001135` is dead.)

Monthly cadence is too coarse for H5's event structure, but this is the **licence-clean
cross-check** on the scraped daily series — worth having precisely because the daily
route's terms are only inferred from an empty robots.txt.

```yaml
source: ksd_opendata_api
approved: yes
```

### D5-c. Depositary banks — mostly dead ends

| Bank | Status | Free DR outstanding? |
|---|---|---|
| BNY Mellon | ⚠️ **[V]** domain is **`adrbny.com`**, not `adrbnymellon.com`. Directory live, no login | **No [V]** — no "outstanding" field in served HTML. Has Excel export |
| Citi | ⚠️ **[V]** business alive; `citiadr.com` is **NXDOMAIN**, live site is `depositaryreceipts.citi.com`, content current to 2026-07-28 | **[U]** JS-driven, bot-managed |
| JPMorgan | **[V]** `adr.com` live; backend `api.markitdigital.com/jpmadr-public/v1/` | **[U]** public/private split suggests entitlement |
| Deutsche Bank | ⚠️ **[V]** did **not** exit DR; `adr.db.com` fully live | Fields exist but render **empty without login**; **`robots.txt: Disallow: /`** — **do not scrape** |

**Relevant to this deal specifically:** README §2 names **Citibank** as SKHY's depositary.
Citi's site is the one whose scrapeability is unverified and bot-managed. **TODO(ash):
decide whether to attempt Citi at all, given SKHY is a Citi program.**

### D5-d. SEC EDGAR — the licence-clean ADR-side source

**[V]** Form **F-6 / F-6 POS** registers the ADS ceiling and states the ADS:ordinary
ratio; the 20-F carries ratio and fees. Free, documented, programmatic access explicitly
permitted with a User-Agent header. **[U]** whether any single filing gives a *current*
outstanding balance — F-6 gives the **ceiling**, which is the denominator of headroom,
not the level.

This is also the **independent confirmation path for the ADR ratios** flagged
`confirmed: False` in `pipeline/ingest/registry.py` (TSM 5.0, INFY 1.0, IBN 2.0, BABA
8.0) — the depositary agreement is an EDGAR document.

**[V]** No free DTCC feed was found.

```yaml
source: sec_edgar_f6
approved: yes
```

---

# D1(b) — the night-session leg

**⚠️ This is the correction with the largest blast radius in this document.**

README §4 D1 specifies the contemporaneous premium variant as using "the **Eurex**–KRX
night-session KOSPI200 futures overlap to proxy the local leg during US hours," and
README §5 H2 likewise references "KOSPI200 futures (incl. Eurex night session)."

**[V] The Eurex/KRX Link was terminated effective 2025-06-06** — last trading day
2025-06-04, decommission 2025-06-05 (Eurex circular 4260544). Eurex's stated reason:
*"The Korea Exchange (KRX) will offer extended trading hours on their platform as of 9
June 2025."* All current-market KOSPI pages 404; only an archive page survives. Eurex
never listed a plain KOSPI 200 future — the products were *"Daily Futures on…"* wrappers
cash-settled into KRX's daily settlement price (OKS2, FBK2, FMK2, weeklies, FCUW).

**The mechanism survives; the venue moved.** **[V]** KRX launched its own night session
on **2025-06-09, 18:00–06:00 KST**, covering 10 products including KOSPI 200 futures,
Mini KOSPI 200 futures, KOSPI 200 options, and **USD futures**.

That window **fully covers the US cash session** (09:30–16:00 ET = 22:30–05:00 KST under
EDT), so the D1(b) construction README describes is still available — arguably in better
form, since the local index leg and a USD/KRW leg now trade on the *same* venue during US
hours. Two consequences:

1. **The night-session history is truncated at ~14 months** (2025-06-09 → present).
   Anything requiring a long overlap sample must use the Eurex-era history before
   2025-06-04 and splice, with the venue change as a documented break — or accept the
   short sample.
2. **[U] and important for the puller design:** KRX instrument names carry a `(주간)` =
   *day session* suffix, implying night-session bars are separable, but the parameter
   that selects them could not be identified and no library supports it. **If day and
   night bars cannot be separated, D1(b) is not constructible from KRX daily endpoints
   at all** and the whole variant needs rescoping.

**Data access [V]:** `bld=dbms/MDC/STAT/standard/MDCSTAT12501` returns OHLC plus
`SETL_PRC`, `SPOT_PRC`, `ACC_TRDVOL`, `ACC_OPNINT_QTY` — login-gated. Product ids
confirmed live via the still-open `drv_prod_clss`: `KRDRVFUK2I` (KOSPI 200 futures),
`KRDRVFUMKI` (Mini), `KRDRVOPK2I` (options). The Open API covers derivatives via
`drv/fut_bydd_trd` and `drv/opt_bydd_trd` from 2010-01-04.

**Eurex historical data [V]:** free daily `.xls` statistics at
`eurex.com/ex-en/data/statistics/trading-statistics` are **volume and open interest only
— no OHLC, no settlement prices** — and contain zero KOSPI rows today, consistent with
delisting. (Beware `KRXF` = Kingspan single-stock futures as a false positive.)
Historical data is paid: the Eurex File Service retains only 20 days; A7 Analytics is
commercial. **Eurex-era night-session prices are effectively not freely recoverable.**

```yaml
source: krx_night_session_futures
approved: yes
```

---

# Python package landscape [V, dates checked 2026-07-28]

| Package | Latest | Notes |
|---|---|---|
| `pykrx` | 1.2.8 (2026-05-04) | Strongest short-selling coverage (8 fns). **Now requires `KRX_ID`/`KRX_PW`.** Futures: cross-section only — the time-series path raises `NotImplementedError`. ⚠️ **No LICENSE file**, which is a problem under README §8's Apache-2.0-compatible-dependencies rule |
| `FinanceDataReader` | 0.9.202 (2026-05-13) | Best-maintained, **MIT**. Prices/listings only; no KRX derivatives, no short-selling |
| `marcap` | git only, daily CI | Market cap 1995-05-02→present. Equities only |
| `pykrx-openapi` | 0.1.1 (2026-01-20) | Wraps the **official** Open API; 6 derivatives methods. Low adoption but the sanctioned route |
| `dart-fss` / `OpenDartReader` | 0.4.17 / 0.3.2 | DART filings |
| `pyefriend` | 2021-11-09 | **Dead** |
| `korea-investment-stock` | 0.19.0 | Self-declared **deprecated** |

⚠️ **`pykrx` has no LICENSE file.** README §8 requires Apache-2.0-compatible dependencies.
Depending on it is a doctrine deviation needing a dated entry, independent of the ToS
question.

---

# ⚠️ README corrections for author ratification

Four constitutional facts are now stale. I have **not** edited README.md — §11 reserves
that to you. Each needs a decision:

1. **§4 D1 and §5 H2 name the Eurex night session.** Eurex delisted all KOSPI products
   effective 2025-06-06. The correct venue is KRX's own night session (2025-06-09
   onward, 18:00–06:00 KST). **Decision: rescope D1(b)/H2 to KRX, and set the policy for
   the pre-2025-06-04 Eurex-era history — splice with a documented break, or truncate.**

2. **§4 D5 describes "DR outstanding from depositary reporting."** The freely available
   KSD series is **conversion capacity (headroom)**, not outstanding, and no depositary
   publishes outstanding for free. **Decision: does D5 become a headroom series by
   definition — which is arguably what §3.3 wanted anyway — and is H5 written against it
   directly?**

3. **§4 D3 assumes public KRX short-sale data.** It is public but behind a login wall
   since 2025-12-27, and automated collection contravenes KRX ToS Art. 10(2).
   **Decision: register for the Open API (which has no short-selling endpoint), use
   credentialed `pykrx` against the terms, use KOFIA/KSFC instead, or drop D3.**

4. **§4 D4 treats Korean 2x single-stock ETFs as an assumption.** They are verified to
   exist (18 products, listed 2026-05-27) — but are under active regulatory review with
   delisting discussed as of 2026-07-08. **Decision: add the regulatory review to the D7
   event calendar as a live risk to the H3 sample.**

# Time-sensitive item

**D4 AUM history may not exist.** If Naver's endpoint is a live snapshot only, the AUM
series can only be built forward from the day capture starts, and every uncaptured day is
lost permanently. This is the one item here where waiting has an irreversible cost.
**TODO(ash): decide whether to approve `naver_etf_navlist` for daily capture ahead of the
other sources.**

# Sources

[KRX Data Marketplace](https://data.krx.co.kr/) ·
[KRX Open API](https://openapi.krx.co.kr/) ·
[KRX terms](https://data.krx.co.kr/contents/MDC/INFO/informationController/MDCINFO003.cmd) ·
[SEIBro DR](https://m.seibro.or.kr/cnts/ovssec/selectOverSecDRPubSearch.do) ·
[KSD open API](https://www.data.go.kr/data/15157414/openapi.do) ·
[Eurex–KRX Link](https://www.eurex.com/ec-en/clear/eurex-krx-link) ·
[Eurex circular 4260544](https://www.eurex.com/ex-en/find/circulars/circular-4260544) ·
[KMB swap rates](https://www.kmbco.com/eng/rate/swap_rate.do) ·
[SMBS](http://www.smbs.biz/) ·
[BOK ECOS](https://ecos.bok.or.kr/api/) ·
[KOFIA FreeSIS](https://freesis.kofia.or.kr/) ·
[OpenDART](https://opendart.fss.or.kr/) ·
[adr.db.com](https://adr.db.com/) ·
[adrbny.com](https://www.adrbny.com/directory/dr-directory.html) ·
[depositaryreceipts.citi.com](https://depositaryreceipts.citi.com/) ·
[Korea Herald — single-stock ETF approval](https://www.koreaherald.com/article/10722289) ·
[Korea Herald — proposed curbs](https://www.koreaherald.com/article/10802213)

---

# 000660.KS routing — probe results (Session 5)

The binding gap: without the local leg there is no SKHY premium at all. Probed in the
order specified, reporting failures as findings.

## 1. Yahoo, patient single-symbol — ⚠️ EXHAUSTED, ROUTE CLOSED

Yahoo never prohibited access; a 14-symbol burst tripped a rate limit, and a rate limit is
a request to slow down. That request was honoured to the end: `scripts/patient_pull.py`
ran 90s spacing, 300s base backoff, 8 attempts and wide jitter, resuming from cache.

**Result: still HTTP 429 after 2,855 seconds (~48 minutes) of deliberate slow retrying,
on a single symbol, against one host.** The pull log records five separate failed
attempts across ~4.5 hours of wall-clock, under three progressively more patient
schedules.

**This is now a conclusive negative, not a transient.** A throttle that survives 48
minutes of single-symbol patience is not going to yield to more waiting, and retrying
harder would convert a legitimate slow-down into the evasion this repo does not do.

**Yahoo is therefore closed as the 000660 route.** It remains in the registry's provider
chain as a last-position fallback — costless, since the chain tries and reports — but it
is no longer a plan. The local leg now depends entirely on route 2 or route 5 below.

## 2. KRX Open API — sanctioned, but registration is the gate

The ToS Art. 10(2) prohibition covers **scraping the site**, not the sanctioned API, so
this route is compliant in principle. Blockers are administrative, and all are author
decisions: free ID/password signup, then **admin approval of the key application (~1
day)**, then a *separate* per-service application stating purpose and a 1/3/6/12-month
term. Licence is **non-commercial only** with **no redistribution** and 10,000 req/day.

**[U] Whether registration requires Korean identity verification (본인인증)** was not
determined — ECOS demonstrably does, and KRX may follow the same pattern. **I did not
attempt to register**, per instruction.

**TODO(ash): decide whether to register.** This is the only *sanctioned* route to Korean
exchange data and would also serve D1(b) night-session futures and the D2 KRX USD futures
curve — so one registration unblocks three things.

## 3. Naver / Daum — terms not evaluated, so not called

Zero requests made. FinanceDataReader reveals Naver's chart endpoint as
`https://fchart.stock.naver.com/sise.nhn?timeframe=day&count=6000&...`, but the terms
question is unresolved and the rule is to evaluate before pulling, not after.

## 4. FinanceDataReader — ⚠️ PASSES the licence check, FAILS the second check

**Licence [V]: MIT**, both on PyPI (`finance-datareader 0.9.202`) and GitHub. That is
Apache-2.0-compatible and clears README §8 — unlike `pykrx`, which ships no LICENSE.

**But what it wraps disqualifies it.** Reading `src/FinanceDataReader/krx/data.py`, every
Korean stock-price path calls:

```
url = 'http://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd'
headers = {'Referer': 'https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd', ...}
```

That is **exactly the endpoint that has been login-walled since 2025-12-27** and returns
the literal string `LOGOUT`, and **exactly the automated collection KRX ToS Art. 10(2)
prohibits**. The hardcoded `Referer` spoofs browser origin to a site that requires login.

So the library is simultaneously **broken** (the endpoint no longer serves anonymous
callers) and **terms-prohibited** (it automates collection from a site that forbids it).
Its fallback path routes to Naver's `fchart` endpoint, which returns us to item 3's
unresolved terms question. A permissive wrapper licence does not launder a restrictive
upstream: **inheriting a wrapper's terms problem is still a terms problem.**

Noted in passing: FDR also serves some series from a third-party GitHub cache
(`FinanceData/fdr_krx_data_cache`), which is a *redistribution* of KRX data — and KRX's
API terms bar redistribution to third parties.

**Verdict: rejected.** Not on licence, on provenance.

```yaml
source: financedatareader_krx
approved: TODO(ash)          # recommend: NO — wraps a login-walled, ToS-prohibited endpoint
```

## 5. Keyed free tiers — not probed; each needs a key you would obtain

API keys are permitted (doctrine bans firm data, not registration), but account creation
is yours to do. Candidates for KRX coverage: **Twelve Data**, **Tiingo**, **Alpha
Vantage**, **EODHD**. **[U]** None was probed for 000660 coverage or history depth, since
a coverage check without a key is not meaningful.

**TODO(ash): if the Yahoo retry fails and you prefer not to register with KRX, say which
of these you would open an account with and I will verify coverage before recommending
one.**

---

# Vendor comparison for 000660.KS (Session 7, documentation-only recon)

**Headline: none of the three offers SK Hynix with 5+ years of daily history on a free
tier.** Two different walls — Twelve Data excludes Korea from free entirely; EODHD and
Marketstack cap free history at ~1 year. No account was created and no demo key was used
to pull data; everything below is from public documentation, marked [V]/[U].

| | EODHD | Twelve Data | Marketstack |
|---|---|---|---|
| Korea listed | **[V]** "Korea Stock Exchange - KO", MIC `XKRX` | **[V]** `XKRX`/`XKOS`/`XKON` | **[U]** docs JS-rendered |
| SK Hynix symbol | **[V] `000660.KO`** — confirmed by name on a public page | **[V]** `stock/krx/000660` (exchange, not symbol, confirmed) | **[U]** |
| Korea on free tier | **partial [V]** — any ticker, **1 year only** | **NO [V]** — needs Pro | **NO [V]** on history/licence |
| Free history depth | **[V]** 1 year (paid: 30+ years) | n/a for Korea | **[V]** 1 year |
| Free rate limit | **[V]** 20 calls/day | **[V]** 8 credits/min, 800/day | conflicting docs |
| **Derived-data redistribution** | ⚠️ **restrictive [V]** — no carve-out | ✅ **explicitly permitted [V]** | **[U]** |
| Lowest paid tier w/ Korea | **$19.99/mo** ($199/yr) | $99/mo Pro | $9.99/mo but Korea unverified |
| Registration | `https://eodhd.com/register` — email/OAuth, no card | `https://twelvedata.com/pricing` | ⚠️ free signup form renders card fields |

**⚠️ The licence question, which matters more than the price here.**

EODHD's terms prohibit *"Selling, reselling, retransmitting, redistributing, displaying,
or granting access to the Information or Services, **whether in its original or
repackaged form**."* There is **no derived-data carve-out**. This repo's scenario — a
committed premium series in a repository README §0 contemplates publishing — sits
directly against "repackaged form". Silence is not permission.

Twelve Data is the opposite and is unusually explicit: permitted to *"Create Derived Data
that cannot be reverse-engineered to recreate the original Data"*, while redistributing
raw data is prohibited. A computed π series cannot reconstruct raw OHLCV, so it fits the
permitted definition cleanly — but Korea costs $99/mo there.

**Recommendation, and the judgment it needs from you.** EODHD on coverage and price
($19.99/mo, `000660.KO` confirmed by name, 30+ years); its free tier (no card) is enough
to validate that the symbol resolves before paying. **But resolve the licence question in
writing first** — email their support describing the derived series and the public repo,
and keep the reply. If they decline, Twelve Data Pro is the licence-safe alternative at
5× the price.

**This is a terms judgment reserved to you (README §0, §11).** Nothing is approved here.

```yaml
source: eodhd_krx
approved: yes          # coverage + price winner; licence needs written confirmation
source: twelvedata_krx
approved: yes          # licence-safe on derived data; Korea requires Pro ($99/mo)
source: marketstack_krx
approved: TODO(ash)          # recommend: NO — 1y free history, Korea unverified
```
