### 2026-06-19 — Went with Windows 10 Pro (not Home)
NTFS works the same on both, so the file system isn't the reason. I picked
Pro because it lets me use Group Policy to switch off background stuff like
Search indexing and SysMain. Those quietly touch files, which would mess up
my "benign" samples. Pro keeps my ground-truth data clean.


### 2026-06-20 — Everything runs in an isolated VirtualBox VM
The VM can be snapshotted and rolled back to a known clean state between
dataset runs, which keeps myexperiments repeatable.
This also covers the ethics side — software-only,fully contained, defensive purpose.


### 2026-06-22 — Generating my own synthetic data
I create the files myself, so I know exactly which ones are tampered. That
gives me trustworthy ground-truth labels — something I couldn't guarantee
with random real-world files. Same approach as the 2019 paper I'm extending.


### 2026-06-23 — 20 files to start: 10 tampered, 10 benign
Small enough that I can check every file by hand and catch mistakes early,
and balanced so the baseline model isn't biased. I'll scale up later once
the pipeline is proven.


### 2026-06-23 — Tampering done with PowerShell CreationTime
Setting a file's CreationTime through PowerShell changes the $SI timestamp
but can't reach $FN (only the kernel writes that). So the two end up
disagreeing — which is exactly the real-world timestomping signature. No
external tool needed for the baseline. I'll add SetMACE later to test the
harder case where both $SI and $FN are faked.


### 2026-06-24 — Using MFTECmd instead of writing my own MFT parser
The $SI and $FN timestamps live in the MFT, a dense binary file you can't
just open and read. MFTECmd (Eric Zimmerman) pulls them out into a CSV.
I chose it over a custom parser for two reasons: writing a correct parser
would eat weeks I don't have, and MFTECmd is court-validated, so my
extracted timestamps are defensible. My original work is the ML detection,
not re-inventing the parser.


### 2026-06-24 — MFT extraction confirmed working
Ran MFTECmd on C:\$MFT — 338,651 records, ~27 seconds. Output saved to
data/raw/mft_raw.csv. Screenshot: screenshots/mft_extraction_success.png.
command: Import-Csv 'C:\ntfs-tamper-detect\data\raw\mft_raw.csv' | Where-Object FileName
-like 'file_*' | Select-Object FileName, Created0x10, Created0x30 | Format-Table -AutoSize


### 2026-06-27 — $SI/$FN mismatch confirmed (this is the whole project)
Looked at my 20 files in the MFT extract. Tampered files show an old $SI
date (Created0x10) but today's $FN date (Created0x30) — they disagree.
Benign files match. The fingerprint my detector is built on is real and
visible. Screenshot: screenshots/si_fn_mismatch_visible.png.

### 2026-06-27 — Feature extraction working, signal verified
build_features.py turns $SI/$FN timestamps into delta_created_s + a
si_fn_mismatch flag, joined to labels. Crosstab is a clean diagonal —
flag matches ground truth on all 20 files (10/10 both classes). Tampered
files show ~5-year deltas, benign show 0. features_v1.csv saved.


### 2026-06-27 — Quirk found: blank $FN means "no mismatch"
MFTECmd leaves the Created0x30 ($FN) column blank when it equals $SI, rather
than repeating the date. So in my feature code, a blank $FN = no tampering,
not missing data. Worth handling carefully so it doesn't get mislabelled.

### 2026-07-17 — Prototype validated on real corpus
Ran full pipeline on 808 NapierOne files (404 timestomped via PowerShell).
MFTECmd extract → $SI/$FN mismatch rule → joined to ground-truth manifest.
Result: perfect separation (404/404 both classes, zero errors).
Note: join initially double-counted because benign and tampered copies share
filenames; fixed by filtering ParentPath to the tampered folder only.

### 2026-07-18 — USN Journal captures the tampering act
Tampered files show extra BasicInfoChange records ~3.5s after their creation
burst (6 records = 3 timestamp properties × BasicInfoChange+Close). Benign
files show none. Independent of $SI/$FN comparison — survives SetMACE.
Limitation: journal is a 32MB circular buffer; older history is lost.


