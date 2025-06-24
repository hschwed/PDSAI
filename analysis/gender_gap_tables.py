# uses [reference/countries.csv] & [outputs/country_output.csv]
# computes penetration rates & gender gaps for the filtered set

# Inputs:
#   outputs/country_output.csv                  (filtered TikTok export)
#   reference/countries.csv                     (region_id → ISO-3 + name)
#   reference/pop_by_country_buckets_stripped.csv
# Outputs:
#   outputs/penetration_by_country.csv
#   outputs/penetration_by_bucket.csv
#   outputs/overall_gap.csv
#   outputs/gap_by_country.csv
from __future__ import annotations

from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import sys

try:
    import pycountry  # ISO‑3 → ISO‑2
except ImportError:
    pycountry = None
    print("⚠️  pycountry not available – country matching may fail", file=sys.stderr)

# ────────────────────────── constants ────────────────────────────
AGE2BKT = {
    "AGE_13_17":  "1014",
    "AGE_18_24":  "2024",
    "AGE_25_34":  "2534",
    "AGE_35_44":  "3544",
    "AGE_45_54":  "4554",
    "AGE_55_100": "55plus",
}
SEX_MAP = {"GENDER_MALE": "male", "GENDER_FEMALE": "female"}
NUMERIC_OPTS = {"errors": "coerce"}  # for pd.to_numeric

# ────────────────────────── helpers ──────────────────────────────

def iso3_to_iso2(code):
    if not isinstance(code, str) or len(code) != 3 or pycountry is None:
        return None
    try:
        return pycountry.countries.get(alpha_3=code.upper()).alpha_2
    except Exception:
        return None


def tidy_population(pop_df: pd.DataFrame) -> pd.DataFrame:
    """Return DF: country_code (ISO‑2), bucket, pop_male, pop_female."""
    pop_df = pop_df.rename(columns={"country_code": "country_code_alpha3"})
    pop_df["country_code"] = pop_df["country_code_alpha3"].apply(iso3_to_iso2)
    pop_df = pop_df.dropna(subset=["country_code"])

    long = (pop_df.set_index(["country_code", "country_name"]).stack().reset_index()
                  .rename(columns={"level_2": "bucket_raw", 0: "pop"}))
    long[["sex", "bucket"]] = long["bucket_raw"].str.split("_", n=1, expand=True)

    tidy = (long.pivot_table(index=["country_code", "bucket"], columns="sex", values="pop", aggfunc="first")
                .reset_index()
                .rename(columns={"male": "pop_male", "female": "pop_female"}))

    tidy["pop_male"]   = pd.to_numeric(tidy["pop_male"],   **NUMERIC_OPTS)
    tidy["pop_female"] = pd.to_numeric(tidy["pop_female"], **NUMERIC_OPTS)
    return tidy


def tidy_tiktok(aud_df: pd.DataFrame) -> pd.DataFrame:
    """Return DF: country_code (ISO‑2), bucket, tiktok_male, tiktok_female."""
    if "est_users" not in aud_df.columns:
        if {"lower_end", "upper_end"}.issubset(aud_df.columns):
            aud_df["est_users"] = (aud_df["lower_end"] + aud_df["upper_end"]) / 2
        else:
            sys.exit("❌ TikTok file must contain est_users or lower_end & upper_end")

    if "sex" not in aud_df.columns:
        if "genders" not in aud_df.columns:
            sys.exit("❌ TikTok file lacks genders column")
        aud_df["sex"] = aud_df["genders"].map(SEX_MAP)

    missing = [c for c in ["country_code", "ages_ranges", "sex", "est_users"] if c not in aud_df.columns]
    if missing:
        sys.exit(f"❌ Missing columns in TikTok file: {missing}")

    aud_df["bucket"] = aud_df["ages_ranges"].map(AGE2BKT)
    if aud_df["bucket"].isna().any():
        bad = aud_df.loc[aud_df["bucket"].isna(), "ages_ranges"].unique()
        sys.exit(f"❌ Unknown age ranges in TikTok file: {bad}")

    tidy = (aud_df.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"].sum()
                    .pivot(index=["country_code", "bucket"], columns="sex", values="est_users").fillna(0)
                    .reset_index()
                    .rename(columns={"male": "tiktok_male", "female": "tiktok_female"}))

    tidy["tiktok_male"]   = pd.to_numeric(tidy["tiktok_male"],   **NUMERIC_OPTS)
    tidy["tiktok_female"] = pd.to_numeric(tidy["tiktok_female"], **NUMERIC_OPTS)
    return tidy


