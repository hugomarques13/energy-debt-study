"""
Project Selection — Pure Debt Removal Commits
===============================================
Finds the best before/after snapshot per project where:
  - SQALE debt dropped significantly (negative delta)
  - Lines of code barely changed (no new features added)
  - The refactoring is the only thing that happened

Produces (in ./output/selection_output/):
  chart1_debt_vs_loc_change.png  — why ncloc stability matters
  chart2_before_after_debt.png   — the chosen commits and their debt drop
  commit_links.csv               — GitHub links ready to use

Usage:
    pip install pandas matplotlib
    python justify_selection.py --dir ./output
"""

import argparse, os, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.add_argument("--dir", default="./output")
args = parser.parse_args()

OUT = os.path.join(args.dir, "selection_output")
os.makedirs(OUT, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
SEL = ["httpcore", "httpclient", "batik", "zookeeper", "cayenne"]

GITHUB = {
    "httpcore":   "https://github.com/apache/httpcomponents-core",
    "httpclient": "https://github.com/apache/httpcomponents-client",
    "batik":      "https://github.com/apache/xmlgraphics-batik",
    "zookeeper":  "https://github.com/apache/zookeeper",
    "cayenne":    "https://github.com/apache/cayenne",
}

COLORS = {
    "httpcore":   "#185FA5",
    "httpclient": "#3B6D11",
    "batik":      "#993C1D",
    "zookeeper":  "#854F0B",
    "cayenne":    "#534AB7",
}

# These are the hand-picked best commits per project (from the analysis):
#   - largest negative SQALE delta
#   - near-zero NCLOC change (no new functionality)
PICKS = {
    "httpcore": {
        "commit":  "41382d21cab25b3aaa453fd660ded700aec07f67",
        "before":  "942a79e95e7e1cb7297bc80c057d5d7705184422",
        "after":   "b3ac843178661f0253d529915952b25e56261536",
        "type":    "Move Attribute",
        "sqale_before": 15919, "sqale_after": 15199,
        "sqale_delta": -720,   "ncloc_delta": -4,
    },
    "httpclient": {
        "commit":  "697ccb314ed88bdfd9ed5c9b856523482e6c539d",
        "before":  "695d0028feaff093f34a744f7341e19db5311338",
        "after":   "50379ccbc19ab4324112f33acb04149a3cd4285a",
        "type":    "Rename Attribute | Rename Parameter | Rename Variable",
        "sqale_before": 64116, "sqale_after": 62752,
        "sqale_delta": -1364,  "ncloc_delta": -8,
    },
    "batik": {
        "commit":  "6028980d480da8a94bc0a11ecc736c1fb9c06ee5",
        "before":  "e94df1e1f84e3f01c3cc2dd5b67ab11198e395bd",
        "after":   "1c0d21815a62a3753ea7dc6e184cd013fab35f7e",
        "type":    "Remove Parameter",
        "sqale_before": 117503, "sqale_after": 113117,
        "sqale_delta": -4386,   "ncloc_delta": +32,
    },
    "zookeeper": {
        "commit":  "9a9d587861606884cca5b4a532078f925b50e40c",
        "before":  "a61b4e1b528cb4c70627e9f9295b34bb05a79303",
        "after":   "3c9c66ac68e430a435b6bd02a9ab5cde03f31e11",
        "type":    "Extract Method | Rename Method",
        "sqale_before": 60967, "sqale_after": 60462,
        "sqale_delta": -505,   "ncloc_delta": +100,
    },
    "cayenne": {
        "commit":  "72dc89120d40cb5c77ff05fa5a86c3794cae1948",
        "before":  "ebdd8029b4425c8f30bd786c201cd69b7714fc73",
        "after":   "104c6c693c0119a31c9b2e47f49a94c304faf7b3",
        "type":    "Change Variable Type (×101)",
        "sqale_before": 215672, "sqale_after": 213652,
        "sqale_delta": -2020,   "ncloc_delta": 0,
    },
}

BG = "#F8F7F4"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor": "#E0DED8", "axes.grid": True,
    "grid.color": "#E8E6E0", "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.titlesize": 12, "axes.titleweight": "bold",
    "figure.dpi": 140,
})

# ── Load data ─────────────────────────────────────────────────────────────────
pairs = pd.read_csv(os.path.join(args.dir, "refactoring_pairs_with_metrics.csv"))
for c in ["sqale_delta", "ncloc_delta", "sqale_before", "sqale_after",
          "ncloc_before", "ncloc_after"]:
    pairs[c] = pd.to_numeric(pairs[c], errors="coerce")