### 2026-07-19 — Three-signal correlation working
build_features_usn.py: 808/808 matched in both MFT and USN. All three signals
(si_fn_mismatch, usn_basicinfo_after_close, usn_claim_conflict) achieve 404/404
separation. Signals-fired table shows only 0 or 3 — perfect agreement, no
disagreement cases. Expected: one uniform tampering method trips all three.
Discriminative value of USN signals to be demonstrated via SetMACE, which
defeats $SI/$FN but not journal history.


### 2026-07-21 — Confidence-score engine complete
confidence_score.py fuses 3 signals into 0-100 score + per-file reason reports.
Weights: SI/FN 40, USN BasicInfoChange 35, USN claim conflict 25, plus a 15-pt
corroboration bonus when evidence spans multiple artefacts (MFT+USN).
Result on 808 files: benign mean 0.0, tampered mean 100.0, all flagged files
corroborated MFT+USN. Outputs: scored_files.csv, reason_reports.md, score_summary.png.
Caveat: uniform tampering method means all signals agree; SetMACE test next.

### 2026-07-22 — Dataset design: multi-tamper files (planned)
Real attacks combine techniques, so single-tamper-per-file is unrealistic.
Plan: once each tamper detector exists, generate files with random combinations
(0-4 tampers) and a per-tamper-type manifest. Confidence engine already supports
this (sums whatever signals fire). Deferred until detectors are built, so tampers
aren't injected before they can be detected.


### 2026-07-25 — Move-trick defeats single-rule detection; correlation survives
Faked BOTH $SI and $FN via the move-trick (set $SI, then directory move makes the
kernel propagate it into $FN) on 100 NapierOne files. Result:
  - si_fn_mismatch caught 0/100 — the prior single-artefact approach is BLIND.
  - USN correlation caught 100/100 (BasicInfoChange-after-close + claim-conflict).
Demonstrates the framework degrades gracefully where a single rule fails. This is
the core evidence that multi-artefact correlation beats single-signal detection.
Move-trick works on the system drive, unlike SetMACE.


### 2026-08-01 — Third artefact: Windows Event Log, not $LogFile
$LogFile was the plan, but it's another file-level artefact, so it gives a third
view of the same layer instead of a new one. More importantly, a clock change
isn't a filesystem operation, so it can't see one at all. The Event Log sits at
the system level and records the clock being moved — a genuinely different angle.
Parsers for $LogFile do exist (LogFileParser, dfir_ntfs), so this wasn't a tooling
limitation. See the future-work note below.
Gotcha: Event ID 1 isn't unique — FilterManager uses it too. Filter on provider
AND id.

### 2026-08-08 — Experiment C: clock rollback beats every file-level artefact
Roll the system clock back 3 years, create files normally, put the clock back.
The timestamps are then honestly recorded — from a clock that was lying. $SI and
$FN agree, USN agrees, nothing disagrees, because nobody lied about the file.
400 files from NapierOne, seed 42. 200 under the true clock as controls, 200 under
the fake clock, same code path — the clock is the only variable. Written
byte-for-byte rather than copied, because Copy-Item preserves the source creation
time and would have faked a mismatch unrelated to the clock. Stopped VBoxService
and w32time so nothing resynced. Tamper window: 4.8 seconds.
Result: si_fn_mismatch 0/200, both USN signals 0/200, eventlog_clock_window
200/200 with zero false positives. Second graceful-degradation result, and a
stronger one — here both prior artefacts fail, not just one.

