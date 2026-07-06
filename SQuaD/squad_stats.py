# squad_stats.py
# Usage: python squad_stats.py "C:\path\to\squad.csv"

import pandas as pd
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "squad.csv"

CHUNK_SIZE = 50_000
COLS = ["project_name", "release_name", "file", "metric_type",
        "measures_ncloc", "measures_sqale_index", "measures_sqale_debt_ratio",
        "measures_code_smells", "measures_bugs", "issues_type", "measures_lines"]

stats = {
    "total_rows": 0,
    "projects": set(),
    "releases": set(),
    "files": set(),
    "measure_rows": 0,
    "issue_rows": 0,
}

print("Scanning...")
for i, chunk in enumerate(pd.read_csv(path, usecols=COLS, chunksize=CHUNK_SIZE, low_memory=False)):
    if i % 50 == 0:
        print(f"  chunk {i}...")

    stats["total_rows"] += len(chunk)
    stats["projects"].update(chunk["project_name"].dropna().unique())
    stats["releases"].update(chunk["release_name"].dropna().unique())
    stats["files"].update(chunk["file"].dropna().unique())
    stats["measure_rows"] += (chunk["metric_type"] == "measure").sum()
    stats["issue_rows"]   += (chunk["metric_type"] == "issue").sum()

print(f"\n=== SQuaD Dataset Statistics ===")
print(f"  Total rows:        {stats['total_rows']:,}")
print(f"  Unique projects:   {len(stats['projects']):,}")
print(f"  Unique releases:   {len(stats['releases']):,}")
print(f"  Unique files:      {len(stats['files']):,}")
print(f"  Measure rows:      {stats['measure_rows']:,}")
print(f"  Issue rows:        {stats['issue_rows']:,}")
print(f"\n  Avg releases/project: {len(stats['releases']) / max(len(stats['projects']),1):.1f}")
print(f"  Avg files/project:    {len(stats['files']) / max(len(stats['projects']),1):.1f}")

print(f"\n=== Top 10 projects by release count ===")
release_counts = {}
for r in stats["releases"]:
    # releases are stored as "project#release" — just count per project
    pass

# Re-scan quickly for per-project release counts
proj_releases = {}
for i, chunk in enumerate(pd.read_csv(path, usecols=["project_name","release_name","metric_type"],
                                        chunksize=CHUNK_SIZE, low_memory=False)):
    chunk = chunk[chunk["metric_type"] == "measure"]
    for proj, grp in chunk.groupby("project_name"):
        if proj not in proj_releases:
            proj_releases[proj] = set()
        proj_releases[proj].update(grp["release_name"].dropna().unique())

top10 = sorted(proj_releases.items(), key=lambda x: len(x[1]), reverse=True)[:10]
for proj, rels in top10:
    print(f"  {proj}: {len(rels)} releases")