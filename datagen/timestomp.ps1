# timestomp_c.ps1 - timestomps half the benign corpus on C:, records ground truth 808 files+ 
$benign   = "C:\ntfs-tamper-detect\datagen\tamper_lab\benign"
$work     = "C:\ntfs-tamper-detect\datagen\tamper_lab\tampered"
$manifest = "C:\ntfs-tamper-detect\datagen\tamper_lab\manifest.csv"
New-Item -ItemType Directory -Force -Path $work | Out-Null

Copy-Item "$benign\*" -Destination $work -Force
$files = Get-ChildItem $work -File

$half = [math]::Floor($files.Count / 2)
$toTamper = $files | Get-Random -Count $half

$rows = foreach ($f in $files) {
    $isTampered = $toTamper -contains $f
    if ($isTampered) {
        $fake = (Get-Date).AddDays(-(Get-Random -Minimum 200 -Maximum 3000))
        $f.CreationTime   = $fake
        $f.LastWriteTime  = $fake
        $f.LastAccessTime = $fake
    }
    [pscustomobject]@{
        FileName  = $f.Name
        tampered  = [int]$isTampered
        tool      = if ($isTampered) { "PowerShell-CreationTime" } else { "" }
        fake_date = if ($isTampered) { $fake.ToString("o") } else { "" }
    }
}
$rows | Export-Csv -Path $manifest -NoTypeInformation -Encoding utf8
Write-Host "Tampered $half of $($files.Count) files on C:."
Write-Host "Manifest: $manifest"