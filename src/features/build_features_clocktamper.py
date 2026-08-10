"""
build_features_clocktamper.py — Experiment C feature extraction.

Correlates three artefacts for the 400-file clock-rollback corpus:
  $MFT        -> si_fn_mismatch            (file-level, expected to FAIL here)
  USN journal -> usn_basicinfo_after_close (file-level, expected to FAIL here)
  Event Log   -> eventlog_clock_window     (system-level, expected to CATCH)

The Event Log signal pairs each backward clock jump with its mirror-image
forward restore, defining a "fake-clock window". Any file whose claimed
creation time falls inside such a window was born under a rolled-back clock.
"""

import re
import pandas as pd
from pathlib import Path

RAW    = Path(r"C:\ntfs-tamper-detect\data\raw")
LABELS = Path(r"C:\ntfs-tamper-detect\data\labels")
OUT    = Path(r"C:\ntfs-tamper-detect\data\processed")
OUT.mkdir(parents=True, exist_ok=True)

JUMP_THRESHOLD_S = 3600           # below this = ambient VM noise
BIG_JUMP_S       = 86400 * 30     # 30 days: above VM suspend noise (max ~8d),
                                  # far below the 3-year tamper (~1095d)
ISO_RX = re.compile(r"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)")


# ---------- 1. Event Log: derive fake-clock windows ----------
def fake_clock_windows(path):
    ev = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    ev = ev[(ev["ProviderName"] == "Microsoft-Windows-Kernel-General") & (ev["Id"] == 1)]

    jumps = []
    for _, row in ev.iterrows():
        msg = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", str(row.get("Message", "")))
        hits = ISO_RX.findall(msg)
        if len(hits) < 2:
            continue
        to_t   = pd.to_datetime(hits[0]).tz_localize(None)
        from_t = pd.to_datetime(hits[1]).tz_localize(None)
        secs   = (to_t - from_t).total_seconds()
        if abs(secs) > JUMP_THRESHOLD_S:
            jumps.append({"from": from_t, "to": to_t, "secs": secs})

    # Pair each backward jump with its mirror-image forward restore.
    # NOTE: sorting by time and scanning forward does NOT work here. A backward
    # jump is logged under the already-rolled-back clock, so it appears years
    # out of sequence relative to its own restore event. Match on magnitude.
    windows = []
    used = set()
    for j in jumps:
        if j["secs"] >= 0 or abs(j["secs"]) < BIG_JUMP_S:
            continue
        for k_i, k in enumerate(jumps):
            if k_i in used or k["secs"] <= 0 or abs(k["secs"]) < BIG_JUMP_S:
                continue
            if abs(k["secs"] + j["secs"]) < 60:          # mirror image
                used.add(k_i)
                windows.append({
                    "start": j["to"],        # first instant under the fake clock
                    "end":   k["from"],      # last instant before restore
                    "jump_secs": j["secs"],
                })
                break
    windows.sort(key=lambda w: w["start"])
    return windows, jumps


# ---------- 2. $MFT: SI/FN comparison ----------
def mft_features(path):
    mft = pd.read_csv(path, encoding="utf-8", low_memory=False, on_bad_lines="skip")
    mft = mft[mft["FileName"].astype(str).str.startswith(("ctben_", "ctfake_"))].copy()

    si = pd.to_datetime(mft["Created0x10"], errors="coerce")
    fn = pd.to_datetime(mft["Created0x30"], errors="coerce")
    fn = fn.fillna(si)      # MFTECmd blanks $FN when it equals $SI

    mft["si_created"]     = si
    mft["fn_created"]     = fn
    mft["delta_si_fn_s"]  = (si - fn).dt.total_seconds().abs()
    mft["si_fn_mismatch"] = (mft["delta_si_fn_s"] > 1).astype(int)
    return mft[["FileName", "si_created", "fn_created", "delta_si_fn_s", "si_fn_mismatch"]]


# ---------- 3. USN: timestamp change after close ----------
def usn_features(path):
    usn = pd.read_csv(path, encoding="utf-8", low_memory=False, on_bad_lines="skip")
    usn = usn[usn["Name"].astype(str).str.startswith(("ctben_", "ctfake_"))].copy()
    usn["UpdateTimestamp"] = pd.to_datetime(usn["UpdateTimestamp"], errors="coerce")

    rows = []
    for name, g in usn.groupby("Name"):
        reasons = " ".join(g["UpdateReasons"].astype(str))
        rows.append({
            "FileName": name,
            "usn_first_seen": g["UpdateTimestamp"].min(),
            "usn_entry_count": len(g),
            "usn_basicinfo_after_close": int("BasicInfoChange" in reasons and "Close" in reasons),
        })
    return pd.DataFrame(rows)


# ---------- 4. Join and score ----------
def main():
    windows, jumps = fake_clock_windows(RAW / "eventlog_clocktamper.csv")
    big = [j for j in jumps if abs(j["secs"]) > BIG_JUMP_S]
    print(f"Clock jumps > {JUMP_THRESHOLD_S}s: {len(jumps)}   "
          f"(of which > 30 days: {len(big)})")
    for j in big:
        print(f"   big jump: {j['from']} -> {j['to']}  ({j['secs']:,.0f}s)")
    print(f"Fake-clock windows identified: {len(windows)}")
    for w in windows:
        span = (w["end"] - w["start"]).total_seconds()
        print(f"   {w['start']} -> {w['end']}  (width {span:.1f}s, jump {w['jump_secs']:,.0f}s)")

    man = pd.read_csv(LABELS / "clocktamper_manifest.csv").rename(columns={"filename": "FileName"})

    df = man.merge(mft_features(RAW / "mft_clocktamper.csv"), on="FileName", how="left")
    df = df.merge(usn_features(RAW / "usn_clocktamper.csv"), on="FileName", how="left")

    print(f"\nmanifest rows: {len(man)}  |  MFT matched: {df['si_created'].notna().sum()}"
          f"  |  USN matched: {df['usn_first_seen'].notna().sum()}")

    claimed = pd.to_datetime(
        df["si_created"].fillna(pd.to_datetime(df["shown_created"], errors="coerce")),
        errors="coerce")
    flag = pd.Series(0, index=df.index)
    for w in windows:
        flag |= claimed.between(w["start"], w["end"]).astype(int)
    df["eventlog_clock_window"] = flag

    for c in ["si_fn_mismatch", "usn_basicinfo_after_close", "eventlog_clock_window"]:
        df[c] = df[c].fillna(0).astype(int)

    df.to_csv(OUT / "features_clocktamper.csv", index=False)

    print("\n--- signal vs ground truth (rows = tampered 0/1) ---")
    for c in ["si_fn_mismatch", "usn_basicinfo_after_close", "eventlog_clock_window"]:
        print(f"\n{c}")
        print(pd.crosstab(df["tampered"], df[c]))

    print(f"\nWritten: {OUT / 'features_clocktamper.csv'}  rows={len(df)}")


if __name__ == "__main__":
    main()