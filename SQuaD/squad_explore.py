# squad_explore.py
# Scans the full CSV in chunks and ranks project-release pairs as RAPL candidates
# Writes squad_candidates.csv
# Usage: python squad_explore.py "path/to/squad.csv"

import pandas as pd
import sys
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else "squad.csv"

CHUNK_SIZE = 50_000
COLS = [
    "project_name", "release_name", "file", "metric_type",
    "measures_sqale_index", "measures_sqale_debt_ratio", "measures_sqale_rating",
    "measures_ncloc", "measures_lines", "measures_code_smells",
    "measures_maintainability_issues_total", "measures_last_commit_date"
]

NUMERIC_COLS = [
    "measures_sqale_index", "measures_sqale_debt_ratio", "measures_sqale_rating",
    "measures_ncloc", "measures_lines", "measures_code_smells",
    "measures_maintainability_issues_total", "measures_last_commit_date"
]

print("Scanning file in chunks...")
aggregated = {}

for i, chunk in enumerate(pd.read_csv(path, usecols=COLS, chunksize=CHUNK_SIZE, low_memory=False)):
    if i % 20 == 0:
        print(f"  chunk {i}...")

    chunk = chunk[chunk["metric_type"] == "measure"]
    chunk = chunk[chunk["release_name"].notna() & chunk["project_name"].notna()]

    for col in NUMERIC_COLS:
        if col in chunk.columns:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

    for (project, release), grp in chunk.groupby(["project_name", "release_name"]):
        key = (project, release)
        row = {
            "sqale_index_sum":  grp["measures_sqale_index"].sum(min_count=1),
            "sqale_debt_ratio": grp["measures_sqale_debt_ratio"].mean(),
            "ncloc":            grp["measures_ncloc"].sum(min_count=1),
            "lines":            grp["measures_lines"].sum(min_count=1),
            "code_smells":      grp["measures_code_smells"].sum(min_count=1),
            "last_commit_date": grp["measures_last_commit_date"].max(),
            "file_count":       grp["file"].nunique(),
        }
        if key in aggregated:
            for k in ["sqale_index_sum", "ncloc", "lines", "code_smells", "file_count"]:
                aggregated[key][k] = (aggregated[key][k] or 0) + (row[k] or 0)
            v1 = aggregated[key]["sqale_debt_ratio"]
            v2 = row["sqale_debt_ratio"]
            if pd.notna(v1) and pd.notna(v2):
                aggregated[key]["sqale_debt_ratio"] = (v1 + v2) / 2
            elif pd.notna(v2):
                aggregated[key]["sqale_debt_ratio"] = v2
            aggregated[key]["last_commit_date"] = max(
                aggregated[key]["last_commit_date"] or 0, row["last_commit_date"] or 0
            )
        else:
            aggregated[key] = row

print(f"\nDone. Found {len(aggregated)} project-release combinations.\n")

df = pd.DataFrame([
    {"project": k[0], "release": k[1], **v}
    for k, v in aggregated.items()
])

df["last_commit_date"] = pd.to_datetime(df["last_commit_date"], unit="ms", errors="coerce")
df = df.sort_values(["project", "last_commit_date"])

# ── Per-project release overview ───────────────────────────────────────────────
print("=== PROJECT RELEASE OVERVIEW ===")
for project, grp in df.groupby("project"):
    print(f"\n  {project}  ({len(grp)} releases)")
    print(grp[["release", "ncloc", "sqale_index_sum", "sqale_debt_ratio", "last_commit_date"]]
          .to_string(index=False))

# ── Find candidate pairs ───────────────────────────────────────────────────────
MAX_LOC_CHANGE_PCT = 0.25   # max 25% NCLOC change between releases
MAX_DATE_GAP_DAYS  = 365    # max 1 year between releases
MIN_DEBT_DROP_PCT  = 0.30   # at least 30% drop in sqale_debt_ratio

print("\n\n=== CANDIDATE PAIRS (high TD drop, stable codebase) ===")
candidates = []

for project, grp in df.groupby("project"):
    grp = grp.reset_index(drop=True)
    for i in range(len(grp) - 1):
        r1, r2 = grp.iloc[i], grp.iloc[i + 1]

        if pd.isna(r1["ncloc"]) or pd.isna(r2["ncloc"]):
            continue
        if pd.isna(r1["sqale_debt_ratio"]) or pd.isna(r2["sqale_debt_ratio"]):
            continue

        loc_change = abs(r2["ncloc"] - r1["ncloc"]) / (r1["ncloc"] + 1)
        debt_drop  = (r1["sqale_debt_ratio"] - r2["sqale_debt_ratio"]) / (r1["sqale_debt_ratio"] + 1e-9)

        date_gap = None
        if pd.notna(r1["last_commit_date"]) and pd.notna(r2["last_commit_date"]):
            date_gap = (r2["last_commit_date"] - r1["last_commit_date"]).days

        if (loc_change   <= MAX_LOC_CHANGE_PCT and
            debt_drop    >= MIN_DEBT_DROP_PCT  and
            (date_gap is None or date_gap <= MAX_DATE_GAP_DAYS)):

            candidates.append({
                "project":         project,
                "release_high_td": r1["release"],
                "release_low_td":  r2["release"],
                "ncloc_r1":        int(r1["ncloc"]),
                "ncloc_r2":        int(r2["ncloc"]),
                "loc_change_pct":  round(loc_change * 100, 1),
                "debt_ratio_r1":   round(r1["sqale_debt_ratio"], 2),
                "debt_ratio_r2":   round(r2["sqale_debt_ratio"], 2),
                "debt_drop_pct":   round(debt_drop * 100, 1),
                "date_gap_days":   date_gap,
            })

if candidates:
    cdf = pd.DataFrame(candidates).sort_values("debt_drop_pct", ascending=False)
    print(cdf.to_string(index=False))
    cdf.to_csv("squad_candidates.csv", index=False)
    print(f"\n✅ Saved {len(cdf)} candidates to squad_candidates.csv")
else:
    print("No candidates found — try relaxing the thresholds at the top of the script.")