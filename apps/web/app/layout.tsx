import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Trongkai — Innovación en Nutrición Circular',
  description:
    'Plataforma inteligente de planificación y operación de la biorrefinería Trongkai. Trongkai Feed (acuicultura + pet food) y Trongkai Food (humanos).',
  icons: {
    icon: '/icon-trongkai.png',
  },
};

// Nav agrupado por categoría visual
const nav: { href: string; label: string }[] = [
  { href: '/', label: 'Inicio' },
  { href: '/comando', label: '⚡ Centro de Mando' },
  { href: '/dashboard-directorio', label: 'Directorio' },
  { href: '/readiness', label: 'Readiness' },
  { href: '/datos', label: 'Datos faltantes' },
  { href: '/variables', label: 'Matriz Variables' },
  { href: '/decisiones', label: '🎯 Decisiones' },
  { href: '/coherencia', label: 'Coherencia' },
  { href: '/red', label: '🕸 Red' },
  { href: '/data-room', label: 'Data Room' },
  { href: '/lp-pack', label: 'LP Pack' },
  { href: '/equipo', label: 'Equipo' },
  { href: '/plan', label: 'Plan 5 años' },
  { href: '/sensitivity', label: 'Sensibilidad' },
  { href: '/stress', label: 'Stress' },
  { href: '/financiamiento', label: 'Financiamiento' },
  { href: '/carbono', label: 'Carbono' },
  { href: '/compliance', label: 'Compliance' },
  { href: '/macro', label: 'Macro' },
  { href: '/api', label: 'API' },
  { href: '/investigacion', label: 'Research' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es-CL">
      <body className="bg-white font-sans text-ink antialiased">
        {/* Apple-style sticky nav: blanco, blur, sombra mínima */}
        <header className="sticky top-0 z-50 border-b border-ink-100 bg-white/80 backdrop-blur-xl">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-3">
            <Link href="/" className="flex shrink-0 items-center gap-2">
              <Image
                src="/logo-trongkai-color.png"
                alt="Trongkai"
                width={140}
                height={32}
                priority
                className="h-7 w-auto"
              />
            </Link>
            <nav className="flex flex-1 items-center justify-end gap-1 overflow-x-auto">
              {nav.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="rounded-full px-3 py-1.5 text-[13px] font-medium text-ink-600 transition-colors hover:bg-ink-50 hover:text-ink"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto max-w-7xl px-6 py-12">{children}</main>

        <footer className="border-t border-ink-100 bg-ink-50/40 px-6 py-8">
          <div className="mx-auto max-w-7xl text-center text-[12px] text-ink-400">
            <p className="font-medium text-ink-600">
              &ldquo;En la naturaleza no existen los residuos, solo recursos.&rdquo;
            </p>
            <p className="mt-1">Trongkai · Innovación en Nutrición Circular · 2026</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
