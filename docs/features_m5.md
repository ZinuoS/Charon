# M5 — 000660 context feature dictionary

**Status: NOT BUILT. Roadmap.**

Nothing here entered M2 or M3 this session, so under the session's own scope rule
("a feature that won't enter M2 this session is out of scope") none of it was built.

| candidate | definition sketch | blocker |
|---|---|---|
| realized-vol state | rolling σ of local returns, terciled | none — buildable, but see below |
| trend / drawdown state | local price vs rolling max | none — buildable |
| listing-era dummy | pre/post 2026-07-10 | trivially buildable |
| lending utilization state | KOFIA/KRX borrow utilization, terciled | **D3 not landed** |
| beta / correlation to a Korea proxy | rolling β to KOSPI200 | **no index series in-repo.** Logged as a probe; not pulled mid-session |

## Why the buildable ones were still not built

The M6 ablation ran first and came back **cut** — one landed macro feature made RMSE and R²
worse at every horizon in every class, under identical folds. That is the prior for M5.

More decisively: **the S4 table did not need features to exist.** Its rows are per-regime,
per-horizon forecast errors of `π_{t+h} ~ π_t`, and the constrained class already reaches
R² 0.92 at h=1 from the level alone. Adding conditioning features to a four-pair panel is
what the capacity rule (README §6) exists to prevent.

M5 becomes worth building when there is a question it answers that the level cannot — most
plausibly *when* the barrier binds (a state question) rather than how persistent the premium
is (answered). Utilization states are the strongest candidate and are gated on D3.
