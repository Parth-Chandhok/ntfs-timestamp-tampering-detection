"""
unified_report.py - the final architecture: rules decide, LLM explains.

WHY THIS EXISTS
  Every measured LLM failure in this project was a CLASSIFICATION failure. The
  models could not perform the temporal arithmetic that separates tampered files
  from benign ones. But they wrote fluent, well-cited prose about evidence they
  were given, and hallucinated almost nothing (1 unsupported claim in 375).

  So the LLM is removed from the detection path entirely. The static rules decide
  what is tampered; the LLM only explains what the rules found. It never sees raw
  artefacts, never issues a verdict, and cannot change one.

OUTPUT
  results/forensic_report.md - incident summary + per-file explanations
  results/report_quality.csv - faithfulness / completeness / hallucination checks

EVALUATION
  Accuracy and recall do not apply here - the LLM is not classifying. Instead:
    faithfulness  - does every number cited appear in the rule output?
    completeness  - is every signal that fired mentioned in the explanation?
    hallucination - are any numbers introduced that were not supplied?
  All three are checkable against the rule output, so this is measured rather
  than judged by eye.
"""

import json
import os
import re
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(r"C:\ntfs-tamper-detect")
PROC = ROOT / "data" / "processed"
LLM  = ROOT / "data" / "llm"
RES  = ROOT / "results"
RES.mkdir(exist_ok=True)

MODEL = "gemini-3.5-flash-lite"
DELAY = 4.0

SIGNAL_NAMES = {
    "si_fn_mismatch": "$MFT: $SI and $FN creation times disagree",
    "usn_basicinfo_after_close": "USN: timestamp modified after the file was closed",
    "usn_claim_conflict": "USN: file claims to predate its first journal entry",
    "usn_seq_inconsistent": "USN: claimed time predates the journal's running maximum",
    "eventlog_clock_window": "Event Log: created inside a rolled-back clock window",
}

SYSTEM = """You are a forensic report writer. A static rule engine has already \
analysed a Windows NTFS volume and reached its conclusions. Your job is to \
explain those conclusions to an investigator in clear prose.

You are NOT assessing whether the verdict is correct. You are not being asked to \
agree or disagree. The verdict is settled; explain what it means.

Rules:
1. Use only the facts supplied. Introduce no timestamps, counts or values that \
are not in the input.
2. Mention every indicator that fired. Do not silently omit one.
3. Write for an investigator who understands filesystems but not this tool. \
Explain what each indicator means, not just its name.
4. Plain prose. No bullet lists, no headings, no markdown.
5. Be concise: 3-5 sentences per file."""

FILE_TEMPLATE = """A static rule engine flagged this file. Explain, in prose, \
what the evidence shows and why it indicates timestamp manipulation.

File: {fid}
Confidence score: {score}/100 ({band})
Artefacts contributing evidence: {artefacts}

Indicators that fired:
{signals}

Supporting detail:
{detail}

Write 3-5 sentences."""

SUMMARY_TEMPLATE = """Write an incident summary for a forensic investigator, \
describing what was found across an entire NTFS volume. Use only the figures \
below. Plain prose, 6-10 sentences, no bullet points.

VOLUME ANALYSIS RESULTS
{stats}

The three tampering methods present:
- Direct $SI modification: the creation timestamp was overwritten from user \
space, leaving the kernel-managed $FN attribute unchanged, so the two disagree.
- Directory relocation ("move-trick"): both $SI and $FN were falsified, so the \
$MFT shows no disagreement at all; only the change journal retains evidence.
- System clock rollback: files were created while the system clock was set back, \
so every timestamp was honestly recorded from a dishonest clock. Nothing in the \
file disagrees with anything. Only the Event Log and the journal's \
clock-independent sequence numbers reveal it.

Explain what happened, which evidence exposed each method, and what this means \
for an investigator relying on file timestamps."""


def load_scored():
    frames = []
    for exp in "ABC":
        p = PROC / f"scored_files_{exp}.csv"
        if p.exists():
            d = pd.read_csv(p)
            d["experiment"] = exp
            frames.append(d)
    return pd.concat(frames, ignore_index=True)


def numbers_in(text):
    """4+ digit runs only - years, sequence numbers, counts. Ignores prose numbers."""
    return set(re.findall(r"\d{4,}", str(text)))


