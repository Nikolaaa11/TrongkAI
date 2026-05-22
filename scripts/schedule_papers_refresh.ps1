# schedule_papers_refresh.ps1
# Trimestral (1ro de marzo/junio/septiembre/diciembre 10:00).
# Busca papers nuevos sobre las 5 MMPP + tecnologías clave.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logDir = Join-Path $repo 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$log = Join-Path $logDir "papers-refresh-$stamp.log"

"=== Papers Refresh turno $stamp ===" | Out-File $log

$claude = "C:\Users\nicol\AppData\Roaming\npm\claude.cmd"
if (-not (Test-Path $claude)) { $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source }
if (-not $claude) { "ERROR: claude CLI no encontrado" | Out-File $log -Append; exit 1 }

$prompt = "Ejecutá /trongkai:papers-refresh. Buscá papers peer-reviewed publicados en los últimos 90 días sobre alperujo, tomasa, orujo uva, levadura, pomasa y tecnologías PEF + SCP + LCA. Si encontrás >=3 papers nuevos relevantes, actualizá docs/PAPERS-CIENTIFICOS.md y commiteá."

cd $repo
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 | Out-File $log -Append

"=== fin turno $stamp ===" | Out-File $log -Append
