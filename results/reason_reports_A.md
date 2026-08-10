# Tampering Assessment - Reason Reports (A)

_Experiment A - PowerShell $SI timestomp_

Files analysed: **808**  |  Flagged: **404**  |  Clean: **404**

Scores are produced by correlating independent forensic indicators. Each line below states the evidence and the points it contributed, so every verdict can be traced back to a specific artefact.

## CSV-tiny_0002-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1741.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1741.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0003-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 446.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 446.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0005-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2456.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2456.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0008-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 863.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 863.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0010-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1469.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1469.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0015-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1245.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1245.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0016-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 521.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 521.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0017-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1751.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1751.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0018-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2186.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2186.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0021-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1897.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1897.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0023-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2897.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2897.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0025-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2356.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2356.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0026-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 315.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 315.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0027-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 611.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 611.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0028-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 747.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 747.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0029-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1929.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1929.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0030-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2967.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2967.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0031-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 749.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 749.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0035-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1260.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1260.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0038-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2610.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2610.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0039-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1032.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1032.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0041-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1478.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1478.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0042-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1317.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1317.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0044-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 2686.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 2686.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

## CSV-tiny_0047-csv.csv
**Score: 100/100 (VERY HIGH)**  |  Artefacts: MFT+USN

- [+40] $STANDARD_INFORMATION creation time disagrees with the kernel-managed $FILE_NAME creation time (discrepancy of 1655.0 days)
- [+35] USN Journal records timestamp/attribute modification AFTER the file's creation sequence completed (6 BasicInfoChange record(s))
- [+25] File claims a creation date earlier than its first appearance in the USN Journal (claims 1655.0 days before first journal entry)
- [+15] Corroborated across independent artefacts (MFT, USN) - tampering is unlikely to be a single-source artefact

_...and 379 further flagged files (full detail in scored_files_A.csv)._