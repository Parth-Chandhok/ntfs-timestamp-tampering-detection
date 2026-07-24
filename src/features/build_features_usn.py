# build_features_usn.py
# Adds two USN Journal signals to the timestomping feature set.
#
# WHY: the $SI/$FN mismatch only sees what a file CLAIMS about itself.
# The USN Journal is Windows' own diary of what ACTUALLY happened.
# Comparing the two gives independent corroboration - and still works
# against tools like SetMACE that fake both $MFT timestamps.
#
# Signals produced:
#   si_fn_mismatch            (existing) $SI vs $FN disagree
#   usn_basicinfo_after_close (new)      timestamps changed AFTER file creation finished
#   usn_claim_conflict        (new)      file claims to predate its own first journal entry
#   signals_fired             (new)      how many of the three fired (0-3)

import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\ntfs-tamper-detect")
mft_path      = ROOT / "data" / "raw" / "mft_corpus.csv"
usn_path      = ROOT / "data" / "raw" / "usn_corpus.csv"
manifest_path = ROOT / "datagen" / "tamper_lab" / "manifest.csv"
out_path      = ROOT / "data" / "processed" / "features_usn.csv"
out_path.parent.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------
# 1. MFT  ->  the $SI/$FN signal (what the file claims about itself)
# ------------------------------------------------------------------
mft = pd.read_csv(mft_path, low_memory=False)
mft = mft[mft["ParentPath"].astype(str)
          .str.contains(r"tamper_lab\\tampered", case=False, na=False, regex=True)].copy()

si = pd.to_datetime(mft["Created0x10"], errors="coerce")   # $SI  - fakeable
fn = pd.to_datetime(mft["Created0x30"], errors="coerce")   # $FN  - kernel-managed
fn = fn.fillna(si)          # MFTECmd leaves $FN blank when it equals $SI

mft["si_created"]      = si
mft["delta_created_s"] = (si - fn).dt.total_seconds().abs()
mft["si_fn_mismatch"]  = (mft["delta_created_s"] > 1.0).astype(int)

mft_small = mft[["FileName", "si_created", "delta_created_s", "si_fn_mismatch"]]

# ------------------------------------------------------------------
# 2. USN Journal  ->  what the system actually observed happening
# ----------------------------------------------------------------
usn = pd.read_csv(usn_path, low_memory=False)
usn["UpdateTimestamp"] = pd.to_datetime(usn["UpdateTimestamp"], errors="coerce")
usn["reasons"] = usn["UpdateReasons"].astype(str)

# only records about our corpus files
usn = usn[usn["Name"].astype(str).str.contains("-tiny_", na=False)].copy()

rows = []
for name, g in usn.groupby("Name"):
    g = g.sort_values("UpdateTimestamp")

    first_seen = g["UpdateTimestamp"].min()

    # when did the creation sequence finish? (first record containing FileCreate + Close)
    creation_close = g[g["reasons"].str.contains("FileCreate", na=False)
                       & g["reasons"].str.contains("Close", na=False)]
    close_time = creation_close["UpdateTimestamp"].min() if len(creation_close) else pd.NaT

    # SIGNAL: BasicInfoChange records occurring AFTER the creation sequence closed
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

# ---------------------------------------------------------------
# 3. Correlate: does the file claim to predate its own journal history?
#    (this is the signal that still works when BOTH $MFT timestamps are faked)
# ------------------------------------------------------------------
manifest = pd.read_csv(manifest_path)          # FileName, tampered, tool, fake_date

df = (manifest
      .merge(mft_small, on="FileName", how="left")
      .merge(usn_feat,  on="FileName", how="left"))

TOL_S = 60      # allow a minute of slack for normal copy/write ordering
claim_gap = (df["usn_first_seen"] - df["si_created"]).dt.total_seconds()
df["usn_claim_gap_s"]    = claim_gap
df["usn_claim_conflict"] = (claim_gap > TOL_S).fillna(False).astype(int)

df["usn_basicinfo_after_close"] = df["usn_basicinfo_after_close"].fillna(0).astype(int)

# how many independent signals fired for each file
df["signals_fired"] = (df["si_fn_mismatch"].fillna(0)
                       + df["usn_basicinfo_after_close"]
                       + df["usn_claim_conflict"])

df.to_csv(out_path, index=False)

# ------------------------------------------------------------------
# 4. Report
# ------------------------------------------------------------------
print(f"Files in manifest : {len(manifest)}")
print(f"Matched in MFT    : {df['si_fn_mismatch'].notna().sum()}")
print(f"Matched in USN    : {df['usn_records'].notna().sum()}\n")

for sig in ["si_fn_mismatch", "usn_basicinfo_after_close", "usn_claim_conflict"]:
    print(f"--- {sig} ---")
    print(pd.crosstab(df["tampered"], df[sig],
                      rownames=["actual"], colnames=["flagged"]))
    print()

print("--- how many signals fired per file ---")
print(pd.crosstab(df["tampered"], df["signals_fired"],
                  rownames=["actual"], colnames=["signals"]))

print("\nSaved ->", out_path)