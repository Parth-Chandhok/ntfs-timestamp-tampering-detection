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


