# schedule_macro_refresh.ps1
# Diario 06:00. Refresca snapshot interno macro Chile + alerta si cambios materiales.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform'
$logDir = Join-Path $repo 'logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$log = Join-Path $logDir "macro-refresh-$stamp.log"

"=== Macro Refresh turno $stamp ===" | Out-File $log

$claude = "C:\Users\nicol\AppData\Roaming\npm\claude.cmd"
if (-not (Test-Path $claude)) {
    $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
}
if (-not $claude) {
    "ERROR: claude CLI no encontrado" | Out-File $log -Append
    exit 1
}

$prompt = "Ejecutá la skill /trongkai:macro-refresh. Si hay cambios materiales en dolar/UF/TPM/IPC vs snapshot interno, actualizalos en apps/engine/trongkai_engine/macro_chile.py:SNAPSHOT_FALLBACK y commiteá. Si no hay cambios, solo loguear."

cd $repo
& $claude -p $prompt --permission-mode acceptEdits --dangerously-skip-permissions 2>&1 | Out-File $log -Append

"=== fin turno $stamp ===" | Out-File $log -Append
