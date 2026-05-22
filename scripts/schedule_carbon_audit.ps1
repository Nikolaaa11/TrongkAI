# schedule_carbon_audit.ps1
# Día 1 de cada mes 07:00. Audit footprint carbono + revenue créditos.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logDir = Join-Path $repo 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$log = Join-Path $logDir "carbon-audit-$stamp.log"

"=== Carbon Audit turno $stamp ===" | Out-File $log

$claude = "C:\Users\nicol\AppData\Roaming\npm\claude.cmd"
if (-not (Test-Path $claude)) { $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source }
if (-not $claude) { "ERROR: claude CLI no encontrado" | Out-File $log -Append; exit 1 }

$prompt = "Invocá al agente trongkai-esg-analyst. Hacé el audit mensual de carbono: ejecutá POST /plan/carbon-footprint, compará con benchmarks literatura, generá reporte estructurado en exports/carbon_audit_$stamp.md y notificá si hay desviación >50% vs literatura."

cd $repo
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 | Out-File $log -Append

"=== fin turno $stamp ===" | Out-File $log -Append
