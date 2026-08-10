# Results Summary - Framework Evaluation

Two experiments, each a different tampering scenario:

- **Experiment A** - attack where the primary signal (SI/FN mismatch) fires.
- **Experiment B** - attack that DEFEATS the primary signal, isolating the value of correlation.

## Headline comparison

| Experiment   | Tampering               |   Files | SI/FN caught   | USN caught   | Framework caught (>=30)   |   Mean score | HIGH+ band   |
|:-------------|:------------------------|--------:|:---------------|:-------------|:--------------------------|-------------:|:-------------|
| A (808)      | PowerShell (SI only)    |     404 | 404/404        | 404/404      | 404/404                   |          100 | 404/404      |
| B (100)      | Move-trick (both faked) |     100 | 0/100          | 100/100      | 100/100                   |           60 | 100/100      |

## What it shows

- Experiment A: all signals fire, mean score 100/100.
- Experiment B: the SI/FN rule catches 0/100 - the single-artefact approach (Alji & Chougdali, 2019) is blinded.
- The framework still catches 100/100 via USN evidence, mean score 60/100.
- The score drop from A to B is the measurable cost of the attack: detection degrades gracefully, it does not fail.