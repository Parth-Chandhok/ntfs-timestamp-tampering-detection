"""
build_llm_bundles.py - assembles per-file forensic evidence bundles for the
LLM triage comparison.

WHAT IT DOES
  Each scored file's evidence is scattered across three artefacts and a scored
  CSV. This turns it into ONE readable text block per file: the "case file" the
  LLM sees.

FAIRNESS
  The bundle contains exactly the evidence the static rules had access to -
  nothing more, nothing less. Withholding evidence from the LLM and then
  declaring the rules superior would not be a valid comparison.

BLINDING
  Filenames are rewritten (ctfake_001_x.csv -> file_0042.csv). The originals
  encode the ground truth, so an unblinded LLM could read the answer off the
  filename rather than reasoning from evidence.

SAMPLING
  150 files, class-balanced at 75 tampered / 75 benign. Experiment B generated
  no benign controls, so its share of the benign half is drawn from A and C -
  all benign files are NapierOne documents written by the same code path, so
  they are interchangeable as controls. Balance matters here: at 100/50 a model
  that answered "tampered" every time would score 67% accuracy, which would look
  respectable while meaning nothing. Sized for prompt iteration within free-tier
  API rate limits.
"""

import json
import pandas as pd
from pathlib import Path

ROOT      = Path(r"C:\ntfs-tamper-detect")
PROCESSED = ROOT / "data" / "processed"
RAW       = ROOT / "data" / "raw"
OUT       = ROOT / "data" / "llm"
OUT.mkdir(parents=True, exist_ok=True)

SEED = 42

# 150 files, class-balanced 75 tampered / 75 benign. Experiment B generated no
# benign controls, so its share of the benign half is drawn proportionally from
# A and C - all benign files are NapierOne documents written by the same code
# path, so they are interchangeable as controls. Stated as a limitation.
SAMPLE = {
    "A": {"tampered": 25, "benign": 38, "scored": "scored_files_A.csv",
          "usn": "usn_corpus.csv"},
    "B": {"tampered": 25, "benign": 0,  "scored": "scored_files_B.csv",
          "usn": "usn_movetrick.csv"},
    "C": {"tampered": 25, "benign": 37, "scored": "scored_files_C.csv",
          "usn": "usn_clocktamper.csv"},
}

RULE_FIELDS = ["si_fn_mismatch", "usn_basicinfo_after_close",
               "usn_claim_conflict", "usn_seq_inconsistent",
               "eventlog_clock_window"]


def load_usn(fname):
    """Per-file USN records, keyed by filename."""
    p = RAW / fname
    if not p.exists():
        return {}
    usn = pd.read_csv(p, encoding="utf-8", low_memory=False, on_bad_lines="skip")
    usn["UpdateTimestamp"] = pd.to_datetime(usn["UpdateTimestamp"], errors="coerce")
    usn["UpdateSequenceNumber"] = pd.to_numeric(usn["UpdateSequenceNumber"],
                                                errors="coerce")
    out = {}
    for name, g in usn.groupby("Name"):
        g = g.sort_values("UpdateSequenceNumber")
        out[name] = [
            {"seq": int(r["UpdateSequenceNumber"]),
             "time": str(r["UpdateTimestamp"]),
             "reason": str(r["UpdateReasons"])}
            for _, r in g.iterrows()
        ]
    return out


def clock_events():
    """Clock-change events from the Event Log, shared volume context."""
    import re
    p = RAW / "eventlog_clocktamper.csv"
    if not p.exists():
        return []
    ev = pd.read_csv(p, encoding="utf-8", on_bad_lines="skip")
    ev = ev[(ev["ProviderName"] == "Microsoft-Windows-Kernel-General")
            & (ev["Id"] == 1)]
    rx = re.compile(r"(\d{4}-\d{2}-\d{2}T[\d:.]+Z)")
    out = []
    for _, row in ev.iterrows():
        msg = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", str(row.get("Message", "")))
        hits = rx.findall(msg)
        if len(hits) < 2:
            continue
        to_t, from_t = pd.to_datetime(hits[0]), pd.to_datetime(hits[1])
        secs = (to_t - from_t).total_seconds()
        if abs(secs) > 86400:
            out.append({"from": str(from_t.tz_localize(None)),
                        "to": str(to_t.tz_localize(None)),
                        "shift_days": round(secs / 86400, 1)})
    return out


