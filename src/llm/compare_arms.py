"""
compare_arms.py - evaluates every arm against the ground-truth manifest.

ARMS
  rules     - static rule engine (from scored_files_*.csv)
  llm       - LLM on raw artefact evidence
  hybrid    - LLM shown the rule verdict and asked to critique it
  ablation  - LLM on Experiment C with the Event Log withheld

CLASS MAPPING
  Ground truth is binary; the LLM emits three classes. SUSPICIOUS is scored
  BOTH ways and reported as a sensitivity analysis, because the choice is a
  methodological judgement rather than a fact:
    lenient - SUSPICIOUS counts as a detection (matches the triage framing,
              where the operational outcome is "escalate for review")
    strict  - only LIKELY_TIMESTOMPING counts (treats hedging as a non-answer)

HALLUCINATION
  Each cited observation is checked for numeric tokens (timestamps, sequence
  numbers) that do not appear in that file's evidence bundle. A model citing
  facts absent from its input is a more serious failure than a wrong verdict.
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT    = Path(r"C:\ntfs-tamper-detect")
LLMDIR  = ROOT / "data" / "llm"
PROC    = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

POSITIVE_STRICT  = {"LIKELY_TIMESTOMPING"}
POSITIVE_LENIENT = {"LIKELY_TIMESTOMPING", "SUSPICIOUS"}


def metrics(pred, truth):
    tp = sum(1 for p, t in zip(pred, truth) if p == 1 and t == 1)
    tn = sum(1 for p, t in zip(pred, truth) if p == 0 and t == 0)
    fp = sum(1 for p, t in zip(pred, truth) if p == 1 and t == 0)
    fn = sum(1 for p, t in zip(pred, truth) if p == 0 and t == 1)
    n = len(pred)
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec  = tp / (tp + fn) if (tp + fn) else float("nan")
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) and not pd.isna(prec) and not pd.isna(rec) else float("nan")
    return {"n": n, "TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "accuracy": (tp + tn) / n if n else float("nan"),
            "precision": prec, "recall": rec, "f1": f1,
            "fpr": fp / (fp + tn) if (fp + tn) else float("nan")}


def fmt(v):
    return "n/a" if v is None or pd.isna(v) else f"{v:.3f}"


def load_bundles():
    out = {}
    with open(LLMDIR / "bundles.jsonl", encoding="utf-8") as f:
        for line in f:
            b = json.loads(line)
            out[b["file_id"]] = b
    return out


def load_arm(name):
    p = LLMDIR / f"responses_{name}.jsonl"
    if not p.exists():
        return None
    rows = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            parsed = r.get("parsed") or {}
            rows.append({
                "file_id": r["file_id"],
                "experiment": r["experiment"],
                "classification": parsed.get("classification"),
                "confidence": parsed.get("confidence"),
                "latency_s": r.get("latency_s"),
                "n_support": len(parsed.get("supporting_evidence") or []),
                "n_contra": len(parsed.get("contradicting_evidence") or []),
                "parsed": parsed,
            })
    return pd.DataFrame(rows)


def hallucination_check(df, bundles):
    """
    Count cited numeric facts absent from the file's own evidence bundle.
    Deliberately conservative: only 4+ digit runs are checked (years, sequence
    numbers, sub-second fractions), so ordinary prose numbers are not flagged.
    """
    flagged = 0
    total_claims = 0
    examples = []
    for _, r in df.iterrows():
        ev = bundles.get(r["file_id"], {}).get("evidence_text", "")
        ev_nums = set(re.findall(r"\d{4,}", ev))
        for item in (r["parsed"].get("supporting_evidence") or []):
            total_claims += 1
            text = f"{item.get('observation','')} {item.get('inference','')}"
            nums = set(re.findall(r"\d{4,}", text))
            unknown = nums - ev_nums
            if unknown:
                flagged += 1
                if len(examples) < 5:
                    examples.append((r["file_id"], sorted(unknown)[:3],
                                     item.get("observation", "")[:110]))
    return {"claims": total_claims, "unsupported": flagged,
            "rate": flagged / total_claims if total_claims else float("nan"),
            "examples": examples}


def main():
    bundles = load_bundles()
    key = pd.read_csv(LLMDIR / "bundle_key.csv")
    truth = dict(zip(key["file_id"], key["true_label"]))
    print(f"bundles: {len(bundles)}  ground truth: {len(truth)}")

    # ---- rules arm, restricted to the sampled files ----
    scored = []
    for exp in "ABC":
        p = PROC / f"scored_files_{exp}.csv"
        if p.exists():
            d = pd.read_csv(p)
            d["experiment"] = exp
            scored.append(d)
    scored = pd.concat(scored, ignore_index=True)
    name_to_score = dict(zip(scored["FileName"], scored["tamper_score"]))

    rules_rows = []
    for fid, b in bundles.items():
        rules_rows.append({
            "file_id": fid,
            "experiment": b["experiment"],
            "rule_positive": 1 if name_to_score.get(b["orig_name"], 0) >= 1 else 0,
            "true": truth[fid],
        })
    rules_df = pd.DataFrame(rules_rows)

    L = ["# Arm Comparison - Static Rules vs LLM Triage", ""]
    L.append("All arms evaluated against the same ground-truth manifest on the "
             "same 150-file sample (75 tampered / 75 benign).")
    L.append("")

    # ---- rules metrics ----
    rm = metrics(rules_df["rule_positive"].tolist(), rules_df["true"].tolist())
    L.append("## Static rules (baseline)")
    L.append("")
    L.append(f"- n {rm['n']} | accuracy **{fmt(rm['accuracy'])}** | "
             f"precision {fmt(rm['precision'])} | recall {fmt(rm['recall'])} | "
             f"F1 {fmt(rm['f1'])} | FPR {fmt(rm['fpr'])}")
    L.append(f"- TP {rm['TP']}, TN {rm['TN']}, FP {rm['FP']}, FN {rm['FN']}")
    L.append("")

    summary = [{"arm": "rules", "scoring": "-", **rm, "mean_latency_s": None}]

    # ---- llm arms ----
    for arm in ["llm", "hybrid", "ablation"]:
        df = load_arm(arm)
        if df is None:
            print(f"  missing responses_{arm}.jsonl - skipped")
            continue
        df["true"] = df["file_id"].map(truth)
        df = df.dropna(subset=["true"])
        df["true"] = df["true"].astype(int)

        L.append(f"## LLM arm: {arm}")
        L.append("")

        for label, posset in (("lenient (SUSPICIOUS = detection)", POSITIVE_LENIENT),
                              ("strict (LIKELY only)", POSITIVE_STRICT)):
            pred = [1 if c in posset else 0 for c in df["classification"]]
            m = metrics(pred, df["true"].tolist())
            L.append(f"**{label}**")
            L.append("")
            L.append(f"- n {m['n']} | accuracy **{fmt(m['accuracy'])}** | "
                     f"precision {fmt(m['precision'])} | recall {fmt(m['recall'])} | "
                     f"F1 {fmt(m['f1'])} | FPR {fmt(m['fpr'])}")
            L.append(f"- TP {m['TP']}, TN {m['TN']}, FP {m['FP']}, FN {m['FN']}")
            L.append("")
            summary.append({"arm": arm, "scoring": label.split(" ")[0], **m,
                            "mean_latency_s": df["latency_s"].mean()})

        L.append("Per-experiment recall (lenient scoring):")
        L.append("")
        L.append("| Exp | tampered n | detected | recall | benign n | false pos | FPR |")
        L.append("|---|---|---|---|---|---|---|")
        for exp in sorted(df["experiment"].unique()):
            sub = df[df["experiment"] == exp]
            tam = sub[sub["true"] == 1]
            ben = sub[sub["true"] == 0]
            det = sum(1 for c in tam["classification"] if c in POSITIVE_LENIENT)
            fp  = sum(1 for c in ben["classification"] if c in POSITIVE_LENIENT)
            L.append(f"| {exp} | {len(tam)} | {det} | "
                     f"{fmt(det/len(tam) if len(tam) else None)} | {len(ben)} | "
                     f"{fp} | {fmt(fp/len(ben) if len(ben) else None)} |")
        L.append("")

        L.append("Class distribution: " +
                 ", ".join(f"{k} {v}" for k, v in
                           df["classification"].value_counts().items()))
        L.append("")

        # confidence calibration
        correct = [c in POSITIVE_LENIENT for c in df["classification"]]
        df["_right"] = [p == (t == 1) for p, t in zip(correct, df["true"])]
        conf_right = df.loc[df["_right"], "confidence"].mean()
        conf_wrong = df.loc[~df["_right"], "confidence"].mean()
        L.append(f"Mean confidence when correct: **{fmt(conf_right)}**, "
                 f"when wrong: **{fmt(conf_wrong)}**. A model that is as "
                 f"confident when wrong as when right offers the analyst no "
                 f"usable signal from its own confidence score.")
        L.append("")

        h = hallucination_check(df, bundles)
        L.append(f"Hallucination check: **{h['unsupported']}/{h['claims']}** "
                 f"cited observations contain numeric values absent from the "
                 f"evidence bundle (**{fmt(h['rate'])}**).")
        if h["examples"]:
            L.append("")
            for fid, nums, obs in h["examples"]:
                L.append(f"  - `{fid}` unsupported {nums}: {obs}...")
        L.append("")
        L.append(f"Mean latency: **{df['latency_s'].mean():.2f}s** per file "
                 f"(total {df['latency_s'].sum()/60:.1f} min for {len(df)} files).")
        L.append("")

    # ---- headline table ----
    sdf = pd.DataFrame(summary)
    L.insert(3, "## Summary")
    L.insert(4, "")
    L.insert(5, "| Arm | Scoring | n | Acc | Prec | Recall | F1 | FPR | Latency |")
    L.insert(6, "|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(summary):
        lat = "<0.01s" if r["mean_latency_s"] is None else f"{r['mean_latency_s']:.2f}s"
        L.insert(7 + i, f"| {r['arm']} | {r['scoring']} | {r['n']} | "
                        f"{fmt(r['accuracy'])} | {fmt(r['precision'])} | "
                        f"{fmt(r['recall'])} | {fmt(r['f1'])} | {fmt(r['fpr'])} | {lat} |")
    L.insert(7 + len(summary), "")

    (RESULTS / "arm_comparison.md").write_text("\n".join(L), encoding="utf-8")
    sdf.to_csv(RESULTS / "arm_comparison.csv", index=False)

    print("\n" + sdf[["arm", "scoring", "n", "accuracy", "precision",
                      "recall", "f1", "fpr"]].to_string(index=False))
    print(f"\nSaved -> {RESULTS / 'arm_comparison.md'}")


if __name__ == "__main__":
    main()
