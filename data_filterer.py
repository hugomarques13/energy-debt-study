"""
Technical Debt Dataset - Extractor / Filterer
==============================================
Extracts before/after refactoring commit pairs with full TD metrics
from SONAR_MEASURES (SQALE_INDEX, CODE_SMELLS, BUGS, COMPLEXITY, NCLOC),
groups by refactoring category, and scores pairs for energy study selection.

Usage:
    pip install pandas
    python data_filterer.py --db td_V2.db --out ./output

Optional:
    --project org.apache:hive     Filter to one project
    --min-debt-delta 60           Only pairs where |SQALE delta| >= N minutes (default 0)
    --top N                       How many top candidates to show per category (default 10)
"""

import sqlite3
import pandas as pd
import argparse
import os
import sys

# ── CLI ───────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--db",             required=True)
parser.add_argument("--out",            default="./td_output")
parser.add_argument("--project",        default=None)
parser.add_argument("--min-debt-delta", type=float, default=0.0)
parser.add_argument("--top",            type=int,   default=10)
args = parser.parse_args()

os.makedirs(args.out, exist_ok=True)

# ── Refactoring type grouping ─────────────────────────────────────────────────
# Maps each RefactoringMiner type to a study category

CATEGORY_MAP = {
    # --- Structural ---
    "Extract Method":           "Structural",
    "Extract Class":            "Structural",
    "Extract Interface":        "Structural",
    "Extract Subclass":         "Structural",
    "Extract Superclass":       "Structural",
    "Inline Method":            "Structural",
    "Pull Up Method":           "Structural",
    "Pull Up Attribute":        "Structural",
    "Push Down Method":         "Structural",
    "Push Down Attribute":      "Structural",
    "Extract Variable":         "Structural",
    "Inline Variable":          "Structural",
    "Merge Method":             "Structural",
    "Split Method":             "Structural",
    "Decompose Conditional":    "Structural",
    # --- Move / Reorganise ---
    "Move Method":              "Move",
    "Move Attribute":           "Move",
    "Move Class":               "Move",
    "Move And Rename Class":    "Move",
    "Move And Rename Method":   "Move",
    "Move And Inline Method":   "Move",
    "Move Source Folder":       "Move",
    "Move Package":             "Move",
    # --- Rename ---
    "Rename Method":            "Rename",
    "Rename Attribute":         "Rename",
    "Rename Variable":          "Rename",
    "Rename Parameter":         "Rename",
    "Rename Class":             "Rename",
    "Rename Package":           "Rename",
    # --- Type Change ---
    "Change Variable Type":     "TypeChange",
    "Change Attribute Type":    "TypeChange",
    "Change Parameter Type":    "TypeChange",
    "Change Return Type":       "TypeChange",
    # --- Modifier / Annotation ---
    "Change Method Access Modifier":    "Modifier",
    "Change Attribute Access Modifier": "Modifier",
    "Change Class Access Modifier":     "Modifier",
    "Add Method Annotation":    "Modifier",
    "Remove Method Annotation": "Modifier",
    "Add Parameter Annotation": "Modifier",
    "Remove Parameter Annotation": "Modifier",
    "Add Attribute Annotation": "Modifier",
    "Remove Attribute Annotation": "Modifier",
    "Add Class Annotation":     "Modifier",
    "Remove Class Annotation":  "Modifier",
    "Modify Method Annotation": "Modifier",
    "Modify Class Annotation":  "Modifier",
    # --- Signature ---
    "Add Parameter":            "Signature",
    "Remove Parameter":         "Signature",
    "Reorder Parameter":        "Signature",
    "Add Thrown Exception Type":"Signature",
    "Remove Thrown Exception Type": "Signature",
    "Change Thrown Exception Type": "Signature",
}

def categorise(refactoring_types_str):
    """Given a '|'-separated string of types, return the dominant category."""
    types = [t.strip() for t in str(refactoring_types_str).split('|')]
    counts = {}
    for t in types:
        cat = CATEGORY_MAP.get(t, "Other")
        counts[cat] = counts.get(cat, 0) + 1
    return max(counts, key=counts.get) if counts else "Other"

def categorise_all(refactoring_types_str):
    """Return all unique categories present in a commit."""
    types = [t.strip() for t in str(refactoring_types_str).split('|')]
    cats  = sorted(set(CATEGORY_MAP.get(t, "Other") for t in types))
    return " | ".join(cats)

