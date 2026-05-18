/**
 * Editor de Supuestos — listado por estado y sensibilidad.
 *
 * En Fase 1 esta página lee directamente la tabla `Supuesto` vía un endpoint
 * tRPC del propio Next.js. Por ahora muestra el contenido estático del MD.
 */

import fs from 'node:fs/promises';
import path from 'node:path';

export const dynamic = 'force-dynamic';

export default async function SupuestosPage() {
  const md = await fs
    .readFile(path.join(process.cwd(), '..', '..', 'docs', 'SUPUESTOS.md'), 'utf-8')
    .catch(() => '');
  const totalPD = (md.match(/\| PD \|/g) ?? []).length;
  const totalOK = (md.match(/\| OK_VALIDADO/g) ?? []).length;

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl text-oliva-900">Editor de Supuestos</h1>
      <div className="grid grid-cols-3 gap-3 text-sm">
        <Stat label="PD activos" value={totalPD} color="text-borgoña" />
        <Stat label="OK validados" value={totalOK} color="text-oliva-900" />
        <Stat label="Total claves" value={(md.match(/^\| `[^`]+` \|/gm) ?? []).length} />
      </div>
      <article className="prose prose-sm max-w-none whitespace-pre-wrap rounded-lg border border-oliva/10 bg-white p-4 font-mono text-xs">
        {md || 'docs/SUPUESTOS.md no encontrado'}
      </article>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="rounded-lg border border-oliva/10 bg-white p-4">
      <div className="text-xs uppercase tracking-wide text-oliva-600">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${color ?? 'text-oliva-900'}`}>{value}</div>
    </div>
  );
}
