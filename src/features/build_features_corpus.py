# build_features_corpus.py - detects timestomping on the 808-file NapierOne corpus
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\ntfs-tamper-detect")
mft_path      = ROOT / "data" / "raw" / "mft_corpus.csv"
manifest_path = ROOT / "datagen" / "tamper_lab" / "manifest.csv"
out_path      = ROOT / "data" / "processed" / "features_corpus.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

# --- load ---
mft      = pd.read_csv(mft_path, low_memory=False)
manifest = pd.read_csv(manifest_path)      # FileName, tampered, tool, fake_date

# --- keep only files in the tampered folder ---
mft = mft[mft["ParentPath"].astype(str).str.contains(r"tamper_lab\\tampered", case=False, na=False, regex=True)].copy()

# --- parse the two creation timestamps ---
si = pd.to_datetime(mft["Created0x10"], errors="coerce")   # $SI  (fakeable)
fn = pd.to_datetime(mft["Created0x30"], errors="coerce")   # $FN  (kernel)
fn = fn.fillna(si)          # blank $FN means it equals $SI -> no mismatch

# --- features ---
mft["delta_created_s"] = (si - fn).dt.total_seconds().abs()
mft["si_fn_mismatch"]  = (mft["delta_created_s"] > 1.0).astype(int)

# --- join evidence to answer key ---
df = manifest.merge(
    mft[["FileName", "delta_created_s", "si_fn_mismatch"]],
    on="FileName", how="left"
)

df.to_csv(out_path, index=False)

print(f"Files in manifest : {len(manifest)}")
print(f"Matched in MFT    : {df['si_fn_mismatch'].notna().sum()}")
print("\nDetector vs truth:")
print(pd.crosstab(df["tampered"], df["si_fn_mismatch"],
                  rownames=["actual"], colnames=["flagged"]))
print("\nSaved ->", out_path)