def render(bundle):
    """Format one bundle as the text block the LLM reads."""
    L = [f"FILE: {bundle['file_id']}",
         f"Extension: {bundle.get('extension', 'unknown')}",
         f"Size: {bundle.get('size_bytes') or 'not recorded'}",
         "",
         "MFT EVIDENCE ($STANDARD_INFORMATION and $FILE_NAME attributes)"]

    si = str(bundle.get("si_created") or "").strip()
    fn = str(bundle.get("fn_created") or "").strip()

    # Experiments A and B store only the SIGNED-MAGNITUDE gap between $SI and
    # $FN, not the raw $FN value, so it is reconstructed here as $SI + delta.
    # This relies on tampering having moved $SI BACKWARDS, which holds for every
    # method used in this project. Never substitute $SI for a missing $FN: doing
    # so would assert agreement where the truth may be a large mismatch, i.e.
    # fabricate exculpatory evidence.
    if not fn or fn in ("nan", "NaT", "None"):
        delta = bundle.get("delta_created_s")
        try:
            delta = float(delta)
        except (TypeError, ValueError):
            delta = None
        if delta is not None and si:
            import pandas as _pd
            base = _pd.to_datetime(si, errors="coerce")
            if _pd.notna(base):
                fn = (f"{base + _pd.to_timedelta(delta, unit='s')}"
                      if delta > 1 else f"{si}  (identical to $SI)")
            else:
                fn = "not recorded"
        else:
            fn = "not recorded"

    L.append(f"  $SI created:  {si or 'not recorded'}")
    L.append(f"  $FN created:  {fn}")
    L.append("")

    L.append("USN JOURNAL EVIDENCE")
    L.append("  Sequence numbers are byte offsets into an append-only journal;")
    L.append("  they increase monotonically and are assigned by the filesystem.")
    recs = bundle.get("usn_records", [])
    if recs:
        for r in recs:
            L.append(f"  seq {r['seq']:>12}  {r['time']}  {r['reason']}")
    else:
        L.append("  (no journal records found for this file)")
    floor = str(bundle.get("usn_seq_floor_time") or "").strip()
    if floor and floor not in ("nan", "NaT"):
        L.append(f"  Highest timestamp recorded at or before this file's first")
        L.append(f"  journal position: {floor}")
    L.append("")

    L.append("SYSTEM EVENT LOG")
    evs = bundle.get("clock_events", [])
    if evs:
        for e in evs:
            L.append(f"  System clock changed: {e['from']} -> {e['to']} "
                     f"({e['shift_days']:+,} days)")
        # JOIN VARIANT: state explicitly whether THIS file was created inside a
        # rolled-back window. Originally the clock events were volume-wide
        # context and the model had to perform the interval containment test
        # itself - arithmetic on a 4.8-second window against a 3-year anomaly.
        # Supplying the join tests whether the failure was comprehension or
        # precision.
        import pandas as _pd
        _claimed = _pd.to_datetime(bundle.get("si_created"), errors="coerce")
        _inside = False
        for _b in evs:
            if float(_b["shift_days"]) >= 0:
                continue
            _start = _pd.to_datetime(_b["to"], errors="coerce")
            for _f in evs:
                if float(_f["shift_days"]) <= 0:
                    continue
                _end = _pd.to_datetime(_f["from"], errors="coerce")
                if _pd.notna(_claimed) and _pd.notna(_start) and _pd.notna(_end):
                    if _start <= _claimed <= _end:
                        _inside = True
        L.append("")
        L.append("  CORRELATION: this file's claimed creation time ("
                 + str(bundle.get("si_created")) + ") falls "
                 + ("INSIDE" if _inside else "OUTSIDE")
                 + " a window during which the system clock was set backwards.")
    else:
        L.append("  No system clock changes recorded on this volume.")
    return "\n".join(L)


def main():
    clocks = clock_events()
    print(f"clock-change events found: {len(clocks)}")

    bundles = []
    counter = 0

    for exp, cfg in SAMPLE.items():
        path = PROCESSED / cfg["scored"]
        if not path.exists():
            print(f"[{exp}] SKIP - missing {cfg['scored']}")
            continue

        df = pd.read_csv(path)
        usn_map = load_usn(cfg["usn"])
        print(f"[{exp}] scored rows {len(df)}, usn files {len(usn_map)}")

        for label, n in (("tampered", cfg["tampered"]), ("benign", cfg["benign"])):
            if n == 0:
                continue
            want = 1 if label == "tampered" else 0
            pool = df[df["tampered"] == want]
            if len(pool) < n:
                print(f"[{exp}] WARNING: only {len(pool)} {label} available, "
                      f"wanted {n}")
                n = len(pool)
            picked = pool.sample(n=n, random_state=SEED)

            for _, r in picked.iterrows():
                counter += 1
                fid = f"file_{counter:04d}{Path(str(r['FileName'])).suffix}"
                b = {
                    "file_id":      fid,
                    "experiment":   exp,
                    "true_label":   int(r["tampered"]),
                    "orig_name":    str(r["FileName"]),
                    "extension":    Path(str(r["FileName"])).suffix,
                    "size_bytes":   r.get("size_bytes"),
                    "si_created":   str(r.get("si_created", "")),
                    "fn_created":   str(r.get("fn_created", "")),
                    "delta_created_s": r.get("delta_created_s", r.get("delta_si_fn_s")),
                    "delta_created_s": r.get("delta_created_s",
                                             r.get("delta_si_fn_s")),
                    "usn_records":  usn_map.get(str(r["FileName"]), []),
                    "usn_seq_floor_time": str(r.get("usn_seq_floor_time", "")),
                    "clock_events": clocks if exp == "C" else [],
                    "rule_results": {k: int(r.get(k, 0)) for k in RULE_FIELDS},
                    "rule_score":   int(r.get("tamper_score", 0)),
                    "rule_band":    str(r.get("score_band", "")),
                    "rule_reasons": str(r.get("reasons", "")),
                }
                b["evidence_text"] = render(b)
                bundles.append(b)

    with open(OUT / "bundles.jsonl", "w", encoding="utf-8") as f:
        for b in bundles:
            f.write(json.dumps(b, default=str) + "\n")

    key = pd.DataFrame([{"file_id": b["file_id"], "experiment": b["experiment"],
                         "true_label": b["true_label"], "orig_name": b["orig_name"]}
                        for b in bundles])
    key.to_csv(OUT / "bundle_key.csv", index=False)

    print(f"\nbundles written: {len(bundles)}")
    print(key.groupby(["experiment", "true_label"]).size().to_string())
    print(f"\nSaved -> {OUT / 'bundles.jsonl'}")
    print(f"Saved -> {OUT / 'bundle_key.csv'}")
    print("\n--- sample bundle ---")
    print(bundles[0]["evidence_text"] if bundles else "(none)")


if __name__ == "__main__":
    main()





