# Trongkai - Auto-procesamiento del Inbox cada 1 hora
#
# Setup (run UNA vez como admin):
#   .\scripts\schedule_inbox_processor.ps1 -Install
#
# Manual run:
#   .\scripts\schedule_inbox_processor.ps1 -Run
#
# Unregister:
#   .\scripts\schedule_inbox_processor.ps1 -Uninstall

param(
    [switch]$Install,
    [switch]$Run,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform"
$LogDir = "$RepoRoot\logs"
$LogFile = "$LogDir\inbox-processor.log"
$TaskName = "TrongkaiInboxProcessor"
$ScriptPath = "$RepoRoot\scripts\schedule_inbox_processor.ps1"

function Write-Log {
    param([string]$Message)
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
    Write-Host "$timestamp | $Message"
}

if ($Install) {
    Write-Log "Instalando schedule TrongkaiInboxProcessor..."
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Run"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 1)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Log "OK Instalado. Correra cada 1 hora. Logs en $LogFile"
    exit 0
}

if ($Uninstall) {
    Write-Log "Desinstalando schedule TrongkaiInboxProcessor..."
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Log "OK Desinstalado."
    } catch {
        Write-Log "WARN: $($_.Exception.Message)"
    }
    exit 0
}

if ($Run) {
    Write-Log "=== Ejecutando procesar_inbox.py ==="
    Set-Location $RepoRoot
    try {
        $output = python scripts/procesar_inbox.py 2>&1
        $output | ForEach-Object { Write-Log $_ }
        Write-Log "=== OK ==="
    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

Write-Host @"
Trongkai Inbox Processor - Schedule

Uso:
  .\scripts\schedule_inbox_processor.ps1 -Install     # Registra task cada 1h
  .\scripts\schedule_inbox_processor.ps1 -Run         # Corre una vez ahora
  .\scripts\schedule_inbox_processor.ps1 -Uninstall   # Quita la task

Logs: $LogFile
"@