# ── Connect ───────────────────────────────────────────────────────────────────

print(f"\n[1/6] Connecting to: {args.db}")
try:
    con = sqlite3.connect(args.db)
except Exception as e:
    print(f"ERROR: {e}"); sys.exit(1)

proj_where_rm = f"WHERE LOWER(PROJECT_ID) = LOWER('{args.project}')" if args.project else ""
proj_where_gc = f"WHERE LOWER(PROJECT_ID) = LOWER('{args.project}')" if args.project else ""
proj_and_sa   = f"AND   LOWER(sa.PROJECT_ID) = LOWER('{args.project}')" if args.project else ""

# ── Step 1: Load REFACTORING_MINER ───────────────────────────────────────────

print("[2/6] Loading refactoring commits...")

refactorings = pd.read_sql(f"""
    SELECT
        PROJECT_ID,
        COMMIT_HASH,
        REFACTORING_TYPE,
        REFACTORING_DETAIL
    FROM REFACTORING_MINER
    {proj_where_rm}
""", con)

print(f"  {len(refactorings):,} refactoring records across "
      f"{refactorings['PROJECT_ID'].nunique()} projects.")

# Collapse to one row per commit: count + pipe-joined type list
ref_per_commit = (
    refactorings
    .groupby(['PROJECT_ID', 'COMMIT_HASH'])
    .agg(
        refactoring_count=('REFACTORING_TYPE', 'count'),
        refactoring_types=('REFACTORING_TYPE',
                           lambda x: ' | '.join(sorted(set(x.dropna()))))
    )
    .reset_index()
)
ref_per_commit['dominant_category'] = ref_per_commit['refactoring_types'].apply(categorise)
ref_per_commit['all_categories']    = ref_per_commit['refactoring_types'].apply(categorise_all)

print(f"  {len(ref_per_commit):,} unique refactoring commits.")

# ── Step 2: Load GIT_COMMITS (ordered) ───────────────────────────────────────

print("[3/6] Loading git commits...")

commits = pd.read_sql(f"""
    SELECT
        PROJECT_ID,
        COMMIT_HASH,
        COMMITTER_DATE  AS COMMIT_DATE,
        COMMIT_MESSAGE
    FROM GIT_COMMITS
    {proj_where_gc}
""", con)

commits['COMMIT_DATE'] = pd.to_datetime(commits['COMMIT_DATE'], errors='coerce', utc=True)
commits = commits.sort_values(['PROJECT_ID', 'COMMIT_DATE'])
commits['row_idx'] = commits.groupby('PROJECT_ID').cumcount()
print(f"  {len(commits):,} commits.")

# ── Step 3: Load SONAR_MEASURES via SONAR_ANALYSIS ───────────────────────────
# SONAR_ANALYSIS: PROJECT_ID, ANALYSIS_KEY, DATE, REVISION (=commit hash)
# SONAR_MEASURES: PROJECT_ID, ANALYSIS_KEY, SQALE_INDEX, CODE_SMELLS, BUGS,
#                 VULNERABILITIES, COMPLEXITY, COGNITIVE_COMPLEXITY, NCLOC,
#                 VIOLATIONS, DUPLICATED_LINES_DENSITY

print("[4/6] Loading SonarQube measures...")

measures = pd.read_sql(f"""
    SELECT
        sa.PROJECT_ID,
        sa.REVISION                         AS COMMIT_HASH,
        sm.SQALE_INDEX,
        sm.CODE_SMELLS,
        sm.BUGS,
        sm.VULNERABILITIES,
        sm.VIOLATIONS,
        sm.COMPLEXITY,
        sm.COGNITIVE_COMPLEXITY,
        sm.NCLOC,
        sm.DUPLICATED_LINES_DENSITY,
        sm.FUNCTIONS,
        sm.CLASSES
    FROM SONAR_MEASURES sm
    JOIN SONAR_ANALYSIS sa ON sm.ANALYSIS_KEY = sa.ANALYSIS_KEY
    WHERE sa.REVISION IS NOT NULL
      AND sa.REVISION != ''
      {proj_and_sa}
""", con)

print(f"  {len(measures):,} measure snapshots.")

# ── Step 4: Build before/after pairs ─────────────────────────────────────────

print("[5/6] Building before/after pairs...")