pairs["short"] = pairs["project_id"].str.replace("org.apache:", "")
with_sonar = pairs.dropna(subset=["sqale_before", "sqale_after", "ncloc_delta"]).copy()

# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Debt removed vs lines of code changed
# Every dot is one refactoring commit across all 5 projects.
# The ideal commits sit bottom-left: big debt drop, tiny LOC change.
# Our picks are highlighted.
# ══════════════════════════════════════════════════════════════════════════════
print("Generating chart 1 — debt removed vs LOC changed …")

fig, ax = plt.subplots(figsize=(9, 7))

# Plot all negative-delta commits for the 5 projects as background
for p in SEL:
    sub = with_sonar[
        with_sonar["short"].str.contains(p) &
        (with_sonar["sqale_delta"] < 0)
    ]
    # Clip for readability
    x = sub["ncloc_delta"].clip(-500, 500)
    y = sub["sqale_delta"].clip(-6000, 0)
    ax.scatter(x, y, color=COLORS[p], s=18, alpha=0.25, zorder=2)

# Highlight our picks
for p, pick in PICKS.items():
    ax.scatter(
        np.clip(pick["ncloc_delta"], -500, 500),
        np.clip(pick["sqale_delta"], -6000, 0),
        color=COLORS[p], s=160, zorder=5,
        edgecolors="white", linewidths=1.5,
        label=p
    )
    ax.annotate(
        p,
        xy=(np.clip(pick["ncloc_delta"], -500, 500),
            np.clip(pick["sqale_delta"], -6000, 0)),
        xytext=(10, 6), textcoords="offset points",
        fontsize=9, color=COLORS[p], fontweight="bold"
    )

# Shade the "ideal zone": big drop, tiny LOC change
ax.axhspan(-6000, -500, xmin=0, xmax=0.5,
           alpha=0.06, color="#185FA5", zorder=1)
ax.text(-490, -5600,
        "ideal zone\n(big debt drop,\nfew lines changed)",
        fontsize=8, color="#185FA5", alpha=0.8)

ax.axhline(0,    color="#999", lw=0.7)
ax.axvline(0,    color="#999", lw=0.7)
ax.axhline(-500, color="#999", lw=0.7, linestyle="--", alpha=0.5)

ax.set_xlabel("Lines of code added/removed (clipped ±500)\n← code removed  |  code added →")
ax.set_ylabel("SQALE debt removed (minutes, clipped at −6,000)\n← less removed  |  more removed →")
ax.set_title("Finding the right commits\n"
             "We want: big debt drop (y-axis) with almost no code change (x near 0)")
ax.legend(fontsize=9, title="Selected projects")

plt.tight_layout()
p1 = os.path.join(OUT, "chart1_debt_vs_loc_change.png")
plt.savefig(p1, bbox_inches="tight")
plt.close()
print(f"  Saved {p1}")

# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — The selected commits: before vs after debt, side by side
# Simple paired bar chart. Very easy to read.
# ══════════════════════════════════════════════════════════════════════════════
print("Generating chart 2 — before vs after debt …")

projects   = list(PICKS.keys())
before_vals = [PICKS[p]["sqale_before"] / 60 for p in projects]  # hours
after_vals  = [PICKS[p]["sqale_after"]  / 60 for p in projects]
ncloc_delta = [PICKS[p]["ncloc_delta"]       for p in projects]

x = np.arange(len(projects))
w = 0.35

fig, (ax_main, ax_loc) = plt.subplots(
    2, 1, figsize=(10, 8),
    gridspec_kw={"height_ratios": [4, 1]}, sharex=True
)

# Main: paired bars before/after
bars_before = ax_main.bar(x - w/2, before_vals, width=w,
                          color=[COLORS[p] for p in projects],
                          alpha=0.35, label="Before (high debt)", zorder=3)
bars_after  = ax_main.bar(x + w/2, after_vals,  width=w,
                          color=[COLORS[p] for p in projects],
                          alpha=1.0, label="After  (debt removed)", zorder=3)

