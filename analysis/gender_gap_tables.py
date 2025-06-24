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
    import pycountry  # for ISO‑3 → ISO‑2 mapping
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

SEX_MAP = {
    "GENDER_MALE":   "male",
    "GENDER_FEMALE": "female"
}

# ────────────────────────── helpers ──────────────────────────────

def iso3_to_iso2(code: str | float) -> str | None:
    """Convert ISO‑3 to ISO‑2; returns **None** if not found."""
    if not isinstance(code, str) or len(code) != 3:
        return None
    if pycountry is None:
        return None
    try:
        return pycountry.countries.get(alpha_3=code.upper()).alpha_2
    except (AttributeError, KeyError):
        return None


def tidy_population(pop_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape population buckets to (country_code, bucket, pop_male, pop_female)."""
    # The file uses ISO‑3 codes in column `country_code` – keep a copy
    pop_df = pop_df.rename(columns={"country_code": "country_code_alpha3"})
    pop_df["country_code"] = pop_df["country_code_alpha3"].apply(iso3_to_iso2)
    pop_df = pop_df.dropna(subset=["country_code"])  # drop aggregates & unknowns

    # long → tidy
    pop_long = (
        pop_df.set_index(["country_code", "country_name"])
               .stack()
               .reset_index()
               .rename(columns={"level_2": "bucket_raw", 0: "pop"})
    )
    pop_long[["sex", "bucket"]] = pop_long["bucket_raw"].str.split("_", n=1, expand=True)

    pop_tidy = (
        pop_long.pivot_table(index=["country_code", "bucket"],
                             columns="sex", values="pop", aggfunc="first")
                .reset_index()
                .rename(columns={"male": "pop_male", "female": "pop_female"})
    )
    return pop_tidy


def tidy_tiktok(aud_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape TikTok export to (country_code, bucket, tiktok_male, tiktok_female)."""
    # Ensure est_users exists
    if "est_users" not in aud_df.columns:
        if {"lower_end", "upper_end"}.issubset(aud_df.columns):
            aud_df["est_users"] = (aud_df["lower_end"] + aud_df["upper_end"]) / 2
        else:
            sys.exit("❌ TikTok file must contain est_users or lower_end & upper_end")

    # Normalise sex
    if "sex" not in aud_df.columns:
        if "genders" not in aud_df.columns:
            sys.exit("❌ TikTok file lacks genders column")
        aud_df["sex"] = aud_df["genders"].map(SEX_MAP)

    # Required cols
    need = ["country_code", "ages_ranges", "sex", "est_users"]
    missing = [c for c in need if c not in aud_df.columns]
    if missing:
        sys.exit(f"❌ Missing columns in TikTok file: {missing}")

    # Map buckets
    aud_df["bucket"] = aud_df["ages_ranges"].map(AGE2BKT)
    bad = aud_df.loc[aud_df["bucket"].isna(), "ages_ranges"].unique()
    if len(bad):
        sys.exit(f"❌ Unknown age ranges in TikTok file: {bad}")

    # Aggregate
    tidy = (
        aud_df.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
              .sum()
              .pivot(index=["country_code", "bucket"],
                     columns="sex", values="est_users")
              .fillna(0)
              .reset_index()
              .rename(columns={"male": "tiktok_male", "female": "tiktok_female"})
    )
    return tidy


def pct_gap(male: pd.Series, female: pd.Series):
    gap_abs = male - female
    denom   = male + female
    gap_pct = np.where(denom > 0, 100 * gap_abs / denom, 0)
    return gap_abs, gap_pct

# ────────────────────────── main ─────────────────────────────────

def main(args):
    aud_path = Path(args.audience)
    pop_path = Path(args.population)
    out_dir  = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load and tidy population
    pop_df = pd.read_csv(pop_path)
    pop_tidy = tidy_population(pop_df)
    if pop_tidy.empty:
        sys.exit("❌ Population tidy dataframe is empty – check ISO conversion")

    # 2) Load and tidy TikTok audience
    aud_df = pd.read_csv(aud_path)
    aud_tidy = tidy_tiktok(aud_df)

    # 3) Merge on (country_code, bucket)
    merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")
    if merged.empty:
        sys.exit("❌ Merge produced zero rows – country codes or buckets do not match")

    # 4) Penetration & gaps per country‑bucket
    merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
    merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
    merged["gap_abs"], merged["gap_pct"] = pct_gap(merged["pen_male"], merged["pen_female"])
    for col in ["pen_male", "pen_female", "gap_abs", "gap_pct"]:
        merged[col] = merged[col].round(4)
    merged.to_csv(out_dir / "penetration_by_country.csv", index=False)

    # 5) World totals by bucket
    world = (
        merged.groupby("bucket")[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]]
              .sum()
    )
    world["pen_male"]   = world["tiktok_male"]   / world["pop_male"]
    world["pen_female"] = world["tiktok_female"] / world["pop_female"]
    world["gap_abs"], world["gap_pct"] = pct_gap(world["pen_male"], world["pen_female"])
    world[["pen_male", "pen_female", "gap_abs", "gap_pct"]] = \
        world[["pen_male", "pen_female", "gap_abs", "gap_pct"]].round(4)
    world.to_csv(out_dir / "penetration_by_bucket.csv")

    # 6) Overall & by‑country (legacy)
    overall = merged[["tiktok_male", "tiktok_female"]].sum().to_frame().T
    overall = overall.rename(columns={"tiktok_male": "total_male", "tiktok_female": "total_female"})
    overall["gap_abs"], overall["gap_pct"] = pct_gap(overall["total_male"], overall["total_female"])
    overall[["gap_abs", "gap_pct"]] = overall[["gap_abs", "gap_pct"]].round(4)
    overall.to_csv(out_dir / "overall_gap.csv", index=False)

    by_cty = (
        merged.groupby("country_code")[["tiktok_male", "tiktok_female"]]
              .sum()
              .reset_index()
              .rename(columns={"tiktok_male": "total_male", "tiktok_female": "total_female"})
    )
    by_cty["gap_abs"], by_cty["gap_pct"] = pct_gap(by_cty["total_male"], by_cty["total_female"])
    by_cty[["gap_abs", "gap_pct"]] = by_cty[["gap_abs", "gap_pct"]].round(4)
    by_cty.to_csv(out_dir / "gap_by_country.csv", index=False)

    print("✓ penetration_by_country.csv")
    print("✓ penetration_by_bucket.csv")
    print("✓ overall_gap.csv & gap_by_country.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute TikTok gender‑gap tables")
    parser.add_argument("-a", "--audience", default="country_output_with_regions.csv",
                        help="TikTok audience CSV (ISO‑2 country codes)")
    parser.add_argument("-p", "--population", default="reference/pop_by_country_buckets_stripped.csv",
                        help="Population buckets CSV (ISO‑3 country codes)")
    parser.add_argument("-o", "--output", default="outputs",
                        help="Output directory")
    args = parser.parse_args()
    main(args)
