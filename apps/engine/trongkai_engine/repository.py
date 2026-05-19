"""Capa de persistencia mínima sobre Postgres.

Usa psycopg3 sync (driver oficial) en lugar de SQLAlchemy para mantener la
superficie chica. Modelo de datos espejo de packages/db/prisma/schema.prisma.

Reglas:
- Toda escritura va en UNA transacción por operación de alto nivel.
- Los INSERT son idempotentes (ON CONFLICT DO UPDATE) cuando hay UNIQUE.
- Las lecturas devuelven dicts simples (no DTOs propios) — el caller decide.

Si `DATABASE_URL` no está definido, las funciones lanzan `RuntimeError`. Eso
evita escrituras accidentales contra un Postgres no intencional.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - opcional en tests sin DB
    psycopg = None
    dict_row = None  # type: ignore[assignment]


class DatabaseUnavailableError(RuntimeError):
    """psycopg no está instalado o DATABASE_URL no está definido."""


# Alias retro-compatible (uso interno previo); puede removerse en próxima major.
DatabaseUnavailable = DatabaseUnavailableError


def _require_dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise DatabaseUnavailableError("DATABASE_URL no está definido en el entorno.")
    if psycopg is None:
        raise DatabaseUnavailableError(
            "psycopg no instalado. Reinstalá con `pip install -e .[dev]` en apps/engine."
        )
    return dsn


@contextmanager
def connect() -> Iterator[Any]:
    dsn = _require_dsn()
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        yield conn


# ============================================================================
# Bulk upserts del seed
# ============================================================================

def upsert_materias_primas(conn, items: list[dict]) -> int:
    sql = """
    INSERT INTO "MateriaPrima"
      (codigo, nombre, temporada_inicio_mes, temporada_fin_mes,
       humedad_inicial_pct, materia_solida_pct, aceite_extraible_pct,
       licopeno_pct, pectina_pct, tiempo_descomposicion_h, notas)
    VALUES (%(codigo)s, %(nombre)s, %(temporadaInicioMes)s, %(temporadaFinMes)s,
       %(humedadInicialPct)s, %(materiaSolidaPct)s, %(aceiteExtraiblePct)s,
       %(licopenoPct)s, %(pectinaPct)s, %(tiempoDescomposicionH)s, %(notas)s)
    ON CONFLICT (codigo) DO UPDATE SET
      nombre                  = EXCLUDED.nombre,
      humedad_inicial_pct     = EXCLUDED.humedad_inicial_pct,
      materia_solida_pct      = EXCLUDED.materia_solida_pct,
      aceite_extraible_pct    = EXCLUDED.aceite_extraible_pct,
      licopeno_pct            = EXCLUDED.licopeno_pct,
      pectina_pct             = EXCLUDED.pectina_pct,
      tiempo_descomposicion_h = EXCLUDED.tiempo_descomposicion_h,
      notas                   = EXCLUDED.notas;
    """
    with conn.cursor() as cur:
        for item in items:
            cur.execute(sql, _with_mmpp_defaults(item))
    return len(items)


def _with_mmpp_defaults(item: dict) -> dict:
    base = {
        "aceiteExtraiblePct": 0.0,
        "licopenoPct": 0.0,
        "pectinaPct": 0.0,
        "tiempoDescomposicionH": None,
        "notas": None,
    }
    base.update(item)
    return base


def upsert_suppliers(conn, items: list[dict]) -> int:
    sql = """
    INSERT INTO "Supplier"
      (nombre, mmpp_id, distancia_km, tarifa_flete_clp_km, caso_logistico,
       pago_recepcion_clp_kg, volumen_anual_comprometido_ton,
       capacidad_camion_ton, status)
    SELECT
      %(nombre)s,
      mp.id,
      %(distanciaKm)s, %(tarifaFleteClpKm)s, %(casoLogistico)s::"CasoLogistico",
      %(pagoRecepcionClpKg)s, %(volumenAnualComprometidoTon)s,
      %(capacidadCamionTon)s, %(status)s::"SupplierStatus"
    FROM "MateriaPrima" mp WHERE mp.codigo = %(mmppCodigo)s::"MMPPCodigo"
    ON CONFLICT (nombre) DO UPDATE SET
      distancia_km                   = EXCLUDED.distancia_km,
      tarifa_flete_clp_km            = EXCLUDED.tarifa_flete_clp_km,
      caso_logistico                 = EXCLUDED.caso_logistico,
      pago_recepcion_clp_kg          = EXCLUDED.pago_recepcion_clp_kg,
      volumen_anual_comprometido_ton = EXCLUDED.volumen_anual_comprometido_ton,
      capacidad_camion_ton           = EXCLUDED.capacidad_camion_ton,
      status                         = EXCLUDED.status,
      updated_at                     = now();
    """
    with conn.cursor() as cur:
        for item in items:
            cur.execute(sql, item)
    return len(items)


def upsert_productos(conn, items: list[dict]) -> int:
    sql = """
    INSERT INTO "Producto"
      (codigo, nombre, mmpp_origen_id, tipo, marca, ano_lanzamiento)
    SELECT %(codigo)s, %(nombre)s,
      (SELECT id FROM "MateriaPrima" WHERE codigo = %(mmppOrigen)s::"MMPPCodigo"),
      %(tipo)s::"TipoProducto",
      %(marca)s::"MarcaProducto",
      %(anoLanzamiento)s
    WHERE %(mmppOrigen)s IS NULL OR EXISTS
      (SELECT 1 FROM "MateriaPrima" WHERE codigo = %(mmppOrigen)s::"MMPPCodigo")
    ON CONFLICT (codigo) DO UPDATE SET
      nombre          = EXCLUDED.nombre,
      tipo            = EXCLUDED.tipo,
      marca           = EXCLUDED.marca,
      mmpp_origen_id  = EXCLUDED.mmpp_origen_id,
      ano_lanzamiento = EXCLUDED.ano_lanzamiento;
    """
    with conn.cursor() as cur:
        for item in items:
            cur.execute(sql, item)
    return len(items)


def upsert_supuestos(conn, items: list[dict]) -> int:
    sql = """
    INSERT INTO "Supuesto"
      (clave, valor_actual, unidad, fuente, estado, sensibilidad, owner, tag)
    VALUES (%(clave)s, %(valorActual)s, %(unidad)s, %(fuente)s,
       %(estado)s::"EstadoSupuesto", %(sensibilidad)s::"SensibilidadSupuesto",
       %(owner)s, %(tag)s)
    ON CONFLICT (clave) DO UPDATE SET
      valor_actual = EXCLUDED.valor_actual,
      unidad       = EXCLUDED.unidad,
      fuente       = EXCLUDED.fuente,
      estado       = EXCLUDED.estado,
      sensibilidad = EXCLUDED.sensibilidad,
      owner        = EXCLUDED.owner,
      tag          = EXCLUDED.tag,
      fecha_actualizacion = now();
    """
    with conn.cursor() as cur:
        for item in items:
            payload = {"unidad": None, "tag": None, "valorActual": None, **item}
            cur.execute(sql, payload)
    return len(items)


def upsert_capacidades(conn, items: list[dict]) -> int:
    sql = """
    INSERT INTO "CapacidadEquipo" (etapa, capacidad_ton_hora, tiempo_residencia_h, opcional)
    VALUES (%(etapa)s::"EtapaProceso", %(capacidadTonHora)s, %(tiempoResidenciaH)s, %(opcional)s)
    ON CONFLICT (etapa) DO UPDATE SET
      capacidad_ton_hora  = EXCLUDED.capacidad_ton_hora,
      tiempo_residencia_h = EXCLUDED.tiempo_residencia_h,
      opcional            = EXCLUDED.opcional,
      updated_at          = now();
    """
    with conn.cursor() as cur:
        for item in items:
            cur.execute(sql, item)
    return len(items)


# ============================================================================
# Lecturas
# ============================================================================

def list_supuestos_pd_por_sensibilidad(conn) -> list[dict]:
    sql = """
    SELECT clave, owner, sensibilidad, estado
    FROM "Supuesto"
    WHERE estado = 'PD'
    ORDER BY
      CASE sensibilidad
        WHEN 'CRITICA' THEN 1
        WHEN 'ALTA' THEN 2
        WHEN 'MEDIA' THEN 3
        WHEN 'BAJA' THEN 4
      END,
      owner;
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()


