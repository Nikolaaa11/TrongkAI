# Trongkai - Knowledge Builder Daily Schedule
# Corre 1 vez al dia, aprende solo de inbox + valida salud + marca snapshot
#
# Install: .\scripts\schedule_knowledge_builder.ps1 -Install
# Run:     .\scripts\schedule_knowledge_builder.ps1 -Run
# Remove:  .\scripts\schedule_knowledge_builder.ps1 -Uninstall

param(
    [switch]$Install,
    [switch]$Run,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform"
$LogDir = "$RepoRoot\logs"
$LogFile = "$LogDir\knowledge-builder-schedule.log"
$TaskName = "TrongkaiKnowledgeBuilder"
$ScriptPath = "$RepoRoot\scripts\schedule_knowledge_builder.ps1"

function Write-Log {
    param([string]$Message)
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
    Write-Host "$timestamp | $Message"
}

if ($Install) {
    Write-Log "Instalando schedule TrongkaiKnowledgeBuilder (1 vez al dia 09:00)..."
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Run"
    $trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Log "OK Instalado. Corre diariamente 09:00. Logs en $LogDir"
    exit 0
}

if ($Uninstall) {
    Write-Log "Desinstalando schedule..."
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Log "OK Desinstalado."
    } catch {
        Write-Log "WARN: $($_.Exception.Message)"
    }
    exit 0
}

if ($Run) {
    Write-Log "=== Ejecutando knowledge_builder.py ==="
    Set-Location $RepoRoot
    try {
        $output = python scripts/knowledge_builder.py 2>&1
        $output | ForEach-Object { Write-Log $_ }
        Write-Log "=== OK ==="
    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

Write-Host @"
Trongkai Knowledge Builder Schedule

Uso:
  .\scripts\schedule_knowledge_builder.ps1 -Install     # Registra task diaria 09:00
  .\scripts\schedule_knowledge_builder.ps1 -Run         # Corre una vez ahora
  .\scripts\schedule_knowledge_builder.ps1 -Uninstall   # Quita la task

Tareas automaticas diarias:
  1. Procesa inbox (clasifica nuevos archivos)
  2. Marca snapshot readiness en historico
  3. Health check completo del motor
  4. Detecta alertas y gaps coherentes nuevos
  5. Calcula commercial intelligence del dia
  6. Registra evento en audit trail
  7. Genera reporte markdown en logs/knowledge-builder-YYYYMMDD.md

Logs: $LogDir
"@
