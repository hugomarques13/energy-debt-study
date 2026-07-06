# squad_pipeline_prep.py
# Extracts all candidates, relaxed thresholds, Java/Maven projects prioritized
import pandas as pd
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "squad_candidates.csv"
df = pd.read_csv(path)

# Relax thresholds vs before
MAX_LOC_CHANGE_PCT = 0.30   # 30% instead of 25%
MIN_DEBT_DROP_PCT  = 0.20   # 20% instead of 30%
MAX_DATE_GAP_DAYS  = 548    # 18 months instead of 12

# Filter
df = df[
    (df["loc_change_pct"] <= MAX_LOC_CHANGE_PCT * 100) &
    (df["debt_drop_pct"]  >= MIN_DEBT_DROP_PCT  * 100) &
    (df["date_gap_days"].isna() | (df["date_gap_days"] <= MAX_DATE_GAP_DAYS))
]

# Drop major version jumps
import re
def is_major_jump(r1, r2):
    def major(v):
        m = re.search(r'(\d+)', str(v))
        return int(m.group(1)) if m else None
    m1, m2 = major(r1), major(r2)
    if m1 is None or m2 is None:
        return False
    return m2 - m1 >= 1 and m1 != m2

df = df[~df.apply(lambda r: is_major_jump(r["release_high_td"], r["release_low_td"]), axis=1)]

# Drop obvious artifacts
df = df[df["debt_drop_pct"] < 99]
df = df[df["debt_ratio_r2"] > 0]

# Sort by debt drop
df = df.sort_values("debt_drop_pct", ascending=False)

print(f"Total candidates: {len(df)}\n")
print(df[["project","release_high_td","release_low_td","loc_change_pct","debt_ratio_r1","debt_ratio_r2","debt_drop_pct","date_gap_days"]].to_string(index=False))

df.to_csv("squad_pipeline_candidates.csv", index=False)
print(f"\nSaved to squad_pipeline_candidates.csv")