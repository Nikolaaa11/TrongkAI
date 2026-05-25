'use client';

import Image from 'next/image';
import { useEffect, useMemo, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Estado = 'PD' | 'OK_PROVISORIO' | 'OK_VALIDADO';

type Celda = {
  variable: string;
  producto: string;
  valor: number | null;
  unidad: string;
  estado: Estado;
  fuente: string;
  nota: string;
};

type Producto = {
  codigo: string;
  nombre: string;
  grupo: string;
  mmpp_origen: string;
};

type MatrizResp = {
  productos: Producto[];
  variables: string[];
  celdas: Celda[];
  stats: {
    total: number;
    PD: number;
    OK_PROVISORIO: number;
    OK_VALIDADO: number;
    pct_cubierto: number;
    pct_validado: number;
  };
};

type IntelligenceResp = {
  inconsistencias: {
    severidad: string;
    tipo: string;
    descripcion: string;
    celdas_involucradas: string[];
  }[];
  sugerencias: {
    variable: string;
    producto: string;
    valor_sugerido: number;
    unidad: string;
    razonamiento: string;
    confianza: number;
  }[];
  confianza_promedio: number;
  confianza_por_grupo: Record<string, number>;
  celdas_criticas: { variable: string; producto: string; producto_nombre: string; grupo: string }[];
};

const COLOR_GRUPO: Record<string, string> = {
  'Base Harinas y Aceite': 'bg-ink-50 text-ink-600',
  'Productos Finales II': 'bg-orange-50 text-orange-600',
  'Productos PTEC': 'bg-brand-50 text-brand',
};

export default function VariablesPage() {
  const [data, setData] = useState<MatrizResp | null>(null);
  const [intelligence, setIntelligence] = useState<IntelligenceResp | null>(null);
  const [celdaSel, setCeldaSel] = useState<Celda | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
    void cargarIntelligence();
  }, []);

  async function cargar() {
    try {
      const r = await fetch(`${ENGINE_URL}/variables/matrix`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    }
  }

  async function cargarIntelligence() {
    try {
      const r = await fetch(`${ENGINE_URL}/variables/intelligence`);
      if (r.ok) setIntelligence(await r.json());
    } catch (e) {
      console.error('intelligence', e);
    }
  }

  // Encuentra sugerencia para una celda específica
  const sugerenciaParaCelda = (variable: string, producto: string) => {
    return intelligence?.sugerencias.find(
      (s) => s.variable === variable && s.producto === producto,
    );
  };

  // Buscar celda por variable + producto
  const celdaIndex = useMemo(() => {
    if (!data) return new Map<string, Celda>();
    return new Map(data.celdas.map((c) => [`${c.variable}|${c.producto}`, c]));
  }, [data]);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Variables Ingredientes Plan 5 Años</h1>
          <p className="mt-2 text-sm text-ink-400">
            Matriz canónica del Excel original. 11 productos × 15 variables = 165 celdas
            con estado de validación trazable. Click en cualquier celda para ver fuente y nota.
          </p>
        </div>
      </header>

      {err && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {err}
        </div>
      )}

      {/* ===== INTELLIGENCE BANNER ===== */}
      {intelligence && (
        <section className="rounded-appleXl bg-brand-50 p-6 ring-1 ring-brand/20">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
                🧠 Matriz Inteligente
              </div>
              <h2 className="mt-1 text-2xl font-semibold tracking-apple text-ink">
                Confianza promedio: {intelligence.confianza_promedio.toFixed(0)}/100
              </h2>
              <p className="mt-1 text-sm text-ink-600">
                {intelligence.inconsistencias.length === 0
                  ? '✓ Cero inconsistencias detectadas. Matriz matemáticamente coherente.'
                  : `⚠ ${intelligence.inconsistencias.length} inconsistencias detectadas`}
                {' · '}
                {intelligence.sugerencias.length} sugerencias automáticas disponibles
                {' · '}
                {intelligence.celdas_criticas.length} celdas críticas (PD en variables clave)
              </p>
            </div>
          </div>

          {/* Confianza por grupo */}
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            {Object.entries(intelligence.confianza_por_grupo).map(([grupo, score]) => (
              <div key={grupo} className="rounded-lg bg-white p-3">
                <div className="text-[10px] uppercase tracking-wider text-ink-400">{grupo}</div>
                <div className="mt-1 flex items-baseline gap-2">
                  <div className="tabular text-2xl font-semibold text-ink">{score.toFixed(0)}</div>
                  <div className="text-xs text-ink-400">/ 100</div>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
                  <div
                    className="h-full bg-brand transition-all"
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ===== INCONSISTENCIAS ===== */}
      {intelligence && intelligence.inconsistencias.length > 0 && (
        <section className="apple-card border border-red-200 bg-red-50/40">
          <h2 className="text-lg font-semibold text-red-600">
            ⚠ Inconsistencias detectadas ({intelligence.inconsistencias.length})
          </h2>
          <ul className="mt-3 space-y-2">
            {intelligence.inconsistencias.slice(0, 5).map((i, idx) => (
              <li key={idx} className="rounded-lg bg-white p-3 text-sm">
                <span className="font-semibold text-red-600">[{i.severidad}]</span>{' '}
                <span className="text-ink-600">{i.descripcion}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ===== CELDAS CRÍTICAS (TOP 5 PD en variables clave) ===== */}
      {intelligence && intelligence.celdas_criticas.length > 0 && (
        <section className="apple-card">
          <h2 className="text-lg font-semibold text-ink">
            🎯 Celdas críticas — atacar primero estas ({intelligence.celdas_criticas.length})
          </h2>
          <p className="mt-1 text-sm text-ink-400">
            Celdas PD en variables clave (Precio, Rendimiento, Costo Producción). Cierra estas primero para máximo uplift en TIR.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2">
            {intelligence.celdas_criticas.slice(0, 8).map((c, idx) => {
              const sug = sugerenciaParaCelda(c.variable, c.producto);
              return (
                <div key={idx} className="rounded-lg bg-ink-50 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-ink">{c.producto_nombre}</div>
                      <div className="text-xs text-ink-600">{c.variable}</div>
                      <div className="text-[10px] uppercase tracking-wider text-ink-400">{c.grupo}</div>
                    </div>
                    {sug && (
                      <div className="text-right">
                        <div className="text-[10px] uppercase tracking-wider text-brand">Sugerido</div>
                        <div className="tabular text-sm font-semibold text-brand">
                          {sug.valor_sugerido.toLocaleString('es-CL', { maximumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] text-ink-400">{sug.unidad}</div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {data && (
        <>
          {/* Stats agregadas */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total celdas" value={data.stats.total} sub="11 × 15" />
            <StatCard label="PD (Por Definir)" value={data.stats.PD} sub={`${(data.stats.PD/data.stats.total*100).toFixed(0)}%`} tone="warn" />
            <StatCard label="OK Provisorio" value={data.stats.OK_PROVISORIO} sub={`${data.stats.pct_cubierto}% cubierto`} tone="mid" />
            <StatCard label="OK Validado" value={data.stats.OK_VALIDADO} sub={`${data.stats.pct_validado}% validado`} tone="ok" />
          </section>

          {/* Leyenda */}
          <section className="flex flex-wrap items-center gap-4 text-xs text-ink-600">
            <span className="font-semibold uppercase tracking-wider text-ink-400">Leyenda:</span>
            <Pill estado="PD" />
            <Pill estado="OK_PROVISORIO" />
            <Pill estado="OK_VALIDADO" />
          </section>

          {/* Matriz */}
          <section className="apple-card overflow-x-auto p-0">
            <table className="w-full border-collapse text-[12px]">
              <thead>
                {/* Fila de grupos */}
                <tr>
                  <th className="sticky left-0 z-10 border-b border-r border-ink-100 bg-white p-2 text-left">
                    <div className="text-[10px] uppercase tracking-wider text-ink-400">Tons</div>
                    <div className="tabular text-sm font-semibold text-ink">50.000</div>
                  </th>
                  {renderGrupos(data.productos)}
                </tr>
                {/* Fila de productos */}
                <tr>
                  <th className="sticky left-0 z-10 border-b border-r border-ink-100 bg-white"></th>
                  {data.productos.map((p) => (
                    <th
                      key={p.codigo}
                      className={`border-b border-ink-100 p-2 text-left text-[11px] font-semibold ${COLOR_GRUPO[p.grupo] || 'bg-ink-50 text-ink'}`}
                    >
                      {p.nombre}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.variables.map((variable) => (
                  <tr key={variable} className="hover:bg-ink-50/50">
                    <td className="sticky left-0 z-10 border-b border-r border-ink-100 bg-white p-2 text-[11px] font-medium text-ink-600">
                      {variable}
                    </td>
                    {data.productos.map((p) => {
                      const c = celdaIndex.get(`${variable}|${p.codigo}`);
                      if (!c) return <td key={p.codigo} className="border-b border-ink-100"></td>;
                      return (
                        <td
                          key={p.codigo}
                          onClick={() => setCeldaSel(c)}
                          className={`cursor-pointer border-b border-ink-100 p-2 text-center text-[11px] transition ${
                            c.estado === 'PD'
                              ? 'text-ink-400'
                              : c.estado === 'OK_PROVISORIO'
                              ? 'text-ink-600'
                              : 'font-semibold text-brand'
                          } ${celdaSel?.variable === c.variable && celdaSel?.producto === c.producto ? 'ring-2 ring-brand ring-inset' : ''}`}
                          title={`${c.fuente}\n${c.nota}`}
                        >
                          {c.estado === 'PD' ? (
                            <span className="font-medium">PD</span>
                          ) : c.estado === 'OK_PROVISORIO' ? (
                            <span>OK*</span>
                          ) : (
                            <span>OK</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* Detalle celda seleccionada */}
          {celdaSel && (
            <section className="apple-card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                    Celda seleccionada
                  </div>
                  <h2 className="mt-1 text-xl font-semibold tracking-apple text-ink">
                    {celdaSel.variable} · {data.productos.find((p) => p.codigo === celdaSel.producto)?.nombre}
                  </h2>
                </div>
                <Pill estado={celdaSel.estado} />
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 border-t border-ink-100 pt-4 md:grid-cols-2">
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                    Valor
                  </div>
                  <div className="tabular mt-1 text-2xl font-semibold text-ink">
                    {celdaSel.valor !== null ? celdaSel.valor.toLocaleString('es-CL', { maximumFractionDigits: 2 }) : '—'}
                  </div>
                  <div className="text-xs text-ink-400">{celdaSel.unidad}</div>
                </div>
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                    Fuente
                  </div>
                  <div className="mt-1 text-sm text-ink-600">{celdaSel.fuente}</div>
                </div>
              </div>
              {celdaSel.nota && (
                <div className="mt-4 rounded-lg bg-ink-50 p-3 text-sm text-ink-600">
                  <span className="font-semibold text-ink">Acción pendiente: </span>
                  {celdaSel.nota}
                </div>
              )}

              {/* Sugerencia inteligente si la celda es PD */}
              {celdaSel.estado === 'PD' && (() => {
                const sug = sugerenciaParaCelda(celdaSel.variable, celdaSel.producto);
                if (!sug) return null;
                return (
                  <div className="mt-4 rounded-lg border border-brand/30 bg-brand-50 p-3 text-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-[11px] font-semibold uppercase tracking-wider text-brand">
                          🧠 Sugerencia automática
                        </div>
                        <div className="mt-1 tabular text-lg font-semibold text-ink">
                          {sug.valor_sugerido.toLocaleString('es-CL', { maximumFractionDigits: 2 })} {sug.unidad}
                        </div>
                        <div className="text-xs text-ink-600">{sug.razonamiento}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] uppercase tracking-wider text-ink-400">Confianza</div>
                        <div className="tabular text-base font-semibold text-brand">
                          {(sug.confianza * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </section>
          )}

          {/* Cómo subir de estado */}
          <section className="rounded-appleXl bg-ink-50 p-8">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">Cómo mover una celda de PD → OK Validado</h2>
            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
              <FlujoCard num="1" titulo="Recibe el dato" desc="Mail / Excel / cotización firmada de la persona responsable (ver /datos)" />
              <FlujoCard num="2" titulo="Actualiza plan_builder.py" desc="Modifica el valor en apps/engine/trongkai_engine/plan_builder.py y commit" />
              <FlujoCard num="3" titulo="Marca OK_VALIDADO" desc="En variables_matrix.py cambia el estado de la celda + agrega fuente" />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function renderGrupos(productos: Producto[]) {
  // Agrupar productos consecutivos por grupo
  const grupos: { grupo: string; count: number }[] = [];
  productos.forEach((p) => {
    const last = grupos[grupos.length - 1];
    if (last && last.grupo === p.grupo) last.count++;
    else grupos.push({ grupo: p.grupo, count: 1 });
  });
  return grupos.map((g, i) => (
    <th
      key={i}
      colSpan={g.count}
      className={`border-b border-ink-100 p-2 text-center text-[12px] font-semibold ${COLOR_GRUPO[g.grupo] || 'bg-ink-50'}`}
    >
      {g.grupo}
    </th>
  ));
}

function Pill({ estado }: { estado: Estado }) {
  const cls =
    estado === 'PD'
      ? 'bg-red-50 text-red-600 ring-red-200'
      : estado === 'OK_PROVISORIO'
      ? 'bg-yellow-50 text-yellow-700 ring-yellow-200'
      : 'bg-brand-50 text-brand ring-brand/30';
  const label = estado === 'PD' ? 'PD · Por Definir' : estado === 'OK_PROVISORIO' ? 'OK* · Provisorio' : 'OK · Validado';
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider ring-1 ${cls}`}>
      {label}
    </span>
  );
}

function StatCard({ label, value, sub, tone }: { label: string; value: number; sub: string; tone?: 'warn' | 'mid' | 'ok' }) {
  const cls =
    tone === 'warn' ? 'bg-red-50 text-red-600' :
    tone === 'mid' ? 'bg-yellow-50 text-yellow-700' :
    tone === 'ok' ? 'bg-brand-50 text-brand' :
    'bg-ink-50 text-ink';
  return (
    <div className={`apple-card text-center ${tone ? '' : ''}`}>
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`tabular mt-1 text-3xl font-semibold ${tone === 'warn' ? 'text-red-600' : tone === 'mid' ? 'text-yellow-700' : tone === 'ok' ? 'text-brand' : 'text-ink'}`}>
        {value}
      </div>
      <div className="text-[11px] text-ink-400">{sub}</div>
    </div>
  );
}

function FlujoCard({ num, titulo, desc }: { num: string; titulo: string; desc: string }) {
  return (
    <div className="apple-card">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white text-sm font-bold">
        {num}
      </div>
      <h3 className="mt-3 font-semibold text-ink">{titulo}</h3>
      <p className="mt-1 text-xs text-ink-600">{desc}</p>
    </div>
  );
}
