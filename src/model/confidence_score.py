# confidence_score.py
# The correlation / confidence-score engine.
#
# WHAT IT DOES
#   Takes the independent signals produced by the feature scripts and fuses them
#   into a single 0-100 tampering confidence score per file, plus a plain-English
#   reason report explaining WHY each file was scored the way it was.
#
# WHY IT EXISTS (the project's contribution)
#   Any single check can be defeated. The framework's claim is that CORRELATING
#   indicators drawn from DIFFERENT forensic artefacts produces an assessment that
#   is both more robust and explainable. Signals are therefore grouped by the
#   artefact they came from, and agreement ACROSS artefacts earns a corroboration
#   bonus - this operationalises the direct/indirect artefact model (Korol, 2025)
#   and Locard's exchange principle.
#
#   Direct artefact   ($MFT)         - what the file CLAIMS about itself
#   Indirect artefact (USN Journal)  - what the system OBSERVED happening
#
# OUTPUT
#   data/processed/scored_files.csv   - every file with score, band, reasons
#   results/reason_reports.md         - human-readable per-file forensic reports
#   results/score_summary.png         - score distribution figure

import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"C:\ntfs-tamper-detect")
features_path = ROOT / "data" / "processed" / "features_usn.csv"
scored_path   = ROOT / "data" / "processed" / "scored_files.csv"
results_dir   = ROOT / "results"
results_dir.mkdir(exist_ok=True)
scored_path.parent.mkdir(parents=True, exist_ok=True)

# ==================================================================
# RULE TABLE
# Each rule = one independent indicator. Kept in one place so the
# weighting is transparent, auditable and easy to justify in the write-up.
#   weight   : points contributed when the rule fires
#   artefact : which forensic source the evidence came from
#   reason   : plain-English explanation shown to the investigator
# ==================================================================
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

# Bonus applied when independent artefacts corroborate each other.
# This is the correlation premium - the reason the framework is more than
# the sum of its individual checks.
CORROBORATION_BONUS = 15

BANDS = [
    (85, "VERY HIGH"),
    (60, "HIGH"),
    (30, "MEDIUM"),
    (1,  "LOW"),
    (0,  "NONE"),
]


def band_for(score):
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "NONE"


def score_row(r):
    """Return (score, band, list_of_reason_strings, artefacts_that_fired)."""
    score = 0
    reasons = []
    artefacts = set()

    for rule in RULES:
        fired = bool(r.get(rule["id"], 0))
        if not fired:
            continue
        score += rule["weight"]
        artefacts.add(rule["artefact"])
        try:
            detail = rule["detail"](r)
        except Exception:
            detail = ""
        reasons.append(f"[+{rule['weight']}] {rule['reason']}"
                       + (f" ({detail})" if detail else ""))

    # correlation premium: evidence from more than one artefact source
    if len(artefacts) > 1:
        score += CORROBORATION_BONUS
        reasons.append(f"[+{CORROBORATION_BONUS}] Corroborated across independent "
                       f"artefacts ({', '.join(sorted(artefacts))}) - "
                       f"tampering is unlikely to be a single-source artefact")

    score = min(score, 100)
    return score, band_for(score), reasons, sorted(artefacts)


# =================================================================
# RUN
# ==================================================================
df = pd.read_csv(features_path)

# make sure the signal columns exist and are numeric
for rule in RULES:
    if rule["id"] not in df.columns:
        df[rule["id"]] = 0
    df[rule["id"]] = df[rule["id"]].fillna(0).astype(int)

scores, bands, reason_lists, artefact_lists = [], [], [], []
for _, r in df.iterrows():
    s, b, reasons, arts = score_row(r)
    scores.append(s)
    bands.append(b)
    reason_lists.append(reasons)
    artefact_lists.append(arts)

df["tamper_score"]  = scores
df["score_band"]    = bands
df["artefacts_hit"] = ["+".join(a) if a else "" for a in artefact_lists]
df["reasons"]       = [" | ".join(r) if r else "No tampering indicators detected"
                       for r in reason_lists]

df.to_csv(scored_path, index=False)

# ------------------------------------------------------------------
# Per-file reason reports (the explainability deliverable)
# ------------------------------------------------------------------
flagged = df[df["tamper_score"] > 0].sort_values("tamper_score", ascending=False)

lines = ["# Tampering Assessment - Reason Reports", ""]
lines.append(f"Files analysed: **{len(df)}**  |  Flagged: **{len(flagged)}**  |  "
             f"Clean: **{len(df) - len(flagged)}**")
lines.append("")
lines.append("Scores are produced by correlating independent forensic indicators. "
             "Each line below states the evidence and the points it contributed, "
             "so every verdict can be traced back to a specific artefact.")
lines.append("")

for _, r in flagged.head(25).iterrows():   # sample for readability
    lines.append(f"## {r['FileName']}")
    lines.append(f"**Score: {r['tamper_score']}/100 ({r['score_band']})**  |  "
                 f"Artefacts: {r['artefacts_hit']}")
    lines.append("")
    for part in str(r["reasons"]).split(" | "):
        lines.append(f"- {part}")
    lines.append("")

if len(flagged) > 25:
    lines.append(f"_...and {len(flagged) - 25} further flagged files "
                 f"(full detail in scored_files.csv)._")

(results_dir / "reason_reports.md").write_text("\n".join(lines), encoding="utf-8")

# -----------------------------------------------------------------
# Figure: score distribution
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 4))
if "tampered" in df.columns:
    ax.hist([df.loc[df["tampered"] == 0, "tamper_score"],
             df.loc[df["tampered"] == 1, "tamper_score"]],
            bins=20, stacked=True, label=["benign (truth)", "tampered (truth)"])
    ax.legend()
else:
    ax.hist(df["tamper_score"], bins=20)
ax.set_xlabel("Tampering confidence score")
ax.set_ylabel("Number of files")
ax.set_title(f"Score distribution (n={len(df)})")
plt.tight_layout()
plt.savefig(results_dir / "score_summary.png", dpi=150)

# ------------------------------------------------------------------
# Console summary
# ------------------------------------------------------------------
print(f"Files scored: {len(df)}\n")

print("--- score bands ---")
print(df["score_band"].value_counts().to_string())
print()

print("--- artefact combinations that fired ---")
print(df["artefacts_hit"].replace("", "(none)").value_counts().to_string())
print()

if "tampered" in df.columns:
    print("--- score band vs ground truth ---")
    print(pd.crosstab(df["tampered"], df["score_band"],
                      rownames=["actual"], colnames=["band"]))
    print()
    print("--- mean score ---")
    print(df.groupby("tampered")["tamper_score"].mean().to_string())
    print()

print("Example report:")
if len(flagged):
    ex = flagged.iloc[0]
    print(f"  {ex['FileName']}  ->  {ex['tamper_score']}/100 ({ex['score_band']})")
    for part in str(ex["reasons"]).split(" | "):
        print(f"    - {part}")

print()
print("Saved ->", scored_path)
print("Saved ->", results_dir / "reason_reports.md")
print("Saved ->", results_dir / "score_summary.png")