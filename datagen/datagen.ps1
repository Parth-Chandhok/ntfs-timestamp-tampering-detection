# datagen.ps1 - generates a small labelled dataset for the tampering detector

# >>> EDIT this one line to your actual project path <
$root = "C:\ntfs-tamper-detect"

$filesDir  = Join-Path $root "data\raw\files"
$labelsDir = Join-Path $root "data\labels"
New-Item -ItemType Directory -Force -Path $filesDir  | Out-Null
New-Item -ItemType Directory -Force -Path $labelsDir | Out-Null

$total   = 20
$tamperN = 10

# create the files
$names = @()
for ($i = 1; $i -le $total; $i++) {
    $name = "file_{0:D2}.txt" -f $i           # file_01.txt ... file_20.txt
    $path = Join-Path $filesDir $name
    "Sample content for $name written $(Get-Date -Format o)" | Out-File -FilePath $path -Encoding utf8
    $names += $name
}

# randomly pick which files to timestomp
$tamperSet = $names | Get-Random -Count $tamperN

$labels = foreach ($name in $names) {
    $path = Join-Path $filesDir $name
    $isTampered = if ($tamperSet -contains $name) { 1 } else { 0 }

    if ($isTampered -eq 1) {
        $fakeDate = (Get-Date).AddDays( -(Get-Random -Minimum 200 -Maximum 2000) )
        $f = Get-Item $path
        $f.CreationTime   = $fakeDate    # touches $SI only -> $FN stays -> mismatch
        $f.LastWriteTime  = $fakeDate
        $f.LastAccessTime = $fakeDate
    }

    [pscustomobject]@{
        FileName   = $name
        ParentPath = $filesDir
        tampered   = $isTampered
    }
}

$labelsCsv = Join-Path $labelsDir "labels_v1.csv"
$labels | Export-Csv -Path $labelsCsv -NoTypeInformation -Encoding utf8

Write-Host "Created $total files in $filesDir"
Write-Host "Tampered $tamperN of them (`$SI dates pushed into the past)"
Write-Host "Labels -> $labelsCsv"