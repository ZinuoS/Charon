# PROPOSED values for the H5 Class C freeze

**Status: PROPOSAL ONLY. Nothing here is in `calls.yaml`.** README §11 permits analysis
sessions to propose and forbids them to ratify. Reply "accept" (or edit any line) and I
will apply them, write Amendment 001, and stage the commit for you to run.

These are derived from what the data actually showed on 2026-07-29, not invented to look
plausible. Where a number is arbitrary I say so.

---

## The constraint that shapes all three fields

The first D5 pull found SK Hynix's **new ADR programme, ISIN `US78392B2060`, with headroom
exactly 0 and a single observation dated 2026-07-15** — the 2.5% deal cap, exhausted at
the offering. The legacy programme `US78392B1070` is a different, unconstrained channel
that would answer a different question.

So H5's stated direction — *"premium-compression episodes are preceded by headroom
creation"* — faces a live possibility that its independent variable **never varies**.
That is not a refutation. A criterion that cannot say so is a broken criterion, which is
why the third field below has three branches rather than two.

---

## Proposed

```yaml
h5_quota_ledger:
  threshold: >-
    Headroom creation is an increase in KSD `DR전환가능주식수량` for ISIN US78392B2060
    (the 2.5%-capped ADR programme, NOT the legacy programme US78392B1070) of at least
    0.25% of that programme's ceiling, measured day-over-day. Premium compression is a
    fall in close-to-close pi of at least 3 percentage points over any 5-trading-day
    window. The call is directional: headroom creation PRECEDES compression.
  resolution_date: 2026-10-31
  resolution_criterion: >-
    CONFIRMED if, over the window from 2026-07-29 to the resolution date, at least two
    distinct headroom-creation episodes (per threshold) are each followed within 5
    trading days by a premium compression episode (per threshold), and the count of
    compression episodes NOT preceded by headroom creation does not exceed the count
    that are. REFUTED if headroom-creation episodes occur but compressions do not follow
    at above that rate. UNTESTABLE if fewer than two headroom-creation episodes are
    observed in the window — including the specific case where US78392B2060 remains
    pinned at 0 throughout, or where KSD publishes no daily series for it. An UNTESTABLE
    resolution is a recorded outcome, not a failure, and is reported as such.
  freeze_class: C
  status: frozen
```

### Where each number comes from

| Field | Basis |
|---|---|
| **0.25% of ceiling** | Calibrated on the legacy programme, the only one with observable movement: over 2026-07-14→07-28 it moved +41,648 shares on a 129.7M base — **0.03%**, a trickle. 0.25% is ~8× that, so it selects genuine episodes rather than settlement noise. **Arbitrary in the sense that any threshold is**; it is anchored to observed noise rather than picked to be round. |
| **3pp over 5 days** | The observed π path moved 51.6→22.3 over four sessions and 30.1→15.8 over two, so 3pp is comfortably inside realised variation — it will not fail for lack of candidate episodes. |
| **5-trading-day lead** | README §5 H5 says the lag is "set by settlement plumbing". DR cancellation runs depositary → KSD → KRX settlement; 5 days spans a normal cycle with slack. **This is the weakest number here** — if you know the actual settlement cycle, override it. |
| **2026-10-31** | Three months of post-conversion-open data. Long enough for episodes to accumulate; short enough to resolve inside the project's horizon. |
| **≥2 episodes** | The minimum that distinguishes a pattern from a coincidence. Deliberately low, because the honest expectation is that few episodes occur — and the UNTESTABLE branch catches that case rather than letting a thin sample masquerade as a result. |

### What I am least confident about

The **5-day lead** and the **0.25%** threshold. Both are anchored to two weeks of data from
the *wrong programme* — the legacy one — because the right programme has produced a single
observation. If either is materially off, the call resolves UNTESTABLE rather than
misleading, which is the failure mode to prefer.

---

## The rest of the freeze, if you accept

H1–H4 need `freeze_class: X` and a `status:` (`exploratory` is the honest one), because
the test suite flips to strict mode the moment `frozen_at` is set and demands zero
`TODO(ash)` anywhere in the file.

Amendment 001 needs from you: the **exact 2Q26 release timestamp (KST)**, the observed
window, and your signature. Its References line should read **"no prior commit"** — with
zero commits, Class P is empty, and §3 instructs that this be declared rather than the
class deleted.

I can draft everything except the release timestamp and the signature.
