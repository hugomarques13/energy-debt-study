"""
Technical Debt Energy Study — Analysis & Visualisation
=======================================================
Reads the 4 CSVs produced by data_filterer.py and generates:
  • Console summary tables
  • 10+ charts saved as PNGs in ./analysis_output/
  • A single combined figure (full_report.png)

Usage:
    pip install pandas matplotlib seaborn scipy
    python data_analysis.py --dir ./output          # folder containing the 4 CSVs
    python data_analysis.py --dir ./output --top 5  # show top N candidates per category
"""

import argparse, os, textwrap, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")

# ── Args ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dir", default="./output", help="Folder with the 4 CSV files")
parser.add_argument("--top", type=int, default=5,  help="Top N candidates per category to print")
args = parser.parse_args()

OUT = os.path.join(args.dir, "analysis_output")
os.makedirs(OUT, exist_ok=True)

# ── Theme ─────────────────────────────────────────────────────────────────────
PALETTE = {
    "Structural":  "#185FA5",
    "Signature":   "#3B6D11",
    "Rename":      "#534AB7",
    "Modifier":    "#854F0B",
    "Move":        "#0F6E56",
    "TypeChange":  "#993C1D",
    "Other":       "#73726c",
}
BG   = "#F8F7F4"
GRID = "#E8E6E0"

plt.rcParams.update({
    "figure.facecolor":  BG,
    "axes.facecolor":    BG,
    "axes.edgecolor":    GRID,
    "axes.grid":         True,
    "grid.color":        GRID,
    "grid.linewidth":    0.6,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.family":       "DejaVu Sans",
    "font.size":         10,
    "axes.titlesize":    12,
    "axes.titleweight":  "bold",
    "axes.labelsize":    10,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "figure.dpi":        140,
})

def fmt_min(x, _=None):
    if abs(x) >= 1000:
        return f"{x/1000:.1f}k"
    return f"{int(x)}"

def cat_color(cat):
    return PALETTE.get(cat, "#999")

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading CSVs …")
pairs = pd.read_csv(os.path.join(args.dir, "refactoring_pairs_with_metrics.csv"))
cat_s = pd.read_csv(os.path.join(args.dir, "summary_by_category.csv"))
proj_s= pd.read_csv(os.path.join(args.dir, "summary_by_project.csv"))
top_c = pd.read_csv(os.path.join(args.dir, "top_candidates_by_category.csv"))

# Numeric coerce (safety net)
NUM = ["sqale_before","sqale_after","sqale_delta",
       "smells_before","smells_after","smells_delta",
       "bugs_before","bugs_after","bugs_delta",
       "complexity_before","complexity_after","complexity_delta",
       "cog_complexity_before","cog_complexity_after","cog_complexity_delta",
       "ncloc_before","ncloc_after","ncloc_delta",
       "duplication_before","duplication_after","duplication_delta",
       "violations_before","violations_after","violations_delta",
       "refactoring_count","candidate_score"]
for c in NUM:
    if c in pairs.columns:
        pairs[c] = pd.to_numeric(pairs[c], errors="coerce")
    if c in top_c.columns:
        top_c[c]  = pd.to_numeric(top_c[c], errors="coerce")

with_sonar = pairs.dropna(subset=["sqale_before","sqale_after"]).copy()
CATS = list(PALETTE.keys())
ordered_cats = [c for c in CATS if c in pairs["dominant_category"].unique()]

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONSOLE TABLES
# ══════════════════════════════════════════════════════════════════════════════
SEP = "─" * 76

def print_table(title, df):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)
    print(df.to_string(index=False))

print(f"\n{'═'*76}")
print("  TECHNICAL DEBT ENERGY STUDY — SUMMARY REPORT")
print(f"{'═'*76}")

