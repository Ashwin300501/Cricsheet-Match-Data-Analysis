import os
import sqlite3
import pandas as pd

# ---------------- Paths ----------------
BASE_DIR = "cricsheet_data"
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")
DB_PATH = "cricsheet_match_data.db"   # DB outside cricsheet_data

# -------- Tables & CSVs --------
TABLE_MAP = {
    "test_table": os.path.join(PROCESSED_DIR, "test.csv"),
    "odi_table":  os.path.join(PROCESSED_DIR, "ODI.csv"),
    "t20_table":  os.path.join(PROCESSED_DIR, "T20.csv"),
    "ipl_table":  os.path.join(PROCESSED_DIR, "IPL.csv"),
}

# -------- DDL --------
DDL_TEMPLATE = """
DROP TABLE IF EXISTS {table};
CREATE TABLE {table} (
    match_id        TEXT,
    match_date      TEXT,
    match_type      TEXT,
    season          TEXT,
    city            TEXT,
    venue           TEXT,
    toss_winner     TEXT,
    toss_decision   TEXT,
    winner          TEXT,
    player_of_match TEXT,
    teams           TEXT,

    team            TEXT,
    over            INTEGER,
    batter          TEXT,
    bowler          TEXT,
    non_striker     TEXT,
    runs_batter     INTEGER,
    runs_extras     INTEGER,
    runs_total      INTEGER,
    wicket          TEXT
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS {t}_idx_match_id    ON {t}(match_id);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_mt_season   ON {t}(match_type, season);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_team_season ON {t}(team, season);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_batter      ON {t}(batter);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_bowler      ON {t}(bowler);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_winner      ON {t}(winner);",
    "CREATE INDEX IF NOT EXISTS {t}_idx_venue       ON {t}(venue);",
]

def load_csv_to_table(conn, table_name, csv_path, expected_match_type=None):
    if not os.path.isfile(csv_path):
        print(f"⚠️  Missing CSV for {table_name}: {csv_path}")
        return 0

    df = pd.read_csv(csv_path, low_memory=False)

    # Optional sanity check on match_type vs expectation
    if expected_match_type and "match_type" in df.columns:
        bad = df[(df["match_type"].notna()) & (df["match_type"] != expected_match_type)]
        if len(bad) > 0:
            print(
                f"⚠️  {len(bad):,} rows in {os.path.basename(csv_path)} have match_type != '{expected_match_type}' "
                f"(examples: {bad['match_type'].dropna().unique()[:5]})"
            )

    df.to_sql(table_name, conn, if_exists="append", index=False, chunksize=50_000)
    return len(df)

def run_sanity_tests(conn):
    cur = conn.cursor()
    print("\n==================== SANITY TESTS ====================")

    # 1) Row counts & distinct match_type per table
    for table in TABLE_MAP.keys():
        cnt = cur.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        mt = cur.execute(f"SELECT match_type, COUNT(*) FROM {table} GROUP BY match_type;").fetchall()
        print(f"\n▶ {table}: rows={cnt:,}")
        for r in mt:
            print("   ", r)

    # 2) Null checks on key columns (team, batter, bowler, runs_total)
    for table in TABLE_MAP.keys():
        q = f"""
        SELECT
          SUM(CASE WHEN team IS NULL OR TRIM(team)='' THEN 1 ELSE 0 END),
          SUM(CASE WHEN batter IS NULL OR TRIM(batter)='' THEN 1 ELSE 0 END),
          SUM(CASE WHEN bowler IS NULL OR TRIM(bowler)='' THEN 1 ELSE 0 END),
          SUM(CASE WHEN runs_total IS NULL THEN 1 ELSE 0 END)
        FROM {table};
        """
        null_team, null_batter, null_bowler, null_runs = cur.execute(q).fetchone()
        print(f"\n▶ NULL checks ({table})")
        print(f"   team NULL/blank     : {null_team:,}")
        print(f"   batter NULL/blank   : {null_batter:,}")
        print(f"   bowler NULL/blank   : {null_bowler:,}")
        print(f"   runs_total NULL     : {null_runs:,}")

    # 3) Basic value sanity (negative runs? over null?)
    for table in TABLE_MAP.keys():
        neg_runs = cur.execute(f"SELECT COUNT(*) FROM {table} WHERE runs_total < 0 OR runs_batter < 0 OR runs_extras < 0;").fetchone()[0]
        null_over = cur.execute(f"SELECT COUNT(*) FROM {table} WHERE over IS NULL;").fetchone()[0]
        print(f"\n▶ Value sanity ({table})")
        print(f"   negative run rows   : {neg_runs:,}")
        print(f"   NULL over rows      : {null_over:,}")

    # 4) IPL match_type quick check (Cricsheet usually marks IPL as T20)
    ipl_mt = cur.execute("SELECT match_type, COUNT(*) FROM ipl_table GROUP BY match_type;").fetchall()
    print("\n▶ IPL match_type distribution (expected to be mostly 'T20'):")
    for r in ipl_mt:
        print("   ", r)

    # 5) Top venues (quick distribution peek)
    for table in TABLE_MAP.keys():
        top_venues = cur.execute(f"""
            SELECT venue, COUNT(*) AS c
            FROM {table}
            GROUP BY venue
            ORDER BY c DESC
            LIMIT 5;
        """).fetchall()
        print(f"\n▶ Top venues ({table})")
        for v in top_venues:
            print("   ", v)

    print("\n================== SANITY TESTS DONE =================")

def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create each table fresh
    for table in TABLE_MAP.keys():
        cur.executescript(DDL_TEMPLATE.format(table=table))
    conn.commit()

    # Load each CSV into its own table
    totals = {}
    totals["test_table"] = load_csv_to_table(conn, "test_table", TABLE_MAP["test_table"], expected_match_type="Test")
    print(f"✅ Loaded {totals['test_table']:,} rows into test_table")

    totals["odi_table"]  = load_csv_to_table(conn, "odi_table",  TABLE_MAP["odi_table"],  expected_match_type="ODI")
    print(f"✅ Loaded {totals['odi_table']:,} rows into odi_table")

    totals["t20_table"]  = load_csv_to_table(conn, "t20_table",  TABLE_MAP["t20_table"],  expected_match_type="T20")
    print(f"✅ Loaded {totals['t20_table']:,} rows into t20_table")

    totals["ipl_table"]  = load_csv_to_table(conn, "ipl_table",  TABLE_MAP["ipl_table"])  # expected_match_type not enforced
    print(f"✅ Loaded {totals['ipl_table']:,} rows into ipl_table")

    print(f"\n📦 Total rows loaded across all tables: {sum(totals.values()):,}")

    # Create indexes for each table
    for table in TABLE_MAP.keys():
        for stmt in INDEXES:
            cur.execute(stmt.format(t=table))
    conn.commit()

    # Analyze for better query planning
    cur.execute("ANALYZE;")
    conn.commit()

    # ---------- SANITY TESTS ----------
    run_sanity_tests(conn)

    conn.close()
    print(f"\n🎯 SQLite DB ready (separate tables): {DB_PATH}")

if __name__ == "__main__":
    main()
