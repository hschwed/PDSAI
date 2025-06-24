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


from pathlib import Path
import argparse
import pandas as pd
import numpy as np
import sys

# ────────────────────────── constants ────────────────────────────
AGE2BKT = {
    # TikTok age‑range  → WB/UN bucket suffix
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
def tidy_population(pop_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape population buckets to
    (country_code, bucket, pop_male, pop_female)"""
    # keep alpha‑3 ISO and readable name
    pop_long = (
        pop_df.set_index(["country_code", "country_name"])
               .stack()
               .reset_index()
               .rename(columns={"level_2": "tmp", 0: "pop"})
    )
    pop_long[["sex", "bucket"]] = pop_long["tmp"].str.split("_", n=1, expand=True)
    pop_tidy = (
        pop_long.pivot_table(index=["country_code", "bucket"],
                             columns="sex", values="pop", aggfunc="first")
                .reset_index()
                .rename(columns={"male": "pop_male",
                                 "female": "pop_female"})
    )
    return pop_tidy


def tidy_tiktok(aud_df: pd.DataFrame) -> pd.DataFrame:
    """Reshape TikTok export to (country_code, bucket, tiktok_male, tiktok_female)"""
    # ensure est_users exists
    if "est_users" not in aud_df.columns:
        if not {"lower_end", "upper_end"}.issubset(aud_df.columns):
            sys.exit("❌ TikTok file must contain either est_users or lower_end/upper_end")
        aud_df["est_users"] = (aud_df["lower_end"] + aud_df["upper_end"]) / 2

    # normalise sex column
    if "sex" not in aud_df.columns:
        if "genders" not in aud_df.columns:
            sys.exit("❌ TikTok file lacks genders column")
        aud_df["sex"] = aud_df["genders"].map(SEX_MAP)

    # basic sanity
    need = ["country_code", "ages_ranges", "sex", "est_users"]
    missing = [c for c in need if c not in aud_df.columns]
    if missing:
        sys.exit(f"❌ Missing columns in TikTok file: {missing}")

    # map WB buckets
    aud_df["bucket"] = aud_df["ages_ranges"].map(AGE2BKT)
    bad = aud_df.loc[aud_df["bucket"].isna(), "ages_ranges"].unique()
    if len(bad):
        sys.exit(f"❌ Unknown age ranges in TikTok file: {bad}")

    # group
    tidy = (
        aud_df.groupby(["country_code", "bucket", "sex"], as_index=False)["est_users"]
              .sum()
              .pivot(index=["country_code", "bucket"],
                     columns="sex", values="est_users")
              .fillna(0)
              .reset_index()
              .rename(columns={"male": "tiktok_male",
                               "female": "tiktok_female"})
    )
    return tidy


def pct_gap(male, female):
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

    # 1) population data
    pop_df   = pd.read_csv(pop_path)
    pop_tidy = tidy_population(pop_df)

    # 2) TikTok audience data
    aud_df   = pd.read_csv(aud_path)
    aud_tidy = tidy_tiktok(aud_df)

    # 3) merge
    merged = aud_tidy.merge(pop_tidy, on=["country_code", "bucket"], how="inner")
    if merged.empty:
        sys.exit("❌ Merge produced zero rows – check country codes and buckets")
    # penetration & gap
    merged["pen_male"]   = merged["tiktok_male"]   / merged["pop_male"]
    merged["pen_female"] = merged["tiktok_female"] / merged["pop_female"]
    merged["gap_abs"], merged["gap_pct"] = pct_gap(merged["pen_male"], merged["pen_female"])
    for c in ["pen_male", "pen_female", "gap_abs", "gap_pct"]:
        merged[c] = merged[c].round(4)

    merged.to_csv(out_dir / "penetration_by_country.csv", index=False)

    # 4) world totals by bucket
    world = (
        merged.groupby("bucket")[["tiktok_male", "tiktok_female", "pop_male", "pop_female"]]
              .sum()
              .assign(pen_male   = lambda d: d["tiktok_male"]   / d["pop_male"],
                      pen_female = lambda d: d["tiktok_female"] / d["pop_female"])
    )
    world["gap_abs"], world["gap_pct"] = pct_gap(world["pen_male"], world["pen_female"])
    world[["pen_male", "pen_female", "gap_abs", "gap_pct"]] = \
        world[["pen_male", "pen_female", "gap_abs", "gap_pct"]].round(4)
    world.to_csv(out_dir / "penetration_by_bucket.csv", index=False)

    # 5) overall totals (legacy)
    overall = (
        merged[["tiktok_male", "tiktok_female"]].sum()
        .rename({"tiktok_male": "total_male", "tiktok_female": "total_female"})
        .to_frame().T
    )
    overall["gap_abs"], overall["gap_pct"] = pct_gap(overall["total_male"], overall["total_female"])
    overall[["gap_abs", "gap_pct"]] = overall[["gap_abs", "gap_pct"]].round(4)
    overall.to_csv(out_dir / "overall_gap.csv", index=False)

    # 6) by‑country summary (legacy)
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
                        help="TikTok audience CSV (default: country_output_with_regions.csv)")
    parser.add_argument("-p", "--population", default="reference/pop_by_country_buckets_stripped.csv",
                        help="Population buckets CSV (default: reference/pop_by_country_buckets_stripped.csv)")
    parser.add_argument("-o", "--output", default="outputs",
                        help="Output directory (default: outputs/)")
    args = parser.parse_args()
    main(args)
