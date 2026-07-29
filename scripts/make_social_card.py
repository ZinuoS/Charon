"""1200x600 social-preview card — the image every share of this repo displays.

GitHub's default is an auto-generated screenshot of the file list, which tells a reader
nothing. This puts the thesis figure and the project's title in front of them instead.

    uv run python -m scripts.make_social_card
    -> data/derived/deck_export/social_card.png   (upload: Settings -> Social preview)
"""
from __future__ import annotations
import matplotlib; matplotlib.use("Agg")
from pathlib import Path
import matplotlib.pyplot as plt
from pipeline.viz import theme
from pipeline.measurement.premium import build_all_variants

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "derived" / "deck_export"


def build(palette: str = "public") -> Path:
    used = theme.apply_palette(palette)
    theme.apply()
    pi = build_all_variants("skhy")[0].series

    # 1200x600 at 2x DPI. GitHub crops to this ratio, so the geometry is fixed rather
    # than left to bbox_inches -- a tight box would change aspect and get cropped badly.
    fig = plt.figure(figsize=(12, 6), dpi=100)
    ax = fig.add_axes([0.06, 0.14, 0.90, 0.52])

    top = float(pi.max()) * 1.16
    ax.axhspan(0.0007, top, color=theme.INK, alpha=0.05, zorder=0)
    ax.axhline(0.0007, color=theme.INK, linewidth=2.0, zorder=2)
    ax.axhline(top, color=theme.CLAY, linewidth=1.8, linestyle=(0, (9, 5)), zorder=2)
    ax.plot(pi.index, pi.values, color=theme.INK, linewidth=2.6,
            marker="o", markersize=4.5, zorder=3)
    theme.pct_axis(ax)
    ax.set_ylim(-0.03, top * 1.10)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y"); ax.grid(axis="x", visible=False); ax.set_axisbelow(True)
    theme.thin_date_ticks(ax, 5)
    ax.tick_params(labelsize=9)

    ax.annotate("OPEN — cancellation, uncapped", xy=(0.005, 0.0007),
                xycoords=("axes fraction", "data"), xytext=(0, -14),
                textcoords="offset points", fontsize=8.5, color=theme.INK,
                fontfamily=theme.SERIF_STACK)
    ax.annotate("DISCRETIONARY — issuance at the Company's determination", xy=(0.005, top),
                xycoords=("axes fraction", "data"), xytext=(0, 7),
                textcoords="offset points", fontsize=8.5, color=theme.CLAY,
                fontfamily=theme.SERIF_STACK)

    fig.text(0.06, 0.90, "C H A R O N", fontsize=11, color=theme.MUTED,
             fontfamily=theme.SERIF_STACK, va="top")
    fig.text(0.06, 0.855, "Pricing a one-sided arbitrage barrier",
             fontsize=27, color=theme.TEXT, fontfamily=theme.SERIF_STACK, va="top")
    fig.text(0.06, 0.765, "The SK Hynix ADR premium as a reflected process",
             fontsize=15, color=theme.MUTED, fontfamily=theme.SERIF_STACK, va="top")
    fig.text(0.06, 0.055, "Public data · reproducible · every claim sourced",
             fontsize=9.5, color=theme.MUTED, fontfamily=theme.SERIF_STACK, va="top")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (f"social_card_{used}.png" if used != "public" else "social_card.png")
    # theme.apply() sets savefig.bbox='tight' globally, which trims whitespace and
    # silently changes the aspect ratio. Passing bbox_inches=None does NOT override it --
    # None means "use the rcParam" -- so the rcParam itself must be overridden. GitHub
    # crops the social card to 2:1, so fixed geometry matters more than tight framing.
    with matplotlib.rc_context({"savefig.bbox": "standard"}):
        fig.savefig(path, dpi=100, facecolor=theme.PAPER)
    plt.close(fig)
    return path


if __name__ == "__main__":
    for pal in ("public", "presentation"):
        p = build(pal)
        print(f"{pal:13s} -> {p.relative_to(ROOT)}")
