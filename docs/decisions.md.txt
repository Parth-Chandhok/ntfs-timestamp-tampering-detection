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


### 2026-07-06 — Dataset direction: HYBRID (real baseline + injected tampering)
The 20-file self-made set only proves the pipeline, not accuracy. To measure
detection rate / precision / recall / false-positive rate I need data that is
BOTH realistic AND reliably labelled. No single ready-made set gives both:
real forensic images (NIST CFReDS, Digital Corpora) aren't labelled for
tampering, and fully self-generated data is trivially separable.
Decision: use a real file corpus as the clean/benign baseline, then inject
known tampering into a recorded subset so labels stay trustworthy. This is the
accepted method in the literature (Alji & Chougdali 2019; Palmbach &
Breitinger 2020; hystck / Göbel et al. 2020). Pending Dr Nabeel's confirmation.


### 2026-07-06 — Corpus choice: NapierOne (Tiny tier, forensics subset)
Picked NapierOne (Davies, Macfarlane & Buchanan 2022, Edinburgh Napier) as the
real baseline — modern, validated, free (ENU licence), 44 file types x 5,000
files, the recognised successor to Govdocs1 (2009). Govdocs1 kept as an
optional 2nd corpus for cross-corpus validation.

IMPORTANT correction: the dataset is NOT on the GitHub repo. The repo
(github.com/simonrdavies/NapierOne) is documentation only. The actual files
live on the public AWS Open Data bucket  s3://napierone.com/  (region
eu-north-1, no account needed) and on napierone.com. Full set is ~2 TB, split
into Tiny (100 files/type), Small (1,000/type) and Total tiers.

Scope taken: TINY tier (100 files/type, sequence 0001-0100) for the
forensics-relevant file types only. 31 types, ~3,100 files. Enough to test the
framework and false-positive behaviour without overloading the VM/snapshots.
Skipped for now: MP3/MP4/MKV (large, low value here), plus DWG/EPS/EPUB/ICS/
ODS/OXPS/ZLIB/DLL/RANDOM/ransomware subsets. DLL and the ransomware-encrypted
subsets can be added later. The NOMAGIC variants (DOC/DOCX/PDF/PPT/PPTX/XLS/
XLSX-NOMAGIC-tiny.zip) are ready-made test material for the file-type-disguise
(magic-byte) rule — grab them when building that rule.