def get_capacidades_etapas(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            'SELECT etapa, capacidad_ton_hora, tiempo_residencia_h, opcional FROM "CapacidadEquipo"'
        )
        return cur.fetchall()


def get_suppliers_activos(conn, mmpp_codigo: str | None = None) -> list[dict]:
    sql = """
    SELECT s.id, s.nombre, mp.codigo AS mmpp_codigo, s.distancia_km, s.tarifa_flete_clp_km,
           s.caso_logistico, s.pago_recepcion_clp_kg, s.volumen_anual_comprometido_ton,
           s.capacidad_camion_ton, s.status
    FROM "Supplier" s
    JOIN "MateriaPrima" mp ON mp.id = s.mmpp_id
    WHERE s.status = 'ACTIVO'
    """
    params: list[Any] = []
    if mmpp_codigo:
        sql += ' AND mp.codigo = %s::"MMPPCodigo"'
        params.append(mmpp_codigo)
    sql += " ORDER BY s.nombre"
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def stats_resumen(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
              (SELECT count(*) FROM "MateriaPrima") AS mmpp,
              (SELECT count(*) FROM "Supplier")     AS suppliers,
              (SELECT count(*) FROM "Producto")     AS productos,
              (SELECT count(*) FROM "Supuesto")     AS supuestos_total,
              (SELECT count(*) FROM "Supuesto" WHERE estado = 'PD') AS supuestos_pd,
              (SELECT count(*) FROM "Supuesto" WHERE estado LIKE 'OK_VALIDADO%%') AS supuestos_validados,
              (SELECT count(*) FROM "CapacidadEquipo") AS capacidades,
              (SELECT count(*) FROM "PlanAnual") AS planes
            """
        )
        return cur.fetchone() or {}


# ============================================================================
# Snapshot inmutable (ADR-005)
# ============================================================================

def snapshot_plan(conn, plan_anual_id: int, aprobado_por: str, comentario: str | None = None) -> dict:
    """Crea VersionPlan con el snapshot completo del PlanAnual."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT row_to_json(p) AS plan FROM "PlanAnual" p WHERE id = %s', (plan_anual_id,)
        )
        plan = cur.fetchone()
        if not plan:
            raise ValueError(f"PlanAnual id={plan_anual_id} no existe")

        cur.execute(
            'SELECT json_agg(row_to_json(f)) AS flujos FROM "FlujoCaja" f WHERE plan_anual_id = %s',
            (plan_anual_id,),
        )
        flujos = cur.fetchone()["flujos"] or []

        cur.execute(
            'SELECT json_agg(row_to_json(s)) AS supuestos FROM "Supuesto" s'
        )
        supuestos = cur.fetchone()["supuestos"] or []

        snapshot = {"plan": plan["plan"], "flujos": flujos, "supuestos": supuestos}
        payload = json.dumps(snapshot, sort_keys=True, default=str).encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()

        cur.execute(
            """
            INSERT INTO "VersionPlan" (plan_anual_id, snapshot, aprobado_por, fecha_aprobacion, hash, comentario)
            VALUES (%s, %s::jsonb, %s, %s, %s, %s)
            RETURNING id, hash;
            """,
            (
                plan_anual_id,
                json.dumps(snapshot, default=str),
                aprobado_por,
                datetime.now(UTC),
                digest,
                comentario,
            ),
        )
        return cur.fetchone()
