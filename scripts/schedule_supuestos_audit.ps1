# schedule_supuestos_audit.ps1
# Auditoría semanal de supuestos. Disparo lunes 09:00.

$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logsDir = Join-Path $repo 'logs'
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$timestamp = Get-Date -Format 'yyyyMMdd-HHmm'
$logFile = Join-Path $logsDir "supuestos-audit-$timestamp.log"

Set-Location $repo

$claude = 'C:\Users\nicol\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe'

& $claude -p '/trongkai:supuestos-audit' --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 |
    Out-File -FilePath $logFile -Encoding utf8
