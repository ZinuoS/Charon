# Confound register

Every effect this repo reports is reported against this list. A confound recorded here
is not thereby neutralised — recording it is how a joint effect stops being presented
as a clean one.

Format: what the confound is, which hypotheses and designs it touches, why it cannot be
cleanly separated, and how results must be phrased.

---

## C1 — 2026-07-29: conversion-open and Q2 earnings fall on the same session

**Status:** live, unresolvable by design.
**Source:** README §2, §5 confound register.

The two-way ADR/local conversion channel opens on 2026-07-29, the same trading day as
SK Hynix's Q2 2026 earnings. These are the two largest scheduled shocks to the premium
in the sample, and they are perfectly collinear on that date.

**Mechanically distinct, empirically fused.**

- *Conversion open* acts on the **barrier state**: it changes the arbitrage capacity of
  the channel (README §3), and so should move the premium through the supply side.
- *Earnings* acts on the **fundamental**: it moves both legs, and moves the premium only
  through differential repricing between the two participant pools.

They predict different signatures — a barrier effect should show up in the premium with
little change in the local line's own volatility, while an earnings effect should move
both legs — but with **one observation** that distinction is not identified. There is no
statistical fix for n=1.

**Affected.** H5 directly (its entire event is this date). H3 and H4 indirectly, since
07-29 is a high-leverage observation for any effect estimated over the short SKHY
sample. Any M2 regime transition dated to 07-29.

**Reporting rule.** Effects estimated on or spanning 2026-07-29 are reported as the
**joint** effect of conversion-open-and-earnings, always named as such. No result may
attribute the 07-29 move to the barrier alone. Where a design can exclude the date, the
exclusion is stated and the result reported both ways.

**Partial mitigations available, none sufficient alone.**

1. Comparator earnings dates in D6 give an earnings-only baseline for a cross-listed
   pair with no simultaneous plumbing change.
2. Samsung (Korean peer, same HBM/AI cycle, no ADR premium) isolates the fundamental
   component of the Korean move.
3. The *lag structure* differs: settlement plumbing takes days, earnings repricing takes
   hours. Post-event dynamics may be more informative than the event-day return.

**TODO(ash):** decide before S6 whether the H5 resolution criterion is evaluated on the
07-29 date itself or only on subsequent, unconfounded headroom episodes. This is a
pre-registration decision and belongs in `calls.yaml`, not here.

---

## C2 — Close-to-close asynchronicity in D1(a)

**Status:** live, quantifiable, partially correctable at S2.
**Source:** README §4 D1.

The KRX close (15:30 KST) and the Nasdaq close (16:00 ET) are **13.5 hours** apart. A
close-to-close premium therefore pairs legs that were never observed simultaneously,
and part of every move in the D1(a) series is a measurement artifact: news arriving in
the gap moves the ADR leg with the local leg frozen.

This is not a small effect for SKHY. The premium path in README §2 (51 → 19 → 33 → 22
within three weeks) spans a period in which the ADR leg alone could move several percent
overnight, and a naive reading attributes all of that to premium dynamics.

**Affected.** Everything built on D1(a): every H, and the M1 measurement layer itself.

**Treatment.** D1(b) — the synthetic contemporaneous variant using the KRW NDF and the
Eurex–KRX night-session KOSPI200 futures overlap — exists precisely to decompose
measured π into a true premium and an asynchronicity term. Until D1(b) has a confirmed
source (`docs/data_sources.md`: neither leg is sourced as of S1), **every chart and
table derived from D1(a) carries the stale-measure label on its axis**, as the S1 smoke
charts do.

**Compounding sub-confound.** The FX leg has its own snapshot time, which is neither of
the two equity closes and is not documented by the provider (assumed 21:00 UTC; see
`pipeline/ingest/registry.py`). So D1(a) as currently constructed mixes *three*
observation instants, not two.

**Update 2026-07-28 — this sub-confound is now fixable.** Two sourcing findings
(`docs/data_sources.md` D2-c, D2-d) bear directly on it:

1. **BOK ECOS table `731Y003` item `0000003` is a 원/달러 close stamped 15:30 KST** — the
   same instant as the KRX equity close. Rebuilding the D1(a) FX leg on it would collapse
   the local side to a single contemporaneous observation, reducing this from a
   three-instant problem to a clean two-instant one (KRX + FX at 15:30 KST vs. Nasdaq at
   16:00 ET). The residual would then be the genuine 13.5h asynchronicity C2 is about,
   with no FX-timing term contaminating it.
2. **FRED `DEXKOUS` is a noon-New-York fix.** It does not fix anything on its own, but a
   third, differently-timed spot series lets the FX-timing component be **measured** by
   differencing two known-time series rather than assumed away.

Both are author decisions (**TODO(ash)**), not defaults: changing the FX leg changes the
definition of π, which is a measurement decision reserved under README §11. Recorded here
so that whoever builds M1 knows the artifact is reducible and does not treat the current
three-instant construction as forced.

---

## C3 — Korea-wide beta contaminates the premium during broad market moves

**Status:** live, controllable.
**Source:** README §2 ("~22% on 07-28, ADR −8.76% amid broad Korea weakness").

When the whole Korean market moves, the ADR and local legs do not reprice in lockstep,
because the two participant pools have different risk appetites and different session
hours. Premium changes on such days partly reflect market-wide beta rather than anything
about the conversion channel.

**Affected.** H2 most directly (the KOSPI200 basis is the dependent variable and the
index is the contaminant). H3's event windows, where a close-window premium change may
be an index move rather than a rebalance flow.

**Treatment.** Control for KOSPI/KOSPI200 returns and for Samsung as a matched Korean
AI-cycle peer. TODO(ash): confirm the control set before H2 is built at S5.

---

## C4 — SKHY sample length: n ≈ 13 trading days at S1

**Status:** live, decays with time, never fully resolved for this deal.

The SKHY series begins 2026-07-10. Any statistic computed on it has an effective sample
in the low tens, and the doctrine is explicit: "n≈12 SKHY days is not validation"
(README §8).

**Affected.** Every hypothesis, as a hard ceiling on what SKHY data can establish.

**Treatment.** All backtests live on the D6 comparator panel; SKHY is forward test only.
This is a doctrine rule rather than a mitigation, and it is the reason D6 coverage — not
SKHY coverage — is the binding constraint on S4/S5.
