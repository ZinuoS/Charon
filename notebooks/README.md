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
| **00** | [`00_executive_pitch.ipynb`](00_executive_pitch.ipynb) | The full argument in prose: background, mechanism, trading insights, execution. Organised around the prospectus finding that the barrier is a *corporate decision*, not an exhausted quota. | ✅ live |
| **01** | [`01_client_note.ipynb`](01_client_note.ipynb) | A desk-voice version of the same material for a prime-finance reader. Derives its section order from the client pack, so the two cannot drift. | ✅ live |
| **02** | [`02_premium_anatomy.ipynb`](02_premium_anatomy.ipynb) | How π is constructed and how much of it is measurement rather than economics. | ✅ live |
| **03** | [`03_comparator_panel.ipynb`](03_comparator_panel.ipynb) | The training universe: three regimes, corporate-action QA, calendar policy. Where the sample is defined and every exclusion is declared with its cause — start here to disagree with anything downstream. | ✅ live |
| **04** | [`04_regimes_convergence.ipynb`](04_regimes_convergence.ipynb) | M2 regimes and M3 convergence dynamics. | ✅ live |
| **05** | [`05_hypothesis_engines.ipynb`](05_hypothesis_engines.ipynb) | H1–H5 status and results: the H5 monitor (registered), H4 variance, the M3 convergence metrics table. | ✅ live |
| **06** | [`06_complexity_ledger.ipynb`](06_complexity_ledger.ipynb) | Parsimony against complexity under one harness. EXPERIMENT, deviation-gated (DEV-004). Verdict: complexity's edge dies in the vol-timing decomposition. | ✅ live |
| **07** | [`07_macro_environment.ipynb`](07_macro_environment.ipynb) | The macro layer as an argument, not a backdrop: four claims, four mechanisms, four numbers — including H6/H6b, registered before testing and null both times. | ✅ live |
| **08** | [`08_pitch_logic.ipynb`](08_pitch_logic.ipynb) | The argument in sentences: the chain, scenario P&L in return-on-margin, the hedge menu, exit discipline, and the P&L identity that settles the decay question. | ✅ live |
| **09** | [`09_tsmc_lab.ipynb`](09_tsmc_lab.ipynb) | The comparator lab: 21.6 years of the nearest regime family. Structural audit first — the differences bound the claims — then the episode census, entry outcomes against the carry brackets, the excursion/stop case, and the FX channel per era. | ✅ live |
| **10** | [`10_financing.ipynb`](10_financing.ipynb) | The carry bracket opened into components: what is measured, what is a desk quote, and the one piece that cannot be measured without a forward curve. The funding differential turns out to be a tailwind. | ✅ live |

| **11** | [`11_pitch_book.ipynb`](11_pitch_book.ipynb) | The presentation material: the trade on page one, then durability, history, macro, structure, scenarios, risk and the ask. Sell-side register, live values, every figure shared with the slide layer. | ✅ live |

Numbers were reserved before the notebooks existed so the sequence stayed stable as it filled
in. **00 and 02 were previously numbered 00_pitch and 01_premium_anatomy**; the renumbering
preserved git history via `git mv`.

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
