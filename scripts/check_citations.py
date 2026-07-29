"""Citation-integrity check: every URL in research_notes.md must resolve.

Dead links are FLAGGED, never removed — a source that has gone offline is a fact about
the record, and silently deleting it would misrepresent what was available at access
time. Ingestion-side by design: this touches the network and lives outside the analysis
tree.
"""
from __future__ import annotations
import re, sys, time
from pathlib import Path
import requests

DOC = Path(__file__).resolve().parents[1] / "docs" / "research_notes.md"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

def main() -> int:
    urls = sorted(set(re.findall(r"https?://[^\s\)\]<>\"]+", DOC.read_text())))
    print(f"checking {len(urls)} distinct URLs from {DOC.name}\n")
    dead, ok, blocked = [], 0, []
    for u in urls:
        u = u.rstrip('.,;')
        try:
            r = requests.head(u, headers=UA, timeout=20, allow_redirects=True)
            if r.status_code >= 400:
                r = requests.get(u, headers=UA, timeout=25, allow_redirects=True)
            code = r.status_code
        except Exception as e:
            code = f"ERR {type(e).__name__}"
        if isinstance(code, int) and code < 400:
            ok += 1
        elif code in (403, 429):
            blocked.append((u, code))
        else:
            dead.append((u, code))
        print(f"  {str(code):>6}  {u[:96]}")
        time.sleep(1.0)
    print(f"\n  resolved: {ok}   bot-blocked (403/429, source still valid): {len(blocked)}   DEAD: {len(dead)}")
    for u, c in dead:
        print(f"  DEAD {c}  {u}")
    print("\n  Dead links are flagged, not removed — access date is recorded in the document.")
    return 1 if dead else 0

if __name__ == "__main__":
    sys.exit(main())
