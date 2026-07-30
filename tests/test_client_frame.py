"""Lint: client-facing artifacts sell SEALED SUPPLY, never a conversion trade.

The thesis is that the premium persists BECAUSE the market cannot arbitrage it. A client
artifact that describes converting or cancelling as the way to capture the gap contradicts
the research it is built on -- and it would be describing a trade the client cannot do, since
issuance needs the Company's consent. Cancellation is an unwind mechanic in the exit terms and
a cost floor; it is not a strategy.

The purge grep found zero hits when this test was written. It exists so that stays true.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLIENT_FACING = [
    ROOT / "scripts" / "export_client_pack.py",
    ROOT / "scripts" / "build_client_note.py",
    ROOT / "scripts" / "build_deck.py",
    ROOT / "scripts" / "build_deck_v2.py",
    ROOT / "pipeline" / "viz" / "figures.py",
    ROOT / "pipeline" / "hedging" / "sheets.py",
]

BANNED = re.compile(
    r"conversion\s+(trade|arb\w*|play|opportunity)"
    r"|convert\s+(to|and)\s+(capture|sell|monetis|monetiz)"
    r"|cancel(lation)?\s+(trade|arb\w*)"
    r"|arb(itrage)?\s+the\s+(gap|premium)",
    re.IGNORECASE)


@pytest.mark.parametrize("path", CLIENT_FACING, ids=lambda p: p.name)
def test_no_conversion_as_a_trade(path):
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    hits = [(i, ln.strip()) for i, ln in enumerate(path.read_text().splitlines(), 1)
            if BANNED.search(ln)]
    assert not hits, (
        f"{path.name} describes conversion or cancellation as a TRADE:\n" +
        "\n".join(f"  line {i}: {ln[:110]}" for i, ln in hits) +
        "\nThe frame is sealed supply: the premium persists because the market cannot "
        "arbitrage it, and the desk manufactures the exposure synthetically. Cancellation "
        "belongs in exit fine print and in the cost floor, nowhere else."
    )
