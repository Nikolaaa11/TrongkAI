export default function Home() {
  return (
    <div className="space-y-8">
      <section>
        <h1 className="font-serif text-3xl text-oliva-900">Dashboard operacional</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Semáforo por etapa, capacidad horaria del cuello de botella y próxima mantención del PEF.
        </p>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {['Recepción', 'Alimentación', 'PEF', 'Prensado', 'Secado (cuello)', 'Homog. final', 'Ensacado', 'Palletizado'].map(
          (etapa) => (
            <div
              key={etapa}
              className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm"
            >
              <div className="text-xs uppercase tracking-wide text-oliva-600">{etapa}</div>
              <div className="mt-2 text-2xl font-semibold text-oliva-900">—</div>
              <div className="text-xs text-oliva-400">ton/h actual vs target</div>
              <span className="mt-3 inline-block h-2 w-2 rounded-full bg-trigo" aria-label="Pendiente" />
              <span className="ml-2 text-xs text-trigo">PD capacidad</span>
            </div>
          ),
        )}
      </section>

      <section className="rounded-lg border border-borgoña/20 bg-borgoña/5 p-4">
        <h2 className="font-serif text-lg text-borgoña">
          Estado de la plataforma — Fase 1 en curso
        </h2>
        <ul className="mt-2 list-disc pl-6 text-sm text-oliva-600">
          <li>Modelo de datos completo (Prisma) — falta `prisma migrate` contra Postgres real.</li>
          <li>Motor de balance de masa funcional (21 tests verde) — listo para Módulo 2.</li>
          <li>Capacidades de proceso aún PD: bloqueante para entregable M1 (ver `docs/PREGUNTAS-ABIERTAS.md`).</li>
          <li>Schedule de mejora automática cada 1 h: configurado (ver `~/.claude/`).</li>
        </ul>
      </section>
    </div>
  );
}
