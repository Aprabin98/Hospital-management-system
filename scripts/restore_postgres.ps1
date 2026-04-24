param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$DbName = $env:DB_NAME,
    [string]$DbUser = $env:DB_USER,
    [string]$DbHost = $env:DB_HOST,
    [string]$DbPort = $env:DB_PORT
)

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

if (-not $DbName) { $DbName = "hms_db" }
if (-not $DbUser) { $DbUser = "hms_user" }
if (-not $DbHost) { $DbHost = "localhost" }
if (-not $DbPort) { $DbPort = "5432" }

Write-Host "Restoring backup into database: $DbName"
pg_restore --clean --if-exists --no-owner --no-privileges --host "$DbHost" --port "$DbPort" --username "$DbUser" --dbname "$DbName" "$BackupFile"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Restore failed. Ensure pg_restore is installed and PGPASSWORD is set."
    exit $LASTEXITCODE
}

Write-Host "Restore completed successfully."
