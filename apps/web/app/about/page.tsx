import Image from 'next/image';

const liderazgo = [
  {
    nombre: 'José Cuevas',
    cargo: 'Fundador & Gerente Técnico',
    background:
      'Experto en innovación, valorización de biomasa y spin-offs tecnológicos. Ex Concha y Toro, ex The Not Company.',
  },
  {
    nombre: 'Jaime Echeverría',
    cargo: 'Gerente General',
    background:
      'Ejecutivo senior en industria alimentaria (Traverso, Parmalat, Danone). Especialista en escalamiento y alianzas globales.',
  },
  {
    nombre: 'Claudia Gotschlich',
    cargo: 'Gerenta de Logística & Administración',
    background:
      'Ingeniera Civil Química. Experta en innovación y financiamiento público. Ex CORFO.',
  },
];

const asesores = [
  { nombre: 'Felipe Ugalde', area: 'Estrategia' },
  { nombre: 'Rodrigo Morales', area: 'Ciencia' },
  { nombre: 'Ricardo Pérez Correa', area: 'Desarrollo de negocio' },
  { nombre: 'Guillermo Reyes', area: 'Desarrollo de negocio' },
];

const directorio = [
  { nombre: 'Guido Rietta', rol: 'Presidente del Directorio' },
  { nombre: 'Juan Pablo Velasco', rol: 'Director' },
  { nombre: 'Ester Sáez', rol: 'Directora' },
  { nombre: 'Andrés Fernández', rol: 'Director' },
];

const marcas = [
  {
    nombre: 'Trongkai Feed',
    descripcion:
      'Ingredientes funcionales para acuicultura y mascotas que reemplazan harina de pescado y aditivos sintéticos por proteínas sostenibles y bioactivos.',
  },
  {
    nombre: 'Trongkai Food',
    descripcion:
      'Harinas funcionales 100% vegetales y circulares (tomate, oliva) ricas en fibra y antioxidantes para panadería, snacks y alimentos saludables.',
  },
  {
    nombre: 'Servicios de Plataforma Tecnológica',
    descripcion:
      'Maquila de ingredientes, licenciamiento de biorefinerías y transferencia tecnológica. Alianzas: Opticept (PEF) y Axolot.',
  },
];

export default function AboutPage() {
  return (
    <div className="space-y-12">
      <header className="space-y-3">
        <Image
          src="/logo-trongkai-color.png"
          alt="Trongkai"
          width={300}
          height={70}
          className="h-16 w-auto"
        />
        <h1 className="font-serif text-3xl text-oliva-900">Innovación en Nutrición Circular</h1>
        <p className="max-w-3xl text-sm text-oliva-600">
          Aceleramos la transición a una <strong>bioeconomía circular</strong> transformando los más de
          800.000 toneladas anuales de subproductos agroindustriales que genera Chile en{' '}
          <strong>nutrición regenerativa</strong> para el planeta, los animales y las personas.
        </p>
      </header>

      <section>
        <h2 className="font-serif text-2xl text-oliva-900">Tres líneas de negocio</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          {marcas.map((m) => (
            <article
              key={m.nombre}
              className="rounded-lg border border-oliva/10 bg-white p-5 shadow-sm"
            >
              <h3 className="font-medium text-oliva-900">{m.nombre}</h3>
              <p className="mt-2 text-sm text-oliva-600">{m.descripcion}</p>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h2 className="font-serif text-2xl text-oliva-900">El viaje circular</h2>
        <ol className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          {[
            ['1. Recepción y Estabilización', 'Recolección planificada de subproductos + estabilización de la biomasa preservando bioactivos.'],
            ['2. Fraccionamiento Inteligente', 'Separar líquidos y sólidos, dirigir cada componente a su ruta de valorización más eficiente.'],
            ['3. Valorización en Cascada', 'Extracción verde + fermentación controlada → ingredientes funcionales de alto valor ("residuo cero").'],
          ].map(([t, d]) => (
            <li key={t} className="rounded-lg border-l-4 border-trigo bg-white p-4">
              <h4 className="font-medium text-oliva-900">{t}</h4>
              <p className="mt-1 text-sm text-oliva-600">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <div>
          <h2 className="font-serif text-2xl text-oliva-900">Liderazgo</h2>
          <ul className="mt-4 space-y-4">
            {liderazgo.map((p) => (
              <li key={p.nombre} className="rounded-lg border border-oliva/10 bg-white p-4">
                <div className="font-medium text-oliva-900">{p.nombre}</div>
                <div className="text-xs uppercase tracking-wide text-trigo">{p.cargo}</div>
                <p className="mt-1 text-sm text-oliva-600">{p.background}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-6">
          <div>
            <h2 className="font-serif text-2xl text-oliva-900">Asesores</h2>
            <ul className="mt-3 space-y-1 text-sm text-oliva-600">
              {asesores.map((a) => (
                <li key={a.nombre}>
                  <span className="font-medium text-oliva-900">{a.nombre}</span> — {a.area}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="font-serif text-2xl text-oliva-900">Directorio</h2>
            <ul className="mt-3 space-y-1 text-sm text-oliva-600">
              {directorio.map((d) => (
                <li key={d.nombre}>
                  <span className="font-medium text-oliva-900">{d.nombre}</span> — {d.rol}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-oliva/20 bg-oliva-50 p-6">
        <h2 className="font-serif text-xl text-oliva-900">Compromiso con la validación</h2>
        <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2 text-sm text-oliva-600">
          <div>
            <strong className="text-oliva-900">ACV — Análisis de Ciclo de Vida.</strong> Cuantificamos
            de forma transparente el impacto ambiental positivo del modelo, desde la reducción de
            residuos hasta la mitigación de emisiones.
          </div>
          <div>
            <strong className="text-oliva-900">SOPs — Protocolos Estandarizados.</strong> Cada etapa
            del proceso cuenta con protocolos rigurosos para garantizar consistencia, seguridad y
            eficacia de cada lote frente a mercados globales.
          </div>
        </div>
      </section>
    </div>
  );
}
