# Arm Comparison - Static Rules vs LLM Triage

All arms evaluated against the same ground-truth manifest on the same 150-file sample (75 tampered / 75 benign).
## Summary

| Arm | Scoring | n | Acc | Prec | Recall | F1 | FPR | Latency |
|---|---|---|---|---|---|---|---|---|
| rules | - | 150 | 0.973 | 0.949 | 1.000 | 0.974 | 0.053 | <0.01s |
| llm | lenient | 150 | 0.767 | 0.803 | 0.707 | 0.752 | 0.173 | 1.96s |
| llm | strict | 150 | 0.793 | 0.893 | 0.667 | 0.763 | 0.080 | 1.96s |
| hybrid | lenient | 150 | 0.753 | 1.000 | 0.507 | 0.673 | 0.000 | 2.17s |
| hybrid | strict | 150 | 0.747 | 1.000 | 0.493 | 0.661 | 0.000 | 2.17s |
| ablation | lenient | 62 | 0.613 | 0.522 | 0.480 | 0.500 | 0.297 | 1.76s |
| ablation | strict | 62 | 0.710 | 0.769 | 0.400 | 0.526 | 0.081 | 1.76s |


## Static rules (baseline)

- n 150 | accuracy **0.973** | precision 0.949 | recall 1.000 | F1 0.974 | FPR 0.053
- TP 75, TN 71, FP 4, FN 0

## LLM arm: llm

**lenient (SUSPICIOUS = detection)**

- n 150 | accuracy **0.767** | precision 0.803 | recall 0.707 | F1 0.752 | FPR 0.173
- TP 53, TN 62, FP 13, FN 22

**strict (LIKELY only)**

- n 150 | accuracy **0.793** | precision 0.893 | recall 0.667 | F1 0.763 | FPR 0.080
- TP 50, TN 69, FP 6, FN 25

Per-experiment recall (lenient scoring):

| Exp | tampered n | detected | recall | benign n | false pos | FPR |
|---|---|---|---|---|---|---|
| A | 25 | 25 | 1.000 | 38 | 5 | 0.132 |
| B | 25 | 25 | 1.000 | 0 | 0 | n/a |
| C | 25 | 3 | 0.120 | 37 | 8 | 0.216 |

Class distribution: BENIGN 84, LIKELY_TIMESTOMPING 56, SUSPICIOUS 10

Mean confidence when correct: **0.936**, when wrong: **0.873**. A model that is as confident when wrong as when right offers the analyst no usable signal from its own confidence score.

Hallucination check: **0/368** cited observations contain numeric values absent from the evidence bundle (**0.000**).

Mean latency: **1.96s** per file (total 4.9 min for 150 files).

## LLM arm: hybrid

**lenient (SUSPICIOUS = detection)**

- n 150 | accuracy **0.753** | precision 1.000 | recall 0.507 | F1 0.673 | FPR 0.000
- TP 38, TN 75, FP 0, FN 37

**strict (LIKELY only)**

- n 150 | accuracy **0.747** | precision 1.000 | recall 0.493 | F1 0.661 | FPR 0.000
- TP 37, TN 75, FP 0, FN 38

Per-experiment recall (lenient scoring):

| Exp | tampered n | detected | recall | benign n | false pos | FPR |
|---|---|---|---|---|---|---|
| A | 25 | 17 | 0.680 | 38 | 0 | 0.000 |
| B | 25 | 20 | 0.800 | 0 | 0 | n/a |
| C | 25 | 1 | 0.040 | 37 | 0 | 0.000 |

Class distribution: BENIGN 112, LIKELY_TIMESTOMPING 37, SUSPICIOUS 1

Mean confidence when correct: **0.979**, when wrong: **0.951**. A model that is as confident when wrong as when right offers the analyst no usable signal from its own confidence score.

Hallucination check: **1/375** cited observations contain numeric values absent from the evidence bundle (**0.003**).

  - `file_0077.html` unsupported ['1302']: The file's first USN journal entry (FileCreate) occurred on 2026-07-25 16:30:02.015235500, which is approximat...

Mean latency: **2.17s** per file (total 5.4 min for 150 files).

## LLM arm: ablation

**lenient (SUSPICIOUS = detection)**

- n 62 | accuracy **0.613** | precision 0.522 | recall 0.480 | F1 0.500 | FPR 0.297
- TP 12, TN 26, FP 11, FN 13

**strict (LIKELY only)**

- n 62 | accuracy **0.710** | precision 0.769 | recall 0.400 | F1 0.526 | FPR 0.081
- TP 10, TN 34, FP 3, FN 15

Per-experiment recall (lenient scoring):

| Exp | tampered n | detected | recall | benign n | false pos | FPR |
|---|---|---|---|---|---|---|
| C | 25 | 12 | 0.480 | 37 | 11 | 0.297 |

Class distribution: BENIGN 39, LIKELY_TIMESTOMPING 13, SUSPICIOUS 10

Mean confidence when correct: **0.930**, when wrong: **0.815**. A model that is as confident when wrong as when right offers the analyst no usable signal from its own confidence score.

Hallucination check: **0/105** cited observations contain numeric values absent from the evidence bundle (**0.000**).

Mean latency: **1.76s** per file (total 1.8 min for 62 files).
