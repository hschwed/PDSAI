from pathlib import Path
import pandas as pd


INST_FILE = Path("data/transformed/inst_final.csv")
POP_FILE = Path("data/transformed/pop_final.csv")
TT_FILE = Path("data/transformed/tt_final.csv")
FB_FILE = Path("data/transformed/fb_final.csv")

FILE_NAMES = {INST_FILE: "inst", POP_FILE: "pop", TT_FILE: "tt", FB_FILE: "fb"}
FILES = [INST_FILE, TT_FILE, FB_FILE,POP_FILE]

for file in FILES:
    df = pd.read_csv(file,sep=";")
    name = FILE_NAMES[file]

    #check for null in data files
    print(f"{name}: {df.isnull().sum()}")
    print(f"{df[df.isnull().any(axis=1)]}\n")

    