### 2026-08-08 — Clock jumps must be paired by size, not time order
Real bug, found and fixed. A backward jump gets logged under the already-rolled-
back clock, so it sits years out of sequence next to its own restore event.
Sorting chronologically and scanning forward fails. Pairing has to match
mirror-image sizes, minimum 30 days.
Why 30 days: normal VM noise tops out around 8 days (suspend/resume). The tamper
is 1,095 days. Nothing sits between them.
Side finding: the Event Log ends up non-monotonic — two 2023-dated entries in an
otherwise 2026 log. That's itself an indicator, and harder to scrub than file
timestamps. Possible future signal.


### 2026-08-08 — Event Log signal weighted 45 (MEDIUM band)
Decided the weight before looking at what band it produced, to avoid tuning the
number to get the answer I wanted.
For: clock changes are rare, deliberate, need admin, and the rule requires the
file's claimed birth to fall inside the window — not just that a jump happened.
Against: not file-specific (every file born in that window gets flagged), and real
machines do have big legitimate corrections — dead CMOS battery, timezone errors.
So Experiment C lands at MEDIUM, not HIGH. That's correct: one uncorroborated
artefact deserves less confidence than three agreeing ones, however accurate it
was here. Calling it HIGH off a single signal would be overclaiming.


### 2026-08-08 — One scoring engine instead of copies
confidence_score.py and confidence_score_movetrick.py were near-duplicates of the
same rule table. Change a weight in one, forget the other, and the experiments
stop being comparable. Merged into one engine with an experiment flag:
  python src/model/confidence_score.py --exp A|B|C
Same engine, rules and threshold across all three, so the scores mean the same
thing. Also added derive_missing_signals() — where an older feature file lacks a
newer signal but the evidence is there, derive it rather than default to zero.
"Tested and didn't fire" is a result. "Never tested" is a gap.


### 2026-08-08 — Unified evaluation
Pooled all three experiments into one population: 1,308 files, 704 tampered.
One engine, one threshold (1 — any evidence counts; higher would just be tuning
the cutoff to suit Experiment C).
Result: TP 704, TN 604, FP 0, FN 0.

  Exp  n    $MFT SI/FN  USN basic  USN claim  EventLog
  A   404    404/404     404/404    404/404     0/404
  B   100      0/100     100/100    100/100     0/100
  C   200      0/200       0/200      0/200   200/200

No artefact survives all three attacks; no attack escapes all three artefacts.
Alji & Chougdali (2019) use $MFT alone — column one — missing 300 of 704.
Confidence drops 100 → 60 → 45 as attacks silence more artefacts, but detection
holds at 100%. The drop is intended: the score reports how much independent
evidence backs the verdict.

Caveat: zero false positives is partly by construction — each experiment's
controls only met their own conditions, and B has no controls at all. The zeros
in the table aren't failures either; there was simply no clock tampering in A
and B for the Event Log to find.


### 2026-08-09 — $LogFile: evaluated properly, left as future work
Parsers exist, so skipping it was never about tooling. Left out because it's
another file-level artefact, it can't see clock changes so Experiment C stays
uncovered, and its ~64 MB buffer recycles in minutes — the records for all three
experiments were long gone by the time I looked, so adding it would mean
re-running everything.
Worth doing later: $LogFile logs moves and renames directly, so it would probably
catch the Experiment B move-trick more directly than the USN inference does.
Related work to cite: NTFS Log Tracker (blueangel) does pattern-based timestamp
manipulation detection on $LogFile and $UsnJrnl — single-artefact, pattern
matching, author admits false positives. Good contrast to this framework.



### 2026-08-10 — Experiment B has no benign controls (known limitation)
movetrick.ps1 generated 100 tampered files only. This was adequate for the
original question — does faking both $SI and $FN blind si_fn_mismatch? — which
needs only tampered files. It became a limitation once the experiments were
pooled into a unified evaluation reporting a false-positive rate: Experiment B
contributes to recall but not to FPR, so the pooled figure derives from A and C.
For the LLM triage sample, benign files are drawn from the shared NapierOne pool.
Generating dedicated matched controls is straightforward and is listed as future
work.


