'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type HealthCheck = {
  healthy: boolean;
  nombre: string;
  detalle: string;
};

type HealthReport = {
  version: string;
  timestamp: string;
  uptime_seconds: number;
  modulos_count: number;
  memory_mb: number | null;
  health_checks: HealthCheck[];
  healthy_count: number;
  checks_total: number;
  salud_global_pct: number;
  artifacts: {
    audit_trail_kb: number;
    readiness_history_kb: number;
    pipeline_lp_kb: number;
    notas_kb: number;
    exports_dir_files: number;
  };
};

export default function SaludPage() {
  const [data, setData] = useState<HealthReport | null>(null);
  const [cacheStats, setCacheStats] = useState<any>(null);
  const [latencies, setLatencies] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void cargar();
    const interval = setInterval(cargar, 30_000);
    return () => clearInterval(interval);
  }, []);

  async function cargar() {
    setLoading(true);
    try {
      // Latency benchmarks
      const endpoints = [
        ['/healthz', null],
        ['/api/snapshot', null],
        ['/readiness/score', null],
        ['/decisiones/top', null],
        ['/alertas', null],
        ['/variables/matrix', null],
      ] as const;

      const newLat: Record<string, number> = {};
      for (const [endpoint] of endpoints) {
        const t0 = performance.now();
        try {
          await fetch(`${ENGINE_URL}${endpoint}`, { method: 'GET' });
          newLat[endpoint] = performance.now() - t0;
        } catch {
          newLat[endpoint] = -1;
        }
      }
      setLatencies(newLat);

      const r = await fetch(`${ENGINE_URL}/health/full`);
      if (r.ok) setData(await r.json());

      const cs = await fetch(`${ENGINE_URL}/cache/stats`);
      if (cs.ok) setCacheStats(await cs.json());
    } finally {
      setLoading(false);
    }
  }

  async function limpiarCache() {
    if (!confirm('¿Limpiar todo el cache? Próximas requests serán cold.')) return;
    await fetch(`${ENGINE_URL}/cache/clear`, { method: 'POST' });
    void cargar();
  }

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">System Health</h1>
            <p className="mt-2 text-sm text-ink-400">
              Estado técnico del motor en tiempo real. Refresh cada 30 segundos. Para detectar regresiones, fallas de red o caídas del modelo.
            </p>
          </div>
        </div>
        <button onClick={cargar} disabled={loading} className="btn-apple btn-apple-ghost text-xs">
          {loading ? 'Verificando...' : '↻ Refresh'}
        </button>
      </header>

      {data && (
        <>
          {/* Hero salud */}
          <section className={`rounded-appleXl p-8 ring-1 ${data.salud_global_pct === 100 ? 'bg-brand-50 ring-brand/20' : data.salud_global_pct >= 70 ? 'bg-orange-50 ring-orange-200' : 'bg-red-50 ring-red-200'}`}>
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Salud global</div>
                <div className={`tabular mt-2 text-5xl font-semibold ${data.salud_global_pct === 100 ? 'text-brand' : data.salud_global_pct >= 70 ? 'text-orange-600' : 'text-red-600'}`}>
                  {data.salud_global_pct.toFixed(0)}%
                </div>
                <div className="text-xs text-ink-600">{data.healthy_count}/{data.checks_total} checks OK</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">Versión motor</div>
                <div className="tabular mt-2 text-2xl font-semibold text-ink">{data.version}</div>
                <div className="text-xs text-ink-600">trongkai-engine</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">Módulos</div>
                <div className="tabular mt-2 text-2xl font-semibold text-ink">{data.modulos_count}</div>
                <div className="text-xs text-ink-600">archivos .py</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">Uptime</div>
                <div className="tabular mt-2 text-2xl font-semibold text-ink">
                  {Math.floor(data.uptime_seconds / 60)}m {data.uptime_seconds % 60}s
                </div>
                <div className="text-xs text-ink-600">{data.memory_mb ? `${data.memory_mb.toFixed(0)} MB RAM` : 'memoria N/A'}</div>
              </div>
            </div>
          </section>

          {/* Health checks */}
          <section>
            <h2 className="mb-4 text-xl font-semibold tracking-apple text-ink">Health Checks ({data.checks_total})</h2>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {data.health_checks.map((c) => (
                <div key={c.nombre} className={`apple-card flex items-center gap-3 ${c.healthy ? '' : 'border-red-200 bg-red-50/40'}`}>
                  <span className={`shrink-0 text-lg ${c.healthy ? 'text-brand' : 'text-red-600'}`}>
                    {c.healthy ? '✓' : '✗'}
                  </span>
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-ink">{c.nombre}</div>
                    <div className="text-xs text-ink-600">{c.detalle}</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Latency */}
          <section className="apple-card">
            <h2 className="mb-4 text-xl font-semibold tracking-apple text-ink">⏱ Latencia de endpoints</h2>
            <div className="space-y-2">
              {Object.entries(latencies).map(([endpoint, ms]) => {
                const tone = ms < 0 ? 'bad' : ms < 200 ? 'ok' : ms < 1000 ? 'warn' : 'bad';
                const cls = tone === 'ok' ? 'text-brand' : tone === 'warn' ? 'text-orange-600' : 'text-red-600';
                const barWidth = ms < 0 ? 100 : Math.min(100, (ms / 2000) * 100);
                return (
                  <div key={endpoint} className="flex items-center gap-3">
                    <code className="w-56 shrink-0 text-xs text-ink-600">{endpoint}</code>
                    <div className="flex-1 h-1.5 rounded-full bg-ink-100 overflow-hidden">
                      <div className={`h-full ${tone === 'ok' ? 'bg-brand' : tone === 'warn' ? 'bg-orange-400' : 'bg-red-500'}`} style={{ width: `${barWidth}%` }} />
                    </div>
                    <span className={`tabular w-20 shrink-0 text-right text-sm font-medium ${cls}`}>
                      {ms < 0 ? 'error' : `${ms.toFixed(0)} ms`}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Cache + Artifacts */}
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* Cache */}
            <div className="apple-card">
              <div className="flex items-baseline justify-between">
                <h2 className="text-lg font-semibold text-ink">💾 Cache In-Memory</h2>
                <button onClick={limpiarCache} className="text-xs text-red-600 hover:underline">Limpiar todo</button>
              </div>
              {cacheStats && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <Stat label="Entries activas" value={cacheStats.active} tone="ok" />
                  <Stat label="Expiradas" value={cacheStats.expired} />
                </div>
              )}
              {cacheStats?.top_entries && cacheStats.top_entries.length > 0 && (
                <div className="mt-3 space-y-1 max-h-32 overflow-y-auto">
                  {cacheStats.top_entries.map((e: any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-[11px]">
                      <code className="truncate text-ink-600">{e.key}</code>
                      <span className="tabular text-ink-400">{e.ttl_restante}s</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Artifacts */}
            <div className="apple-card">
              <h2 className="text-lg font-semibold text-ink">📁 Artifacts (datos persistentes)</h2>
              <div className="mt-3 space-y-2">
                <ArtifactRow label="Audit Trail" sizeKb={data.artifacts.audit_trail_kb} />
                <ArtifactRow label="Readiness History" sizeKb={data.artifacts.readiness_history_kb} />
                <ArtifactRow label="Pipeline LP" sizeKb={data.artifacts.pipeline_lp_kb} />
                <ArtifactRow label="Notas" sizeKb={data.artifacts.notas_kb} />
                <div className="flex items-baseline justify-between text-sm">
                  <span className="text-ink-600">Exports/PDFs generados</span>
                  <span className="tabular font-medium text-ink">{data.artifacts.exports_dir_files} archivos</span>
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number | string; tone?: 'ok' | 'warn' }) {
  const cls = tone === 'ok' ? 'text-brand' : tone === 'warn' ? 'text-orange-600' : 'text-ink';
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`tabular mt-1 text-2xl font-semibold ${cls}`}>{value}</div>
    </div>
  );
}

function ArtifactRow({ label, sizeKb }: { label: string; sizeKb: number }) {
  return (
    <div className="flex items-baseline justify-between text-sm">
      <span className="text-ink-600">{label}</span>
      <span className="tabular font-medium text-ink">
        {sizeKb > 0 ? `${sizeKb.toFixed(1)} KB` : <span className="text-ink-400">vacío</span>}
      </span>
    </div>
  );
}
