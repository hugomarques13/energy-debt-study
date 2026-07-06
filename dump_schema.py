"""
dump_schema.py — Inspect the dataset: prints columns and 2 sample rows
for the key tables (SONAR_ANALYSIS, SONAR_MEASURES, REFACTORING_MINER,
GIT_COMMITS, ...). Handy as a first step to understand the DB.

Usage: python dump_schema.py --db td_V2.db
"""
import sqlite3, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--db", required=True)
args = parser.parse_args()

con = sqlite3.connect(args.db)

TABLES_OF_INTEREST = [
    'SONAR_ANALYSIS', 'SONAR_ANALYSES',
    'SONAR_ISSUES', 'SONAR_MEASURES',
    'REFACTORING_MINER', 'GIT_COMMITS',
]

all_tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()]

for t in all_tables:
    if t not in TABLES_OF_INTEREST:
        continue
    cols = con.execute(f"PRAGMA table_info({t})").fetchall()
    print(f"\n{'='*60}")
    print(f"TABLE: {t}")
    print(f"{'='*60}")
    for col in cols:
        # cid, name, type, notnull, dflt, pk
        print(f"  {col[1]:<40} {col[2]}")

    # Show 2 sample rows
    try:
        rows = con.execute(f"SELECT * FROM {t} LIMIT 2").fetchall()
        print(f"\n  -- Sample rows --")
        for row in rows:
            print(f"  {row}")
    except Exception as e:
        print(f"  (could not sample: {e})")

con.close()