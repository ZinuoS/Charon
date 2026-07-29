# Minimal Class C freeze — checklist

**Calls left out of this freeze are exploratory. That is a legitimate, labeled status —
not a debt.** A ledger with three honestly-frozen calls and four openly-exploratory ones
is a stronger artifact than seven calls frozen carelessly, and far stronger than seven
left in limbo. Freezing less, well, is the winning move.

Nothing in this file is filled in. Every value is yours (README §11).

---

## Why H5 first

H5 is the only call whose resolution data **did not exist and was not forecastable** at
the time of the 2Q26 release — DR conversion-flow readings begin accumulating after the
2026-07-29 conversion open. That makes it the cleanest Class C candidate in the ledger:
the earnings outcome is known context, but the *outcome the call resolves against* is
still in the future.

H1 (post-open derivatives closes) and H3 (post-open cross-market close windows) are the
same shape. Everything else is either contaminated or resolvable from what was already
public, and belongs in Class X.

---

## Minimum viable freeze: H5 only (3 fields)

In `preregistration/calls.yaml`, under `h5_quota_ledger:`

- [ ] `threshold:` — the decision level. Currently `TODO(ash)`.
- [ ] `resolution_date:` — a YAML date. Must be far enough out that settlement plumbing
      has produced observable headroom movement.
- [ ] `resolution_criterion:` — what counts as confirmed vs. refuted, stated so that a
      reader who disagrees with you can still apply it.
- [ ] `freeze_class: C` — per Amendment 001 §3.
- [ ] `status:` — change `frozen_pending_signature` → `frozen`.

**One open empirical question to resolve or explicitly defer** before writing the
criterion: `docs/data_sources.md` D5 records that KSD ties `DR전환가능주식수량` to the
*foreign ownership limit*, while SKHY's binding constraint is the *2.5% deal cap*. Which
the series reflects cannot be settled from documentation — only the first post-07-29
prints decide it. You may either write the criterion against the KSD field directly and
accept that risk on the record, or write it against a derived measure and specify the
derivation. Either is defensible; leaving it unstated is not.

## If you also want H1 and H3 (3 fields each)

Same five items under `h1_term_structure:` and `h3_letf_loop:`. Both have
`known_blockers` listed in `calls.yaml` — H1's derivatives sources and H3's LETF AUM are
still unsourced, so a resolution date should assume sourcing risk. A call that resolves
"untestable — data never materialised" is a legitimate recorded outcome, but say so in
the criterion rather than discovering it later.

## Top-level, two lines

- [ ] `frozen_at:` — UTC timestamp of the freeze, e.g. `"2026-07-29T14:05:00+00:00"`.
      Must match the commit you are about to make.
- [ ] `commit_note:` — one sentence. Worth naming what is *not* in the freeze.

`tests/test_preregistration.py` flips to strict mode the moment `frozen_at` is non-null:
it then asserts no `TODO(ash)` survives anywhere in the file and every `status` reads
`frozen`. **So a partial freeze needs the excluded calls explicitly marked** — give them
`freeze_class: X` and a `status:` you are happy to defend (`exploratory` is the honest
one), rather than leaving them as `TODO(ash)`.

Run before committing:

```bash
# from the repo root:
uv run pytest tests/test_preregistration.py -q
```

---

## Amendment 001 — same sitting, or the freeze means less

`preregistration/amendments/001_partitioned_freeze.md` does not exist yet. The template
you drafted carries five unfilled markers; three must be completed for the partition to
bind:

- [ ] **§1 release timestamp** — the exact KST instant SK Hynix published 2Q26 results.
      This is the pivot the whole partition turns on: Class P is defined as *committed
      before it*.
- [ ] **§2 observed window** — the date/time range of price action you had seen when you
      wrote the amendment.
- [ ] **§3 Class X enumeration** — which calls are demoted to exploratory, named
      individually. An unenumerated Class X list binds nothing.
- [ ] **References line** — the `calls.yaml` commit hash, or the literal words *"no prior
      commit"*.
- [ ] **Signature.**

**On Class P, stated once so it is on the record rather than discovered later:** with zero
commits in the repo, no call predates the release timestamp, so **Class P is empty**.
Amendment 001 §3 already instructs that this be declared explicitly rather than by
deleting the class. Write it as an empty class; that sentence is the amendment doing its
job.

---

## Commit

```bash
# from the repo root:
git add -A && git commit -m "S0: Class C freeze (H5) + Amendment 001 partition" && git tag s0-freeze -m "Class C freeze" && git log -1 --format=%H%n%cI
```

Add `-S` to `commit` and `-s` to `tag` if you have GPG configured; both are optional and
the freeze is valid without them.

The final `git log` prints the commit hash and committer timestamp — record both in
`docs/gate_reports/S0.md`, and the hash in Amendment 001's References line.

---

## After

- [ ] `docs/gate_reports/S0.md` — fill commit hash, tag, `frozen_at`, and whether the
      commit preceded the release timestamp.
- [ ] Confirm `uv run pytest tests/test_preregistration.py` passes in strict mode.
