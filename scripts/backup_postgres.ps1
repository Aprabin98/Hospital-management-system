param(
    [string]$DbName = $env:DB_NAME,
    [string]$DbUser = $env:DB_USER,
    [string]$DbHost = $env:DB_HOST,
    [string]$DbPort = $env:DB_PORT,
    [string]$OutputDir = "./backups"
)

if (-not $DbName) { $DbName = "hms_db" }
if (-not $DbUser) { $DbUser = "hms_user" }
if (-not $DbHost) { $DbHost = "localhost" }
if (-not $DbPort) { $DbPort = "5432" }

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dumpFile = Join-Path $OutputDir ("hms_backup_{0}.dump" -f $timestamp)

Write-Host "Creating PostgreSQL backup: $dumpFile"
pg_dump --format=custom --file "$dumpFile" --host "$DbHost" --port "$DbPort" --username "$DbUser" "$DbName"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Backup failed. Ensure pg_dump is installed and PGPASSWORD is set."
    exit $LASTEXITCODE
}

Write-Host "Backup completed successfully."
