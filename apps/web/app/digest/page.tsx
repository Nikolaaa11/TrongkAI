'use client';

import Image from 'next/image';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

export default function DigestPage() {
  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Weekly Digest</h1>
          <p className="mt-2 text-sm text-ink-400">
            Resumen ejecutivo semanal listo para mandar por email. Se regenera automáticamente
            con los datos del modelo en cada visita. Apple-style HTML standalone.
          </p>
        </div>
      </header>

      {/* Acciones */}
      <section className="apple-card flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-ink">¿Qué incluye?</h2>
          <p className="mt-1 text-sm text-ink-400">
            Score con delta vs semana anterior · Top 3 acciones · Alertas activas · KPIs core · Audit trail semanal · CTAs
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a
            href={`${ENGINE_URL}/weekly-digest.html`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-apple text-sm"
          >
            Abrir en nueva pestaña
          </a>
          <button
            onClick={async () => {
              const r = await fetch(`${ENGINE_URL}/weekly-digest.html`);
              const html = await r.text();
              await navigator.clipboard.writeText(html);
              alert('HTML copiado al portapapeles. Pégalo en tu cliente de email.');
            }}
            className="btn-apple btn-apple-ghost text-sm"
          >
            📋 Copiar HTML
          </button>
        </div>
      </section>

      {/* Iframe preview */}
      <section className="apple-card overflow-hidden p-0">
        <div className="border-b border-ink-100 bg-ink-50 px-4 py-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-ink-400">
            Preview · Email Apple-style
          </span>
        </div>
        <iframe
          src={`${ENGINE_URL}/weekly-digest.html`}
          title="Weekly Digest Preview"
          className="w-full"
          style={{ height: '900px', border: 'none' }}
        />
      </section>

      {/* Cómo enviarlo */}
      <section className="rounded-appleXl bg-ink-50 p-8">
        <h2 className="text-2xl font-semibold tracking-apple text-ink">Cómo mandarlo cada lunes</h2>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <FlujoCard num="1" titulo="Copia el HTML" desc="Botón '📋 Copiar HTML' arriba. Captura el digest live al momento." />
          <FlujoCard num="2" titulo="Pega en Gmail/Outlook" desc="Crea nuevo correo, modo HTML, pega. Apple Mail también acepta." />
          <FlujoCard num="3" titulo="Manda a directorio" desc="Lista de distribución del directorio + advisors + key LPs." />
        </div>
        <div className="mt-6 rounded-lg bg-white p-4 text-sm text-ink-600">
          <strong className="text-ink">💡 Pro tip:</strong> Configurar un schedule semanal (cron) que fetchee este HTML y lo mande automáticamente. Stack típico: cron + curl + sendmail.
        </div>
      </section>
    </div>
  );
}

function FlujoCard({ num, titulo, desc }: { num: string; titulo: string; desc: string }) {
  return (
    <div className="apple-card">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">{num}</div>
      <h3 className="mt-3 font-semibold text-ink">{titulo}</h3>
      <p className="mt-1 text-xs text-ink-600">{desc}</p>
    </div>
  );
}
