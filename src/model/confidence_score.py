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
#   is both more robust and explainable. Signals are grouped by the artefact they
#   came from, and agreement ACROSS artefacts earns a corroboration bonus - this
#   operationalises the direct/indirect artefact model (Korol, 2025) and Locard's
#   exchange principle.
#
#     Direct artefact   ($MFT)        - what the file CLAIMS about itself
#     Indirect artefact (USN Journal) - what the filesystem OBSERVED happening
#     Indirect artefact (Event Log)   - what the OPERATING SYSTEM observed happening
#
#   The same engine and the same rule table are applied to every experiment, so
#   scores across experiments are directly comparable.
#
# USAGE
#   python src/model/confidence_score.py --exp A     (PowerShell $SI timestomp)
#   python src/model/confidence_score.py --exp B     (move-trick)
#   python src/model/confidence_score.py --exp C     (clock rollback)

import argparse
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"C:\ntfs-tamper-detect")

# ==================================================================
# EXPERIMENT REGISTRY
# One entry per controlled tampering experiment. Adding an experiment
# means adding a row here - never a new copy of the engine.
# ==================================================================
EXPERIMENTS = {
    "A": {
        "label":    "Experiment A - PowerShell $SI timestomp",
        "features": ROOT / "data" / "processed" / "features_usn.csv",
    },
    "B": {
        "label":    "Experiment B - move-trick ($SI and $FN both faked)",
        "features": ROOT / "data" / "processed" / "features_movetrick.csv",
    },
    "C": {
        "label":    "Experiment C - system clock rollback",
        "features": ROOT / "data" / "processed" / "features_clocktamper.csv",
    },
}

# ==================================================================
# RULE TABLE
# Each rule = one independent indicator. Kept in one place so the
# weighting is transparent, auditable and easy to justify in the write-up.
#   weight   : points contributed when the rule fires
#   artefact : which forensic source the evidence came from
#   reason   : plain-English explanation shown to the investigator
# ==================================================================


def _get(r, *names):
    """Fetch the first present, non-null column from a list of aliases."""
    for n in names:
        if n in r.index and pd.notna(r[n]):
            return r[n]
    return None


def _days(v):
    return f"{abs(float(v)) / 86400:.1f} days" if v is not None else None


RULES = [
    {
        "id":       "si_fn_mismatch",
        "weight":   40,
        "artefact": "MFT",
        "reason":   ("$STANDARD_INFORMATION creation time disagrees with the "
                     "kernel-managed $FILE_NAME creation time"),
        "detail":   lambda r: (lambda d: f"discrepancy of {d}" if d else "")(
                        _days(_get(r, "delta_created_s", "delta_si_fn_s"))),
    },
    {
        "id":       "usn_basicinfo_after_close",
        "weight":   35,
        "artefact": "USN",
        "reason":   ("USN Journal records timestamp/attribute modification AFTER "
                     "the file's creation sequence completed"),
        "detail":   lambda r: (lambda n: f"{int(n)} BasicInfoChange record(s)" if n else "")(
                        _get(r, "usn_basicinfo_after_close_n")),
    },
    {
        "id":       "usn_claim_conflict",
        "weight":   25,
        "artefact": "USN",
        "reason":   ("File claims a creation date earlier than its first appearance "
                     "in the USN Journal"),
        "detail":   lambda r: (lambda d: f"claims {d} before first journal entry" if d else "")(
                        _days(_get(r, "usn_claim_gap_s"))),
    },
    {
        # Added for Experiment C. System-level artefact: the OS itself recorded
        # the clock being moved. Weighted above the USN signals (a clock change
        # is rare and deliberate, and this rule requires temporal correlation
        # between the change and the file's claimed birth) but below
        # si_fn_mismatch, which is bound to the individual file rather than to
        # a time window shared by every file created within it.
        "id":       "eventlog_clock_window",
        "weight":   45,
        "artefact": "EventLog",
        "reason":   ("File's claimed creation time falls inside a window during "
                     "which the Windows Event Log records the system clock as "
                     "having been rolled backwards"),
        "detail":   lambda r: (lambda d: f"clock displaced by {d}" if d else "")(
                        _days(_get(r, "eventlog_jump_secs"))),
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

    # correlation premium: evidence from more than one artefact family
    if len(artefacts) > 1:
        score += CORROBORATION_BONUS
        reasons.append(f"[+{CORROBORATION_BONUS}] Corroborated across independent "
                       f"artefacts ({', '.join(sorted(artefacts))}) - "
                       f"tampering is unlikely to be a single-source artefact")

    return min(score, 100), band_for(min(score, 100)), reasons, sorted(artefacts)


def derive_missing_signals(df):
    """
    Some feature files predate later signals. Where the underlying evidence is
    present, derive the signal rather than defaulting it to zero: 'tested and
    did not fire' is a result, 'never tested' is a gap in the method.
    """
    if "usn_claim_conflict" not in df.columns and {"si_created", "usn_first_seen"} <= set(df.columns):
        si  = pd.to_datetime(df["si_created"], errors="coerce")
        usn = pd.to_datetime(df["usn_first_seen"], errors="coerce")
        gap = (si - usn).dt.total_seconds()
        df["usn_claim_gap_s"]    = gap
        df["usn_claim_conflict"] = (gap < -1).astype(int)
        print("  derived usn_claim_conflict from $SI vs first USN entry")
    return df


# ==================================================================
# RUN
# ==================================================================
ap = argparse.ArgumentParser()
ap.add_argument("--exp", choices=sorted(EXPERIMENTS), default="A",
                help="which controlled experiment to score")
args = ap.parse_args()

cfg = EXPERIMENTS[args.exp]
features_path = cfg["features"]
results_dir   = ROOT / "results"
results_dir.mkdir(exist_ok=True)
scored_path   = ROOT / "data" / "processed" / f"scored_files_{args.exp}.csv"
scored_path.parent.mkdir(parents=True, exist_ok=True)

print(f"{cfg['label']}")
print(f"Reading {features_path}")

df = pd.read_csv(features_path)
df = derive_missing_signals(df)

# make sure every signal column exists and is numeric
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

lines = [f"# Tampering Assessment - Reason Reports ({args.exp})", "",
         f"_{cfg['label']}_", ""]
lines.append(f"Files analysed: **{len(df)}**  |  Flagged: **{len(flagged)}**  |  "
             f"Clean: **{len(df) - len(flagged)}**")
lines.append("")
lines.append("Scores are produced by correlating independent forensic indicators. "
             "Each line below states the evidence and the points it contributed, "
             "so every verdict can be traced back to a specific artefact.")
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
    lines.append(f"_...and {len(flagged) - 25} further flagged files "
                 f"(full detail in scored_files_{args.exp}.csv)._")

(results_dir / f"reason_reports_{args.exp}.md").write_text("\n".join(lines), encoding="utf-8")

# ------------------------------------------------------------------
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
ax.set_title(f"{cfg['label']} (n={len(df)})", fontsize=9)
plt.tight_layout()
plt.savefig(results_dir / f"score_summary_{args.exp}.png", dpi=150)

# ------------------------------------------------------------------
# Console summary
# ------------------------------------------------------------------
print(f"\nFiles scored: {len(df)}\n")

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
print("Saved ->", results_dir / f"reason_reports_{args.exp}.md")
print("Saved ->", results_dir / f"score_summary_{args.exp}.png")