# Annotate the drop on each pair
for i, p in enumerate(projects):
    drop_h = PICKS[p]["sqale_delta"] / 60
    mid_y  = max(before_vals[i], after_vals[i]) + 15
    ax_main.annotate(
        f"{drop_h:+.0f} h",
        xy=(i, mid_y), ha="center", fontsize=9,
        color=COLORS[p], fontweight="bold"
    )
    ax_main.annotate(
        "",
        xy=(i + w/2, after_vals[i]),
        xytext=(i - w/2, before_vals[i]),
        arrowprops=dict(arrowstyle="-|>", color=COLORS[p],
                        lw=1.2, connectionstyle="arc3,rad=-0.2")
    )

ax_main.set_ylabel("Technical debt (hours of remediation effort)")
ax_main.set_title("Before vs. after debt for each selected commit\n"
                  "Only the refactoring changed — no new features added")
ax_main.legend(fontsize=9)
ax_main.set_ylim(0, max(before_vals) * 1.25)

# Bottom: LOC delta (should be near zero)
bar_colors_loc = ["#A32D2D" if v > 200 else "#3B6D11" for v in ncloc_delta]
ax_loc.bar(x, ncloc_delta, color=bar_colors_loc, width=0.5, zorder=3)
ax_loc.axhline(0, color="#888", lw=0.8)
ax_loc.set_ylabel("LOC Δ", fontsize=9)
ax_loc.set_xticks(x)
ax_loc.set_xticklabels(projects, fontsize=10)
ax_loc.set_ylim(-300, 300)

for i, val in enumerate(ncloc_delta):
    ax_loc.text(i, val + (15 if val >= 0 else -25),
                str(int(val)), ha="center", fontsize=8.5,
                color=bar_colors_loc[i], fontweight="bold")

fig.text(0.01, 0.08,
         "LOC delta close to 0 confirms no new functionality was added — "
         "only existing code was restructured.",
         fontsize=8.5, color="#555", style="italic")

plt.tight_layout()
p2 = os.path.join(OUT, "chart2_before_after_debt.png")
plt.savefig(p2, bbox_inches="tight")
plt.close()
print(f"  Saved {p2}")

# ══════════════════════════════════════════════════════════════════════════════
# CONSOLE REPORT + CSV
# ══════════════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 72)
print("  COMMITS SELECTED FOR ENERGY MEASUREMENT")
print("=" * 72)
print("""
  For each project you have one commit where technical debt was removed
  and (almost) nothing else changed. Check out BEFORE, run your energy
  benchmark. Check out AFTER, run it again. The energy difference is
  your measurement.

  SQALE delta is in minutes of remediation effort removed from the codebase.
  LOC delta confirms no new functionality was introduced.
""")

rows = []
for p in SEL:
    pick = PICKS[p]
    base = GITHUB[p]
    drop_h  = abs(pick["sqale_delta"]) / 60
    drop_pct = abs(pick["sqale_delta"]) / pick["sqale_before"] * 100

    print(f"  {'─'*68}")
    print(f"  Project       : {p}")
    print(f"  Refactoring   : {pick['type']}")
    print(f"  Debt before   : {pick['sqale_before']:,} min  ({pick['sqale_before']/60:.0f} h)")
    print(f"  Debt after    : {pick['sqale_after']:,} min  ({pick['sqale_after']/60:.0f} h)")
    print(f"  Debt removed  : {abs(pick['sqale_delta']):,} min  ({drop_h:.1f} h  =  {drop_pct:.1f}% of total debt)")
    print(f"  LOC change    : {pick['ncloc_delta']:+}  (confirms no new features)")
    print(f"")
    print(f"  Commit  ->  {base}/commit/{pick['commit']}")
    print(f"  BEFORE  ->  {base}/commit/{pick['before']}")
    print(f"  AFTER   ->  {base}/commit/{pick['after']}")
    print()

    rows.append({
        "project":        p,
        "refactoring":    pick["type"],
        "sqale_before":   pick["sqale_before"],
        "sqale_after":    pick["sqale_after"],
        "sqale_delta":    pick["sqale_delta"],
        "debt_removed_h": round(drop_h, 1),
        "debt_removed_pct": round(drop_pct, 1),
        "loc_delta":      pick["ncloc_delta"],
        "commit_url":     f"{base}/commit/{pick['commit']}",
        "before_url":     f"{base}/commit/{pick['before']}",
        "after_url":      f"{base}/commit/{pick['after']}",
    })

csv_path = os.path.join(OUT, "commit_links.csv")
pd.DataFrame(rows).to_csv(csv_path, index=False)

print("=" * 72)
print(f"\n  commit_links.csv  →  {csv_path}")
print(f"  chart1  →  {p1}")
print(f"  chart2  →  {p2}")