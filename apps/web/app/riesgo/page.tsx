'use client';

import { useEffect, useState } from 'react';
import { HistogramaChart } from '@/components/HistogramaChart';
import { TornadoChart } from '@/components/TornadoChart';
import {
  trongkai,
  type MonteCarloResponse,
  type RepCalendar,
  type TornadoEntry,
} from '@/lib/trongkai-client';

const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? '—' : `${(n * 100).toFixed(1)}%`;
const fmtB = (n: number) => `$${(n / 1e9).toFixed(2)}B`;

type Estado = {
  sinClima: MonteCarloResponse | null;
  conClima: MonteCarloResponse | null;
  tornado: TornadoEntry[] | null;
  baseTir: number | null;
  rep: RepCalendar | null;
  climaDetalle: any | null;
};

export default function RiesgoPage() {
  const [st, setSt] = useState<Estado>({
    sinClima: null, conClima: null, tornado: null, baseTir: null, rep: null, climaDetalle: null,
  });
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    setLoading(true);
    try {
      const [plan, sinClima, conClima, tornado, rep, climaDetalle] = await Promise.all([
        trongkai.plan(),
        trongkai.monteCarlo({ n_runs: 800 }),
        trongkai.monteCarloIntegrado({ n_runs: 800, incluir_clima: true }),
        trongkai.tornado(),
        trongkai.repCalendar(),
        trongkai.climateRisk({ n_runs: 800 }),
      ]);
      setSt({
        sinClima, conClima, tornado, rep, climaDetalle,
        baseTir: plan.kpis.tir_proyecto_anual,
      });
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-8 text-oliva-600">Cargando análisis integrado de riesgo...</div>;
  if (err) return <div className="p-8 text-borgoña">Error: {err}</div>;

  const deltaTirPp = st.sinClima?.tir_p50 && st.conClima?.tir_p50
    ? (st.conClima.tir_p50 - st.sinClima.tir_p50) * 100 : null;
  const deltaProbPp = st.sinClima && st.conClima
    ? (st.conClima.prob_tir_supera_wacc - st.sinClima.prob_tir_supera_wacc) * 100 : null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Análisis integrado de riesgo</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Vista unificada: <strong>riesgo financiero</strong> (precios + WACC + costos) +{' '}
          <strong>riesgo climático</strong> (4 eventos chilenos) + <strong>riesgo regulatorio</strong> (Ley REP).
          Pensado para directorio: comparación lado a lado del plan optimista vs realista.
        </p>
      </header>

      {/* ===== Comparativa sin clima vs con clima ===== */}
      <section>
        <h2 className="font-serif text-xl text-oliva-900">Sin riesgo climático vs Con riesgo climático</h2>
        <p className="mt-1 text-xs text-oliva-600">
          Monte Carlo 800 corridas: precios lognormal σ=0.20, WACC normal σ=0.02, rendimientos σ=0.05.
          La versión "con clima" suma 4 eventos chilenos (sequía 25%, helada 15%, granizo 10%, ola calor 30%).
        </p>
        <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
          <ComparativeCol
            titulo="📊 Sin clima (visión optimista)"
            mc={st.sinClima}
            tone="ok"
          />
          <ComparativeCol
            titulo="🌪️ Con clima (visión realista)"
            mc={st.conClima}
            tone="warn"
          />
        </div>
        {deltaTirPp !== null && (
          <div className="mt-3 rounded-lg border border-trigo/40 bg-trigo/5 p-4 text-sm">
            <strong>Impacto del clima:</strong> TIR P50 baja <strong>{deltaTirPp.toFixed(1)} pp</strong>
            {' '}y la probabilidad de superar WACC baja <strong>{deltaProbPp?.toFixed(1)} pp</strong>.
            Esto es la cifra que el directorio necesita ver — TIR ajustada por riesgo climático real Chile.
          </div>
        )}
      </section>

      {/* ===== Histograma integrado ===== */}
      {st.conClima?.histograma_tir && st.conClima.tir_p50 !== null && (
        <section className="rounded-lg border border-oliva/10 bg-white p-3 shadow-sm">
          <HistogramaChart
            bins={st.conClima.histograma_tir}
            p5={st.conClima.tir_p5}
            p50={st.conClima.tir_p50}
            p95={st.conClima.tir_p95}
            baseValue={st.baseTir ?? undefined}
            title="Distribución TIR — riesgos financieros + climáticos integrados"
            height={280}
          />
        </section>
      )}

      {/* ===== Tornado financiero + estadísticos clima ===== */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {st.tornado && st.baseTir && (
          <div className="rounded-lg border border-oliva/10 bg-white p-3 card-hover">
            <h3 className="font-medium text-oliva-900">Sensibilidades financieras (Tornado ±20%)</h3>
            <TornadoChart entries={st.tornado} baseTir={st.baseTir} height={240} />
          </div>
        )}

        {st.climaDetalle && (
          <div className="rounded-lg border border-oliva/10 bg-white p-4 card-hover">
            <h3 className="font-medium text-oliva-900">Riesgo climático cuantificado</h3>
            <dl className="mt-3 space-y-3 text-sm">
              <Row dt="Pérdida acumulada P50" dd={fmtPct(st.climaDetalle.perdida_acumulada_p50_pct)} />
              <Row dt="Pérdida acumulada P95" dd={fmtPct(st.climaDetalle.perdida_acumulada_p95_pct)} highlight />
              <Row dt="Prob. año con evento crítico (>15% pérdida)" dd={fmtPct(st.climaDetalle.probabilidad_evento_critico)} />
            </dl>
            <h4 className="mt-4 text-xs uppercase tracking-wide text-oliva-600">Volumen efectivo año 5</h4>
            <div className="mt-2 grid grid-cols-3 gap-2 text-center text-sm">
              <Banda label="P5 (peor)" value={`${(st.climaDetalle.volumen_p5_anual[4] / 1000).toFixed(1)}k`} tone="warn" />
              <Banda label="P50" value={`${(st.climaDetalle.volumen_p50_anual[4] / 1000).toFixed(1)}k`} />
              <Banda label="P95 (mejor)" value={`${(st.climaDetalle.volumen_p95_anual[4] / 1000).toFixed(1)}k`} tone="ok" />
            </div>
            <p className="mt-2 text-xs text-oliva-600">vs base 50k ton/año</p>
          </div>
        )}
      </section>

      {/* ===== Riesgo regulatorio próximos hitos ===== */}
      {st.rep && (
        <section className="rounded-lg border border-borgoña/30 bg-borgoña/5 p-4">
          <h2 className="font-medium text-borgoña">⚠ Próximos hitos regulatorios</h2>
          <p className="mt-1 text-xs text-oliva-600">
            Total hitos: {st.rep.total_hitos} · Costo compliance 5y: ${(st.rep.costo_compliance_5y_clp.total_clp / 1e6).toFixed(0)}M CLP
          </p>
          <div className="mt-3 space-y-2">
            {st.rep.proximos.slice(0, 4).map((h, i) => (
              <div key={i} className="flex items-start justify-between rounded bg-white p-2 text-sm">
                <div>
                  <div className="font-medium text-oliva-900">{h.nombre}</div>
                  <div className="text-xs text-oliva-600">{h.impacto_trongkai}</div>
                </div>
                <div className="ml-3 text-right text-xs">
                  <div className="font-medium text-oliva-900">{new Date(h.fecha_vigor).toLocaleDateString('es-CL', { year: 'numeric', month: 'short' })}</div>
                  <div className={h.severidad === 'ALTA' || h.severidad === 'CRITICA' ? 'text-borgoña' : 'text-oliva-700'}>{h.severidad}</div>
                  {h.costo_estimado_clp && (
                    <div className="text-trigo tabular">${(h.costo_estimado_clp / 1e6).toFixed(0)}M</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ===== Síntesis directorio ===== */}
      <section className="rounded-lg border-2 border-oliva-900/20 bg-oliva-50/30 p-4">
        <h2 className="font-serif text-xl text-oliva-900">Síntesis para directorio</h2>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3 text-sm">
          <div>
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Riesgo financiero</div>
            <p className="mt-1 text-oliva-900">
              TIR sensible a <strong>precio promedio</strong> y <strong>rendimiento MMPP</strong>. Cobertura
              robusta con Monte Carlo 800 corridas.
            </p>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Riesgo climático</div>
            <p className="mt-1 text-oliva-900">
              {st.climaDetalle && `${(st.climaDetalle.probabilidad_evento_critico * 100).toFixed(0)}%`} de los años hay evento
              crítico (&gt;15% pérdida). Pérdida P95 acumulada: {st.climaDetalle && fmtPct(st.climaDetalle.perdida_acumulada_p95_pct)}.
            </p>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Riesgo regulatorio</div>
            <p className="mt-1 text-oliva-900">
              {st.rep && `${st.rep.por_estado.CERCANA.length}`} hitos próximos (&lt;12 meses). Costo cumplimiento:{' '}
              {st.rep && `$${(st.rep.costo_compliance_5y_clp.total_clp / 1e6).toFixed(0)}M`} 5y.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function ComparativeCol({ titulo, mc, tone }: { titulo: string; mc: MonteCarloResponse | null; tone: 'ok' | 'warn' }) {
  const cls = tone === 'ok' ? 'border-oliva/20 bg-oliva-50/30' : 'border-borgoña/30 bg-borgoña/5';
  return (
    <div className={`card-hover rounded-lg border-2 p-4 ${cls}`}>
      <h3 className="font-medium text-oliva-900">{titulo}</h3>
      {mc ? (
        <dl className="mt-3 space-y-2 text-sm">
          <Row dt="TIR P5 (peor 5%)" dd={fmtPct(mc.tir_p5)} />
          <Row dt="TIR P50 (mediana)" dd={fmtPct(mc.tir_p50)} highlight />
          <Row dt="TIR P95 (mejor 5%)" dd={fmtPct(mc.tir_p95)} />
          <Row dt="VAN P50" dd={fmtB(mc.van_p50)} />
          <Row dt="Prob TIR > WACC" dd={fmtPct(mc.prob_tir_supera_wacc)} highlight />
          <Row dt="Prob VAN > 0" dd={fmtPct(mc.prob_van_positivo)} />
          {mc.promedio_anos_critico_por_corrida !== undefined && (
            <Row dt="Años críticos/corrida" dd={`${mc.promedio_anos_critico_por_corrida.toFixed(2)} / 5`} />
          )}
        </dl>
      ) : <p className="mt-2 text-sm text-oliva-400">No data</p>}
    </div>
  );
}

function Row({ dt, dd, highlight }: { dt: string; dd: string; highlight?: boolean }) {
  return (
    <div className="flex items-baseline justify-between border-b border-oliva/5 py-1">
      <dt className="text-oliva-600">{dt}</dt>
      <dd className={`tabular ${highlight ? 'font-semibold text-oliva-900' : 'text-oliva-700'}`}>{dd}</dd>
    </div>
  );
}

function Banda({ label, value, tone }: { label: string; value: string; tone?: 'ok' | 'warn' }) {
  const cls = tone === 'ok' ? 'bg-oliva-50' : tone === 'warn' ? 'bg-borgoña/10' : 'bg-trigo/10';
  return (
    <div className={`rounded p-2 ${cls}`}>
      <div className="text-[10px] uppercase tracking-wide text-oliva-600">{label}</div>
      <div className="tabular text-base font-semibold text-oliva-900">{value} ton</div>
    </div>
  );
}
