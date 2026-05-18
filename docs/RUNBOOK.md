# Runbook operativo

Para el sysadmin de Trongkai. Pendiente expansión en Fase 6.

## Levantar entorno local

```powershell
docker compose up -d postgres redis
cd apps/engine; pip install -e .[dev]; pytest
cd apps/web; npm install; npm run dev
```

## Backup de DB

`docker exec trongkai_postgres pg_dump -U trongkai trongkai > backup-$(date +%F).sql`

Programar diario en cron del host (Fase 6).

## Reiniciar motor de cálculo en caliente

`docker compose restart engine`

## Si el balance de masa empieza a fallar (`MassBalanceError`)

1. Revisar logs: `docker compose logs engine | grep mass_balance_error`
2. Validar inputs del lote en `Recepcion`: humedad medida vs humedad declarada.
3. Si el error persiste, ABRIR la página `/balance` y reproducir el caso con los inputs.
4. La regla §0.4 obliga test antes de cerrar: si hay bug en el motor, agregar caso en `tests/test_mass_balance.py`.

## Si el secador real tiene capacidad distinta a la declarada en `CapacidadEquipo`

1. Editar `CapacidadEquipo.SECADO.capacidadTonHora` en la UI de Supuestos.
2. El cambio queda en `AuditLog` automáticamente.
3. El solver de bottleneck recalcula al próximo refresh del dashboard.

## Si llega un camión rechazado por calidad

1. Crear `Recepcion` con `calidadAceptada=false` y `motivoRechazo`.
2. No actualiza el plan automáticamente — el operador decide si reasignar capacidad.
