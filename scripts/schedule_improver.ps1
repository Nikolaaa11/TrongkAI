# schedule_improver.ps1
# Worker autónomo que invoca a Claude para correr /trongkai:improve cada 1 hora.
#
# Lo dispara el Task Scheduler de Windows (tarea TrongkAI-Improver).
# Logs por turno en C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform\logs\improver-YYYYMMDD-HHMM.log

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logsDir = Join-Path $repo 'logs'
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }

$timestamp = Get-Date -Format 'yyyyMMdd-HHmm'
$logFile = Join-Path $logsDir "improver-$timestamp.log"

"=== TrongkAI Improver turno $timestamp ===" | Out-File -FilePath $logFile -Encoding utf8

Set-Location $repo

# 1. git pull para alinear con cualquier cambio externo
git pull --rebase --autostash origin main 2>&1 | Out-File -FilePath $logFile -Append -Encoding utf8

# 2. invocar Claude en modo print con el comando /trongkai:improve
$claude = 'C:\Users\nicol\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe'

$prompt = @'
/trongkai:improve

Sos el TrongkAI improver autónomo, turno cron de 1 hora. Estás parado en el repo trongkai-platform. Una mejora chica si encontrás algo, tests verdes obligatorios, commit semántico y push a main si todo OK. Si nada que mejorar, NO comitees vacío y devolvé NOOP. Output máximo 25 líneas.
'@

# Modo no interactivo, con permisos amplios para Edit/Bash/Write
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 |
    Out-File -FilePath $logFile -Append -Encoding utf8

"=== fin turno $timestamp ===" | Out-File -FilePath $logFile -Append -Encoding utf8

# Limpiar logs > 14 días
Get-ChildItem $logsDir -Filter 'improver-*.log' |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
    Remove-Item -Force -ErrorAction SilentlyContinue
