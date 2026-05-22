# schedule_monitor_health.ps1
# Cada 6 horas. Health check de toda la plataforma.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logDir = Join-Path $repo 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$log = Join-Path $logDir "monitor-$stamp.log"

"=== Monitor Health turno $stamp ===" | Out-File $log

$claude = "C:\Users\nicol\AppData\Roaming\npm\claude.cmd"
if (-not (Test-Path $claude)) { $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source }
if (-not $claude) { "ERROR: claude CLI no encontrado" | Out-File $log -Append; exit 1 }

$prompt = "Invocá al agente trongkai-monitor. Ejecutá la checklist completa (engine health, 13 paginas Vercel, tests pytest, schedules Windows, lint ruff, audit hardcodes). Si encontrás algun problema, escribí alerta en logs/alerts-$stamp.md."

cd $repo
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 | Out-File $log -Append

"=== fin turno $stamp ===" | Out-File $log -Append
