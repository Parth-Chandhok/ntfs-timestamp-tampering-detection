# Unified Evaluation — All Controlled Experiments

A single scoring engine, a single rule table and a single detection threshold applied to every tampering method, evaluated as one pooled population.

## Pooled result

- Files: **1308** (704 tampered, 604 benign)
- Accuracy: **1.000**
- Precision: **1.000**
- Recall: **1.000**
- F1: **1.000**
- False positive rate: **0.000**
- Confusion: TP 704, TN 604, FP 0, FN 0

## Per-experiment breakdown

| Exp | Tampering | n | Recall | FPR | Mean score (tampered) | Band |
|---|---|---|---|---|---|---|
| A | PowerShell $SI timestomp | 808 | 1.000 | 0.000 | 100.0 | VERY HIGH |
| B | Move-trick ($SI and $FN both faked) | 100 | 1.000 | n/a | 60.0 | HIGH |
| C | System clock rollback | 400 | 1.000 | 0.000 | 45.0 | MEDIUM |

## Which artefact caught which attack

Signals firing on tampered files. The zeros are the finding: each tampering method defeats a different artefact, and no single artefact survives all three.

| Exp | n | $MFT SI/FN | USN BasicInfo | USN claim | Event Log |
|---|---|---|---|---|---|
| A | 404 | 404/404 | 404/404 | 404/404 | 0/404 |
| B | 100 | 0/100 | 100/100 | 100/100 | 0/100 |
| C | 200 | 0/200 | 0/200 | 0/200 | 200/200 |

## Interpretation

Detection accuracy holds across all three tampering methods while the confidence score falls (100 → 60 → 45) as successive attacks silence more artefacts. That decline is intended behaviour: the score reports how much independent evidence supports the verdict, so a finding resting on one artefact is correctly reported at lower confidence than one corroborated by three. A single-artefact detector — such as the $MFT-only approach of Alji & Chougdali (2019) — records zero detections for Experiments B and C.

**Limitations.** Experiment B has no benign control group, so the pooled false-positive rate is derived from the controls of Experiments A and C only. All tampering was injected under controlled conditions against a known ground-truth manifest; performance on real-world adversarial tampering is unvalidated.