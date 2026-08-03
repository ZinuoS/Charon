# Who holds the local leg: a Korean 5%-filing screen

**What this is.** A screen of Korea's substantial-shareholding regime for managers who
demonstrably execute the KRX leg. It is a capability screen built from public filings. It is
not a client list, a prospect list, or a claim about anyone's intentions.

**Source.** OpenDART `majorstock.json`, pulled 2026-08-02, 82 filings across five issuers:
SK hynix (000660), KT (030200), SK Telecom (017670), Samsung Electronics (005930), SK Square
(402340). Filings are citable individually at
`https://dart.fss.or.kr/dsaf001/main.do?rcpNo=<rcept_no>`.

**Why this regime and no other.** No US disclosure reaches a KRX line. Form 13F reports
US-listed longs; Korean common and preference lines are not SEC-registered, so no
beneficial-ownership regime touches them. Korea's own 5% regime is the only public source that
sees this leg at all.

---

## The roster

Excluded as non-candidates on structural grounds stated rather than inferred: the National
Pension Service (국민연금공단), a domestic state pension that custodies domestically, and Samsung
C&T (삼성물산), a strategic affiliate rather than a manager.

| filer | issuers | filings | window | peak stake | latest | DR-citing filings |
|---|---|---|---|---|---|---|
| Wellington Management Company LLP | KT, SK Telecom | 7 | 2025-12-02 → 2026-07-30 | 7.65% | 7.65% (rcpNo 20260730000099) | **6** |
| The Capital Group Companies, Inc. | SK hynix | 4 | 2024-12-16 → 2025-10-14 | 7.23% | 0.00% (rcpNo 20251014000028) | 0 |
| Capital Research and Management Company | SK hynix | 3 | 2025-10-14 → 2026-06-09 | 6.84% | 3.53% (rcpNo 20260609000049) | 0 |
| Macquarie Investment Management Business Trust | SK Square | 5 | 2025-04-16 → 2025-12-10 | 6.72% | 0.07% (rcpNo 20251210000421) | 0 |
| Nomura Investment Management Business Trust | SK Square | 2 | 2025-12-08 → 2026-06-08 | 6.38% | 4.97% (rcpNo 20260608000396) | 0 |
| T. Rowe Price Associates, Inc. | KT | 8 | 2024-08-27 → 2026-02-09 | 5.09% | 4.99% (rcpNo 20260209000286) | 0 |
| BlackRock Fund Advisors | SK hynix | 1 | 2026-02-20 | 5.00% | 5.00% (rcpNo 20260220000091) | 0 |
| Silchester International Investors LLP | KT | 1 | 2025-02-24 | 4.14% | 4.14% (rcpNo 20250224001573) | 0 |
| Norges Bank | SK Square | 1 | 2025-06-20 | 4.10% | 4.10% (rcpNo 20250620000490) | 0 |

---

## The one discriminating observation

Of 82 filings by ten reporters, exactly one reporter's filings state a reason mentioning
`증권예탁증권` — depositary receipts. Filings by Wellington Management Company LLP dated 2025-12-02,
2025-12-18, 2026-01-22, 2026-06-22 and 2026-07-30 each report buying KT shares
on-exchange and depositary receipts off-exchange; the filing dated 2026-05-13 reports selling
SK Telecom shares on-exchange for capital-recovery purposes while buying depositary receipts
off-exchange. All six fall on the two pairs this repository classifies as one-way-constrained.

**This is a proxy and must be read as one.** Korea's regime aggregates depositary receipts with
the underlying shares into a single stake, because a receipt represents deposited local shares.
A dual-format holding is therefore the ordinary presentation for a long that happens to sit in
both formats — it is **not a hedged pair**, and no short leg appears in this or any regime.
Every one of those filings is a simplified report declaring passive investment intent, which
cuts against an arbitrage reading rather than supporting one. What the filings evidence is
capability: the filer operates both formats, off-exchange, on the constrained names.

---

## The strongest result is a negative

Korea's 5% regime carries a contract column (`ctr_stkqy` / `ctr_stkrt`) capturing
contract-based holdings — the field where derivative and swap exposure would surface. It is
demonstrably live: Samsung C&T populates it across all 40 of its filings from 2024-10-25 to
2026-07-31, and the contract portion moves from 1.63% to 0.68% over that window.

**Zero foreign managers populate it, in any of the five issuers.**

The swap-financed structure is therefore invisible even in the one regime that built a field to
see it. That is the strong form of the claim. Absence in a regime that never asks the question
proves nothing; absence in a regime that asks is a determination.

---

## Two readings to avoid

- **The Capital Group filings dated 2025-10-14 are not an exit.** `TheCapitalGroupCompanies,
  Inc.` reports 0.00% and `CapitalResearchandManagementCompany` reports 6.84% on the same day,
  the stated reason citing a change of principal reporter. One house, one position, two
  reporting entities. Read as a sale it would invert the position's direction.
- **T. Rowe Price Associates crosses 5.00% eight times on KT** across filings from 2024-08-27
  to 2026-02-09 (5.05, 5.06, 5.01, 5.09, 5.01, 4.77, 5.00, 4.99). That is the disclosure
  threshold generating filings, not eight investment decisions.
