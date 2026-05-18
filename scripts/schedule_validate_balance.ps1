# schedule_validate_balance.ps1
# Smoke test diario del motor de balance de masa. Disparo todos los días 08:00.

$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logsDir = Join-Path $repo 'logs'
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$timestamp = Get-Date -Format 'yyyyMMdd-HHmm'
$logFile = Join-Path $logsDir "validate-balance-$timestamp.log"

Set-Location (Join-Path $repo 'apps\engine')
$env:PYTHONPATH = '.'
python -m pytest tests/ -q 2>&1 | Out-File -FilePath $logFile -Encoding utf8

if ($LASTEXITCODE -ne 0) {
    "ALERTA: tests del motor en rojo" | Out-File -FilePath $logFile -Append -Encoding utf8
    # Aquí se podría disparar notificación (Slack, email) — TODO en Fase 6
}
