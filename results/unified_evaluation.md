# Unified Evaluation - All Controlled Experiments

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
| B | Move-trick (SI and FN both faked) | 100 | 1.000 | n/a | 95.0 | VERY HIGH |
| C | System clock rollback | 400 | 1.000 | 0.000 | 95.0 | VERY HIGH |

## Which indicator caught which attack

Signals firing on tampered files. The zeros are the finding: each tampering method defeats a different indicator.

Note that USN seq is distinct from the other two USN entries: it reads the journal's clock-INDEPENDENT sequence numbers rather than its timestamps, which is why it survives clock manipulation where the timestamp-based USN signals do not.

| Exp | n | $MFT SI/FN | USN BasicInfo | USN claim | USN seq | Event Log |
|---|---|---|---|---|---|---|
| A | 404 | 404/404 | 404/404 | 404/404 | 404/404 | 0/404 |
| B | 100 | 0/100 | 100/100 | 100/100 | 100/100 | 0/100 |
| C | 200 | 0/200 | 0/200 | 0/200 | 200/200 | 200/200 |

## Interpretation

Detection holds across all three tampering methods with no false positives. A single-artefact detector - such as the $MFT-only approach of Alji & Chougdali (2019) - records zero detections for Experiments B and C.

The USN sequence signal refines rather than contradicts the case for a third artefact. Clock rollback leaves the journal's TIMESTAMPS internally consistent, so timestamp-based USN rules are defeated; but USN sequence numbers are byte offsets into an append-only journal and cannot be rewound by changing the clock, so the inconsistency survives in a field the attacker cannot reach. The finding is therefore not simply that more artefacts are better, but that a naive reading of an artefact can miss what a careful reading recovers. The Event Log remains necessary: it supplies direct evidence of when the clock moved and by how much, where the sequence signal can only infer that something is inconsistent.

**Limitations.** Experiment B has no benign control group, so the pooled false-positive rate derives from Experiments A and C only. The USN sequence signal cannot distinguish tampering from a legitimately old file copied onto the volume, which produces an identical pattern; corroboration from other artefacts is required. All tampering was injected under controlled conditions against a known ground-truth manifest; performance on real-world adversarial tampering is unvalidated.