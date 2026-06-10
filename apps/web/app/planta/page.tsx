'use client';

import { useEffect, useState } from 'react';
import { ConectadoCon } from '@/components/ConectadoCon';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Ficha = {
  id: string; nombre: string; tipo: string; etapa_asociada: string;
  proveedor: string; modelo: string; capacidad_kg_h: number;
  capacidad_unidad: string; potencia_kw: number;
  modalidad: string; arriendo_clp_mes: number;
  notas: string; foto_url: string;
  nivel_dato: 'PD' | 'OK_PROVISORIO' | 'OK_VALIDADO';
};

// Estructura del flujo: paso a paso con qué equipos están en cada uno
const FLUJO = [
  { paso: 1, etapa: 'Recepción y Alimentación', icono: '📥', equipos: ['BOMBA_VALISI_VSHH4'], color: 'from-blue-500 to-blue-600' },
  { paso: 2, etapa: 'Pretratamiento PEF', icono: '⚡', equipos: ['PEF_OPTICEPT_ODIN', 'PEF_OPTICEPT_SUBPRODUCTOS'], color: 'from-purple-500 to-purple-600' },
  { paso: 3, etapa: 'Separación Mecánica', icono: '⚙️', equipos: ['PRENSA_OELWERK_510', 'PRENSA_EXTRACTORA_ACEITE', 'CENTRIFUGA_BIOBASE'], color: 'from-orange-500 to-orange-600' },
  { paso: 4, etapa: 'Secado / Deshidratación', icono: '🔥', equipos: ['SECADOR_IKE_WRH300'], color: 'from-red-500 to-red-600' },
  { paso: 5, etapa: 'Molienda', icono: '🌾', equipos: ['MOLINO_MARTILLOS_HARINERO'], color: 'from-yellow-500 to-yellow-600' },
  { paso: 6, etapa: 'Captación de Polvo', icono: '💨', equipos: ['ASPIRADOR_POLVO'], color: 'from-cyan-500 to-cyan-600' },
  { paso: 7, etapa: 'Transporte a Tolva', icono: '🔄', equipos: ['TORNILLO_ELEVADOR'], color: 'from-teal-500 to-teal-600' },
  { paso: 8, etapa: 'Ensacado + Cosido (línea integrada)', icono: '📦', equipos: ['ENSACADORA_AUTOMATICA'], color: 'from-brand to-brand-light' },
];

const AUXILIARES = ['COMPRESOR_PISTON', 'EQUIPOS_MEDICION', 'TABLERO_ELECTRICO_EXTERIOR', 'TABLERO_ELECTRICO_INTERIOR'];

const NIVEL_DOT: Record<string, string> = {
  PD: 'bg-red-500',
  OK_PROVISORIO: 'bg-yellow-500',
  OK_VALIDADO: 'bg-brand',
};