# Merge ref commits with their row index in git history
ref_idx = ref_per_commit.merge(
    commits[['PROJECT_ID', 'COMMIT_HASH', 'row_idx', 'COMMIT_DATE', 'COMMIT_MESSAGE']],
    on=['PROJECT_ID', 'COMMIT_HASH'],
    how='left'
)

project_commits_map = {
    pid: grp.set_index('row_idx')
    for pid, grp in commits.groupby('PROJECT_ID')
}

rows = []
for _, r in ref_idx.iterrows():
    pid = r['PROJECT_ID']
    idx = r['row_idx']
    pc  = project_commits_map.get(pid, pd.DataFrame())

    before_hash = pc.at[idx - 1, 'COMMIT_HASH'] if (idx - 1) in pc.index else None
    after_hash  = pc.at[idx + 1, 'COMMIT_HASH'] if (idx + 1) in pc.index else None

    rows.append({
        'project_id':          pid,
        'refactoring_commit':  r['COMMIT_HASH'],
        'refactoring_date':    r['COMMIT_DATE'],
        'commit_message':      r['COMMIT_MESSAGE'],
        'refactoring_count':   r['refactoring_count'],
        'refactoring_types':   r['refactoring_types'],
        'dominant_category':   r['dominant_category'],
        'all_categories':      r['all_categories'],
        'commit_before':       before_hash,
        'commit_after':        after_hash,
    })

pairs = pd.DataFrame(rows)

# ── Step 5: Attach measures for before and after commits ─────────────────────

measures_slim = measures[[
    'PROJECT_ID', 'COMMIT_HASH',
    'SQALE_INDEX', 'CODE_SMELLS', 'BUGS', 'VULNERABILITIES',
    'VIOLATIONS', 'COMPLEXITY', 'COGNITIVE_COMPLEXITY',
    'NCLOC', 'DUPLICATED_LINES_DENSITY', 'FUNCTIONS', 'CLASSES'
]].drop_duplicates(subset=['PROJECT_ID', 'COMMIT_HASH'])

for side in ['before', 'after']:
    suffix = f'_{side}'
    pairs = pairs.merge(
        measures_slim.rename(columns={
            'COMMIT_HASH':            f'commit_{side}',
            'PROJECT_ID':             'project_id',
            'SQALE_INDEX':            f'sqale{suffix}',
            'CODE_SMELLS':            f'smells{suffix}',
            'BUGS':                   f'bugs{suffix}',
            'VULNERABILITIES':        f'vulns{suffix}',
            'VIOLATIONS':             f'violations{suffix}',
            'COMPLEXITY':             f'complexity{suffix}',
            'COGNITIVE_COMPLEXITY':   f'cog_complexity{suffix}',
            'NCLOC':                  f'ncloc{suffix}',
            'DUPLICATED_LINES_DENSITY': f'duplication{suffix}',
            'FUNCTIONS':              f'functions{suffix}',
            'CLASSES':                f'classes{suffix}',
        }),
        on=['project_id', f'commit_{side}'],
        how='left'
    )

# Coerce all metric columns to numeric (SQLite stores some as TEXT)
METRIC_BASES = ["sqale", "smells", "bugs", "vulns", "violations",
                "complexity", "cog_complexity", "ncloc", "duplication",
                "functions", "classes"]
for base in METRIC_BASES:
    for side in ["before", "after"]:
        col = f"{base}_{side}"
        if col in pairs.columns:
            pairs[col] = pd.to_numeric(pairs[col], errors="coerce")

# Compute deltas (after - before; negative = debt reduced = good refactoring)
for metric in ["sqale", "smells", "bugs", "vulns", "violations",
               "complexity", "cog_complexity", "ncloc", "duplication"]:
    b, a = f"{metric}_before", f"{metric}_after"
    if b in pairs.columns and a in pairs.columns:
        pairs[f"{metric}_delta"] = pairs[a] - pairs[b]

# Filter by min debt delta
has_sqale = 'sqale_delta' in pairs.columns
if args.min_debt_delta > 0 and has_sqale:
    before_n = len(pairs)
    pairs = pairs[pairs['sqale_delta'].abs() >= args.min_debt_delta]
    print(f"  Filtered to {len(pairs):,} pairs (was {before_n:,}; |sqale_delta| >= {args.min_debt_delta})")