def pct_gap(male, female):
    gap_abs = male - female
    denom   = male + female
    gap_pct = np.where(denom > 0, 100 * gap_abs / denom, np.nan)
    return gap_abs, gap_pct

# ────────────────────────── main ─────────────────────────────────

def main(args):
    aud_path, pop_path, out_dir = Path(args.audience), Path(args.population), Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    pop_tidy = tidy_population(pd.read_csv(pop_path))
    if pop_tidy.empty:
        sys.exit("❌ Population tidy dataframe is empty – check ISO conversion")

    aud_tidy = tidy_tiktok(pd.read_csv(aud_path))

    merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")
    if merged.empty:
        sys.exit("❌ Merge produced zero rows – country codes or buckets do not match")

    # ensure numeric (sometimes division on object gives object)
    num_cols = ["tiktok_male", "tiktok_female", "pop_male", "pop_female"]
    merged[num_cols] = merged[num_cols].apply(pd.to_numeric, **NUMERIC_OPTS)

    # Penetration & gaps
    merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"].replace({0: np.nan})
    merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"].replace({0: np.nan})
    merged["gap_abs"], merged["gap_pct"] = pct_gap(merged["pen_male"], merged["pen_female"])

    for col in ["pen_male", "pen_female", "gap_abs", "gap_pct"]:
        merged[col] = merged[col].round(4)

    merged.to_csv(out_dir / "penetration_by_country.csv", index=False)

    # World totals by bucket
    world = (merged.groupby("bucket")[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]].sum())
    world["pen_male"]   = world["tiktok_male"]   / world["pop_male"].replace({0: np.nan})
    world["pen_female"] = world["tiktok_female"] / world["pop_female"].replace({0: np.nan})
    world["gap_abs"], world["gap_pct"] = pct_gap(world["pen_male"], world["pen_female"])
    world[["pen_male", "pen_female", "gap_abs", "gap_pct"]] = world[["pen_male", "pen_female", "gap_abs", "gap_pct"]].round(4)
    world.to_csv(out_dir / "penetration_by_bucket.csv", index=False)

    # Overall & country totals
    overall = merged[["tiktok_male", "tiktok_female"]].sum().to_frame().T
    overall.columns = ["total_male", "total_female"]
    overall["gap_abs"], overall["gap_pct"] = pct_gap(overall["total_male"], overall["total_female"])
    overall[["gap_abs", "gap_pct"]] = overall[["gap_abs", "gap_pct"]].round(4)
    overall.to_csv(out_dir / "overall_gap.csv", index=False)

    by_cty = (merged.groupby("country_code")[["tiktok_male", "tiktok_female"]].sum().reset_index())
    by_cty = by_cty.rename(columns={"tiktok_male": "total_male", "tiktok_female": "total_female"})
    by_cty["gap_abs"], by_cty["gap_pct"] = pct_gap(by_cty["total_male"], by_cty["total_female"])
    by_cty[["gap_abs", "gap_pct"]] = by_cty[["gap_abs", "gap_pct"]].round(4)
    by_cty.to_csv(out_dir / "gap_by_country.csv", index=False)

    print("✓ penetration_by_country.csv")
    print("✓ penetration_by_bucket.csv")
    print("✓ overall_gap.csv & gap_by_country.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compute TikTok gender‑gap tables")
    p.add_argument("-a", "--audience", default="country_output_with_regions.csv")
    p.add_argument("-p", "--population", default="reference/pop_by_country_buckets_stripped.csv")
    p.add_argument("-o", "--output", default="outputs")
    main(p.parse_args())
