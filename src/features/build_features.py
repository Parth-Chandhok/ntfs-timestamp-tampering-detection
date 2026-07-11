# build_features.py - turns MFT timestamps into numeric features for the model
import pandas as pd
import re
from pathlib import Path

ROOT = Path(r"C:\ntfs-tamper-detect")
mft_path    = ROOT / "data" / "raw" / "mft_raw.csv"
labels_path = ROOT / "data" / "labels" / "labels_v1.csv"
out_path    = ROOT / "data" / "processed" / "features_v1.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

# --- load ---
mft    = pd.read_csv(mft_path, low_memory=False)
labels = pd.read_csv(labels_path)   # FileName, ParentPath, tampered

# --- keep only my test files: file_01.txt ... file_20.txt ---
pattern = re.compile(r"^file_\d{2}\.txt$")
mft = mft[mft["FileName"].astype(str).str.match(pattern)].copy()

# --- parse the two creation timestamps ---
si = pd.to_datetime(mft["Created0x10"], errors="coerce")  # $SI (fakeable)
fn = pd.to_datetime(mft["Created0x30"], errors="coerce")  # $FN (kernel)

# blank $FN means it equals $SI -> no mismatch. Fill it with $SI.
fn = fn.fillna(si)

# --- features ---
mft["delta_created_s"] = (si - fn).dt.total_seconds().abs()
mft["si_fn_mismatch"]  = (mft["delta_created_s"] > 1.0).astype(int)  # 1s tolerance

# --- join to labels (answer key) ---
df = labels.merge(
    mft[["FileName", "delta_created_s", "si_fn_mismatch"]],
    on="FileName", how="left"
)

# --- save ---
df.to_csv(out_path, index=False)

print(df[["FileName", "tampered", "delta_created_s", "si_fn_mismatch"]].to_string(index=False))
print("\nSaved ->", out_path)
print("\nSanity check (does my flag match the truth?):")
print(pd.crosstab(df["tampered"], df["si_fn_mismatch"],
                  rownames=["actual"], colnames=["flagged"]))