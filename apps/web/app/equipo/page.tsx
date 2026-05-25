'use client';

import Image from 'next/image';

type Persona = {
  nombre: string;
  rol: string;
  bio: string;
  expertise: string[];
  email?: string;
  linkedin?: string;
};

const FUNDADORES: Persona[] = [
  {
    nombre: 'Nicolás Rietta',
    rol: 'COO & Co-fundador',
    bio: 'COO de Cehta Capital (FIP de US$160M). Lidera la estrategia financiera y operativa de Trongkai. Background en finanzas estructuradas y bioeconomía.',
    expertise: ['Finanzas', 'Estrategia', 'Bioeconomía', 'Inversiones'],
    email: 'nicolasrietta@gmail.com',
  },
  {
    nombre: 'Jaime',
    rol: 'CTO & Co-fundador',
    bio: 'Ingeniero industrial. Diseñó el proceso técnico de biorrefinería. Lidera operaciones, ingeniería de planta y validación tecnológica.',
    expertise: ['Ingeniería de procesos', 'Operaciones', 'Validación técnica'],
  },
  {
    nombre: 'Sergio',
    rol: 'CCO & Co-fundador',
    bio: 'Comercial senior. Lidera la apertura de mercados Feed (acuicultura, mascotas) y Food (humanos). Relación con clientes y proveedores MMPP.',
    expertise: ['Ventas B2B', 'Acuicultura', 'Food ingredients'],
  },
];

const DIRECTORIO: Persona[] = [
  {
    nombre: 'Por definir',
    rol: 'Presidente del Directorio',
    bio: 'Posición abierta. Buscamos líder con experiencia en agroindustria, M&A LATAM o fondos de inversión sustentables.',
    expertise: ['Liderazgo estratégico', 'M&A', 'Sustentabilidad'],
  },
];

const ADVISORS: Persona[] = [
  {
    nombre: 'Por sumar',
    rol: 'Advisor técnico',
    bio: 'Buscamos advisor con experiencia en plantas de procesamiento alimentario industrial, idealmente con exposición a olivar / vinícola.',
    expertise: ['Plantas industriales', 'Olive processing'],
  },
  {
    nombre: 'Por sumar',
    rol: 'Advisor ESG / Carbono',
    bio: 'Buscamos consultor LCA con experiencia en SFDR Art 8/9 y reportes para DFIs.',
    expertise: ['LCA', 'SFDR', 'Reportes ESG'],
  },
];

const ALIANZAS = [
  { nombre: 'CORFO', tipo: 'Programa de transferencia tecnológica', estado: 'Activa', monto: '~CLP 350M/año' },
  { nombre: 'Universidad XX', tipo: 'I+D conjunto proceso PTEC', estado: 'En conversación', monto: 'Por definir' },
  { nombre: 'Olivar Cosecha SpA', tipo: 'Proveedor estratégico alperujo', estado: 'En conversación', monto: 'Cap 20k ton/año' },
];

