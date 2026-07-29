# Notebooks — reading guide

Two audiences, one sequence.

**If you are here to read the argument**, start at **00** and stop when you are satisfied.
It is written to stand alone: what the premium is, why it persists, what could be traded
against it, and what it would cost — with every number traceable to a repository series or
a cited source.

**If you are here to check the work**, continue into **02** onward. Those are the
methods documents: how the premium is constructed, what the comparator panel says, and
where each hypothesis actually stands. They assume you will disagree and give you the
material to do it.

---

## The sequence

| | Notebook | What it is | Status |
|---|---|---|---|
| **00** | [`00_executive_pitch.ipynb`](00_executive_pitch.ipynb) | The full argument: background, trading insights, execution. Organised around the prospectus finding that the barrier is a *corporate decision*, not an exhausted quota. | ✅ live, 6 figures |
| 01 | `01_client_note.ipynb` | A desk-voice version of the same material for a prime-finance reader | not written |
| **02** | [`02_premium_anatomy.ipynb`](02_premium_anatomy.ipynb) | How π is constructed and how much of it is measurement rather than economics | ✅ live, 8 figures |
| 03 | `03_comparator_panel.ipynb` | The training universe: three regimes, corporate-action QA, calendar policy | not written — needs the taxonomy ratified |
| 04 | `04_regimes_convergence.ipynb` | M2 regimes and M3 convergence dynamics | not written — models are quarantined pending taxonomy ratification |
| **05** | [`05_hypothesis_engines.ipynb`](05_hypothesis_engines.ipynb) | H1–H5 status + results: H5 monitor (registered), H4 variance, M3 convergence metrics table | ✅ live, 4 figures |

Numbers are reserved even where the notebook does not exist yet, so the sequence stays
stable as it fills in. **00 and 02 were previously numbered 00_pitch and
01_premium_anatomy**; the renumbering preserved git history via `git mv`.

## Rendering

GitHub's `.ipynb` viewer is unreliable on large notebooks — it truncates, and sometimes
fails outright on figure-heavy files. If a notebook does not render here, use nbviewer:

- [00 — executive pitch on nbviewer](https://nbviewer.org/github/ZinuoS/Charon/blob/main/notebooks/00_executive_pitch.ipynb)
- [02 — premium anatomy on nbviewer](https://nbviewer.org/github/ZinuoS/Charon/blob/main/notebooks/02_premium_anatomy.ipynb)

## What to know before reading

**Notebooks are committed with their outputs.** The repository is the display medium, so a
reader should see the figures and results without running anything. `make notebook`
verifies that a fresh offline re-execution reproduces them.

**Everything executes offline.** Ingestion is a separate, logged, network-permitted stage;
analysis modules import no networking library, and a test walks the AST of every analysis
module to enforce it.

**The pre-registration ledger is not frozen at the time of writing.** Each notebook opens
with a cell that reads `preregistration/calls.yaml` and prints the governing status. While
it is unfrozen, *every hypothesis is exploratory* and is labelled as such — nothing is
described as a pre-registered forward test unless the ledger says so on the record.

**"Arbitrage" appears only for the conversion channel that does not work.** Everything live
is relative value against a one-sided barrier, and the figures say so — see G4, which puts
the unbounded-loss side on the same page as the convergence expression.
