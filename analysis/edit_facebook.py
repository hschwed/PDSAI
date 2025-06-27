import pandas as pd
#from gender_gap_tables import iso3_to_iso2
import pycountry

IN = "./dgg_facebook_national.csv"
OUT = "outputs/fb_clean.csv"

df = pd.read_csv(IN, encoding="utf-8-sig")
df = df[df['outcome'].isin(['internet_fm_ratio'])]

df = df.rename(columns={
    "gid_0": "country_code",
    "predicted": "fb_fm"
})

keep = [
    "country_code", "fb_fm"
]
df = df[keep]

df.to_csv(OUT, index=False)

print(df.head())