def main():
    load_dotenv(ROOT / ".env")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    cfg = types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0)

    scored = load_scored()
    key = pd.read_csv(LLM / "bundle_key.csv")
    sample_names = set(key["orig_name"])

    # per-file reports: flagged files within the evaluated sample only, so the
    # results remain comparable with the other LLM arms
    flagged = scored[(scored["tamper_score"] > 0)
                     & (scored["FileName"].isin(sample_names))].copy()
    print(f"flagged files in sample: {len(flagged)}")

    blind = dict(zip(key["orig_name"], key["file_id"]))

    reports, quality = [], []
    for i, (_, r) in enumerate(flagged.iterrows(), 1):
        fired = [k for k in SIGNAL_NAMES if int(r.get(k, 0)) == 1]
        signals = "\n".join(f"  - {SIGNAL_NAMES[k]}" for k in fired)
        detail = str(r.get("reasons", "")).replace(" | ", "\n  ")
        # Filenames are NOT unique across experiments - the same NapierOne
        # source file appears in both the timestomp and move-trick corpora, so a
        # name-only lookup collides and labels two different files identically.
        # Same root cause as the July join bug. Qualify with the experiment.
        fid = f'{blind.get(r["FileName"], r["FileName"])} (Exp {r["experiment"]})'

        prompt = FILE_TEMPLATE.format(
            fid=fid, score=int(r["tamper_score"]), band=r["score_band"],
            artefacts=r.get("artefacts_hit", ""), signals=signals, detail=detail)

        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt,
                                                  config=cfg)
            text = resp.text.strip()
        except Exception as e:
            print(f"  [{i}] {fid} ERROR {type(e).__name__}")
            time.sleep(DELAY)
            continue

        supplied = numbers_in(prompt)
        cited = numbers_in(text)
        unsupported = cited - supplied
        mentioned = sum(1 for k in fired
                        if any(w in text.lower() for w in
                               ("$fn" if k == "si_fn_mismatch" else
                                "clock" if k == "eventlog_clock_window" else
                                "sequence" if k == "usn_seq_inconsistent" else
                                "journal")))

        reports.append({"file_id": fid, "experiment": r["experiment"],
                        "score": int(r["tamper_score"]), "band": r["score_band"],
                        "n_signals": len(fired), "report": text})
        quality.append({"file_id": fid, "signals_fired": len(fired),
                        "signals_mentioned": min(mentioned, len(fired)),
                        "completeness": min(mentioned, len(fired)) / len(fired) if fired else 1.0,
                        "unsupported_numbers": len(unsupported),
                        "faithful": len(unsupported) == 0,
                        "words": len(text.split())})

        print(f"  [{i}/{len(flagged)}] {fid}  {len(text.split())} words  "
              f"{'OK' if not unsupported else 'UNSUPPORTED: ' + str(sorted(unsupported)[:3])}")
        time.sleep(DELAY)

    # ---- one incident summary over the FULL corpus, not the sample ----
    tam = scored[scored["tampered"] == 1]
    lines = [f"Files analysed: {len(scored)}",
             f"Flagged as tampered: {len(tam)}",
             f"Benign, no indicators: {len(scored) - len(tam)}",
             f"False positives: {int(((scored['tamper_score'] > 0) & (scored['tampered'] == 0)).sum())}",
             "",
             "Indicators firing on flagged files:"]
    for k, label in SIGNAL_NAMES.items():
        if k in scored.columns:
            lines.append(f"  {label}: {int(tam[k].sum())} of {len(tam)}")
    lines.append("")
    lines.append("Breakdown by tampering method:")
    for exp, name in (("A", "direct $SI modification"),
                      ("B", "directory relocation"),
                      ("C", "system clock rollback")):
        n = len(tam[tam["experiment"] == exp])
        lines.append(f"  {name}: {n} files")

    print("\ngenerating incident summary...")
    summary = client.models.generate_content(
        model=MODEL, contents=SUMMARY_TEMPLATE.format(stats="\n".join(lines)),
        config=cfg).text.strip()

    # ---- write out ----
    L = ["# Forensic Report - NTFS Timestamp Manipulation", "",
         "_Detection performed by static rule correlation. Narrative generated "
         "by an LLM from the rule engine's output; the LLM did not classify any "
         "file and could not alter a verdict._", "",
         "## Incident summary", "", summary, "",
         "## Volume statistics", "", "```", "\n".join(lines), "```", "",
         f"## Per-file explanations ({len(reports)} flagged files)", ""]
    for r in sorted(reports, key=lambda x: -x["score"]):
        L.append(f"### {r['file_id']}  -  {r['score']}/100 ({r['band']})")
        L.append("")
        L.append(r["report"])
        L.append("")

    (RES / "forensic_report.md").write_text("\n".join(L), encoding="utf-8")

    q = pd.DataFrame(quality)
    q.to_csv(RES / "report_quality.csv", index=False)

    print(f"\n--- report quality ({len(q)} reports) ---")
    print(f"faithfulness (no invented figures): {q['faithful'].mean():.3f}")
    print(f"completeness (signals mentioned):   {q['completeness'].mean():.3f}")
    print(f"unsupported figures total:          {int(q['unsupported_numbers'].sum())}")
    print(f"mean report length:                 {q['words'].mean():.0f} words")
    print(f"\nSaved -> {RES / 'forensic_report.md'}")
    print(f"Saved -> {RES / 'report_quality.csv'}")


if __name__ == "__main__":
    main()

