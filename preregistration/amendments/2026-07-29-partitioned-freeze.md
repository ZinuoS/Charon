# Amendment 001 — Partitioned freeze around the 2026-07-29 Q2 release

**File:** `preregistration/amendments/2026-07-29-partitioned-freeze.md`
**Author:** Ash (sole ratifying authority per README §11)
**Committed:** 2026-07-29 (UTC; see the freeze commit hash recorded in `docs/gate_reports/S0.md`)
**References:** `calls.yaml` — **no prior commit** (the repository had zero commits before
this freeze; Class P is therefore empty, declared below rather than deleted).

---

## 1. Event record

SK Hynix released 2Q26 results **before the 2026-07-29 KRX open (09:00 KST)** — the Q2
conference call is documented at 09:00 KST (6-K, 2026-07-15). The exact release minute is
not in the public record retrieved; it is stated here as *pre-open* and may be pinned more
precisely by the author. Per `docs/confounds.md` C1, this date is simultaneously the
opening of two-way ADR/common-share conversion. **The earnings information event has
occurred; the conversion-flow event (first observable movement in DR-outstanding headroom,
D5) has not** — as of the freeze the capped programme US78392B2060 reads headroom 0 with a
single observation dated 2026-07-15.

## 2. Declaration

At the time of this amendment the author has observed: the earnings release and associated
headlines; the SKHY premium path 2026-07-10 → 2026-07-28 (repo data, 12 observations,
15.8%–51.6%, last 22.6%); and **no** post-release US-session trading, **no** post-release
derivatives closes, and **no** DR-outstanding flow (the capped programme has not moved).

## 3. Partition of registered calls

Each call in `calls.yaml` is assigned exactly one class, appended as `freeze_class:` and
immutable after this commit.

- **Class P (pre-event frozen): EMPTY.** No call was committed to git before the release
  timestamp — the repository had zero commits until this freeze. This is declared
  explicitly rather than by deleting the class. **No claim in this repository is a blind
  pre-event forward test.**

- **Class C (post-earnings, pre-flow frozen): H5** (`h5_quota_ledger`). Its resolution
  depends on DR-flow data (D5) that did not exist and was not forecastable from the
  earnings release at the time of this amendment. Frozen with the earnings outcome
  acknowledged as known context. Its threshold and four-branch resolution criterion (the
  option-(a) scoping, with an INDETERMINATE branch for the consent-gate divergence) are as
  in `calls.yaml`, unchanged by this amendment.

- **Class X (event-contaminated; exploratory): H1, H2, H3, H4.** These are analysed as
  exploratory hypotheses, labelled as such (`status: exploratory`), and are **not reported
  as pre-registered forward tests anywhere, ever.** They may be re-registered as new calls
  with new resolution dates only via a subsequent numbered amendment. H4's realized
  variance decomposition and H5's headroom monitor have been *run* (see notebooks); running
  an exploratory hypothesis and reporting it as exploratory is permitted, registering it
  retroactively is not.

## 4. Rationale

A pre-registration ledger that survives contact with an event calendar by partitioning
honestly is evidence of process; one that survives by silence is evidence of nothing. The
confound between earnings and conversion-open was registered in `docs/confounds.md` before
the event and fired as documented. No claim here presents a Class C call as blind to
earnings, and no claim presents a Class X call as pre-registered. Class P being empty is
the honest cost of not having committed the ledger before the release — recorded, not
hidden.

## 5. Binding rules going forward

1. This file is append-only history; never edited after commit.
2. `calls.yaml` received only the `freeze_class:` additions and the H5 value fill described
   above — no value change to any already-frozen field in a later commit.
3. Any future in-window information event triggers the same protocol by a new numbered
   amendment.

**Signed:** Ash — **confirmed 2026-07-29.** The author has ratified the H5 threshold values and this partition.

*Note (recorded per the deviation log): the H5 threshold values and this amendment's
structure were drafted by an analysis session and applied on the author's explicit
instruction to freeze. **The author has since confirmed both the H5 numbers and this
amendment (2026-07-29).** The exact release minute in §1 stands as "before the 09:00 KST
KRX open" — the documented bound — unless the author later pins it more precisely by a
further amendment.*
