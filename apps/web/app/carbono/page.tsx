'use client';

import { useEffect, useState } from 'react';
import { trongkai } from '@/lib/trongkai-client';

type CarbonResponse = Record<
  'baseline' | 'renovable' | 'beccs',
  {
    emisiones_netas_5y_ton: number;
    emisiones_evitadas_5y_ton: number;
    revenue_creditos_5y_clp: number;
    es_carbono_neutro: boolean;
    es_carbono_negativo: boolean;
    detalle_anual: {
      brutas_ton: number[];
      evitadas_ton: number[];
      netas_ton: number[];
      revenue_clp: number[];
    };
  }
>;

const escenarioMeta = [
  {
    key: 'baseline' as const,
    titulo: 'Baseline',
    desc: 'Mix energético actual Chile (60% renovable, 40% fósil).',
    color: 'border-oliva/20 bg-white',
    badgeColor: 'bg-oliva-700/15 text-oliva-700',
  },
  {
    key: 'renovable' as const,
    titulo: 'Renovable 100%',
    desc: 'Energía solar/eólica certificada. Sin BECCS.',
    color: 'border-trigo/30 bg-trigo/5',
    badgeColor: 'bg-trigo/20 text-trigo',
  },
  {
    key: 'beccs' as const,
    titulo: 'BECCS (futuro)',
    desc: 'Bioenergía con captura y almacenamiento. Net-negative.',
    color: 'border-oliva-700/30 bg-oliva-50/50',
    badgeColor: 'bg-oliva-900/20 text-oliva-900',
  },
];

const fmtTon = (n: number) => `${n.toLocaleString('es-CL', { maximumFractionDigits: 0 })} ton`;
const fmtClp = (n: number) => `$${(n / 1e6).toFixed(0)}M CLP`;

