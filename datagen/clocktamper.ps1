# clocktamper.ps1 — Experiment C: clock-rollback tampering
# Generates 200 benign + 200 tampered files from the NapierOne benign corpus.
# Tampered files are written while the system clock is rolled back 3 years,
# producing internally-consistent $SI/$FN timestamps that file-level artefacts
# cannot flag. Detection relies on the Windows Event Log (Kernel-General ID 1).
# Requires: admin PowerShell, VBoxService + w32time stopped beforehand.
# Author: Parth Chandhok

$srcRoot  = "C:\ntfs-tamper-detect\datagen\tamper_lab\benign"
$outRoot  = "C:\ntfs-tamper-detect\datagen\tamper_lab\clocktamper"
$manifest = "C:\ntfs-tamper-detect\data\labels\clocktamper_manifest.csv"
$nBenign  = 200
$nTamper  = 200

if (-not (Test-Path $srcRoot)) { Write-Host "SOURCE NOT FOUND: $srcRoot" -ForegroundColor Red; return }
$src = @(Get-ChildItem -Path $srcRoot -File -Recurse)
Write-Host "Source files:" $src.Count
if ($src.Count -lt ($nBenign + $nTamper)) { Write-Host "Not enough source files." -ForegroundColor Red; return }

# archive the synthetic pilot run
if (Test-Path $outRoot) {
    $pilot = Join-Path (Split-Path $outRoot) ("clocktamper_pilot_" + (Get-Date -Format "yyyyMMddHHmmss"))
    Move-Item $outRoot $pilot -Force
    Write-Host "Pilot run archived to:" $pilot
}
New-Item -ItemType Directory -Path "$outRoot\benign","$outRoot\tampered" -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path $manifest) -Force | Out-Null

# deterministic selection (seed = reproducible for the write-up)
$shuffled  = $src | Get-Random -Count $src.Count -SetSeed 42
$benignSet = $shuffled[0..($nBenign-1)]
$tamperSet = $shuffled[$nBenign..($nBenign+$nTamper-1)]
$log = @()

# --- A. benign controls, REAL clock ---
$i = 0
foreach ($f in $benignSet) {
    $i++
    $name = "ctben_{0:d3}_{1}" -f $i, $f.Name
    $dest = Join-Path "$outRoot\benign" $name
    [System.IO.File]::WriteAllBytes($dest, [System.IO.File]::ReadAllBytes($f.FullName))
    $log += [pscustomobject]@{ filename=$name; path=$dest; tampered=0; tamper_type="none"
                               source=$f.Name; offset=$null }
}
Write-Host "$nBenign benign controls written."

# --- B. roll clock back 3 years ---
$anchor = Get-Date
$sw = [System.Diagnostics.Stopwatch]::StartNew()
Set-Date -Date $anchor.AddYears(-3) | Out-Null
Write-Host "Clock rolled back. System believes:" (Get-Date)

# --- C. tampered files, FAKE clock ---
$i = 0
foreach ($f in $tamperSet) {
    $i++
    $name = "ctfake_{0:d3}_{1}" -f $i, $f.Name
    $dest = Join-Path "$outRoot\tampered" $name
    [System.IO.File]::WriteAllBytes($dest, [System.IO.File]::ReadAllBytes($f.FullName))
    $log += [pscustomobject]@{ filename=$name; path=$dest; tampered=1; tamper_type="clock_rollback"
                               source=$f.Name; offset=$sw.Elapsed.TotalSeconds }
}
Write-Host "$nTamper tampered files written under fake clock."

# --- D. restore real time ---
$sw.Stop()
Set-Date -Date $anchor.Add($sw.Elapsed) | Out-Null
Write-Host "Clock restored:" (Get-Date) "| tamper window:" ([math]::Round($sw.Elapsed.TotalSeconds,1)) "s"

# --- E. manifest (built AFTER restore, keeps the window short) ---
$rows = foreach ($e in $log) {
    $it = Get-Item $e.path
    [pscustomobject]@{
        filename      = $e.filename
        tampered      = $e.tampered
        tamper_type   = $e.tamper_type
        source_file   = $e.source
        extension     = $it.Extension
        size_bytes    = $it.Length
        shown_created = $it.CreationTime.ToString("s")
        real_created  = if ($e.tampered -eq 1) { $anchor.AddSeconds($e.offset).ToString("s") }
                        else { $it.CreationTime.ToString("s") }
    }
}
$rows | Export-Csv -Path $manifest -NoTypeInformation -Encoding utf8
Write-Host "Manifest written:" $manifest "| rows:" $rows.Count