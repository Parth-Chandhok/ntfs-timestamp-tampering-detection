# build_features_movetrick.py
# Runs the detector on the MOVE-TRICK test set (both $SI and $FN faked).
#
# EXPECTED RESULT (the whole point of this experiment):
#   si_fn_mismatch            -> fires on ~0 files   (the single-artefact rule is DEFEATED)
#   usn_basicinfo_after_close -> still fires         (journal recorded the tampering)
#   usn_claim_conflict        -> still fires         (file claims to predate its journal history)
#
# i.e. the approach used by prior work goes blind, but the correlated framework
# still catches the tampering via the USN Journal.

import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\ntfs-tamper-detect")
mft_path      = ROOT / "data" / "raw" / "mft_movetrick.csv"
usn_path      = ROOT / "data" / "raw" / "usn_movetrick.csv"     # FRESH extraction!
manifest_path = ROOT / "datagen" / "tamper_lab" / "movetrick_manifest.csv"
out_path      = ROOT / "data" / "processed" / "features_movetrick.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

FOLDER_TAG = "movetrick"          # isolates this experiment's files

# ------------------------------------------------------------------
# 1. MFT  ->  the $SI/$FN signal
# ------------------------------------------------------------------
mft = pd.read_csv(mft_path, low_memory=False)
mft = mft[mft["ParentPath"].astype(str)
          .str.contains("movetrick_staging", case=False, na=False)].copy()

si = pd.to_datetime(mft["Created0x10"], errors="coerce")   # $SI
fn = pd.to_datetime(mft["Created0x30"], errors="coerce")   # $FN
fn = fn.fillna(si)          # blank $FN means it equals $SI (the move-trick made them agree)

mft["si_created"]      = si
mft["delta_created_s"] = (si - fn).dt.total_seconds().abs()
mft["si_fn_mismatch"]  = (mft["delta_created_s"] > 1.0).astype(int)

mft_small = mft[["FileName", "si_created", "delta_created_s", "si_fn_mismatch"]]

# ------------------------------------------------------------------
# 2. USN Journal  ->  what actually happened (fresh extraction)
# ------------------------------------------------------------------
usn = pd.read_csv(usn_path, low_memory=False)
usn["UpdateTimestamp"] = pd.to_datetime(usn["UpdateTimestamp"], errors="coerce")
usn["reasons"] = usn["UpdateReasons"].astype(str)

# ParentPath is blank in this USN export, so match our corpus files by name
usn = usn[usn["Name"].astype(str).str.contains("-tiny_", na=False)].copy()

rows = []
for name, g in usn.groupby("Name"):
    g = g.sort_values("UpdateTimestamp")
    first_seen = g["UpdateTimestamp"].min()

    creation_close = g[g["reasons"].str.contains("FileCreate", na=False)
                       & g["reasons"].str.contains("Close", na=False)]
    close_time = creation_close["UpdateTimestamp"].min() if len(creation_close) else pd.NaT

    if pd.notna(close_time):
        later = g[(g["UpdateTimestamp"] > close_time)
                  & (g["reasons"].str.contains("BasicInfoChange", na=False))]
        n_later = len(later)
    else:
        n_later = 0

    rows.append({
        "FileName": name,
        "usn_first_seen": first_seen,
        "usn_records": len(g),
        "usn_basicinfo_after_close_n": n_later,
        "usn_basicinfo_after_close": int(n_later > 0),
    })

usn_feat = pd.DataFrame(rows)

# ------------------------------------------------------------------
# 3. Correlate + join to manifest
# ------------------------------------------------------------------
manifest = pd.read_csv(manifest_path)          # all rows tampered=1 here

df = (manifest
      .merge(mft_small, on="FileName", how="left")
      .merge(usn_feat,  on="FileName", how="left"))

TOL_S = 60
claim_gap = (df["usn_first_seen"] - df["si_created"]).dt.total_seconds()
df["usn_claim_gap_s"]    = claim_gap
df["usn_claim_conflict"] = (claim_gap > TOL_S).fillna(False).astype(int)

df["si_fn_mismatch"]            = df["si_fn_mismatch"].fillna(0).astype(int)
df["usn_basicinfo_after_close"] = df["usn_basicinfo_after_close"].fillna(0).astype(int)

df["signals_fired"] = (df["si_fn_mismatch"]
                       + df["usn_basicinfo_after_close"]
                       + df["usn_claim_conflict"])

df.to_csv(out_path, index=False)

# ------------------------------------------------------------------
# 4. Report
# ------------------------------------------------------------------
n = len(df)
print(f"Move-trick files : {n}")
print(f"Matched in MFT   : {df['delta_created_s'].notna().sum()}")
print(f"Matched in USN   : {df['usn_records'].notna().sum()}\n")

print("How many files each signal fired on (all files are tampered):")
for sig in ["si_fn_mismatch", "usn_basicinfo_after_close", "usn_claim_conflict"]:
    fired = int(df[sig].sum())
    print(f"  {sig:28} {fired:3}/{n}")

print("\nInterpretation:")
mm = int(df["si_fn_mismatch"].sum())
usn_any = int(((df["usn_basicinfo_after_close"] + df["usn_claim_conflict"]) > 0).sum())
print(f"  $SI/$FN mismatch rule caught : {mm}/{n}   (prior-work approach)")
print(f"  USN correlation caught       : {usn_any}/{n}   (this framework)")

print("\nSaved ->", out_path)