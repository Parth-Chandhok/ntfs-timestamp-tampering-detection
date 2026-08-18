import datetime
"""
run_llm_triage.py - sends evidence bundles to the LLM and records verdicts.

USAGE
  python src/llm/run_llm_triage.py --arm llm       (evidence only)
  python src/llm/run_llm_triage.py --arm hybrid    (evidence + rule verdict to critique)
  python src/llm/run_llm_triage.py --arm ablation  (Exp C only, Event Log withheld)
  python src/llm/run_llm_triage.py --arm llm --limit 5    (test run)

DESIGN
  - Temperature 0 and a pinned model version, so the run is reproducible.
  - Every raw response is written to disk before parsing. Re-scoring never
    requires re-calling the API, and every verdict has an audit trail.
  - Resumable: bundles already present in the output file are skipped, so an
    interrupted run continues rather than restarting.
  - Per-call latency is recorded. Detection latency is one of the supervisor's
    KPIs and is the clearest operational difference between the arms.
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

import prompts

ROOT = Path(r"C:\ntfs-tamper-detect")
LLM  = ROOT / "data" / "llm"

MODEL = "gemini-3.5-flash-lite"
# Free tier for gemini-3.5-flash allows 20 requests per minute. Pacing is
# measured from the START of each call, not the end: response latency (15-35s)
# already consumes most of the window, so sleeping a fixed delay AFTER each
# response lets calls bunch against the limit.
RPM         = 12                # below the 15/min ceiling for flash-lite
MIN_SPACING = 60.0 / RPM
MAX_RETRIES = 5
RUN_START = datetime.datetime.now(datetime.timezone.utc).isoformat()


def load_bundles():
    with open(LLM / "bundles.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def strip_eventlog(text):
    """Remove the Event Log section for the ablation arm."""
    marker = "SYSTEM EVENT LOG"
    idx = text.find(marker)
    if idx == -1:
        return text
    return text[:idx].rstrip() + "\n\n(System event log not available for this volume.)"


def build_prompt(arm, b):
    if arm == "hybrid":
        reasons = str(b.get("rule_reasons", "")).replace(" | ", "\n  - ")
        return prompts.HYBRID_ARM_TEMPLATE.format(
            evidence=b["evidence_text"],
            rule_band=b.get("rule_band", "unknown"),
            rule_score=b.get("rule_score", 0),
            rule_reasons="  - " + reasons)
    if arm == "ablation":
        return prompts.ABLATION_TEMPLATE.format(
            evidence=strip_eventlog(b["evidence_text"]))
    return prompts.LLM_ARM_TEMPLATE.format(evidence=b["evidence_text"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["llm", "hybrid", "ablation"])
    ap.add_argument("--limit", type=int, default=None,
                    help="process only the first N bundles (for testing)")
    ap.add_argument("--model", default=MODEL,
                    help="override model; output tagged so runs do not collide")
    ap.add_argument("--exp", default=None, choices=["A", "B", "C"],
                    help="restrict to one experiment")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    model = args.model
    bundles = load_bundles()
    if args.exp:
        bundles = [b for b in bundles if b['experiment'] == args.exp]
        print(f'restricted to experiment {args.exp}: {len(bundles)} bundles')
    if args.arm == "ablation":
        bundles = [b for b in bundles if b["experiment"] == "C"]
        print(f"ablation arm: {len(bundles)} Experiment C bundles")
    if args.limit:
        bundles = bundles[:args.limit]

    tag = args.arm
    if args.model != MODEL:
        tag += '_' + args.model.replace('gemini-', '').replace('.', '')
    if args.exp:
        tag += f'_exp{args.exp}'
    out_path = LLM / f"responses_{tag}.jsonl"
    done = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["file_id"])
                except Exception:
                    pass
        print(f"resuming: {len(done)} already processed")

    todo = [b for b in bundles if b["file_id"] not in done]
    print(f"model {model} | arm {args.arm} | to process: {len(todo)}")
    if not todo:
        print("nothing to do")
        return

    # Latency (15-35s per call) dominates, not the rate limit, so estimate on
    # observed response time rather than the pacing interval.
    est = len(todo) * 25 / 60
    print(f"estimated time: ~{est:.0f} min (latency-bound, not rate-bound)\n")

    config = types.GenerateContentConfig(
        system_instruction=prompts.SYSTEM_INSTRUCTION,
        temperature=0,
        response_mime_type="application/json",
        response_schema=prompts.RESPONSE_SCHEMA,
    )

    ok = err = 0
    with open(out_path, "a", encoding="utf-8") as fout:
        for i, b in enumerate(todo, 1):
            prompt = build_prompt(args.arm, b)
            rec = {"file_id": b["file_id"], "experiment": b["experiment"],
                   "arm": args.arm, "model": model}
            rec["run_started_utc"] = RUN_START

            # Retry on rate-limit rejections rather than recording them as
            # results. A 429 returns in ~0.3s, so without backoff the loop
            # accelerates into the limit instead of waiting it out.
            verdict = None
            for attempt in range(MAX_RETRIES):
                wait_until = time.perf_counter() + MIN_SPACING
                t0 = time.perf_counter()
                try:
                    resp = client.models.generate_content(
                        model=model, contents=prompt, config=config)
                    rec["latency_s"] = round(time.perf_counter() - t0, 3)
                    rec["raw"] = resp.text
                    rec["tokens_in"]  = resp.usage_metadata.prompt_token_count
                    rec["tokens_out"] = resp.usage_metadata.candidates_token_count
                    rec["attempts"] = attempt + 1
                    try:
                        rec["parsed"] = json.loads(resp.text)
                        verdict = rec["parsed"].get("classification", "?")
                    except json.JSONDecodeError:
                        rec["parse_error"] = True
                        verdict = "PARSE_FAIL"
                    ok += 1
                    break
                except Exception as e:
                    msg = str(e)
                    # 429 = quota exhausted, 503 = model overloaded. Both
                    # are transient; a 503 says nothing about your limits,
                    # only about current server demand.
                    if any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                        backoff = 60 * (attempt + 1)
                        print(f"      rate limited, waiting {backoff}s "
                              f"(attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(backoff)
                        continue
                    rec["latency_s"] = round(time.perf_counter() - t0, 3)
                    rec["api_error"] = f"{type(e).__name__}: {e}"
                    verdict = "API_ERROR"
                    err += 1
                    break
            if verdict is None:
                rec["api_error"] = "rate limited after all retries"
                rec["latency_s"] = 0.0
                verdict = "RATE_LIMITED"
                err += 1
            rec.setdefault("latency_s", 0.0)

            fout.write(json.dumps(rec, default=str) + "\n")
            fout.flush()

            print(f"  [{i:>3}/{len(todo)}] {b['file_id']:<18} "
                  f"exp {b['experiment']}  {verdict:<20} "
                  f"{rec['latency_s']:>6.2f}s")

            # space from call START, so latency counts toward the interval
            remaining = wait_until - time.perf_counter()
            if i < len(todo) and remaining > 0:
                time.sleep(remaining)

    print(f"\ncompleted: {ok} ok, {err} errors")
    print(f"Saved -> {out_path}")


if __name__ == "__main__":
    main()