# 1a. Overall stats
total      = len(pairs)
with_s     = len(with_sonar)
neg_delta  = (with_sonar["sqale_delta"] < 0).sum()
pos_delta  = (with_sonar["sqale_delta"] > 0).sum()
print(f"\n  Total refactoring commit pairs : {total:>7,}")
print(f"  Pairs with Sonar coverage      : {with_s:>7,}  ({with_s/total*100:.1f}%)")
print(f"  Pairs where TD decreased       : {neg_delta:>7,}  ({neg_delta/with_s*100:.1f}%)")
print(f"  Pairs where TD increased       : {pos_delta:>7,}  ({pos_delta/with_s*100:.1f}%)")
print(f"  Max single-commit debt drop    : {with_sonar['sqale_delta'].min():>10,.0f} min")
print(f"  Max single-commit debt gain    : {with_sonar['sqale_delta'].max():>10,.0f} min")

# 1b. Category summary
cat_tbl = cat_s[[
    "dominant_category",
    "refactoring_count_count","refactoring_count_median",
    "sqale_delta_median","sqale_delta_mean","sqale_delta_count",
    "smells_delta_median","complexity_delta_median"
]].copy()
cat_tbl.columns = [
    "Category","Total Commits","Med Refact/Commit",
    "Median SQALE Δ","Mean SQALE Δ","Pairs w/Sonar",
    "Median Smells Δ","Median Complexity Δ"
]
cat_tbl = cat_tbl.sort_values("Median SQALE Δ", ascending=False)
for c in ["Median SQALE Δ","Mean SQALE Δ","Median Smells Δ","Median Complexity Δ"]:
    cat_tbl[c] = cat_tbl[c].map(lambda x: f"{x:+.1f}" if pd.notna(x) else "—")
print_table("CATEGORY-LEVEL TECHNICAL DEBT DELTA", cat_tbl)

# 1c. Project summary
proj_tbl = proj_s[[
    "project_id",
    "refactoring_count_count","sqale_delta_median","sqale_delta_mean",
    "smells_delta_median","complexity_delta_median"
]].copy()
proj_tbl.columns = [
    "Project","Pairs w/Sonar",
    "Median SQALE Δ","Mean SQALE Δ",
    "Median Smells Δ","Median Complexity Δ"
]
proj_tbl["Project"] = proj_tbl["Project"].str.replace("org.apache:","")
proj_tbl = proj_tbl.sort_values("Median SQALE Δ", ascending=False)
for c in ["Median SQALE Δ","Mean SQALE Δ","Median Smells Δ","Median Complexity Δ"]:
    proj_tbl[c] = proj_tbl[c].map(lambda x: f"{x:+.1f}" if pd.notna(x) else "—")
print_table("PROJECT-LEVEL TECHNICAL DEBT DELTA", proj_tbl)

# 1d. Top candidates
print(f"\n{SEP}")
print(f"  TOP {args.top} CANDIDATES PER CATEGORY (for energy measurement)")
print(SEP)
display_cols = ["project_id","refactoring_commit","dominant_category",
                "refactoring_count","sqale_delta","smells_delta",
                "complexity_delta","ncloc_before","candidate_score"]
