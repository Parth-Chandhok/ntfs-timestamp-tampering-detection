# movetrick.ps1 - fakes $SI, then moves the file so the kernel copies it into $FN.
# Result: both $SI and $FN show the fake date -> the mismatch rule is defeated.
$work     = "C:\ntfs-tamper-detect\datagen\tamper_lab\movetrick_test"
$staging  = "C:\ntfs-tamper-detect\datagen\tamper_lab\movetrick_staging"
$manifest = "C:\ntfs-tamper-detect\datagen\tamper_lab\movetrick_manifest.csv"
New-Item -ItemType Directory -Force -Path $staging | Out-Null

$files = Get-ChildItem $work -File
$rows = foreach ($f in $files) {
    $fake = (Get-Date).AddDays(-(Get-Random -Minimum 200 -Maximum 3000))

    # 1. fake $SI
    $f.CreationTime   = $fake
    $f.LastWriteTime  = $fake
    $f.LastAccessTime = $fake

    # 2. move to another folder -> kernel rewrites $FN from the (faked) $SI
    $moved = Join-Path $staging $f.Name
    Move-Item $f.FullName -Destination $moved -Force

    # 3. re-assert $SI after the move (move can nudge it), keeping SI==FN
    $g = Get-Item $moved
    $g.CreationTime   = $fake
    $g.LastWriteTime  = $fake
    $g.LastAccessTime = $fake

    [pscustomobject]@{
        FileName  = $f.Name
        tampered  = 1
        tool      = "move-trick (SI+FN faked)"
        fake_date = $fake.ToString("o")
    }
}
$rows | Export-Csv -Path $manifest -NoTypeInformation -Encoding utf8
Write-Host "Move-trick applied to $($files.Count) files."
Write-Host "Files now in: $staging"
Write-Host "Manifest: $manifest"