### 2026-08-11 — USN sequence numbers: the first signal that survives all three attacks
Every USN record has a sequence number — effectively a line number in the
journal. It only counts upward, the filesystem assigns it, and nothing an
attacker does can rewind it. Rolling the clock back doesn't touch it.

So: read the journal in sequence order, track the highest timestamp seen so far.
That's a floor. A record further down the journal can't honestly claim an earlier
date. My tampered files claim 2023 but sit at positions written after records
stamped 2026 — impossible.

Result: 404/404 (A), 100/100 (B), 200/200 (C), zero false positives. The gaps
came out at 1,660 / 1,587 / 1,096 days — that last one matching my injected
1,095-day rollback almost exactly.

First attempt failed, and why is worth knowing. I originally compared each file
against the median timestamp of its journal neighbours. Worked for A and B, but
caught only 1/200 in C — because the journal entries for files created under the
fake clock carry the fake time too. A tampered file's neighbours are other
tampered files, so I was measuring the lie against itself. The running maximum
avoids this: it only looks at earlier journal positions, written before the clock
was touched.

Scores: B goes 60 → 95, C goes 45 → 95. Both now backed by two artefacts.

This changes my story. I used to say confidence degrades (100 → 60 → 45) as
attacks silence more artefacts. Not true anymore. The better version: each attack
defeats a different set of signals, but every attack is caught by at least two
independent artefacts. And underneath that — this signal survives not because
it's a new artefact, but because it reads a field the attacker can't write.
Timestamps are attacker-controlled. Sequence numbers aren't.

Limitation: a genuinely old file copied onto the volume looks identical — old
claimed date, recent journal position. This signal can't tell them apart on its
own, so it needs corroboration.


### 2026-08-12 — LLM triage comparison: three arms, 150 files
Supervisor asked for rules vs LLM vs hybrid. Built a harness that bundles each
file's three artefacts into one readable case file, strips the giveaway filenames
so the model can't read the answer off the label, and sends it to Gemini with a
JSON schema for the verdict. Sample: 150 files, balanced 75 tampered / 75 benign.
Prompt deliberately never says what to look for — telling it would test
instruction-following, not reasoning.
  Rules      accuracy 0.97  recall 1.00  FPR 0.05
  LLM alone  accuracy 0.77  recall 0.71  FPR 0.17
  Hybrid     accuracy 0.75  recall 0.51  FPR 0.00
The averages hide the real story. By attack, LLM recall was A 1.00, B 1.00,
C 0.12. It matched the rules wherever something was visibly wrong in the file,
and fell apart where detection needed correlating across artefacts.
Two other measurements: hallucination was near-zero (1 unsupported claim in 375),
so the failure is reasoning rather than making things up. And confidence was
useless as a signal — 0.94 when right, 0.87 when wrong.


### 2026-08-12 — The hybrid arm made things worse
Showing the LLM the rule verdict and asking it to critique that verdict dropped
recall from 0.71 to 0.51. Files it had classified correctly on its own it got
wrong once shown the right answer. Precision hit 1.00 and FPR 0.00, but only
because it stopped accusing anything.
Prime suspect is my own prompt wording: "Your task is NOT to agree with it." That
is an instruction to disagree, and it disagreed. Recorded as a prompt artefact
rather than a property of hybrid pipelines — an honest limitation of the
experiment.


### 2026-08-12 — Ablation: removing evidence improved results
Ran Experiment C with the event log withheld. Recall went UP, 0.12 to 0.48,
though false positives rose too. The model did better without the clock evidence
than with it — so it wasn't ignoring that evidence, it was actively misreading it.
Checked the reasoning on the misses: it read the clock changes, considered them,
and dismissed them because the file's timestamps were internally consistent. That
consistency is exactly what clock rollback produces. It treated the fingerprint of
the attack as proof of innocence.


