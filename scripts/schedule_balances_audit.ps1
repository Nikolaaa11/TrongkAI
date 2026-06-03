# Trongkai - Balances Audit Schedule
# Corre cada 6 horas: valida los 4 balances, detecta alarmas criticas
#
# Install: .\scripts\schedule_balances_audit.ps1 -Install
# Run:     .\scripts\schedule_balances_audit.ps1 -Run
# Remove:  .\scripts\schedule_balances_audit.ps1 -Uninstall

param(
    [switch]$Install,
    [switch]$Run,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform"
$LogDir = "$RepoRoot\logs"
$LogFile = "$LogDir\balances-audit-schedule.log"
$TaskName = "TrongkAI-BalancesAudit"
$ScriptPath = "$RepoRoot\scripts\schedule_balances_audit.ps1"

function Write-Log {
    param([string]$Message)
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
    Write-Host "$timestamp | $Message"
}

if ($Install) {
    Write-Log "Instalando schedule TrongkAI-BalancesAudit (cada 6h)..."
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -Run"
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
        -RepetitionInterval (New-TimeSpan -Hours 6)
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Force | Out-Null
    Write-Log "OK Instalado. Corre cada 6h. Logs en $LogDir"
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
    Write-Log "=== Ejecutando audit_balances.py ==="
    Set-Location $RepoRoot
    try {
        $output = python scripts/audit_balances.py 2>&1
        $output | ForEach-Object { Write-Log $_ }
        Write-Log "=== OK ==="
    } catch {
        Write-Log "ERROR: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

Write-Host @"
Trongkai Balances Audit Schedule

Uso:
  .\scripts\schedule_balances_audit.ps1 -Install     # Registra task cada 6h
  .\scripts\schedule_balances_audit.ps1 -Run         # Corre una vez ahora
  .\scripts\schedule_balances_audit.ps1 -Uninstall   # Quita la task

Funciones automaticas:
  1. Fetch /balance/integrado al engine
  2. Genera HTML resumen en entregables/Balances-YYYYMMDD-HHMM.html
  3. Si hay alarmas criticas escribe logs/balances-alert-*.md
  4. Marca evento en audit_trail si alarmas criticas

Logs: $LogDir
"@
