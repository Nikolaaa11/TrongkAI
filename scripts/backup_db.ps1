# backup_db.ps1
# Backup diario de Postgres Trongkai. Programar 03:00 via Windows Task Scheduler.
# Retención local: 14 días. Mensual: 12 meses (1 por mes).

$ErrorActionPreference = 'Stop'

$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$backupDir = Join-Path $repo 'backups'
$monthlyDir = Join-Path $backupDir 'monthly'
foreach ($d in @($backupDir, $monthlyDir)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$dailyFile = Join-Path $backupDir "trongkai-$stamp.sql.gz"

# Backup via docker exec (asume el container trongkai_postgres está corriendo)
$cmd = "docker exec trongkai_postgres pg_dump -U trongkai trongkai | gzip > `"$dailyFile`""
Invoke-Expression $cmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pg_dump falló con código $LASTEXITCODE"
    exit 1
}

$size = (Get-Item $dailyFile).Length
Write-Host "Backup OK: $dailyFile ($([math]::Round($size / 1KB, 1)) KB)"

# Monthly archive: si es el primer día del mes, copia a monthly/
if ((Get-Date).Day -eq 1) {
    $monthlyFile = Join-Path $monthlyDir "trongkai-$(Get-Date -Format 'yyyyMM').sql.gz"
    Copy-Item -Path $dailyFile -Destination $monthlyFile -Force
    Write-Host "Monthly snapshot: $monthlyFile"
}

# Retención: borrar daily > 14 días
Get-ChildItem $backupDir -Filter 'trongkai-*.sql.gz' -File |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
    ForEach-Object {
        Write-Host "Purgando: $($_.Name)"
        Remove-Item $_.FullName -Force
    }

# Retención monthly: 12 meses
Get-ChildItem $monthlyDir -Filter 'trongkai-*.sql.gz' -File |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddMonths(-12) } |
    ForEach-Object { Remove-Item $_.FullName -Force }