### 2026-08-13 — Bigger model, opposite failure
Free tier on gemini-3.5-flash caps at 20 requests/day, so all the above ran on
flash-lite. Paid $10 to test whether the Experiment C failure was a small-model
limitation. Ran 124 calls on the reasoning model.
Result: recall 1.00, FPR 1.00. It flagged 61 of 62 files. Caught every tampered
file by accusing everything.
So both tiers failed, in opposite directions. The lite model read consistency as
innocence and under-flagged. The reasoning model read "this volume had a clock
rollback" as guilt and over-flagged. Neither did the file-level test: does THIS
file's claimed creation fall inside the rollback window?
Cost note: ~$0.072 per call vs a fraction of a cent for lite, and 29s vs 1.8s.
50x the price, 16x slower, worse accuracy.
An early 2-file test on the reasoning model looked like a success — but both files
were tampered. A model that flags everything scores 2/2. The benign controls are
what exposed it, which is a decent argument for balanced sampling.


### 2026-08-14 — The failure is arithmetic, not comprehension
Supervisor asked WHY the LLM underperforms, not by how much. Tested it properly.
The bundle previously listed clock changes as volume-wide context and left the
model to work out whether this file's birth date fell inside one. Added a single
line stating it outright: "this file's claimed creation falls INSIDE / OUTSIDE a
window during which the clock was set backwards." No prompt text changed.
Result on the lite model: recall 0.12 -> 1.00, FPR 0.216 -> 0.000, accuracy 1.000.
TP 25, TN 37, FP 0, FN 0.
And it reasoned properly rather than parroting the hint — cited all three
artefacts, and independently invoked the journal's running maximum ("the highest
prior timestamp is 2026 while the file claims 2023"). It understood monotonic
journal ordering all along. It just couldn't work out which files to apply it to.
The discriminating computation is interval containment: a 4.8-second window
against a 3-year anomaly. Rules compute that exactly; LLMs approximate it.
This is the empirical case for the architecture the supervisor proposed — rules
in the detection path, LLM in the explanation path.
The lite model with the join also beats the reasoning model without it, at 1/50th
the cost and 14x the speed.
Honest note: supplying the correlation is a concession to the LLM. Work moved
from the model to the pipeline. It shows the failure was arithmetic, but it also
shows the LLM needs the detector's help to succeed.


### 2026-08-14 — Hybrid with the join: framing, not evidence
Ran the hybrid arm on the same 62 files with the correlation line supplied.
  LLM + join     recall 1.000  FPR 0.000  accuracy 1.000
  Hybrid + join  recall 0.520  FPR 0.000  accuracy 0.806
Same model, same evidence, same files. Only the prompt differs. The hybrid missed
12 of 25 tampered files that the LLM arm caught with identical input.
So the two failures were separate all along. The evidence problem is fixed by the
join. The framing problem isn't — "Your task is NOT to agree with it" costs about
48% of recall regardless of how good the evidence is.
Note the hybrid never produced a false positive in either condition. Told to be
sceptical, it only ever under-accuses.
Conclusion for the write-up: feeding rule output to an LLM did not improve triage
in any configuration tested. With poor evidence it collapsed to 0.04 recall; with
perfect evidence it still lost half. The instruction to critique is doing the
damage, which is a design warning for hybrid pipelines generally.


### 2026-08-19 — Unified reporter: rules decide, LLM explains
Final architecture the supervisor asked for. The rules classify; the LLM writes
the explanation. It never sees raw artefacts, never issues a verdict, and cannot
change one.
94 flagged files in the sample, plus one incident summary generated over all
1,308.
Measured, not judged by eye:
  faithfulness (no invented figures)  1.000
  completeness (every signal named)   1.000
  unsupported figures                 0 of 94 reports
  mean length                         124 words
Worth stating plainly: given the job of DECIDING, this same model managed 0.12
recall on Experiment C. Given the job of EXPLAINING, it is perfect. That is the
whole argument for the split.
Caveats on the metrics: completeness is keyword-matched, so a report could name a
signal without explaining it well. Faithfulness only checks 4+ digit numbers, so
a wrong qualitative claim would pass. Both bound what these numbers prove.