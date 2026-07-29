"""Pre-push audit: what must never leave this machine.

Run before the first push. Scans everything git WOULD track (not the working tree —
gitignored payloads are irrelevant) for five classes of leak.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "key material": [
        re.compile(r"\b[0-9a-f]{32}\b"),                    # FRED-style
        re.compile(r"\b[0-9a-f]{14}\.[0-9]{8}\b"),          # EODHD-style
        re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*['\"]?[A-Za-z0-9._-]{12,}"),
    ],
    "absolute local path": [re.compile(r"/Users/[a-z0-9]+/", re.I)],
    "withheld-source data": [re.compile(r"(?i)(smbs|investing\.com)[-_/]?(scrape|fx_swap_xml)")],
}
# Desk/firm names are deliberately NOT hardcoded here — writing them into a committed
# audit script would itself be the leak. The check is structural: flag any capitalised
# multi-word token adjacent to desk vocabulary for human review.
DESK_HINT = re.compile(r"(?i)\b(desk|colleague|internal (?:memo|email|call)|our team)\b")

SKIP_SUFFIX = {".png", ".ipynb", ".lock", ".pyc"}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    files = [ROOT / f for f in out.splitlines() if f.strip()]
    if not files:  # no commits yet — audit what WOULD be tracked
        out = subprocess.run(["git", "add", "-An", "--dry-run", "."], cwd=ROOT,
                             capture_output=True, text=True).stdout
        files = [ROOT / m.group(1) for line in out.splitlines()
                 if (m := re.match(r"add '(.+)'", line))]
    return [f for f in files if f.is_file() and f.suffix not in SKIP_SUFFIX]


def main() -> int:
    files = tracked_files()
    print(f"auditing {len(files)} files git would track\n")
    findings: list[tuple[str, str, int, str]] = []
    for f in files:
        try:
            text = f.read_text(errors="replace")
        except Exception:
            continue
        rel = f.relative_to(ROOT).as_posix()
        for i, line in enumerate(text.splitlines(), 1):
            for label, pats in PATTERNS.items():
                for p in pats:
                    if p.search(line):
                        findings.append((label, rel, i, line.strip()[:110]))
            if DESK_HINT.search(line):
                findings.append(("desk-vocabulary (review)", rel, i, line.strip()[:110]))

    if not findings:
        print("  CLEAN — no key material, local paths, withheld-source data or desk vocabulary.")
    for label, rel, i, snippet in findings:
        print(f"  [{label}] {rel}:{i}\n      {snippet}")

    blocking = [f for f in findings if not f[0].startswith("desk-vocabulary")]
    print(f"\n  blocking: {len(blocking)}   review-only: {len(findings) - len(blocking)}")
    print("\n  REMINDER: README §0 requires this repo stay PRIVATE until the internship")
    print("  concludes or compliance clears. Confirm the GitHub setting before pushing.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
