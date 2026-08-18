"""
compare_expC.py - Experiment C across every arm and model variant.

Experiment C is the discriminating case: clock rollback leaves every file-level
timestamp internally consistent, so detection requires correlating the file's
claimed creation time against a system clock-change window.

The "join supplied" variants add ONE line to the evidence bundle stating whether
that file's claimed creation falls INSIDE or OUTSIDE a rolled-back window. No
prompt text changed. This isolates whether the LLM's failure was conceptual (it
did not understand the evidence) or arithmetic (it understood but could not
resolve a 4.8-second interval against a 3-year anomaly).
"""

import json
from pathlib import Path

import pandas as pd

LLM = Path(r"C:\ntfs-tamper-detect\data\llm")
key = pd.read_csv(LLM / "bundle_key.csv")
truth = dict(zip(key["file_id"], key["true_label"]))

LEN = {"LIKELY_TIMESTOMPING", "SUSPICIOUS"}
STR = {"LIKELY_TIMESTOMPING"}


def load(name):
    p = LLM / name
    if not p.exists():
        return None
    rows = []
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        if r["experiment"] != "C":
            continue
        pa = r.get("parsed") or {}
        rows.append({"file_id": r["file_id"],
                     "cls": pa.get("classification"),
                     "conf": pa.get("confidence"),
                     "lat": r.get("latency_s"),
                     "true": truth.get(r["file_id"])})
    df = pd.DataFrame(rows)
    return df if len(df) else None


def m(df, posset):
    p = [1 if c in posset else 0 for c in df["cls"]]
    t = df["true"].tolist()
    tp = sum(1 for a, b in zip(p, t) if a == 1 and b == 1)
    tn = sum(1 for a, b in zip(p, t) if a == 0 and b == 0)
    fp = sum(1 for a, b in zip(p, t) if a == 1 and b == 0)
    fn = sum(1 for a, b in zip(p, t) if a == 0 and b == 1)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) and prec == prec and rec == rec else float("nan")
    return {"n": len(df), "TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "acc": (tp + tn) / len(df), "prec": prec, "rec": rec, "f1": f1,
            "fpr": fp / (fp + tn) if fp + tn else float("nan"),
            "lat": df["lat"].mean()}


ARMS = [
    ("lite   llm      volume-wide", "responses_llm.jsonl"),
    ("lite   hybrid   volume-wide", "responses_hybrid.jsonl"),
    ("lite   ablation no eventlog", "responses_ablation.jsonl"),
    ("flash  llm      volume-wide", "responses_llm_35-flash_expC.jsonl"),
    ("flash  hybrid   volume-wide", "responses_hybrid_35-flash_expC.jsonl"),
    ("lite   llm      JOIN SUPPLIED", "responses_llm_expC.jsonl"),
    ("lite   hybrid   JOIN SUPPLIED", "responses_hybrid_expC.jsonl"),
]

print("EXPERIMENT C ONLY  (25 tampered / 37 benign)")
print("Static rules baseline: recall 1.000, FPR 0.000, latency <0.01s\n")
print(f"{'arm':<30} {'scoring':<8} {'n':>3} {'TP':>3} {'TN':>3} {'FP':>3} {'FN':>3} "
      f"{'acc':>6} {'prec':>6} {'rec':>6} {'fpr':>6} {'lat':>7}")
print("-" * 104)

rows = []
for label, fname in ARMS:
    df = load(fname)
    if df is None:
        print(f"{label:<30} (not run)")
        continue
    for sc, ps in (("lenient", LEN), ("strict", STR)):
        r = m(df, ps)
        print(f"{label:<30} {sc:<8} {r['n']:>3} {r['TP']:>3} {r['TN']:>3} "
              f"{r['FP']:>3} {r['FN']:>3} {r['acc']:>6.3f} {r['prec']:>6.3f} "
              f"{r['rec']:>6.3f} {r['fpr']:>6.3f} {r['lat']:>6.1f}s")
        rows.append({"arm": label, "scoring": sc, **r})
    print(f"{'':<30} classes: " +
          ", ".join(f"{k} {v}" for k, v in df["cls"].value_counts().items()))
    print()

out = Path(r"C:\ntfs-tamper-detect\results") / "expC_all_arms.csv"
pd.DataFrame(rows).to_csv(out, index=False)
print("Saved ->", out)
