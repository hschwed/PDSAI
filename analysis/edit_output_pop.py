from pathlib import Path
import pandas as pd
import numpy as np
import re
import unicodedata

# ───────────────────────────── file paths ───────────────────────────
POP_FILE  = Path("reference/pop_by_country_buckets_stripped.csv")
OUT_DIR   = Path("outputs"); OUT_DIR.mkdir(exist_ok=True)
OUT       = Path("outputs/pop_clean.csv")

# -------------------------------------------------------------------
#  STEP A · read population file (absolute headcounts)
# -------------------------------------------------------------------
pop = pd.read_csv(POP_FILE)

# reshape to long form and tidy
pop_long = (
    pop.set_index(["country_code", "country_name"]).stack()
       .reset_index().rename(columns={"level_2": "tmp", 0: "pop"})
)
pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
# -------------------------------------------------------------------
# 6) wide format, columns female and male
# -------------------------------------------------------------------
pop = pop_long.pivot_table(
    index=["country_code", "bucket"],
    columns="sex",
    values="pop",
    aggfunc="first"  # or 'sum' if you may have duplicates
).reset_index()

# Rename columns
pop.columns.name = None  # remove the pivot column name
pop = pop.rename(columns={
    "male": "pop_male",
    "female": "pop_female"
})
pop = pop[pop["bucket"]!="1519"]
keep = [
    "country_code", "bucket","pop_male","pop_female"
]
pop = pop[keep]

# get rid of 1014 because TT does not have this age group
keep_buckets = ["1519", "2024", "2534", "3544", "4554", "55plus"]
pop = pop[pop["bucket"].isin(keep_buckets)]

#print(pop_long["bucket"].unique())

pop.to_csv(OUT, index=False)