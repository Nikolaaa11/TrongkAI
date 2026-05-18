"""Seed inicial de la DB Trongkai desde los 3 Excels del cliente.

Lee:
- contexto/Info_Plan_5_anos_Estructura_A.xlsx — proveedores + base rendimiento
- contexto/Cuadro_PPTO_Variables_PD_Plan_5_Anos_A.xlsx — supuestos (PD/OK) por SKU
- contexto/Tareas_Plan_5_anos.xlsx — backlog (NO se siembra a DB, queda en docs)

Resultado:
- Inserta 5 MateriaPrima, 10 Supplier (4 con datos + 6 placeholders), 12 Producto,
  ~70 Supuesto, 10 CapacidadEquipo (capacidades reales todas null/PD por ahora).

Uso:
    python scripts/seed-from-excel.py [--dry-run]

Requiere DATABASE_URL en .env. Si no hay DB conectada, --dry-run produce
`scripts/seed_dryrun.json` con el payload que se hubiera insertado.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
CTX = ROOT / "contexto"

INFO_FILE = CTX / "Info_Plan_5_anos_Estructura_A.xlsx"
CUADRO_FILE = CTX / "Cuadro_PPTO_Variables_PD_Plan_5_Anos_A.xlsx"


@dataclass
class SeedPayload:
    materias_primas: list[dict] = field(default_factory=list)
    suppliers: list[dict] = field(default_factory=list)
    productos: list[dict] = field(default_factory=list)
    supuestos: list[dict] = field(default_factory=list)
    capacidades: list[dict] = field(default_factory=list)


MMPP_CATALOGO = [
    dict(
        codigo="ALPERUJO",
        nombre="Alperujo de olivas",
        temporadaInicioMes=4,
        temporadaFinMes=6,
        humedadInicialPct=0.65,
        materiaSolidaPct=0.35,
        aceiteExtraiblePct=0.02,
        notas="Subproducto almazaras de oliva. Objetivo aceite 2% con PEF (competencia 1.3-1.45).",
    ),
    dict(
        codigo="TOMASA",
        nombre="Tomasa (subproducto tomate)",
        temporadaInicioMes=1,
        temporadaFinMes=3,
        humedadInicialPct=0.82,
        materiaSolidaPct=0.18,
        licopenoPct=0.001,
        pectinaPct=0.002,
        notas="Humedad ~82% — peor MS. Tiempo descomposición PD (estimado 3h).",
    ),
    dict(
        codigo="POMASA",
        nombre="Pomasa (manzana/pera)",
        temporadaInicioMes=3,
        temporadaFinMes=5,
        humedadInicialPct=0.80,
        materiaSolidaPct=0.20,
        pectinaPct=0.003,
    ),
    dict(
        codigo="ORUJO_UVA",
        nombre="Orujo de uva",
        temporadaInicioMes=4,
        temporadaFinMes=6,
        humedadInicialPct=None,
        materiaSolidaPct=None,
        notas="Humedad variable — pendiente medición.",
    ),
    dict(
        codigo="LEVADURA",
        nombre="Levadura (cerveza/vino)",
        temporadaInicioMes=1,
        temporadaFinMes=12,
        notas="Año corrido. PTEC: proteína unicelular.",
    ),
]


def parse_suppliers(ws) -> list[dict]:
    """Extrae los 4 oliveros con datos del Excel."""
    suppliers = []
    # Filas 5-14 = Olivero 1..10. Columnas B,C,D-F,G,H,I,J.
    for row in range(5, 15):
        nombre = ws.cell(row=row, column=2).value
        if not nombre:
            continue
        dist = ws.cell(row=row, column=3).value
        # Las filas con datos tienen costo flete en una de D/E/F según tarifa
        flete_1800 = ws.cell(row=row, column=4).value or 0
        flete_2100 = ws.cell(row=row, column=5).value or 0
        flete_2500 = ws.cell(row=row, column=6).value or 0
        # Caso heurístico: si está en D, tarifa 1800; en E, 2100; en F, 2500
        if flete_1800 and not isinstance(flete_1800, str):
            tarifa = 1800
        elif flete_2100 and not isinstance(flete_2100, str):
            tarifa = 2100
        elif flete_2500 and not isinstance(flete_2500, str):
            tarifa = 2500
        else:
            tarifa = 0
        pago_recepcion = ws.cell(row=row, column=8).value or 0
        volumen = ws.cell(row=row, column=9).value or 0
        cap_camion = ws.cell(row=row, column=10).value or 22.5
        caso_str = ws.cell(row=row, column=11).value or ""
        caso_logistico = {
            "Caso 1": "CASO_1",
            "Caso 2": "CASO_2",
            "Caso 3 ": "CASO_3",
            "Caso 3": "CASO_3",
            "Caso 4": "CASO_4",
        }.get(caso_str.strip() if isinstance(caso_str, str) else "", "CASO_3")

        if dist in (None, "") or not isinstance(dist, (int, float)):
            # Placeholder sin datos
            status = "PROSPECT"
            dist_val = 0.0
        else:
            status = "ACTIVO"
            dist_val = float(dist)

        suppliers.append(
            dict(
                nombre=nombre.strip(),
                mmppCodigo="ALPERUJO",  # esta hoja es solo oliveros
                distanciaKm=dist_val,
                tarifaFleteClpKm=float(tarifa),
                casoLogistico=caso_logistico,
                pagoRecepcionClpKg=float(pago_recepcion) if isinstance(pago_recepcion, (int, float)) else 0.0,
                volumenAnualComprometidoTon=float(volumen) if isinstance(volumen, (int, float)) else 0.0,
                capacidadCamionTon=float(cap_camion) if isinstance(cap_camion, (int, float)) else 22.5,
                status=status,
            )
        )
    return suppliers


PRODUCTOS_CATALOGO = [
    ("HARINA_ALPERUJO", "Harina de Alperujo", "ALPERUJO", "BASE", 1),
    ("ACEITE_ALPERUJO", "Aceite de Alperujo", "ALPERUJO", "BASE", 1),
    ("HARINA_ORUJO", "Harina de Orujo", "ORUJO_UVA", "BASE", 1),
    ("HARINA_TOMASA", "Harina de Tomasa", "TOMASA", "BASE", 1),
    ("HARINA_POMASA", "Harina de Pomasa", "POMASA", "BASE", 1),
    ("PECTINA", "Pectina", "POMASA", "AGREGADO", 2),
    ("LICOPENO", "Licopeno", "TOMASA", "AGREGADO", 2),
    ("PROTEINA_UNICEL", "Proteína Unicelular", "LEVADURA", "PTEC", 3),
    ("ANTIOXIDANTE", "Antioxidante", "ALPERUJO", "PTEC", 3),
    ("AGLOMERANTE", "Aglomerante", None, "PTEC", 4),
    ("UMAMI", "Umami", None, "PTEC", 5),
    ("ACEITE_ORUJO_UVA", "Aceite de Orujo (eventual)", "ORUJO_UVA", "BASE", 2),
]


def parse_supuestos_cuadro(ws) -> list[dict]:
    """Extrae los PD/OK/OK* de la matriz Datos x Plan 5 años."""
    out = []
    # Variables en columna B (fila 4..23), SKUs en columnas C..O fila 4.
    sku_headers = {}
    for col in range(3, 16):
        h = ws.cell(row=4, column=col).value
        if h:
            sku_headers[col] = h.strip()

    estado_map = {
        "PD": "PD",
        "OK": "OK_PROVISORIO",
        "OK*": "OK_PROVISORIO",
        "PD/2": "PD",
        "OK*/PD": "PD",
    }

    for row in range(4, 24):
        variable = ws.cell(row=row, column=2).value
        if not variable:
            continue
        for col, sku in sku_headers.items():
            v = ws.cell(row=row, column=col).value
            if v is None or v == "":
                continue
            v_str = str(v).strip()
            estado = estado_map.get(v_str, "NO_APLICA")
            clave = f"{variable.lower().replace(' ', '_').strip()}.{sku.lower().replace('.', '').replace(' ', '_')}"
            out.append(
                dict(
                    clave=clave[:200],
                    valorActual=None,
                    unidad=None,
                    fuente="Cuadro_PPTO_Variables_PD_Plan_5_Anos_A.xlsx",
                    estado=estado,
                    sensibilidad="MEDIA",
                    owner="Matías" if "Volumen" in variable or "Costo Transporte" in variable else "Jaime",
                )
            )
    return out


def parse_capacidades_pd() -> list[dict]:
    """Capacidades default — todas null/PD según SUPUESTOS.md."""
    etapas = [
        "RECEPCION",
        "ALIMENTACION",
        "HOMOG_1",
        "PEF",
        "PRENSADO_MECANICO",
        "TRICANTER",
        "EXTRACCION",
        "SECADO",
        "HOMOG_2",
        "ENSACADO",
    ]
    return [
        dict(
            etapa=e,
            capacidadTonHora=None,
            tiempoResidenciaH=None,
            opcional=(e in ("PEF", "TRICANTER", "EXTRACCION")),
        )
        for e in etapas
    ]


def build_payload() -> SeedPayload:
    payload = SeedPayload()
    payload.materias_primas = MMPP_CATALOGO

    wb_info = openpyxl.load_workbook(INFO_FILE, data_only=True)
    ws_prov = wb_info["IngresosCostos Proveedores"]
    payload.suppliers = parse_suppliers(ws_prov)

    payload.productos = [
        dict(codigo=c, nombre=n, mmppOrigen=m, tipo=t, anoLanzamiento=a) for c, n, m, t, a in PRODUCTOS_CATALOGO
    ]

    wb_cuadro = openpyxl.load_workbook(CUADRO_FILE, data_only=True)
    ws_datos = wb_cuadro["Datos x Plan 5 años"]
    payload.supuestos = parse_supuestos_cuadro(ws_datos)

    payload.capacidades = parse_capacidades_pd()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="No conectar a DB; volcar JSON.")
    args = parser.parse_args()

    payload = build_payload()

    if args.dry_run or "DATABASE_URL" not in __import__("os").environ:
        out_path = ROOT / "scripts" / "seed_dryrun.json"
        out_path.write_text(json.dumps(asdict(payload), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"[dry-run] Payload escrito en {out_path}")
        print(f"  - MMPP:        {len(payload.materias_primas)}")
        print(f"  - Suppliers:   {len(payload.suppliers)} ({sum(1 for s in payload.suppliers if s['status']=='ACTIVO')} activos)")
        print(f"  - Productos:   {len(payload.productos)}")
        print(f"  - Supuestos:   {len(payload.supuestos)}")
        print(f"  - Capacidades: {len(payload.capacidades)}")
        return 0

    # TODO: integrar con asyncpg/psycopg cuando DB esté disponible.
    print("DATABASE_URL detectado — pero el insert está pendiente de Fase 1.")
    print("Use --dry-run para validar el payload por ahora.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
