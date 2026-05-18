export default function PlanPage() {
  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl text-oliva-900">Plan 5 años — EERR y KPIs</h1>
      <p className="text-sm text-oliva-600">
        Mensual a 60 meses, exportable a Excel formato directorio. Pendiente de Fase 4.
      </p>
      <div className="rounded-lg border border-trigo/40 bg-trigo/10 p-4 text-sm text-oliva-900">
        Bloqueantes para activar esta vista: precios de venta (12 SKUs PD), WACC del FIP CEHTA, costo del secador.
        Detalle en <code className="font-mono">docs/PREGUNTAS-ABIERTAS.md</code>.
      </div>
    </div>
  );
}
