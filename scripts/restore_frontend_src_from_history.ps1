$ErrorActionPreference = "Stop"
$workspace = "C:\Users\aprab\Desktop\Hospital management system"
$historyRoot = Join-Path $env:APPDATA "Code\User\History"
$cutoff = (Get-Date).Date.AddHours(11).AddMinutes(58)
$restored = @{}

function Normalize-LocalPath([string]$uri) {
  $p = [System.Uri]::new($uri).LocalPath
  if ($p -match '^/[A-Za-z]:') { $p = $p.Substring(1) }
  return $p
}

Get-ChildItem -Path $historyRoot -Recurse -Filter entries.json -ErrorAction SilentlyContinue | ForEach-Object {
  try {
    $json = Get-Content $_.FullName -Raw | ConvertFrom-Json
    if (-not $json.resource) { return }
    if ($json.resource -notlike "*Desktop/Hospital%20management%20system/frontend/src/*") { return }
    if ($json.resource -like "*OneDrive*") { return }

    $targetPath = Normalize-LocalPath $json.resource
    if ($targetPath -notlike "$workspace\frontend\src\*") { return }

    $valid = @($json.entries | Where-Object { [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$_.timestamp).LocalDateTime -le $cutoff })
    if ($valid.Count -eq 0) { return }
    $latest = $valid | Sort-Object {[int64]$_.timestamp} -Descending | Select-Object -First 1
    $ts = [DateTimeOffset]::FromUnixTimeMilliseconds([int64]$latest.timestamp).LocalDateTime

    if ($restored.ContainsKey($targetPath) -and $restored[$targetPath].Time -ge $ts) { return }

    $blob = Join-Path $_.Directory.FullName $latest.id
    if (-not (Test-Path $blob)) { return }

    $parent = Split-Path -Path $targetPath -Parent
    if (-not (Test-Path $parent)) { New-Item -Path $parent -ItemType Directory -Force | Out-Null }

    Copy-Item -Path $blob -Destination $targetPath -Force
    $restored[$targetPath] = [PSCustomObject]@{ Time = $ts; Id = $latest.id }
  } catch {}
}

Write-Output ("Restored src files: " + $restored.Count)
$restored.GetEnumerator() | Sort-Object Name | Select-Object -First 200 @{n='File';e={$_.Name}}, @{n='SnapshotTime';e={$_.Value.Time}}, @{n='EntryId';e={$_.Value.Id}} | Format-Table -AutoSize
