# confidence_score_movetrick.py
# Runs the confidence-score engine on the MOVE-TRICK set (both $SI and $FN faked).
#
# The point: these files have CONSISTENT $SI/$FN timestamps, so a timestamp-
# comparison check clears them - yet the engine still scores them HIGH via the
# independent USN Journal evidence. The reason reports make that explicit.
#
# Identical to confidence_score.py except for the four paths marked below.

import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"C:\ntfs-tamper-detect")
features_path = ROOT / "data" / "processed" / "features_movetrick.csv"      # <-- changed
scored_path   = ROOT / "data" / "processed" / "scored_movetrick.csv"        # <-- changed
results_dir   = ROOT / "results"
results_dir.mkdir(exist_ok=True)
scored_path.parent.mkdir(parents=True, exist_ok=True)

REPORT_NAME = "reason_reports_movetrick.md"     # <-- changed
FIGURE_NAME = "score_summary_movetrick.png"     # <-- changed

RULES = [
    {
        "id":       "si_fn_mismatch",
        "weight":   40,
        "artefact": "MFT",
        "reason":   ("$STANDARD_INFORMATION creation time disagrees with the "
                     "kernel-managed $FILE_NAME creation time"),
        "detail":   lambda r: f"discrepancy of {r['delta_created_s']/86400:.1f} days",
    },
    {
        "id":       "usn_basicinfo_after_close",
        "weight":   35,
        "artefact": "USN",
        "reason":   ("USN Journal records timestamp/attribute modification AFTER "
                     "the file's creation sequence completed"),
        "detail":   lambda r: f"{int(r['usn_basicinfo_after_close_n'])} BasicInfoChange record(s)",
    },
    {
        "id":       "usn_claim_conflict",
        "weight":   25,
        "artefact": "USN",
        "reason":   ("File claims a creation date earlier than its first appearance "
                     "in the USN Journal"),
        "detail":   lambda r: f"claims {abs(r['usn_claim_gap_s'])/86400:.1f} days before first journal entry",
    },
]

CORROBORATION_BONUS = 15

BANDS = [(85, "VERY HIGH"), (60, "HIGH"), (30, "MEDIUM"), (1, "LOW"), (0, "NONE")]


def band_for(score):
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "NONE"


def score_row(r):
    score, reasons, artefacts = 0, [], set()
    for rule in RULES:
        if not bool(r.get(rule["id"], 0)):
            continue
        score += rule["weight"]
        artefacts.add(rule["artefact"])
        try:
            detail = rule["detail"](r)
        except Exception:
            detail = ""
        reasons.append(f"[+{rule['weight']}] {rule['reason']}"
                       + (f" ({detail})" if detail else ""))
    if len(artefacts) > 1:
        score += CORROBORATION_BONUS
        reasons.append(f"[+{CORROBORATION_BONUS}] Corroborated across independent "
                       f"artefacts ({', '.join(sorted(artefacts))})")
    return min(score, 100), band_for(min(score, 100)), reasons, sorted(artefacts)


df = pd.read_csv(features_path)
for rule in RULES:
    if rule["id"] not in df.columns:
        df[rule["id"]] = 0
    df[rule["id"]] = df[rule["id"]].fillna(0).astype(int)

scores, bands, reason_lists, artefact_lists = [], [], [], []
for _, r in df.iterrows():
    s, b, reasons, arts = score_row(r)
    scores.append(s); bands.append(b); reason_lists.append(reasons); artefact_lists.append(arts)

df["tamper_score"]  = scores
df["score_band"]    = bands
df["artefacts_hit"] = ["+".join(a) if a else "" for a in artefact_lists]
df["reasons"]       = [" | ".join(r) if r else "No tampering indicators detected"
                       for r in reason_lists]
df.to_csv(scored_path, index=False)

flagged = df[df["tamper_score"] > 0].sort_values("tamper_score", ascending=False)

lines = ["# Tampering Assessment - Move-Trick Set (both timestamps faked)", ""]
lines.append(f"Files analysed: **{len(df)}**  |  Flagged: **{len(flagged)}**")
lines.append("")
lines.append("These files were tampered so that $SI and $FN AGREE - a timestamp-"
             "comparison check clears them. They are nonetheless flagged below, "
             "on independent USN Journal evidence.")
lines.append("")
for _, r in flagged.head(25).iterrows():
    lines.append(f"## {r['FileName']}")
    lines.append(f"**Score: {r['tamper_score']}/100 ({r['score_band']})**  |  "
                 f"Artefacts: {r['artefacts_hit']}")
    lines.append("")
    for part in str(r["reasons"]).split(" | "):
        lines.append(f"- {part}")
    lines.append("")
if len(flagged) > 25:
    lines.append(f"_...and {len(flagged) - 25} further flagged files._")
(results_dir / REPORT_NAME).write_text("\n".join(lines), encoding="utf-8")

fig, ax = plt.subplots(figsize=(6, 4))
ax.hist(df["tamper_score"], bins=20)
ax.set_xlabel("Tampering confidence score")
ax.set_ylabel("Number of files")
ax.set_title(f"Move-trick set score distribution (n={len(df)})")
plt.tight_layout()
plt.savefig(results_dir / FIGURE_NAME, dpi=150)

print(f"Files scored: {len(df)}\n")
print("--- score bands ---")
print(df["score_band"].value_counts().to_string())
print()
if "tampered" in df.columns:
    print("--- mean score (all tampered) ---")
    print(df["tamper_score"].mean())
    print()
print("KEY POINT: si_fn_mismatch fired on",
      int(df["si_fn_mismatch"].sum()), "of", len(df),
      "- yet mean score is", round(df["tamper_score"].mean(), 1),
      "because USN evidence still flags them.\n")
if len(flagged):
    ex = flagged.iloc[0]
    print("Example report:")
    print(f"  {ex['FileName']}  ->  {ex['tamper_score']}/100 ({ex['score_band']})")
    for part in str(ex["reasons"]).split(" | "):
        print(f"    - {part}")
print("\nSaved ->", scored_path)
print("Saved ->", results_dir / REPORT_NAME)
print("Saved ->", results_dir / FIGURE_NAME)