"""Importador del dump P1 → inbox/ con clasificación automática.

Mapea las 7 carpetas del dump P1 (Clientes, Cotizaciones, Finanzas,
Ingeniería, Productos, Tecnologías) a las categorías correctas del inbox.

Usage:
    python scripts/import_dump_p1.py [--dry-run] [--no-process]

Mapeo:
    P1/Clientes/*          → inbox/01-comercial/contratos-firmados/  (subcarpetas clientes)
    P1/Clientes/*.pdf      → inbox/07-mercado/benchmarks-precios/    (PDFs especs proteínas)
    P1/Cotizaciones/*      → inbox/02-financiero/capex-cotizaciones/
    P1/Finanzas/*.xlsm     → inbox/02-financiero/eerr-historicos/
    P1/Ingeniería/Layout   → inbox/03-operacional/capacidad-equipos/
    P1/Ingeniería/PCI      → inbox/03-operacional/consumo-energetico/
    P1/Ingeniería/PEF      → inbox/03-operacional/rendimientos-medidos/
    P1/Ingeniería/*        → inbox/03-operacional/cronograma-obra/
    P1/Productos/*         → inbox/03-operacional/rendimientos-medidos/
    P1/Tecnologías/*       → inbox/03-operacional/capacidad-equipos/
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
INBOX = ROOT / "inbox"
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Default dump location (puede pasarse via --source)
DEFAULT_DUMP = Path("C:/Users/nicol/OneDrive/Documentos/0.1.1 TrongkAI/P1-20260529T181108Z-3-001/P1")


def _filename_pcs_pef(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in ("pef", "deshidrat", "pulsator", "opticept", "infrasonido", "micro molienda", "micromolien"))


def _filename_pci(name: str) -> bool:
    n = name.lower()
    return "pci" in n or "calorific" in n or "calor" in n


def _filename_layout(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in ("layout", "plano", "planos", "p&id", "pid"))


def _filename_resultados(name: str) -> bool:
    n = name.lower()
    return any(kw in n for kw in ("resultado", "prueba", "test ", "ensayo"))


def categorizar_archivo(src: Path, p1_subdir: str) -> tuple[str, str] | None:
    """Devuelve (categoria_inbox, subcategoria) o None si skip.
    p1_subdir: 'Clientes' | 'Cotizaciones' | 'Finanzas' | 'Ingeniería' | 'Productos' | 'Tecnologías'
    """
    name = src.name
    name_lower = name.lower()
    suffix = src.suffix.lower()

    if p1_subdir == "Clientes":
        # PDFs sueltos en raíz = especs benchmark de competencia/insumos
        # Carpetas con nombre de cliente = info de clientes (LOIs, contratos potenciales)
        if suffix == ".pdf" and any(kw in name_lower for kw in ("protein", "powder", "concentrate", "yellow pea", "fava")):
            return ("07-mercado", "benchmarks-precios")
        return ("01-comercial", "contratos-firmados")

    if p1_subdir == "Cotizaciones":
        return ("02-financiero", "capex-cotizaciones")

    if p1_subdir == "Finanzas":
        return ("02-financiero", "eerr-historicos")

    if p1_subdir == "Ingeniería":
        if _filename_layout(name_lower):
            return ("03-operacional", "capacidad-equipos")
        if _filename_pci(name_lower):
            return ("03-operacional", "consumo-energetico")
        if _filename_pcs_pef(name_lower):
            return ("03-operacional", "rendimientos-medidos")
        if "etapa" in name_lower or "propuesta" in name_lower or "cronograma" in name_lower:
            return ("03-operacional", "cronograma-obra")
        return ("03-operacional", "capacidad-equipos")  # default

    if p1_subdir == "Productos":
        if _filename_resultados(name_lower):
            return ("03-operacional", "rendimientos-medidos")
        return ("01-comercial", "contratos-firmados")  # productos terminados

    if p1_subdir == "Tecnologías":
        return ("03-operacional", "capacidad-equipos")

    return None


def importar_dump(source: Path, dry_run: bool = False) -> dict:
    """Camina recursivamente y copia archivos manteniendo metadata jerárquica."""
    stats = {
        "encontrados": 0,
        "copiados": 0,
        "skipped": 0,
        "errores": 0,
        "por_categoria": {},
        "archivos": [],
    }

    if not source.exists():
        print(f"ERROR: No existe {source}")
        return stats

    for p1_subdir_path in source.iterdir():
        if not p1_subdir_path.is_dir():
            continue
        p1_subdir = p1_subdir_path.name  # 'Clientes', 'Cotizaciones', etc.

        print(f"\n=== {p1_subdir} ===")

        # Recorrer todos los archivos recursivamente
        for archivo in p1_subdir_path.rglob("*"):
            if not archivo.is_file():
                continue
            # Saltar archivos del sistema
            if archivo.name.startswith(".") or archivo.name.startswith("~$"):
                continue

            stats["encontrados"] += 1
            rel_from_p1 = archivo.relative_to(p1_subdir_path)
            cat_info = categorizar_archivo(archivo, p1_subdir)

            if cat_info is None:
                stats["skipped"] += 1
                print(f"  [SKIP] {rel_from_p1}")
                continue

            categoria, subcat = cat_info
            # Preservar jerarquía: si rel_from_p1 tiene subcarpetas, las mantenemos
            # bajo un prefijo del cliente/equipo
            sub_partes = rel_from_p1.parts
            if len(sub_partes) > 1:
                # Hay subcarpeta en P1 → preservar como prefijo
                prefijo = "_".join(sub_partes[:-1])
                target_name = f"{prefijo}__{archivo.name}"
            else:
                target_name = archivo.name

            dest_dir = INBOX / categoria / subcat
            dest = dest_dir / target_name

            try:
                if dry_run:
                    print(f"  [DRY] {rel_from_p1}  →  {categoria}/{subcat}/{target_name}")
                else:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(archivo), str(dest))
                    print(f"  [OK]  {rel_from_p1}  →  {categoria}/{subcat}/{target_name}")
                stats["copiados"] += 1
                key = f"{categoria}/{subcat}"
                stats["por_categoria"][key] = stats["por_categoria"].get(key, 0) + 1
                stats["archivos"].append({
                    "src": str(rel_from_p1),
                    "dest": f"{categoria}/{subcat}/{target_name}",
                    "size_kb": archivo.stat().st_size / 1024,
                })
            except Exception as e:
                stats["errores"] += 1
                print(f"  [ERR] {rel_from_p1}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=str(DEFAULT_DUMP), help="Path al dump P1")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se haría, sin copiar")
    parser.add_argument("--no-process", action="store_true", help="No ejecutar procesar_inbox.py después")
    args = parser.parse_args()

    source = Path(args.source)
    print(f"Fuente: {source}")
    print(f"Destino: {INBOX}")
    if args.dry_run:
        print("*** DRY RUN — no se copia nada ***")
    print()

    stats = importar_dump(source, dry_run=args.dry_run)

    print()
    print("=" * 60)
    print("RESUMEN IMPORTACION")
    print("=" * 60)
    print(f"Encontrados: {stats['encontrados']}")
    print(f"Copiados:    {stats['copiados']}")
    print(f"Skipped:     {stats['skipped']}")
    print(f"Errores:     {stats['errores']}")
    print()
    print("Por categoria destino:")
    for cat, n in sorted(stats["por_categoria"].items()):
        print(f"  {cat:50s} {n:3d}")
    print()

    if not args.dry_run and not args.no_process and stats["copiados"] > 0:
        print("Procesando inbox (clasificador + text extractor + sync)...")
        print()
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "procesar_inbox.py")],
            cwd=str(ROOT),
            capture_output=False,
        )
        print()
        if result.returncode == 0:
            print("OK Inbox procesado.")
        else:
            print("WARN procesar_inbox.py retorno codigo no-cero.")


if __name__ == "__main__":
    main()