export default function PlantaPage() {
  const [fichas, setFichas] = useState<Ficha[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/equipos/fichas`).then((r) => r.json()).then((d) => setFichas(d.fichas || []));
  }, []);

  const ficha = (id: string) => fichas.find((f) => f.id === id);
  const selected = selectedId ? ficha(selectedId) : null;

  const totalKw = fichas
    .filter((f) => f.nivel_dato !== 'PD')
    .reduce((s, f) => s + (f.potencia_kw || 0), 0);

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Vista visual planta piloto</p>
        <h1 className="mt-2 text-4xl font-bold">🏭 Planta Trongkai — Layout en vivo</h1>
        <p className="mt-2 text-ink-500">
          Recorrido visual del proceso completo con fotos reales de cada equipo. Click para ficha técnica.
        </p>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KPI label="Pasos del proceso" valor="8" sub="línea principal piloto" />
        <KPI label="Equipos catalogados" valor={`${fichas.length}`} sub="con fichas técnicas" />
        <KPI label="Potencia instalada" valor={`${totalKw.toFixed(1)} kW`} sub="total piloto" />
        <KPI label="Cuello botella" valor="25 kg/h" sub="prensa Oelwerk" />
      </div>

      {/* FLOWLINE - Layout visual */}
      <section>
        <h2 className="mb-4 text-xl font-bold">El proceso paso a paso</h2>
        <div className="space-y-6">
          {FLUJO.map((paso, idx) => {
            const isLast = idx === FLUJO.length - 1;
            return (
              <div key={paso.paso} className="relative">
                <div className="grid grid-cols-12 gap-4 items-start">
                  {/* Columna numero + flecha vertical */}
                  <div className="col-span-1 flex flex-col items-center">
                    <div className={`w-14 h-14 rounded-full bg-gradient-to-br ${paso.color} flex items-center justify-center text-white text-2xl shadow-md`}>
                      {paso.paso}
                    </div>
                    {!isLast && (
                      <div className="w-0.5 flex-1 bg-gradient-to-b from-ink-200 to-transparent mt-2" style={{ minHeight: '60px' }} />
                    )}
                  </div>
                  {/* Contenido del paso */}
                  <div className="col-span-11">
                    <div className="rounded-2xl border border-ink-100 bg-white p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="text-lg font-bold flex items-center gap-2">
                            <span className="text-2xl">{paso.icono}</span> {paso.etapa}
                          </h3>
                        </div>
                        <span className="text-xs text-ink-400">{paso.equipos.length} equipo{paso.equipos.length > 1 ? 's' : ''}</span>
                      </div>
                      {/* Grid de fotos de equipos */}
                      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
                        {paso.equipos.map((eqId) => {
                          const eq = ficha(eqId);
                          if (!eq) return null;
                          return (
                            <button
                              key={eq.id}
                              onClick={() => setSelectedId(eq.id === selectedId ? null : eq.id)}
                              className="group rounded-xl border border-ink-100 bg-ink-50/30 overflow-hidden text-left hover:border-brand hover:shadow-md transition-all"
                            >
                              {eq.foto_url && (
                                <div className="aspect-square bg-white overflow-hidden">
                                  <img src={eq.foto_url} alt={eq.nombre}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                                </div>
                              )}
                              <div className="p-3">
                                <div className="flex items-start gap-1">
                                  <span className={`inline-block w-2 h-2 rounded-full mt-1.5 ${NIVEL_DOT[eq.nivel_dato]}`} />
                                  <p className="text-xs font-semibold leading-tight line-clamp-2">{eq.nombre}</p>
                                </div>
                                {eq.proveedor && (
                                  <p className="text-[10px] text-ink-500 mt-1 truncate">📍 {eq.proveedor}</p>
                                )}
                                {eq.capacidad_kg_h > 0 && (
                                  <p className="text-[10px] text-ink-500 truncate">
                                    📊 {eq.capacidad_kg_h.toLocaleString()} {eq.capacidad_unidad.split(' ')[0]}
                                  </p>
                                )}
                                {eq.potencia_kw > 0 && (
                                  <p className="text-[10px] text-ink-500">⚡ {eq.potencia_kw} kW</p>
                                )}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Equipos auxiliares */}
      <section>
        <h2 className="mb-4 text-xl font-bold">🔧 Equipos auxiliares y soporte</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {AUXILIARES.map((eqId) => {
            const eq = ficha(eqId);
            if (!eq) return null;
            return (
              <button
                key={eq.id}
                onClick={() => setSelectedId(eq.id === selectedId ? null : eq.id)}
                className="rounded-xl border border-ink-100 bg-white overflow-hidden text-left hover:border-brand hover:shadow-md transition-all"
              >
                {eq.foto_url && (
                  <div className="aspect-video bg-ink-50/30">
                    <img src={eq.foto_url} alt={eq.nombre} className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="p-3">
                  <p className="text-sm font-semibold">{eq.nombre}</p>
                  <p className="text-xs text-ink-500 mt-1">{eq.notas?.slice(0, 80)}...</p>
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Modal detalle equipo */}
      {selected && (
        <div
          onClick={() => setSelectedId(null)}
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="grid md:grid-cols-2">
              {selected.foto_url && (
                <div className="bg-ink-50/40">
                  <img src={selected.foto_url} alt={selected.nombre}
                    className="w-full h-full object-cover max-h-96" />
                </div>
              )}
              <div className="p-6">
                <h2 className="text-xl font-bold">{selected.nombre}</h2>
                <p className="text-xs text-ink-500 mt-1">{selected.etapa_asociada} · {selected.tipo}</p>

                <div className="mt-4 space-y-2 text-sm">
                  {selected.proveedor && <Row k="Proveedor" v={selected.proveedor} />}
                  {selected.modelo && <Row k="Modelo" v={selected.modelo} />}
                  {selected.capacidad_kg_h > 0 && <Row k="Capacidad" v={selected.capacidad_unidad} />}
                  {selected.potencia_kw > 0 && <Row k="Potencia" v={`${selected.potencia_kw} kW`} />}
                  <Row k="Modalidad" v={selected.modalidad} />
                  {selected.arriendo_clp_mes > 0 && <Row k="Arriendo" v={`$${(selected.arriendo_clp_mes / 1e6).toFixed(1)}M CLP/mes`} />}
                  <Row k="Calibración" v={selected.nivel_dato} />
                </div>

                {selected.notas && (
                  <div className="mt-4 rounded-lg bg-ink-50/50 p-3">
                    <p className="text-xs text-ink-400 uppercase font-semibold mb-1">Notas técnicas</p>
                    <p className="text-sm text-ink-700">{selected.notas}</p>
                  </div>
                )}

                <button
                  onClick={() => setSelectedId(null)}
                  className="mt-5 w-full rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ConectadoCon links={[
        { href: '/equipos', label: 'Fichas Equipos', razon: 'Editar specs de estas máquinas' },
        { href: '/simulacion', label: 'Simulación', razon: 'Simular la producción de esta planta' },
        { href: '/balance-integral', label: 'Balances', razon: 'Energía, agua y RRHH de la operación' },
        { href: '/costeo', label: 'Costeo', razon: 'El costo por etapa del proceso' },
      ]} />
    </div>
  );
}

function KPI({ label, valor, sub }: { label: string; valor: string; sub?: string }) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="text-[11px] uppercase text-ink-400">{label}</p>
      <p className="mt-1 text-2xl font-bold tabular">{valor}</p>
      {sub && <p className="text-xs text-ink-400">{sub}</p>}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between items-baseline gap-3">
      <span className="text-xs text-ink-400 uppercase font-medium">{k}</span>
      <span className="text-sm font-semibold text-right">{v}</span>
    </div>
  );
}
