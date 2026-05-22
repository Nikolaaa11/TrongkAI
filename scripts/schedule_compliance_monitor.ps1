# schedule_compliance_monitor.ps1
# Lunes 09:00. Chequea hitos REP próximos + alertas regulatorias.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logDir = Join-Path $repo 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$log = Join-Path $logDir "compliance-monitor-$stamp.log"

"=== Compliance Monitor turno $stamp ===" | Out-File $log

$claude = "C:\Users\nicol\AppData\Roaming\npm\claude.cmd"
if (-not (Test-Path $claude)) { $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source }
if (-not $claude) { "ERROR: claude CLI no encontrado" | Out-File $log -Append; exit 1 }

$prompt = "Invocá al agente trongkai-compliance-officer. Hacé el check semanal de hitos Ley REP próximos 90 días. Si detectás un hito CRITICA o ALTA con < 60 días sin acción asignada, escalá. Buscá novedades regulatorias MMA / SII desde la última corrida."

cd $repo
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 | Out-File $log -Append

"=== fin turno $stamp ===" | Out-File $log -Append
