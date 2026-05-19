import Link from 'next/link';
import { seed, stats, suppliersActivos } from '@/lib/seed-data';

const ETAPAS_ORDER = [
  'RECEPCION',
  'ALIMENTACION',
  'HOMOG_1',
  'PEF',
  'PRENSADO_MECANICO',
  'TRICANTER',
  'EXTRACCION',
  'SECADO',
  'HOMOG_2',
  'ENSACADO',
];

const NOMBRES_ETAPAS: Record<string, string> = {
  RECEPCION: 'Recepción',
  ALIMENTACION: 'Alimentación',
  HOMOG_1: 'Homog. 1',
  PEF: 'PEF (Opticept)',
  PRENSADO_MECANICO: 'Prensado',
  TRICANTER: 'Tricánter',
  EXTRACCION: 'Extracción',
  SECADO: 'Secado (cuello)',
  HOMOG_2: 'Homog. final',
  ENSACADO: 'Ensacado',
};

function StatCard({
  label,
  value,
  suffix,
  warn,
}: {
  label: string;
  value: string | number;
  suffix?: string;
  warn?: boolean;
}) {
  return (
    <div className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wide text-oliva-600">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${warn ? 'text-borgoña' : 'text-oliva-900'}`}>
        {value}
        {suffix && <span className="ml-1 text-sm font-normal text-oliva-600">{suffix}</span>}
      </div>
    </div>
  );
}

export default function Home() {
  const sortedEtapas = [...seed.capacidades].sort(
    (a, b) => ETAPAS_ORDER.indexOf(a.etapa) - ETAPAS_ORDER.indexOf(b.etapa),
  );
  const cobertura = (stats.volumenComprometidoActual / stats.volumenContratoTon) * 100;

  return (
    <div className="space-y-8">
      <section>
        <h1 className="font-serif text-3xl text-oliva-900">Dashboard operacional</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Visión integral de la planta. Estado vigente al{' '}
          {new Date().toLocaleDateString('es-CL')}.
        </p>
      </section>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-5">
        <StatCard label="Cuota contractual" value={stats.volumenContratoTon.toLocaleString('es-CL')} suffix="ton/año" />
        <StatCard
          label="Volumen comprometido"
          value={stats.volumenComprometidoActual.toLocaleString('es-CL')}
          suffix={`ton (${cobertura.toFixed(1)}%)`}
          warn={cobertura < 50}
        />
        <StatCard label="Suppliers activos" value={`${stats.suppliersActivos}/${stats.suppliersTotal}`} />
        <StatCard
          label="SKUs Feed / Food"
          value={`${stats.productosFeed} / ${stats.productosFood}`}
        />
        <StatCard label="Capacidades PD" value={stats.capacidadesPD} warn={stats.capacidadesPD > 5} />
      </section>

      <section>
        <h2 className="font-serif text-xl text-oliva-900">Línea de proceso — capacidades por etapa</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-5">
          {sortedEtapas.map((c) => {
            const pd = c.capacidadTonHora == null;
            return (
              <div key={c.etapa} className="rounded-lg border border-oliva/10 bg-white p-3">
                <div className="text-xs uppercase tracking-wide text-oliva-600">
                  {NOMBRES_ETAPAS[c.etapa] ?? c.etapa}
                </div>
                <div className="mt-1 text-lg font-semibold text-oliva-900">
                  {pd ? '—' : `${c.capacidadTonHora?.toFixed(1)} ton/h`}
                </div>
                <span
                  className={`inline-block h-2 w-2 rounded-full ${
                    pd ? 'bg-trigo' : c.etapa === 'SECADO' ? 'bg-borgoña' : 'bg-oliva-400'
                  }`}
                />
                <span className="ml-2 text-xs text-oliva-600">
                  {pd ? 'PD' : c.opcional ? 'Opcional' : 'OK'}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="font-serif text-xl text-oliva-900">Proveedores ACTIVOS</h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-oliva/10 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-oliva-50 text-xs uppercase tracking-wide text-oliva-600">
              <tr>
                <th className="px-3 py-2 text-left">Supplier</th>
                <th className="px-3 py-2 text-left">MMPP</th>
                <th className="px-3 py-2 text-right">Km</th>
                <th className="px-3 py-2 text-right">$/km</th>
                <th className="px-3 py-2 text-right">$/kg recep.</th>
                <th className="px-3 py-2 text-right">Volumen (ton)</th>
                <th className="px-3 py-2 text-left">Caso</th>
              </tr>
            </thead>
            <tbody>
              {suppliersActivos().map((s) => (
                <tr key={s.nombre} className="border-t border-oliva/5">
                  <td className="px-3 py-2 font-medium text-oliva-900">{s.nombre}</td>
                  <td className="px-3 py-2 text-oliva-600">{s.mmppCodigo}</td>
                  <td className="px-3 py-2 text-right">{s.distanciaKm}</td>
                  <td className="px-3 py-2 text-right">{s.tarifaFleteClpKm.toLocaleString('es-CL')}</td>
                  <td
                    className={`px-3 py-2 text-right ${
                      s.pagoRecepcionClpKg < 0 ? 'text-borgoña' : 'text-oliva-900'
                    }`}
                  >
                    {s.pagoRecepcionClpKg > 0
                      ? `+${s.pagoRecepcionClpKg}`
                      : s.pagoRecepcionClpKg}
                  </td>
                  <td className="px-3 py-2 text-right">{s.volumenAnualComprometidoTon.toLocaleString('es-CL')}</td>
                  <td className="px-3 py-2 text-xs text-oliva-600">{s.casoLogistico.replace('_', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-oliva-600">
          Total comprometido en ACTIVOS:{' '}
          <strong>{stats.volumenComprometidoActual.toLocaleString('es-CL')} ton/año</strong> —{' '}
          ver <Link href="/agenda" className="underline">agenda de camiones</Link>.
        </p>
      </section>

      <section className="rounded-lg border border-borgoña/20 bg-borgoña/5 p-4">
        <h2 className="font-serif text-lg text-borgoña">Bloqueantes operacionales activos</h2>
        <ul className="mt-2 list-disc pl-6 text-sm text-oliva-700">
          <li>
            <strong>Capacidad del secador (bottleneck esperado)</strong> aún PD — sin dato, la agenda usa cota inferior.
          </li>
          <li>
            <strong>Tiempo de descomposición de tomasa / pomasa / alperujo</strong> sin medición real — afecta ventana segura.
          </li>
          <li>
            <strong>{stats.supuestosPD}</strong> supuestos PD activos — ver{' '}
            <Link href="/supuestos" className="underline">/supuestos</Link>.
          </li>
        </ul>
      </section>
    </div>
  );
}