display_cols = [c for c in display_cols if c in top_c.columns]
for cat, grp in top_c.groupby("dominant_category"):
    chunk = grp.head(args.top)[display_cols].copy()
    chunk["project_id"]       = chunk["project_id"].str.replace("org.apache:","")
    chunk["refactoring_commit"]= chunk["refactoring_commit"].str[:10]
    print(f"\n  [{cat}]")
    print(chunk.to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — INDIVIDUAL CHARTS
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("  Generating charts …")
print(SEP)

# ── Chart 1: Median SQALE Δ by category (horizontal bar) ─────────────────────
fig, ax = plt.subplots(figsize=(9, 4))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
cats_sorted = cat_s.sort_values("sqale_delta_median", ascending=True)
colors = [cat_color(c) for c in cats_sorted["dominant_category"]]
bars = ax.barh(cats_sorted["dominant_category"],
               cats_sorted["sqale_delta_median"],
               color=colors, height=0.55, zorder=3)
for bar, val in zip(bars, cats_sorted["sqale_delta_median"]):
    x_pos = val + (abs(cats_sorted["sqale_delta_median"].max())*0.02)
    ax.text(x_pos, bar.get_y()+bar.get_height()/2,
            f"{val:+.0f} min", va="center", fontsize=9)
ax.axvline(0, color="#999", linewidth=0.8, zorder=2)
ax.set_xlabel("Median SQALE index delta (minutes)")
ax.set_title("Median technical debt change by refactoring category")
ax.xaxis.set_major_formatter(FuncFormatter(fmt_min))
plt.tight_layout()
p = os.path.join(OUT, "01_median_sqale_by_category.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 2: SQALE Δ distribution violin by category ─────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
clipped = with_sonar[with_sonar["sqale_delta"].between(-5000, 5000)].copy()
data_by_cat = [clipped[clipped["dominant_category"]==c]["sqale_delta"].dropna().values
               for c in ordered_cats if c in clipped["dominant_category"].unique()]
valid_cats = [c for c in ordered_cats if c in clipped["dominant_category"].unique()]
parts = ax.violinplot(data_by_cat, positions=range(len(valid_cats)),
                      showmedians=True, showextrema=False, widths=0.65)
for i, (pc, cat) in enumerate(zip(parts["bodies"], valid_cats)):
    pc.set_facecolor(cat_color(cat)); pc.set_alpha(0.65)
parts["cmedians"].set_colors("#222"); parts["cmedians"].set_linewidth(2)
ax.set_xticks(range(len(valid_cats))); ax.set_xticklabels(valid_cats, fontsize=9)
ax.axhline(0, color="#999", linewidth=0.8, linestyle="--")
ax.set_ylabel("SQALE delta (minutes, clipped ±5k)")
ax.set_title("Distribution of SQALE delta by refactoring category")
plt.tight_layout()
p = os.path.join(OUT, "02_sqale_delta_violin.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 3: Count of pairs per category (stacked: with/without Sonar) ────────
fig, ax = plt.subplots(figsize=(9, 4))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
cat_counts = pairs.groupby("dominant_category").size().reset_index(name="total")
cat_sonar  = with_sonar.groupby("dominant_category").size().reset_index(name="with_sonar")
cat_merged = cat_counts.merge(cat_sonar, on="dominant_category", how="left").fillna(0)
cat_merged = cat_merged.sort_values("total", ascending=False)
x = range(len(cat_merged))
ax.bar(x, cat_merged["total"], color="#D3D1C7", label="No Sonar data", zorder=3, width=0.6)
ax.bar(x, cat_merged["with_sonar"],
       color=[cat_color(c) for c in cat_merged["dominant_category"]],
       label="With Sonar data", zorder=4, width=0.6)
ax.set_xticks(list(x)); ax.set_xticklabels(cat_merged["dominant_category"], fontsize=9)
ax.set_ylabel("Number of refactoring commits")
ax.set_title("Refactoring pairs per category — Sonar coverage")
ax.legend(fontsize=9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{int(v):,}"))
plt.tight_layout()
p = os.path.join(OUT, "03_pairs_per_category.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 4: Top 15 projects by median SQALE Δ ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
top_proj = proj_s.nlargest(15, "sqale_delta_median").copy()
top_proj["name"] = top_proj["project_id"].str.replace("org.apache:","")
colors_p = ["#A32D2D" if v < 0 else "#185FA5" for v in top_proj["sqale_delta_median"]]
bars = ax.barh(top_proj["name"], top_proj["sqale_delta_median"],
               color=colors_p, height=0.55, zorder=3)
ax.axvline(0, color="#999", linewidth=0.8)
for bar, val in zip(bars, top_proj["sqale_delta_median"]):
    ax.text(val + (top_proj["sqale_delta_median"].max()*0.02),
            bar.get_y()+bar.get_height()/2,
            f"{val:+.0f}", va="center", fontsize=8.5)
ax.set_xlabel("Median SQALE delta (minutes)")
ax.set_title("Top 15 projects — median technical debt delta per refactoring")
plt.tight_layout()
p = os.path.join(OUT, "04_top_projects_sqale.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 5: SQALE Δ vs Complexity Δ scatter (per pair, sampled) ──────────────
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
sample = with_sonar.dropna(subset=["sqale_delta","complexity_delta"])
sample = sample[sample["sqale_delta"].between(-10000,10000) &
                sample["complexity_delta"].between(-2000,2000)]
for cat in ordered_cats:
    sub = sample[sample["dominant_category"]==cat]
    if len(sub):
        ax.scatter(sub["complexity_delta"], sub["sqale_delta"],
                   c=cat_color(cat), s=10, alpha=0.4, label=cat)
ax.axhline(0, color="#999", lw=0.8, linestyle="--")
ax.axvline(0, color="#999", lw=0.8, linestyle="--")
# Regression line
xv = sample["complexity_delta"].values
yv = sample["sqale_delta"].values
mask = np.isfinite(xv) & np.isfinite(yv)
if mask.sum() > 10:
    slope, intercept, r, p_val, _ = stats.linregress(xv[mask], yv[mask])
    xl = np.linspace(xv[mask].min(), xv[mask].max(), 200)
    ax.plot(xl, slope*xl+intercept, color="#333", lw=1.5,
            label=f"OLS  r={r:.3f}")
ax.set_xlabel("Complexity delta"); ax.set_ylabel("SQALE delta (minutes)")
ax.set_title("Complexity change vs. SQALE change per refactoring commit")
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, fontsize=8, markerscale=2,
          framealpha=0.6, loc="upper left")
plt.tight_layout()
p = os.path.join(OUT, "05_sqale_vs_complexity_scatter.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 6: Code smells Δ by category (box plot) ─────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
clipped_s = with_sonar[with_sonar["smells_delta"].between(-300,300)].copy()
bp_data = [clipped_s[clipped_s["dominant_category"]==c]["smells_delta"].dropna().values
           for c in ordered_cats if c in clipped_s["dominant_category"].unique()]
valid_cats2 = [c for c in ordered_cats if c in clipped_s["dominant_category"].unique()]
bp = ax.boxplot(bp_data, patch_artist=True, notch=False,
                medianprops=dict(color="#111", lw=2),
                flierprops=dict(marker=".", markersize=2, alpha=0.3),
                whiskerprops=dict(lw=0.8), capprops=dict(lw=0.8))
for patch, cat in zip(bp["boxes"], valid_cats2):
    patch.set_facecolor(cat_color(cat)); patch.set_alpha(0.7)
ax.set_xticklabels(valid_cats2, fontsize=9)
ax.axhline(0, color="#999", lw=0.8, linestyle="--")
ax.set_ylabel("Code smells delta (clipped ±300)")
ax.set_title("Code smell change distribution by refactoring category")
plt.tight_layout()
p = os.path.join(OUT, "06_smells_boxplot_by_category.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 7: Refactoring count histogram (how isolated are the commits?) ───────
fig, ax = plt.subplots(figsize=(8, 4))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
rc = pairs["refactoring_count"].clip(upper=50)
ax.hist(rc, bins=40, color="#185FA5", alpha=0.75, edgecolor=BG, zorder=3)
ax.axvline(rc.median(), color="#854F0B", lw=1.5, linestyle="--",
           label=f"Median = {rc.median():.0f}")
ax.set_xlabel("Refactoring count per commit (capped at 50)")
ax.set_ylabel("Number of commits")
ax.set_title("Distribution of refactoring count per commit\n(Lower = more isolated = cleaner energy attribution)")
ax.legend(fontsize=9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{int(v):,}"))
plt.tight_layout()
p = os.path.join(OUT, "07_refactoring_count_histogram.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 8: SQALE debt before vs after (per category, paired means) ──────────
fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
before_means = with_sonar.groupby("dominant_category")["sqale_before"].mean()
after_means  = with_sonar.groupby("dominant_category")["sqale_after"].mean()
cats_ba = before_means.index.tolist()
x = np.arange(len(cats_ba)); w = 0.35
bars1 = ax.bar(x - w/2, before_means.values/1000, width=w, label="Before",
               color=[cat_color(c) for c in cats_ba], alpha=0.5, zorder=3)
bars2 = ax.bar(x + w/2, after_means.values/1000, width=w, label="After",
               color=[cat_color(c) for c in cats_ba], alpha=0.9, zorder=3)
for b1, b2, b, a in zip(bars1, bars2, before_means.values, after_means.values):
    diff = a - b
    sign = "+" if diff >= 0 else ""
    ax.text(b2.get_x()+b2.get_width()/2, b2.get_height()+0.5,
            f"{sign}{diff/1000:.1f}k", ha="center", fontsize=7.5, color="#333")
ax.set_xticks(x); ax.set_xticklabels(cats_ba, fontsize=9)
ax.set_ylabel("Mean SQALE index (thousands of minutes)")
ax.set_title("Mean SQALE debt before vs. after refactoring — by category")
ax.legend(fontsize=9)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f"{v:.0f}k"))
plt.tight_layout()
p = os.path.join(OUT, "08_before_after_sqale_by_category.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 9: SQALE Δ over time (monthly median, all categories) ───────────────
fig, ax = plt.subplots(figsize=(12, 4))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
ts = with_sonar.dropna(subset=["refactoring_date","sqale_delta"]).copy()
ts["refactoring_date"] = pd.to_datetime(ts["refactoring_date"], utc=True, errors="coerce")
ts["month"] = ts["refactoring_date"].dt.to_period("Q")
monthly = ts.groupby("month")["sqale_delta"].median().reset_index()
monthly["month_dt"] = monthly["month"].dt.to_timestamp()
ax.fill_between(monthly["month_dt"], monthly["sqale_delta"],
                alpha=0.25, color="#185FA5")
ax.plot(monthly["month_dt"], monthly["sqale_delta"],
        color="#185FA5", lw=1.5, zorder=3)
ax.axhline(0, color="#999", lw=0.8, linestyle="--")
ax.set_xlabel("Quarter"); ax.set_ylabel("Median SQALE delta (min)")
ax.set_title("Median SQALE delta per quarter across all projects")
plt.tight_layout()
p = os.path.join(OUT, "09_sqale_delta_over_time.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 10: Candidate score distribution (top_candidates) ───────────────────
if "candidate_score" in top_c.columns:
    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
    for cat in ordered_cats:
        sub = top_c[top_c["dominant_category"]==cat]["candidate_score"].dropna()
        if len(sub):
            ax.scatter(sub.values, [cat]*len(sub),
                       c=cat_color(cat), s=60, alpha=0.75, zorder=3)
    ax.axvline(0.7, color="#854F0B", lw=1, linestyle="--",
               label="Score 0.7 threshold")
    ax.set_xlabel("Candidate score (0 = poor, 1 = ideal for energy study)")
    ax.set_title("Top-candidate scores per refactoring category")
    ax.set_xlim(0, 1.05)
    ax.legend(fontsize=9)
    plt.tight_layout()
    p = os.path.join(OUT, "10_candidate_scores.png")
    plt.savefig(p, bbox_inches="tight"); plt.close()
    print(f"  Saved {p}")

# ── Chart 11: Heatmap — SQALE Δ (mean) by project × category ─────────────────
hm_data = (with_sonar.groupby(["project_id","dominant_category"])["sqale_delta"]
           .mean().unstack(fill_value=np.nan))
hm_data.index = hm_data.index.str.replace("org.apache:","")
hm_data = hm_data.reindex(columns=ordered_cats, fill_value=np.nan)
# Keep projects with at least 5 valid cells
hm_data = hm_data[hm_data.notna().sum(axis=1) >= 2]

fig, ax = plt.subplots(figsize=(12, 8))
fig.patch.set_facecolor(BG)
vmax = min(abs(hm_data.values[np.isfinite(hm_data.values)]).max(), 500)
sns.heatmap(hm_data, ax=ax, cmap="RdYlGn_r",
            center=0, vmin=-vmax, vmax=vmax,
            linewidths=0.4, linecolor=BG,
            annot=True, fmt=".0f", annot_kws={"size":7.5},
            cbar_kws={"label":"Mean SQALE delta (min)", "shrink":0.6})
ax.set_title("Mean SQALE delta — project × refactoring category\n(Green = debt reduced, Red = debt increased)")
ax.set_xlabel("Refactoring category"); ax.set_ylabel("")
plt.tight_layout()
p = os.path.join(OUT, "11_heatmap_project_x_category.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ── Chart 12: ncloc vs |SQALE delta| scatter (project-level) ─────────────────
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
proj_ncloc = (with_sonar.groupby("project_id")
              .agg(med_ncloc=("ncloc_before","median"),
                   med_sqale_abs=("sqale_delta", lambda x: x.abs().median()))
              .reset_index())
proj_ncloc["name"] = proj_ncloc["project_id"].str.replace("org.apache:","")
ax.scatter(proj_ncloc["med_ncloc"]/1000, proj_ncloc["med_sqale_abs"],
           s=60, color="#185FA5", alpha=0.8, zorder=3)
for _, row in proj_ncloc.iterrows():
    ax.annotate(row["name"],
                (row["med_ncloc"]/1000, row["med_sqale_abs"]),
                fontsize=7.5, ha="left", va="bottom",
                xytext=(3,3), textcoords="offset points", color="#444")
ax.set_xlabel("Median NCLOC (thousands)"); ax.set_ylabel("Median |SQALE delta| (minutes)")
ax.set_title("Project size vs. absolute SQALE delta magnitude")
plt.tight_layout()
p = os.path.join(OUT, "12_ncloc_vs_sqale_delta.png")
plt.savefig(p, bbox_inches="tight"); plt.close()
print(f"  Saved {p}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — COMBINED FULL REPORT FIGURE
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n  Building combined full_report.png …")

fig = plt.figure(figsize=(20, 28), facecolor=BG)
fig.suptitle("Technical Debt Energy Study — Full Analysis Report",
             fontsize=16, fontweight="bold", y=0.995)

gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.45, wspace=0.35)

def load_img(fname):
    return plt.imread(os.path.join(OUT, fname))

panels = [
    (gs[0,0], "01_median_sqale_by_category.png"),
    (gs[0,1], "03_pairs_per_category.png"),
    (gs[0,2], "07_refactoring_count_histogram.png"),
    (gs[1,0], "02_sqale_delta_violin.png"),
    (gs[1,1], "06_smells_boxplot_by_category.png"),
    (gs[1,2], "08_before_after_sqale_by_category.png"),
    (gs[2,0], "05_sqale_vs_complexity_scatter.png"),
    (gs[2,1], "04_top_projects_sqale.png"),
    (gs[2,2], "10_candidate_scores.png"),
    (gs[3,0:2], "09_sqale_delta_over_time.png"),
    (gs[3,2],   "12_ncloc_vs_sqale_delta.png"),
]
for slot, fname in panels:
    ax_img = fig.add_subplot(slot)
    try:
        ax_img.imshow(load_img(fname))
    except FileNotFoundError:
        ax_img.text(0.5, 0.5, fname, ha="center", va="center", fontsize=8)
    ax_img.axis("off")

report_path = os.path.join(OUT, "full_report.png")
plt.savefig(report_path, bbox_inches="tight", dpi=140)
plt.close()
print(f"  Saved {report_path}")

# ── Heatmap added separately (it's large) ─────────────────────────────────────
print(f"\n{SEP}")
print(f"  Done!  All outputs in: {OUT}/")
print(f"  Charts : 01 – 12 individual PNGs")
print(f"  Summary: full_report.png  (all charts combined)")
print(SEP)