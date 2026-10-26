"""Shared publication style for the manuscript figures.

One palette and one geometry for every figure so that the four figures in the
paper read as a set:

* Palette: the canonical nature-figure palette (see the nature-figure skill,
  ``references/api.md``), restricted to six colours.  Series are additionally
  separated by line style and marker shape, so the figures stay readable in
  greyscale and for colour-blind readers; red/orange pairs are avoided.
* Geometry: canvas width equals the printed text width (6.5 in for the TEST
  single-column layout), fonts are 7--8 pt *at print size* (not scaled down
  from a larger canvas), spines are cleaned, and panel descriptors live in the
  caption, not in axes titles.
* Export: vector PDF with embedded TrueType fonts, plus a 300 dpi PNG preview.

The multi-panel alignment gate of the nature-figure skill is called from
``finish`` when the skill scripts are available on this machine; otherwise the
call is skipped with a warning so that the released code stays portable.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import LogFormatterSciNotation, LogLocator, NullFormatter  # noqa: E402

# --- palette (nature-figure canonical) -------------------------------------
OURS = "#0F4D92"        # blue_main      joint / proposed interval
HELD = "#3775BA"        # blue_secondary held-out estimand
BASE = "#767676"        # neutral_mid    training-only (baseline)
EVAL = "#42949E"        # teal           evaluation-only / evaluation noise
POP = "#B64342"         # red_strong     population estimand / audit budget
REF = "#4D4D4D"         # neutral_dark   nominal reference lines
GRID = "#E8E8E8"        # hairline grid

TEXT_WIDTH_IN = 6.5     # \textwidth of the TEST manuscript (1 in margins)

SKILL_SCRIPTS = Path(
    os.environ.get(
        "NATURE_FIGURE_SCRIPTS",
        r"C:\Users\29582\.dsh\skills\nature-figure\scripts",
    )
)


def apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7,
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#4D4D4D",
        "axes.labelcolor": "#272727",
        "text.color": "#272727",
        "xtick.color": "#4D4D4D",
        "ytick.color": "#4D4D4D",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "lines.linewidth": 1.2,
        "lines.markersize": 3.2,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        # Opaque legend background: the collision audit treats text crossed by
        # grid strokes as a failure, and a white frame is the standard fix.
        "legend.frameon": True,
        "legend.facecolor": "white",
        "legend.edgecolor": "none",
        "legend.framealpha": 1.0,
        "legend.borderpad": 0.35,
        "legend.handlelength": 2.2,
        "legend.labelspacing": 0.3,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 300,
    })


def panel_label(ax, letter: str, *, x: float = -0.17, y: float = 1.05) -> None:
    """Bold lower-case panel letter in the top-left corner, above the axes."""
    ax.annotate(
        letter,
        xy=(x, y),
        xycoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="#272727",
        annotation_clip=False,
    )


def nominal_handle(label: str = "nominal 0.95") -> Line2D:
    return Line2D([], [], color=REF, ls=(0, (1, 1.6)), lw=1.0, label=label)


def log_axis(ax, which: str = "y") -> None:
    """Clean decade labels (10^n) instead of ``6 x 10^0``-style minor labels."""
    axis = ax.yaxis if which == "y" else ax.xaxis
    axis.set_major_locator(LogLocator(base=10.0, numticks=6))
    axis.set_major_formatter(LogFormatterSciNotation(base=10.0))
    axis.set_minor_formatter(NullFormatter())


def finish(fig, pdf_path: Path, png_path: Path, *, align: bool, align_json: Path | None = None) -> None:
    """Save vector PDF + PNG preview, running the panel-alignment gate if asked."""
    if align:
        try:
            if str(SKILL_SCRIPTS) not in sys.path:
                sys.path.insert(0, str(SKILL_SCRIPTS))
            from audit_panel_alignment import require_matplotlib_panel_alignment

            require_matplotlib_panel_alignment(
                fig,
                json_out=align_json,
                require_panel_labels=False,
            )
        except ImportError:
            print("[style] nature-figure skill scripts not found; alignment gate skipped")
        except Exception as exc:  # gate failure must be visible, not swallowed
            raise RuntimeError(f"panel alignment gate failed: {exc}") from exc
    fig.savefig(pdf_path)
    fig.savefig(png_path)
    plt.close(fig)
    print(f"[fig] {pdf_path.name}")
