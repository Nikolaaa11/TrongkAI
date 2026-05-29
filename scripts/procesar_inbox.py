"""Procesar Inbox - clasificador inteligente de archivos nuevos.

Usage:
    python scripts/procesar_inbox.py             # Procesa lo nuevo
    python scripts/procesar_inbox.py --status    # Solo muestra estado
    python scripts/procesar_inbox.py --reprocess-all  # Re-procesa todo

Para cada archivo nuevo:
1. Calcula hash MD5 (detecta duplicados)
2. Infiere categoría desde el path
3. Sugiere celdas de matriz a actualizar (keywords del filename)
4. Registra evento en audit trail
5. Indexa en inbox/_index.json
6. NO mueve a _procesados automáticamente (requiere --move)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Permitir import del engine
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "apps" / "engine"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

INBOX = ROOT / "inbox"
INDEX_FILE = INBOX / "_index.json"
PROCESADOS = INBOX / "_procesados"


def _hash_md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def _categoria_desde_path(p: Path) -> str:
    """Infiere categoría desde el path relativo al inbox."""
    try:
        rel = p.relative_to(INBOX)
        parts = rel.parts
        if len(parts) >= 1:
            return parts[0]  # ej "01-comercial"
    except ValueError:
        pass
    return "99-sin-clasificar"


def _subcategoria_desde_path(p: Path) -> str:
    try:
        rel = p.relative_to(INBOX)
        parts = rel.parts
        if len(parts) >= 2:
            return parts[1]  # ej "cotizaciones-mmpp"
    except ValueError:
        pass
    return ""


# Regex de keywords que sugieren actualizar celdas específicas
SUGERENCIAS_KEYWORDS = [
    # (regex_path_or_filename, descripcion, celdas_sugeridas)
    (r"cotizacion.*mmpp|mmpp.*cotizacion|alperujo|tomasa|pomasa|orujo", "Cotización MMPP",
     ["Precio Recepción Subproducto", "Costo Transporte Subproducto"]),
    (r"loi|carta.*intencion|letter.*intent", "LOI cliente firmada",
     ["Precio de Venta"]),
    (r"opex.*mensual|mes.*opex|contadora.*mes", "OpEx mensual real",
     ["Costo Administración", "Costo Energía", "Costo Servicios Generales", "Costo Mantención Industrial"]),
    (r"term.*sheet|bice|santander.*term", "Term sheet bancario",
     ["Financiamiento → DSCR/LLCR"]),
    (r"capex.*cotiz|cotiz.*equipo|secador.*spec|prensa.*spec", "CapEx cotización equipo",
     ["CapEx anual"]),
    (r"rendimiento.*medido|piloto.*planta|prueba.*kg", "Rendimiento medido planta",
     ["Rendimiento"]),
    (r"haccp|gmp\+|b.corp|iso.*certif|certificacion", "Certificación ESG/QA",
     ["Data Room: certificaciones-esg"]),
    (r"rca|rup|sag|seremi|permiso.*sanit", "Permiso sanitario/ambiental",
     ["Data Room: rca, permisos-sanitarios"]),
    (r"escritura|estatutos.*soc|constituc", "Documento societario legal",
     ["Data Room: escritura-constitucion, estatutos"]),
    (r"cv|curriculum|bio.*adv", "CV o bio (equipo/advisor)",
     ["Data Room: cvs-fundadores"]),
    (r"mou|alianza|partnership.*acuerdo|convenio", "Alianza estratégica / MOU",
     ["Data Room: alianzas-estrategicas"]),
    (r"paper|estudio|research|publicacion|peer.review", "Paper científico",
     ["docs/PAPERS-CIENTIFICOS.md → calibración benchmarks"]),
    (r"lca|huella.*carbono|carbon.*foot", "LCA medido",
     ["/carbono validar baseline"]),
]


def sugerir_actualizaciones(filename: str, categoria: str, subcategoria: str) -> list[dict]:
    """Detecta keywords en filename y devuelve sugerencias de actualización."""
    fn_lower = (filename + " " + subcategoria).lower()
    sugerencias = []
    for pattern, desc, celdas in SUGERENCIAS_KEYWORDS:
        if re.search(pattern, fn_lower):
            sugerencias.append({
                "tipo_dato": desc,
                "celdas_o_modulo": celdas,
                "confianza": "alta" if re.search(pattern, subcategoria.lower()) else "media",
            })
    return sugerencias


def cargar_index() -> dict:
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"archivos": {}, "version": 1}
    return {"archivos": {}, "version": 1}


def guardar_index(idx: dict) -> None:
    INDEX_FILE.write_text(json.dumps(idx, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def listar_archivos_inbox(incluir_procesados: bool = False) -> list[Path]:
    """Lista archivos válidos en el inbox (excluye .gitkeep, README.md, _procesados/, _index.json)."""
    archivos = []
    for p in INBOX.rglob("*"):
        if not p.is_file():
            continue
        if p.name in (".gitkeep", "README.md") or p.name.startswith("_"):
            continue
        if not incluir_procesados and "_procesados" in p.parts:
            continue
        archivos.append(p)
    return sorted(archivos)


def procesar_archivo(p: Path, idx: dict, log_audit: bool = True) -> dict:
    """Procesa UN archivo: indexa, clasifica, extrae contenido, sugiere, registra."""
    hash_md5 = _hash_md5(p)
    rel_path = str(p.relative_to(ROOT)).replace("\\", "/")
    categoria = _categoria_desde_path(p)
    subcategoria = _subcategoria_desde_path(p)
    size_kb = p.stat().st_size / 1024

    # Sugerencias basadas en nombre + path
    sugerencias = sugerir_actualizaciones(p.name, categoria, subcategoria)

    # NUEVO: extraer texto y entidades del contenido
    extraccion = {}
    entidades = {}
    metodo_extraccion = "skipped"
    try:
        from text_extractor import extraer_texto, resumen_entidades
        ext_result = extraer_texto(p)
        metodo_extraccion = ext_result["metodo"]
        entidades = ext_result["entidades"]
        extraccion = {
            "metodo": metodo_extraccion,
            "longitud_texto": len(ext_result["texto"]),
            "resumen_entidades": resumen_entidades(entidades),
        }
        # Sugerencias adicionales basadas en contenido extraído
        texto_lower = ext_result["texto"].lower()
        sugerencias_contenido = sugerir_actualizaciones(texto_lower[:500], categoria, subcategoria)
        # Merge sin duplicados
        existing_tipos = {s["tipo_dato"] for s in sugerencias}
        for sc in sugerencias_contenido:
            if sc["tipo_dato"] not in existing_tipos:
                sc["confianza"] = "media"  # Detectado en contenido, no en nombre
                sc["fuente"] = "contenido"
                sugerencias.append(sc)
    except ImportError:
        pass
    except Exception as e:
        extraccion = {"error": str(e), "metodo": metodo_extraccion}

    entry = {
        "ruta": rel_path,
        "filename": p.name,
        "hash_md5": hash_md5,
        "categoria": categoria,
        "subcategoria": subcategoria,
        "size_kb": round(size_kb, 1),
        "extension": p.suffix.lower(),
        "fecha_procesado": datetime.now(timezone.utc).isoformat(),
        "sugerencias": sugerencias,
        "extraccion": extraccion,
        "entidades": entidades,
    }

    # Detectar duplicado por hash
    es_duplicado = False
    for existing_hash, existing_entry in idx["archivos"].items():
        if existing_hash == hash_md5:
            es_duplicado = True
            entry["duplicado_de"] = existing_entry.get("ruta", "")
            break

    idx["archivos"][hash_md5] = entry

    # Registrar en audit trail
    if log_audit and not es_duplicado:
        try:
            from trongkai_engine.audit_trail import log_evento
            sugerencias_str = "; ".join(s["tipo_dato"] for s in sugerencias) if sugerencias else "(sin sugerencias automáticas)"
            log_evento(
                tipo="datos_equipo_recibidos",
                descripcion=f"Inbox: {p.name} ({categoria}/{subcategoria}) - {sugerencias_str}",
                actor="inbox-classifier",
                metadata={
                    "ruta": rel_path,
                    "hash": hash_md5,
                    "size_kb": entry["size_kb"],
                    "sugerencias": sugerencias,
                },
                impacto_estimado=f"Sugerencias: {len(sugerencias)} celdas/módulos potencialmente actualizables",
            )
        except Exception as e:
            print(f"  [WARN] No se pudo registrar audit: {e}")

    return entry


def render_status(idx: dict) -> str:
    """Reporta estado del inbox."""
    archivos = listar_archivos_inbox()
    procesados = list(PROCESADOS.rglob("*")) if PROCESADOS.exists() else []

    por_cat: dict[str, int] = {}
    sugerencias_total = 0
    for h, e in idx["archivos"].items():
        cat = e.get("categoria", "?")
        por_cat[cat] = por_cat.get(cat, 0) + 1
        sugerencias_total += len(e.get("sugerencias", []))

    out = []
    out.append("=" * 60)
    out.append("INBOX TRONGKAI - Estado")
    out.append("=" * 60)
    out.append(f"Archivos en inbox/ (sin procesar): {len(archivos)}")
    out.append(f"Archivos en _procesados/:          {len(procesados)}")
    out.append(f"Total indexados en _index.json:    {len(idx['archivos'])}")
    out.append(f"Sugerencias automáticas totales:   {sugerencias_total}")
    out.append("")
    out.append("Por categoría:")
    for cat in sorted(por_cat.keys()):
        out.append(f"  {cat:30s} {por_cat[cat]:3d} archivos")
    out.append("")
    return "\n".join(out)


def sync_a_engine(idx: dict, engine_url: str = "https://trongkai-engine.fly.dev") -> bool:
    """Sube el _index.json al engine para que /inbox/status web lo vea."""
    try:
        import urllib.request
        data = json.dumps({"archivos": idx.get("archivos", {}), "version": idx.get("version", 1)}).encode("utf-8")
        req = urllib.request.Request(
            f"{engine_url}/inbox/sync",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  [WARN] Sync engine falló: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Solo mostrar estado")
    parser.add_argument("--reprocess-all", action="store_true", help="Re-procesar todo (incluye _procesados)")
    parser.add_argument("--move", action="store_true", help="Mover archivos a _procesados/ tras procesar")
    parser.add_argument("--no-sync", action="store_true", help="No sincronizar al engine prod")
    args = parser.parse_args()

    if not INBOX.exists():
        print(f"ERROR: No existe carpeta {INBOX}")
        sys.exit(1)

    idx = cargar_index()

    if args.status:
        print(render_status(idx))
        return

    archivos = listar_archivos_inbox(incluir_procesados=args.reprocess_all)

    if not archivos:
        print("Inbox vacío. Nada que procesar.")
        print()
        print(render_status(idx))
        return

    print(f"Procesando {len(archivos)} archivo(s)...")
    print()

    procesados_count = 0
    duplicados_count = 0
    for p in archivos:
        hash_actual = _hash_md5(p)
        es_nuevo = hash_actual not in idx["archivos"]
        entry = procesar_archivo(p, idx, log_audit=es_nuevo)
        if entry.get("duplicado_de"):
            duplicados_count += 1
            print(f"  [DUP] {p.relative_to(INBOX)} (duplicado de {entry['duplicado_de']})")
        else:
            procesados_count += 1
            print(f"  [OK]  {p.relative_to(INBOX)} ({entry['size_kb']:.1f} KB)")
            if entry["sugerencias"]:
                for s in entry["sugerencias"]:
                    celdas = s["celdas_o_modulo"]
                    celdas_str = ", ".join(celdas) if isinstance(celdas, list) else str(celdas)
                    print(f"        -> Sugiere: {s['tipo_dato']} ({s['confianza']}) -> {celdas_str}")

        if args.move and not entry.get("duplicado_de"):
            try:
                rel = p.relative_to(INBOX)
                destino = PROCESADOS / rel
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(destino))
            except Exception as e:
                print(f"        [WARN] No se pudo mover: {e}")

    guardar_index(idx)

    # Sync al engine prod (para que /inbox/status web lo vea)
    if not args.no_sync:
        print()
        print("Sincronizando al engine prod...")
        if sync_a_engine(idx):
            print("  [OK] Sync exitoso → /inbox/status actualizado en https://trongkai-web.vercel.app/inbox")
        else:
            print("  [WARN] Sync omitido (sin conexión o engine down). Local OK igual.")

    print()
    print(f"OK Procesados: {procesados_count}  |  Duplicados: {duplicados_count}")
    print()
    print(render_status(idx))


if __name__ == "__main__":
    main()
