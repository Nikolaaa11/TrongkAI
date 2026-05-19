# Runbook operativo TrongkAI

Para el sysadmin de Trongkai. Cubre operación, backup, recuperación y debugging.

## 1. Levantar entorno local

```powershell
cd C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform
docker compose up -d postgres redis
cd apps\engine
pip install -e .[dev]
$env:PYTHONPATH = "."
python -m pytest tests/
uvicorn trongkai_engine.main:app --reload --port 8000

# En otra terminal:
cd apps\web
npm install
npm run dev
```

URLs:
- Frontend: <http://localhost:3000>
- Engine: <http://localhost:8000>
- Docs OpenAPI: <http://localhost:8000/docs>

## 2. Aplicar migración inicial

```powershell
psql $env:DATABASE_URL -f packages\db\prisma\migrations\0001_init\migration.sql
# o, vía docker:
docker exec -i trongkai_postgres psql -U trongkai trongkai < packages\db\prisma\migrations\0001_init\migration.sql
```

## 3. Seed inicial desde Excels

```powershell
# Dry-run (no toca DB)
python scripts\seed-from-excel.py --dry-run

# Aplicar a DB
$env:DATABASE_URL = "postgresql://trongkai:trongkai_dev@localhost:5432/trongkai"
python scripts\seed-from-excel.py --apply
```

Salida esperada: `MMPP=5, Suppliers=9 (4 activos), Productos=12, Supuestos≈165, Capacidades=10`.

## 4. Backup de DB

Tarea Windows `TrongkAI-Backup` (registrarla manualmente):

```powershell
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform\scripts\backup_db.ps1"'
$trigger = New-ScheduledTaskTrigger -Daily -At '03:00'
Register-ScheduledTask -TaskName 'TrongkAI-Backup' -Action $action -Trigger $trigger -Description 'Backup diario de Postgres Trongkai' -Force
```

Retención: 14 días daily + 12 meses monthly (snapshot del día 1 de cada mes).

Restore manual:

```powershell
docker exec -i trongkai_postgres psql -U trongkai trongkai < (gzip -d -c backups\trongkai-20260601-0300.sql.gz)
```

## 5. Recuperación ante incidentes

### El balance de masa empieza a fallar (`MassBalanceError`)

1. Logs: `docker compose logs engine | Select-String "mass_balance_error"`
2. Validar inputs del lote en `Recepcion`: humedad medida vs humedad declarada.
3. Reproducir el caso en `/balance` con los mismos inputs.
4. Si hay bug en el motor, agregar test en `tests/test_mass_balance.py`. Regla §0.4: no se cierra el fix sin test.

### El engine no responde

```powershell
docker compose logs engine | Select-Object -Last 50
docker compose restart engine
# Healthcheck del Dockerfile chequea /docs cada 30s
```

### Tests del schedule diario `TrongkAI-ValidateBalance` rojos

Esto es una señal: alguien commiteo código sin tests verdes (saltó al improver). Acciones:

```powershell
Get-Content logs\validate-balance-*.log | Select-Object -Last 30
cd apps\engine
$env:PYTHONPATH = "."
python -m pytest tests/ -v
git log --oneline -10
```

Si el último commit fue del improver, considerá revertir:

```powershell
git revert HEAD --no-edit
git push origin main
```

### Capacidad real del secador difiere de la declarada

1. UI `/supuestos` → buscar `cap.secado_ton_h` → editar.
2. El cambio queda en `AuditLog` automáticamente.
3. Forzar refresh del `/agenda` para recomputar bottleneck.

### Camión rechazado por calidad

1. Crear `Recepcion` con `calidadAceptada=false` + `motivoRechazo`.
2. El plan no se actualiza automáticamente — el operador decide si reasignar capacidad a otro supplier desde `/agenda`.

## 6. Observabilidad

- **Frontend**: `pino` logs en consola del browser y server-side de Next.js.
- **Engine**: `structlog` con formato JSON. Para correr en prod con stdout estructurado:
  ```bash
  uvicorn trongkai_engine.main:app --host 0.0.0.0 --port 8000 --workers 2 --log-config null
  ```
- **Métricas**: Fase 6+ — Prometheus exporter pendiente. Por ahora, los counters internos de `compute_mass_balance` y `compute_bottleneck` se exponen via `/health`.

## 7. Schedules autónomos

| Tarea | Cron | Owner |
|---|---|---|
| TrongkAI-Improver | cada 1h | el improver autónomo (Claude) |
| TrongkAI-SupuestosAudit | lunes 09:00 | agente trongkai-supuestos |
| TrongkAI-ValidateBalance | diario 08:00 | trongkai-qa |
| TrongkAI-Backup | diario 03:00 | sysadmin |

Inspeccionar:
```powershell
Get-ScheduledTask | Where-Object TaskName -like 'TrongkAI-*' | Format-Table TaskName,State,@{n='LastRun';e={(Get-ScheduledTaskInfo $_).LastRunTime}},@{n='LastResult';e={(Get-ScheduledTaskInfo $_).LastTaskResult}}
```

## 8. Auditoría de hardcodes

```powershell
python scripts\audit_hardcodes.py
```

Falla con exit 1 si hay `TODO: parametrizar` sin referencia a `docs\SUPUESTOS.md`.

## 9. Deploy

Hoy: Docker Compose en servidor único.

Producción Trongkai (cuando esté listo):
- **Engine**: fly.io en región scl (Santiago). Config en `apps/engine/fly.toml`. Deploy: `flyctl deploy --app trongkai-engine`.
- **Web**: Vercel con framework Next.js auto-detectado. Variable `NEXT_PUBLIC_ENGINE_URL` apuntando al engine fly.
- **DB**: pendiente — opciones (a) Supabase Postgres compartido con cehta-platform (b) Postgres dedicado en fly.io.

## 10. Contactos de escalación

| Tema | Owner |
|---|---|
| Negocio + producto | Jaime Echeverría (GG) |
| Balance de masa | José Cuevas (CTO) y Claudio (validador) |
| Compliance + dirección | Nicolás Rietta (COO Cehta), Guido Rietta (presidente directorio) |
| Logística MMPP | Claudia Gotschlich + Matías |
| Plataforma técnica | el usuario (operador de Claude Code) |
