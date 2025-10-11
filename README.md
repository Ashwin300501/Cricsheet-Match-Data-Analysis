# Cricsheet Match Data Analysis
End-to-end cricket analytics project using Cricsheet data: automated scraping, JSON parsing → tidy CSVs, a SQLite database, SQL analysis, pandas + seaborn EDA, and a Power BI dashboard.

---

## 📂 Project Structure
```plaintext
.
├─ cricsheet_data/
│  ├─ Test/   ODI/   T20/   IPL/        # raw JSONs extracted by scraper
│  └─ processed/
│      ├─ test.csv  ODI.csv  T20.csv  IPL.csv
│      └─ (optional) all_matches.csv, match_level.csv
├─ Data_Scraping.ipynb
├─ create_DB.py
├─ queries.ipynb
├─ visualization.ipynb
├─ CricSheet_PowerBI-Dashboard.pbix      # (not included)
└─ README.md
```

**Unified schema (columns across CSVs/DB):**

`[batter, bowler, city, match_date, match_format, match_id, match_type, non_stricker, over, player_of_match, runs_batter, runs_extra, runs_total, season, team, toss_decision, toss_winner, venue, wicket, winner]`

## ⚙️ Environment
- Python 3.9+ (tested with 3.10/3.11/3.12)
- Jupyter / Python
- Packages: `requests`, `pandas`, `matplotlib`, `seaborn`, `sqlite3` (stdlib), `zipfile` (stdlib)

---

## 🚀 How to Run
### 1. Scrape & Parse → CSVs
- Open `Data_Scraping.ipynb` and run all cells:
- Downloads:
    - Tests: `tests_json.zip`
    - ODIs: `odis_json.zip`
    - T20s: `t20s_json.zip`
    - IPL: `ipl_json.zip`
- Extracts JSONs into cricsheet_data/<FORMAT>/
- Parses to CSVs at cricsheet_data/processed/{test,ODI,T20,IPL}.csv
- Includes stable match_id (from filename) and match_date (first value in info.dates)

- Output(Examples):
```bash
cricsheet_data/processed/test.csv
cricsheet_data/processed/ODI.csv
cricsheet_data/processed/T20.csv
cricsheet_data/processed/IPL.csv
```

### 2. Build SQLite DB
Run:
```bash
python create_DB.py
```
What it does:
- Creates cricsheet_match_data.db outside the cricsheet_data/ folder

- Creates four tables (fresh each run):
    - test_table
    - odi_table
    - t20_table
    - ipl_table
- Loads each CSV (append mode per run), builds useful indexes, runs quick sanity checks (row counts, null checks, negative values, venue distribution).

### 3. SQL Analysis (Notebook)

- Open `queries.ipynb`:
    - Connect to `cricsheet_match_data.db`
-Run the queries

### 4. Visualization (Notebook)

- Open `visualization.ipynb`:
- Load CSVs:
```python
import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
BASE = "cricsheet_data/processed"
test_df = pd.read_csv(f"{BASE}/test.csv", low_memory=False)
odi_df  = pd.read_csv(f"{BASE}/ODI.csv" , low_memory=False)
t20_df  = pd.read_csv(f"{BASE}/T20.csv" , low_memory=False)
ipl_df  = pd.read_csv(f"{BASE}/IPL.csv" , low_memory=False)
```
- Run visualization code snippets

### 5. PowerBI Dashboard (PBIX)

**Data source:**
- **Folder connector** Pointed at `cricsheet_data/processed/`
- Use `Source.Name` to derive `Match Type` in Power Query:
    - e.g., if file name contains “ODI”, set match_format = "ODI"

**Modeling:**
- Append all four CSVs into one table (Power Query → Append Queries as New)
- Keep `season` as Text and create `Season Year = Text.BeforeDelimiter([season], ",")` for sorting
- Visuals:
    - **Page 1(Overview)**:KPIs, matches by format, runs trend, toss decisions, city map
    - **Page 2(Team & Match Insights)**:wins by team, toss outcomes by team, top venues, matches per season, format×winner matrix
    - **Page 3(Player Performance)**:top batters/bowlers, frequent PoM, scoring rate by season, wickets by season

### 🔍 Troubleshooting
- Mixed season values (“2012” vs “2012/13”):keep `season` as Text; use a derived numeric `Season Year` for sorting.
- Large loads: set `pandas.read_csv(..., low_memory=False)` and `to_sql(..., chunksize=50_000) `(already in code).
-IPL `match_type`: often tagged as “T20” in Cricsheet — expected. Sanity prints include distribution.

### ✅ Summary
1. Run `Data_Scraping.ipynb` → produce CSVs
2. Run `create_DB.py` → build SQLite with 4 tables + indexes + sanity checks
3. Explore with `queries.ipynb` (SQL)
4. Visualize with `visualization.ipynb` (pandas + seaborn)
5. Build/refresh Power BI dashboard from the `processed/` folder