export default function CarbonoPage() {
  const [data, setData] = useState<CarbonResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    try {
      setData(await trongkai.carbonFootprint());
    } catch (e) {
      setErr(String(e));
    }
  }

  if (err) return <div className="p-8 text-borgoña">Error: {err}</div>;
  if (!data) return <div className="p-8 text-oliva-600">Calculando footprint carbono…</div>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Footprint Carbono · LCA</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Análisis del ciclo de vida (cradle-to-gate) del plan 5 años bajo 3 escenarios energéticos.
          Métricas calibradas con literatura peer-reviewed: ACS Sustainable Chem Eng 2025, ScienceDirect 2024,
          ResearchGate succinic biorefinery. Revenue créditos a precios mercado voluntario VCM.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {escenarioMeta.map((esc) => {
          const r = data[esc.key];
          return (
            <article key={esc.key} className={`card-hover rounded-xl border-2 p-5 ${esc.color}`}>
              <div className="flex items-center justify-between">
                <h2 className="font-serif text-xl text-oliva-900">{esc.titulo}</h2>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${esc.badgeColor}`}>
                  {r.es_carbono_negativo ? 'Carbono negativo' : r.es_carbono_neutro ? 'Neutro' : 'Positivo'}
                </span>
              </div>
              <p className="mt-1 text-xs text-oliva-600">{esc.desc}</p>

              <div className="mt-4 space-y-3">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Emisiones netas 5y</div>
                  <div className={`tabular text-2xl font-bold ${r.emisiones_netas_5y_ton < 0 ? 'text-oliva-900' : 'text-borgoña'}`}>
                    {r.emisiones_netas_5y_ton < 0 ? '−' : ''}
                    {fmtTon(Math.abs(r.emisiones_netas_5y_ton))}
                  </div>
                  <div className="text-[10px] text-oliva-500">CO₂eq cradle-to-gate</div>
                </div>

                <div>
                  <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Emisiones evitadas 5y</div>
                  <div className="tabular text-base font-semibold text-oliva-700">
                    {fmtTon(r.emisiones_evitadas_5y_ton)}
                  </div>
                  <div className="text-[10px] text-oliva-500">residuos NO descompuestos en vertedero</div>
                </div>

                <div className="rounded border border-trigo/40 bg-trigo/5 p-2">
                  <div className="text-[10px] uppercase tracking-[0.08em] text-trigo">Revenue créditos CO₂ 5y</div>
                  <div className="tabular text-xl font-bold text-trigo">{fmtClp(r.revenue_creditos_5y_clp)}</div>
                  <div className="text-[10px] text-oliva-500">VCM USD 15-80/ton CO₂eq</div>
                </div>
              </div>
            </article>
          );
        })}
      </section>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
        <h2 className="font-medium text-oliva-900">Detalle anual (escenario baseline)</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-oliva-50 text-xs uppercase tracking-wide text-oliva-600">
              <tr>
                <th className="px-3 py-2 text-left">Año</th>
                <th className="px-3 py-2 text-right">Emisiones brutas</th>
                <th className="px-3 py-2 text-right">Emisiones evitadas</th>
                <th className="px-3 py-2 text-right">Net</th>
                <th className="px-3 py-2 text-right">Revenue créditos</th>
              </tr>
            </thead>
            <tbody>
              {data.baseline.detalle_anual.brutas_ton.map((bruta, i) => {
                const evitada = data.baseline.detalle_anual.evitadas_ton[i];
                const net = data.baseline.detalle_anual.netas_ton[i];
                const rev = data.baseline.detalle_anual.revenue_clp[i];
                return (
                  <tr key={i} className="border-t border-oliva/5">
                    <td className="px-3 py-2 font-medium">A{i + 1}</td>
                    <td className="px-3 py-2 text-right tabular text-borgoña">+{fmtTon(bruta)}</td>
                    <td className="px-3 py-2 text-right tabular text-oliva-700">−{fmtTon(evitada)}</td>
                    <td className={`px-3 py-2 text-right tabular font-medium ${net < 0 ? 'text-oliva-900' : 'text-borgoña'}`}>
                      {net < 0 ? '−' : ''}{fmtTon(Math.abs(net))}
                    </td>
                    <td className="px-3 py-2 text-right tabular text-trigo">{fmtClp(rev)}</td>
                  </tr>
                );
              })}
              <tr className="border-t-2 border-oliva/20 bg-oliva-50/50">
                <td className="px-3 py-2 font-semibold">Total 5y</td>
                <td className="px-3 py-2 text-right font-semibold tabular text-borgoña">
                  +{fmtTon(data.baseline.detalle_anual.brutas_ton.reduce((a, b) => a + b, 0))}
                </td>
                <td className="px-3 py-2 text-right font-semibold tabular text-oliva-700">
                  −{fmtTon(data.baseline.emisiones_evitadas_5y_ton)}
                </td>
                <td className="px-3 py-2 text-right font-semibold tabular text-oliva-900">
                  −{fmtTon(Math.abs(data.baseline.emisiones_netas_5y_ton))}
                </td>
                <td className="px-3 py-2 text-right font-semibold tabular text-trigo">
                  {fmtClp(data.baseline.revenue_creditos_5y_clp)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
        <h3 className="font-medium">Cómo se calcula</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-oliva-700">
          <li><strong>Emisiones brutas</strong>: kg producto × factor GWP del escenario (0.79 baseline / 0.35 renovable / -1.05 BECCS).</li>
          <li><strong>Emisiones evitadas</strong>: ton MMPP × 0.5 ton CO₂eq (IPCC: residuos orgánicos no descompuestos en vertedero).</li>
          <li><strong>Net</strong>: brutas − evitadas. Negativo = más carbono evitado que emitido.</li>
          <li><strong>Revenue créditos</strong>: ton net negativas × USD 15/ton (mercado voluntario avoidance) × TC CLP.</li>
        </ul>
        <p className="mt-2 text-xs">
          Fuentes:{' '}
          <a className="text-trigo hover:underline" href="https://pubs.acs.org/doi/abs/10.1021/acssuschemeng.4c07901" target="_blank" rel="noopener noreferrer">
            ACS Sustainable Chem Eng 2025
          </a>
          {', '}
          <a className="text-trigo hover:underline" href="https://www.sciencedirect.com/science/article/pii/S0959652624018092" target="_blank" rel="noopener noreferrer">
            ScienceDirect 2024
          </a>
          .
        </p>
      </section>
    </div>
  );
}
