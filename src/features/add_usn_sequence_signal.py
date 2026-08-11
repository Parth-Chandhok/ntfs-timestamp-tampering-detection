"""
add_usn_sequence_signal.py — adds the clock-independent USN sequence signal
to all three experiments' feature files.

WHY THIS SIGNAL EXISTS
  Every USN journal record carries an UpdateSequenceNumber: a byte offset into
  the journal that only ever increases. It is assigned by the filesystem and is
  completely independent of the system clock — rolling the clock back cannot
  rewind it.

  Because the journal is append-only, its timestamps should never decrease as
  sequence numbers increase. The RUNNING MAXIMUM timestamp at any sequence
  position is therefore a floor: no record at a higher sequence position can
  legitimately claim to predate it.

WHY NOT A LOCAL NEIGHBOURHOOD MEDIAN
  A previous version compared each file against the median timestamp of nearby
  journal records. That fails against clock rollback: the journal records for
  files created under a rolled-back clock are THEMSELVES stamped with the fake
  time, so a tampered file's neighbours are other tampered files and the
  comparison becomes self-referential. The running maximum cannot be
  contaminated this way, because it depends only on records at LOWER sequence
  positions, written before the clock was touched and impossible to rewrite.

KNOWN LIMITATION
  A legitimately old file copied onto the volume produces the same pattern.
  This signal requires corroboration; stated in every reason report.
"""

import pandas as pd
from pathlib import Path

RAW  = Path(r"C:\ntfs-tamper-detect\data\raw")
PROC = Path(r"C:\ntfs-tamper-detect\data\processed")

SEQ_INCONSISTENCY_S = 86400 * 7

EXPERIMENTS = {
    "A": {"usn": "usn_corpus.csv",      "features": "features_usn.csv",
          "prefix": ("-tiny_",)},
    "B": {"usn": "usn_movetrick.csv",   "features": "features_movetrick.csv",
          "prefix": ("-tiny_",)},
    "C": {"usn": "usn_clocktamper.csv", "features": "features_clocktamper.csv",
          "prefix": ("ctben_", "ctfake_")},
}


def usn_sequence_features(usn_path, prefixes):
    usn = pd.read_csv(usn_path, encoding="utf-8", low_memory=False,
                      on_bad_lines="skip")

    seq_col = "UpdateSequenceNumber"
    if seq_col not in usn.columns:
        raise KeyError(f"{seq_col} not in {usn_path.name}")

    usn["UpdateTimestamp"] = pd.to_datetime(usn["UpdateTimestamp"], errors="coerce")
    usn[seq_col] = pd.to_numeric(usn[seq_col], errors="coerce")
    usn = usn.dropna(subset=["UpdateTimestamp", seq_col])

    timeline = (usn[[seq_col, "UpdateTimestamp"]]
                .sort_values(seq_col)
                .reset_index(drop=True))
    timeline["running_max"] = timeline["UpdateTimestamp"].cummax()

    ours = usn[usn["Name"].astype(str).str.contains("|".join(prefixes), na=False)]

    rows = []
    for name, g in ours.groupby("Name"):
        first_seq = g[seq_col].min()
        idx = timeline[seq_col].searchsorted(first_seq)
        idx = min(max(idx, 0), len(timeline) - 1)
        rows.append({
            "FileName": name,
            "usn_seq_first": first_seq,
            "usn_seq_floor_time": timeline.loc[idx, "running_max"],
        })

    return pd.DataFrame(rows)


def main():
    for exp, cfg in EXPERIMENTS.items():
        usn_path  = RAW / cfg["usn"]
        feat_path = PROC / cfg["features"]

        if not usn_path.exists() or not feat_path.exists():
            print(f"[{exp}] SKIP - missing input")
            continue

        print(f"\n[{exp}] reading {usn_path.name}")
        seq = usn_sequence_features(usn_path, cfg["prefix"])
        print(f"[{exp}] files found in journal: {len(seq)}")

        df = pd.read_csv(feat_path)
        df = df.drop(columns=[c for c in df.columns if c.startswith("usn_seq")
                              or c == "usn_neighbourhood_time"], errors="ignore")
        df = df.merge(seq, on="FileName", how="left")

        claimed = pd.to_datetime(df.get("si_created"), errors="coerce")
        if claimed.isna().all():
            claimed = pd.to_datetime(df.get("shown_created"), errors="coerce")

        floor = pd.to_datetime(df["usn_seq_floor_time"], errors="coerce")

        df["usn_seq_gap_s"] = (floor - claimed).dt.total_seconds()
        df["usn_seq_inconsistent"] = (
            df["usn_seq_gap_s"] > SEQ_INCONSISTENCY_S).fillna(False).astype(int)

        df.to_csv(feat_path, index=False)

        matched = df["usn_seq_first"].notna().sum()
        print(f"[{exp}] merged: {matched}/{len(df)} matched to journal")
        if "tampered" in df.columns:
            print(pd.crosstab(df["tampered"], df["usn_seq_inconsistent"],
                              rownames=["tampered"], colnames=["seq_inconsistent"]))
            fired = df[df["usn_seq_inconsistent"] == 1]
            if len(fired):
                print(f"[{exp}] median gap when fired: "
                      f"{fired['usn_seq_gap_s'].median()/86400:,.1f} days")

    print("\nDone.")


if __name__ == "__main__":
    main()