print(f"  Total pairs: {len(pairs):,}")

# ── Step 6: Score and rank candidates for energy study ───────────────────────
# A good candidate for energy measurement has:
#   - Large TD reduction (high |sqale_delta|)          → weight 0.40
#   - Isolated refactoring (low refactoring_count)     → weight 0.20
#     (fewer changes = cleaner energy attribution)
#   - Meaningful codebase size (ncloc_before)          → weight 0.15
#   - Both before and after have Sonar data            → hard requirement
#   - Measurable complexity change                     → weight 0.25

if has_sqale:
    scored = pairs.dropna(subset=['sqale_before', 'sqale_after']).copy()

    def normalise(s):
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn + 1e-9)

    scored['score_sqale']      =  normalise(scored['sqale_delta'].abs())
    scored['score_isolation']  =  1 - normalise(scored['refactoring_count'])
    scored['score_complexity'] =  normalise(scored['complexity_delta'].abs()) if 'complexity_delta' in scored.columns else 0
    scored['score_size']       =  normalise(scored['ncloc_before'].fillna(0))

    scored['candidate_score'] = (
        0.40 * scored['score_sqale'] +
        0.20 * scored['score_isolation'] +
        0.25 * scored['score_complexity'] +
        0.15 * scored['score_size']
    )
    scored = scored.sort_values('candidate_score', ascending=False)

    # Top candidates per category
    top_per_category = (
        scored
        .groupby('dominant_category')
        .head(args.top)
        .sort_values(['dominant_category', 'candidate_score'], ascending=[True, False])
    )
else:
    scored = pairs.copy()
    scored['candidate_score'] = None
    top_per_category = pairs.groupby('dominant_category').head(args.top)

# ── Summary by project ────────────────────────────────────────────────────────

metric_cols = [c for c in [
    'refactoring_count', 'sqale_before', 'sqale_after', 'sqale_delta',
    'smells_before', 'smells_after', 'smells_delta',
    'complexity_delta', 'bugs_delta'
] if c in pairs.columns]

summary = (
    pairs.groupby('project_id')[metric_cols]
    .agg(['mean', 'median', 'sum', 'count'])
    .reset_index()
)
summary.columns = ['_'.join(c).strip('_') for c in summary.columns]

# Summary by refactoring category
cat_cols = [c for c in [
    'refactoring_count', 'sqale_delta', 'smells_delta', 'complexity_delta'
] if c in pairs.columns]

cat_summary = (
    pairs.groupby('dominant_category')[cat_cols]
    .agg(['mean', 'median', 'count'])
    .reset_index()
)
cat_summary.columns = ['_'.join(c).strip('_') for c in cat_summary.columns]

# ── Export ────────────────────────────────────────────────────────────────────

out_pairs    = os.path.join(args.out, "refactoring_pairs_with_metrics.csv")
out_top      = os.path.join(args.out, "top_candidates_by_category.csv")
out_proj     = os.path.join(args.out, "summary_by_project.csv")
out_cat      = os.path.join(args.out, "summary_by_category.csv")

pairs.to_csv(out_pairs, index=False)
top_per_category.to_csv(out_top, index=False)
summary.to_csv(out_proj, index=False)
cat_summary.to_csv(out_cat, index=False)

print("\n✅ Done!")
print(f"   {out_pairs}")
print(f"     → {len(pairs):,} pairs with full TD metrics (sqale, smells, bugs, complexity)")
print(f"   {out_top}")
print(f"     → Top {args.top} candidates per refactoring category, scored for energy study")
print(f"   {out_proj}")
print(f"     → TD delta stats aggregated per project")
print(f"   {out_cat}")
print(f"     → TD delta stats aggregated per refactoring category")

if has_sqale:
    print(f"\n📊 Category breakdown (pairs with Sonar data):")
    for cat, grp in scored.groupby('dominant_category'):
        n = len(grp)
        med_delta = grp['sqale_delta'].median()
        print(f"   {cat:<15} {n:>5} pairs  |  median sqale_delta = {med_delta:>8.0f} min")
else:
    print("\n⚠️  No Sonar measures were matched to commit hashes.")
    print("   The pairs CSV still has before/after commit hashes for git checkout.")
    print("   Check that SONAR_ANALYSIS.REVISION values match GIT_COMMITS.COMMIT_HASH format.")

con.close()