# Tampering Assessment - Reason Reports (C)

_Experiment C - system clock rollback_

Files analysed: **400**  |  Flagged: **200**  |  Clean: **200**

Scores are produced by correlating independent forensic indicators. Each line below states the evidence and the points it contributed, so every verdict can be traced back to a specific artefact.

## ctfake_001_CSV-tiny_0081-csv.csv
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_002_TXT-tiny_0054-txt.txt
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_003_DOCX-tiny_0011-docx.docx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_004_XLSX-tiny_0045-xlsx.xlsx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_005_DOCX-tiny_0088-docx.docx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_006_CSV-tiny_0010-csv.csv
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_007_PNG-c0-tiny_C0.pdf
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_008_TXT-tiny_0014-txt.txt
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_009_XLSX-tiny_0009-xlsx.xlsx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_010_DOCX-tiny_0041-docx.docx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_011_DOC-tiny_0029-doc.doc
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_012_TXT-tiny_0053-txt.txt
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_013_PDF-tiny_0006-pdf.pdf
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_014_PNG-c0-tiny_0020-png-c0.png
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_015_HTML-tiny_0061-html.html
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_016_PNG-c0-tiny_0056-png-c0.png
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_017_XLSX-tiny_0079-xlsx.xlsx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_018_DOCX-tiny_0070-docx.docx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_019_XLSX-tiny_0069-xlsx.xlsx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_020_HTML-tiny_0063-html.html
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_021_TXT-tiny_0092-txt.txt
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_022_PNG-c0-tiny_0100-png-c0.png
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_023_DOCX-tiny_0093-docx.docx
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_024_TXT-tiny_0033-txt.txt
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

## ctfake_025_DOC-tiny_0054-doc.doc
**Score: 95/100 (VERY HIGH)**  |  Artefacts: EventLog+USN

- [+35] File's claimed creation time is far older than the journal records written around it; USN sequence numbers are clock-independent and cannot be rewound (NOTE: a legitimately old file copied onto this volume would produce the same pattern) (claims 1,096 days older than its journal neighbourhood)
- [+45] File's claimed creation time falls inside a window during which the Windows Event Log records the system clock as having been rolled backwards
- [+15] Corroborated across independent artefacts (EventLog, USN) - tampering is unlikely to be a single-source artefact

_...and 175 further flagged files (full detail in scored_files_C.csv)._