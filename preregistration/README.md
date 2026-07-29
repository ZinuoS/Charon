# preregistration/

The freeze. `calls.yaml` records what was claimed about H1–H5 **before** SKHY outcome
data was examined, so that a later result cannot be quietly reinterpreted into a
prediction that was never made.

## The rule

**`calls.yaml` is append-only after the freeze commit. It is never edited.**

Once `frozen_at` is set and the file is committed, a change to any threshold,
direction, resolution date or resolution criterion is a *new dated amendment file*, not
an edit. The git history alone is not sufficient — an amendment must be legible without
running `git log`.

## Amendments

One file per amendment, in `preregistration/amendments/`, named
`<YYYY-MM-DD>-<slug>.md`. Each must state:

1. **What changed** — the exact field, its frozen value and its new value.
2. **Why** — the reason, in mechanism terms.
3. **What was already observed** — the outcome data visible at the time of the
   amendment. This is the field that makes the amendment honest or dishonest, and it is
   not optional. An amendment made after seeing the result it affects is still
   permissible; an amendment that hides having seen it is not.
4. **Scope** — which hypotheses and which already-reported results are affected.

An amendment never deletes or rewrites `calls.yaml`. Readers reconstruct the live state
by reading `calls.yaml` and then applying amendments in date order.

## Freeze checklist

- [ ] Every `TODO(ash)` in `calls.yaml` replaced with a value.
- [ ] `frozen_at` set to the UTC freeze timestamp.
- [ ] `commit_note` written.
- [ ] Every hypothesis `status` changed from `frozen_pending_signature` to `frozen`.
- [ ] `uv run pytest tests/test_preregistration.py` passes.
- [ ] Committed and tagged before **2026-07-29 09:00 KST / 2026-07-28 20:00 ET**.
- [ ] Commit hash recorded in `docs/gate_reports/S0.md` (README §9, S0 gate).
