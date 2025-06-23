# Just used for finding an error


# find error that makes it unable to match columns



# analysis/diagnose_gender_pipeline.py
# -------------------------------------------------------------------
# A self-contained debugger for the TikTok-vs-population pipeline.
#
# It reproduces each stage from gender_gap_tables.py but never crashes.
# Instead it captures exceptions, prints row/column counts, and
# appends every warning to outputs/pipeline_diagnostics.txt
#
# Run from repo root:
#     python analysis/diagnose_gender_pipeline.py
# -------------------------------------------------------------------
from pathlib import Path
import pandas as pd
import re
import traceback
from datetime import datetime

# ---------- paths ---------------------------------------------------
OUT_DIR   = Path("outputs");  OUT_DIR.mkdir(exist_ok=True)
LOG_FILE  = OUT_DIR / "pipeline_diagnostics.txt"
TT_FILE   = Path("outputs/tt_clean.csv")
POP_FILE  = Path("reference/pop_by_country_buckets_stripped.csv")

# ---------- helper --------------------------------------------------
def log(msg: str) -> None:
    print(msg)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")

def section(title: str) -> None:
    log("\n" + "-"*60)
    log(title)

# fresh log
LOG_FILE.write_text(f"Pipeline diagnostics run {datetime.utcnow()} UTC\n")

# ---------- 1 · load files ------------------------------------------
section("1) LOAD FILES")

try:
    pop = pd.read_csv(POP_FILE)
    log(f"✓ population file read   → {pop.shape[0]:,} rows , {pop.shape[1]} cols")
except Exception:
    log("✗ failed to read population file")
    log(traceback.format_exc())
    raise SystemExit

try:
    aud = pd.read_csv(TT_FILE)
    log(f"✓ TikTok file read        → {aud.shape[0]:,} rows , {aud.shape[1]} cols")
except Exception:
    log("✗ failed to read tt_clean.csv")
    log(traceback.format_exc())
    raise SystemExit

# ---------- 2 · normalise names, map ISO ----------------------------
section("2) MAP ISO CODES FROM COUNTRY NAMES")

normalize = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
name2iso = {normalize(n): c for n,c in
            zip(pop["country_name"], pop["country_code"])}

if aud["country_code"].notna().any():
    log(f"→ TikTok already has country_code for {aud['country_code'].notna().sum():,} rows")
else:
    aud["country_code"] = aud["country_name"].map(lambda x: name2iso.get(normalize(x)))
    missing = aud["country_code"].isna().sum()
    log(f"→ mapped ISO-3 from names ; unmapped rows = {missing:,}")

# ---------- 3 · map age buckets ------------------------------------
section("3) MAP AGE BUCKETS")

RANGE_MAP = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}

aud["bucket"] = aud["age_bucket"].map(RANGE_MAP)
bad_buckets = aud[aud["bucket"].isna()]["age_bucket"].unique()
if len(bad_buckets):
    log(f"⚠ unmapped TikTok age_bucket values: {bad_buckets[:8]}{' …' if len(bad_buckets)>8 else ''}")
else:
    log("✓ all age_bucket labels mapped")

# ---------- 4 · melt population into tidy form ---------------------
section("4) POPULATION → LONG FORMAT")

try:
    pop_long = (pop
        .set_index(["country_code","country_name"])
        .stack()
        .reset_index()
        .rename(columns={"level_2":"tmp",0:"pop"}))
    pop_long[["sex","bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
    pop_tidy = (pop_long
        .pivot_table(index=["country_code","bucket"], columns="sex", values="pop")
        .reset_index()
        .rename(columns={"male":"pop_male","female":"pop_female"}))
    log(f"✓ pop_tidy shape : {pop_tidy.shape}")
except Exception:
    log("✗ failed while reshaping population data")
    log(traceback.format_exc())

# ---------- 5 · TikTok group+pivot ---------------------------------
section("5) TIKTOK → GROUP + PIVOT")

try:
    if "est_users" not in aud.columns:
        aud["est_users"] = (aud["lower_end"]+aud["upper_end"])/2
    tt_pivot = (aud
        .dropna(subset=["country_code","bucket"])
        .groupby(["country_code","bucket","sex"],as_index=False)["est_users"]
        .sum()
        .pivot(index=["country_code","bucket"], columns="sex", values="est_users")
        .fillna(0)
        .reset_index())
    tt_pivot = tt_pivot.rename(columns=lambda c: f"tiktok_{c.lower()}" if c in ("male","female") else c)
    log(f"✓ tt_pivot shape : {tt_pivot.shape}")
    log(f"  tt_pivot columns: {list(tt_pivot.columns)}")
except Exception:
    log("✗ failed while pivoting TikTok data")
    log(traceback.format_exc())

# ---------- 6 · merge preview --------------------------------------
section("6) MERGE PREVIEW")

try:
    merged = tt_pivot.merge(pop_tidy,on=["country_code","bucket"],how="inner")
    log(f"✓ after merge : {merged.shape[0]:,} rows")
    if merged.empty:
        log("⚠ merged result is empty → check ISO codes & bucket labels")
    else:
        log("sample rows:\n"+merged.head().to_string(index=False))
except Exception:
    log("✗ merge step failed")
    log(traceback.format_exc())

log("\nDiagnostics complete – see outputs/pipeline_diagnostics.txt")

