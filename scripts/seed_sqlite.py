"""Seed completo a SQLite local — alternativa a Postgres para dev/demo.

Lee del seed_dryrun.json (generado por seed-from-excel.py --dry-run) y carga
todo a un archivo SQLite local. Útil para demos sin docker.

Uso:
    python scripts/seed_sqlite.py [--db path/to/trongkai.db]

Resultado: DB con 5 MMPP, 9 suppliers, 12 productos, 165 supuestos, 10 capacidades.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRYRUN_JSON = ROOT / "scripts" / "seed_dryrun.json"
MIGRATION_SQL = ROOT / "packages" / "db" / "prisma" / "migrations" / "0001_init" / "migration.sqlite.sql"


def setup_schema(conn: sqlite3.Connection) -> None:
    sql = MIGRATION_SQL.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def insert_payload(conn: sqlite3.Connection, payload: dict) -> dict:
    counts = {}
    cur = conn.cursor()

    # MMPP
    cur.executemany(
        """
        INSERT OR REPLACE INTO "MateriaPrima"
          (codigo, nombre, temporada_inicio_mes, temporada_fin_mes,
           humedad_inicial_pct, materia_solida_pct, aceite_extraible_pct,
           licopeno_pct, pectina_pct, tiempo_descomposicion_h, notas)
        VALUES (:codigo, :nombre, :temporadaInicioMes, :temporadaFinMes,
           :humedadInicialPct, :materiaSolidaPct, :aceiteExtraiblePct,
           :licopenoPct, :pectinaPct, :tiempoDescomposicionH, :notas)
        """,
        [
            {
                "codigo": m["codigo"],
                "nombre": m["nombre"],
                "temporadaInicioMes": m["temporadaInicioMes"],
                "temporadaFinMes": m["temporadaFinMes"],
                "humedadInicialPct": m.get("humedadInicialPct"),
                "materiaSolidaPct": m.get("materiaSolidaPct"),
                "aceiteExtraiblePct": m.get("aceiteExtraiblePct", 0),
                "licopenoPct": m.get("licopenoPct", 0),
                "pectinaPct": m.get("pectinaPct", 0),
                "tiempoDescomposicionH": m.get("tiempoDescomposicionH"),
                "notas": m.get("notas"),
            }
            for m in payload["materias_primas"]
        ],
    )
    counts["materias_primas"] = len(payload["materias_primas"])

    # Suppliers (resolviendo mmpp_id por código)
    for s in payload["suppliers"]:
        cur.execute(
            """
            INSERT OR REPLACE INTO "Supplier"
              (nombre, mmpp_id, distancia_km, tarifa_flete_clp_km, caso_logistico,
               pago_recepcion_clp_kg, volumen_anual_comprometido_ton, capacidad_camion_ton, status)
            SELECT ?, mp.id, ?, ?, ?, ?, ?, ?, ?
            FROM "MateriaPrima" mp WHERE mp.codigo = ?
            """,
            (s["nombre"], s["distanciaKm"], s["tarifaFleteClpKm"], s["casoLogistico"],
             s["pagoRecepcionClpKg"], s["volumenAnualComprometidoTon"], s["capacidadCamionTon"],
             s["status"], s["mmppCodigo"]),
        )
    counts["suppliers"] = len(payload["suppliers"])

    # Productos
    for p in payload["productos"]:
        cur.execute(
            """
            INSERT OR REPLACE INTO "Producto"
              (codigo, nombre, mmpp_origen_id, tipo, marca, ano_lanzamiento)
            SELECT ?, ?,
              (SELECT id FROM "MateriaPrima" WHERE codigo = ?),
              ?, ?, ?
            """,
            (p["codigo"], p["nombre"], p.get("mmppOrigen"), p["tipo"], p["marca"], p["anoLanzamiento"]),
        )
    counts["productos"] = len(payload["productos"])

    # Supuestos
    for s in payload["supuestos"]:
        cur.execute(
            """
            INSERT OR REPLACE INTO "Supuesto"
              (clave, valor_actual, unidad, fuente, estado, sensibilidad, owner, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (s["clave"], s.get("valorActual"), s.get("unidad"), s["fuente"],
             s["estado"], s["sensibilidad"], s.get("owner"), s.get("tag")),
        )
    counts["supuestos"] = len(payload["supuestos"])

    # Capacidades
    for c in payload["capacidades"]:
        cur.execute(
            """
            INSERT OR REPLACE INTO "CapacidadEquipo"
              (etapa, capacidad_ton_hora, tiempo_residencia_h, opcional)
            VALUES (?, ?, ?, ?)
            """,
            (c["etapa"], c.get("capacidadTonHora"), c.get("tiempoResidenciaH"),
             1 if c.get("opcional") else 0),
        )
    counts["capacidades"] = len(payload["capacidades"])

    conn.commit()
    return counts


def stats(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()
    out = {}
    for t in ("MateriaPrima", "Supplier", "Producto", "Supuesto", "CapacidadEquipo"):
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        out[t] = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "Supuesto" WHERE estado = ?', ("PD",))
    out["supuestos_pd"] = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "Supuesto" WHERE estado LIKE ?', ("OK_VALIDADO%",))
    out["supuestos_validados"] = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM "Supuesto" WHERE estado = ?', ("OK_PROVISORIO",))
    out["supuestos_ok_prov"] = cur.fetchone()[0]
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(ROOT / "scripts" / "trongkai_local.db"))
    args = parser.parse_args()

    if not DRYRUN_JSON.exists():
        print(f"FALTA: {DRYRUN_JSON}. Correr primero: python scripts/seed-from-excel.py --dry-run", file=sys.stderr)
        return 1

    payload = json.loads(DRYRUN_JSON.read_text(encoding="utf-8"))

    db_path = Path(args.db)
    if db_path.exists():
        db_path.unlink()  # idempotente: reset
    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")

    setup_schema(conn)
    insert_payload(conn, payload)
    s = stats(conn)
    conn.close()

    print(f"[OK] SQLite DB: {args.db}")
    print(f"  MMPP:                {s['MateriaPrima']}")
    print(f"  Suppliers:           {s['Supplier']}")
    print(f"  Productos:           {s['Producto']}")
    print(f"  Supuestos total:     {s['Supuesto']}")
    print(f"    PD:                {s['supuestos_pd']}")
    print(f"    OK_PROVISORIO:     {s['supuestos_ok_prov']}")
    print(f"    OK_VALIDADO_*:     {s['supuestos_validados']}")
    print(f"  Capacidades:         {s['CapacidadEquipo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
