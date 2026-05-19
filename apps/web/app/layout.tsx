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

const nav: { href: string; label: string }[] = [
  { href: '/', label: 'Operacional' },
  { href: '/agenda', label: 'Agenda camiones' },
  { href: '/balance', label: 'Balance de masa' },
  { href: '/plan', label: 'Plan 5 años' },
  { href: '/whatif', label: 'What-if' },
  { href: '/supuestos', label: 'Supuestos' },
  { href: '/about', label: 'Equipo' },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es-CL">
      <body className="font-sans antialiased">
        <header className="border-b border-oliva/20 bg-oliva-900 text-crema">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
            <Link href="/" className="flex items-center gap-3">
              <Image
                src="/logo-trongkai-white.png"
                alt="Trongkai"
                width={140}
                height={32}
                priority
                className="h-7 w-auto"
              />
              <span className="hidden text-xs uppercase tracking-widest text-crema/70 md:inline">
                Plataforma interna
              </span>
            </Link>
            <nav className="flex gap-5 text-sm">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-trigo">
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        <footer className="mx-auto mt-12 max-w-7xl px-6 py-4 text-xs text-oliva-600">
          <span>
            "En la naturaleza no existen los residuos, solo recursos." — Trongkai 2026
          </span>
        </footer>
      </body>
    </html>
  );
}