export default function EquipoPage() {
  return (
    <div className="space-y-16">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Equipo, Directorio y Alianzas</h1>
          <p className="mt-2 text-sm text-ink-400">
            La gente detrás de Trongkai. Liderazgo ejecutivo + advisors + partnerships estratégicos.
          </p>
        </div>
      </header>

      {/* Fundadores */}
      <section>
        <h2 className="mb-6 text-2xl font-semibold tracking-apple text-ink">Fundadores</h2>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {FUNDADORES.map((p) => (
            <PersonCard key={p.nombre} p={p} highlight />
          ))}
        </div>
      </section>

      {/* Directorio */}
      <section>
        <h2 className="mb-2 text-2xl font-semibold tracking-apple text-ink">Directorio</h2>
        <p className="mb-6 text-sm text-ink-400">
          Posiciones del board en proceso de definición. Buscamos perfil senior con
          experiencia en agroindustria, finanzas sustentables y/o M&A LATAM.
        </p>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {DIRECTORIO.map((p) => (
            <PersonCard key={p.nombre + p.rol} p={p} placeholder />
          ))}
        </div>
      </section>

      {/* Advisors */}
      <section>
        <h2 className="mb-2 text-2xl font-semibold tracking-apple text-ink">Advisors</h2>
        <p className="mb-6 text-sm text-ink-400">
          Network de expertise externa. Estamos sumando perfiles específicos por área.
        </p>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {ADVISORS.map((p) => (
            <PersonCard key={p.nombre + p.rol} p={p} placeholder />
          ))}
        </div>
      </section>

      {/* Alianzas */}
      <section>
        <h2 className="mb-6 text-2xl font-semibold tracking-apple text-ink">Alianzas Estratégicas</h2>
        <div className="apple-card overflow-hidden p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-ink-100 bg-ink-50/50">
                <th className="p-4 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Partner</th>
                <th className="p-4 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Tipo de alianza</th>
                <th className="p-4 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Estado</th>
                <th className="p-4 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Monto / Volumen</th>
              </tr>
            </thead>
            <tbody>
              {ALIANZAS.map((a) => (
                <tr key={a.nombre} className="border-b border-ink-100 last:border-0">
                  <td className="p-4 font-semibold text-ink">{a.nombre}</td>
                  <td className="p-4 text-sm text-ink-600">{a.tipo}</td>
                  <td className="p-4">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${
                      a.estado === 'Activa'
                        ? 'bg-brand-50 text-brand ring-brand/20'
                        : 'bg-yellow-50 text-yellow-700 ring-yellow-200'
                    }`}>{a.estado}</span>
                  </td>
                  <td className="p-4 text-sm text-ink-600">{a.monto}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* CTA */}
      <section className="rounded-appleXl bg-brand px-6 py-16 text-center text-white">
        <h2 className="text-2xl font-semibold tracking-apple md:text-3xl">¿Te interesa sumarte al directorio o advisor board?</h2>
        <p className="mx-auto mt-3 max-w-xl text-white/85">
          Estamos abiertos a conversar con perfiles senior que sumen expertise en bioeconomía,
          finanzas sustentables, agroindustria o expansión LATAM.
        </p>
        <a
          href="mailto:nicolasrietta@gmail.com?subject=%5BTRONGKAI%5D%20Interes%20en%20Directorio/Advisor"
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-medium text-brand transition hover:scale-105"
        >
          Conversemos
        </a>
      </section>
    </div>
  );
}

function PersonCard({ p, highlight, placeholder }: { p: Persona; highlight?: boolean; placeholder?: boolean }) {
  const initials = p.nombre.split(' ').map((s) => s[0]).join('').slice(0, 2).toUpperCase();
  const isPlaceholder = placeholder || p.nombre === 'Por definir' || p.nombre === 'Por sumar';

  return (
    <div className={`apple-card ${highlight ? 'bg-brand-50 ring-1 ring-brand/20' : ''}`}>
      <div className="flex items-center gap-4">
        <div className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full text-xl font-semibold ${
          isPlaceholder ? 'bg-ink-100 text-ink-400' : 'bg-brand text-white'
        }`}>
          {isPlaceholder ? '?' : initials}
        </div>
        <div className="flex-1">
          <div className={`font-semibold ${isPlaceholder ? 'text-ink-400' : 'text-ink'}`}>{p.nombre}</div>
          <div className="text-sm text-ink-600">{p.rol}</div>
        </div>
      </div>
      <p className="mt-4 text-sm leading-relaxed text-ink-600">{p.bio}</p>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {p.expertise.map((e) => (
          <span key={e} className="rounded-full bg-ink-50 px-2.5 py-0.5 text-[11px] font-medium text-ink-600">
            {e}
          </span>
        ))}
      </div>
      {p.email && (
        <a href={`mailto:${p.email}`} className="mt-4 inline-block text-xs font-medium text-brand">
          {p.email}
        </a>
      )}
    </div>
  );
}
