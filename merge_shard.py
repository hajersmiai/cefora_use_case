import pandas as pd
from glob import glob

files = sorted(glob("data/raw/actiris_shard_*_*.csv"))  # les CSV finaux
dfs = []
for f in files:
    dfs.append(pd.read_csv(f, dtype=str))
df = pd.concat(dfs, ignore_index=True).fillna("")
df = df.drop_duplicates(subset=["reference", "title", "lieu", "url"], keep="first")

df.to_csv("data/cleaned/actiris_full.csv", index=False)
try:
    df.to_parquet("data/cleaned/actiris_full.parquet", index=False)
except Exception as e:
    print("Parquet non écrit (pyarrow manquant ?) :", e)

print("✅ Fusion OK:", df.shape, "→ data/cleaned/actiris_full.*")
