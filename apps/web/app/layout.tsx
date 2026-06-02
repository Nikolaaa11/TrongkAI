import type { Metadata } from 'next';
import { CommandK } from '@/components/CommandK';
import NavMenu from '@/components/NavMenu';
import './globals.css';

export const metadata: Metadata = {
  title: 'Trongkai — Innovación en Nutrición Circular',
  description:
    'Plataforma inteligente de planificación y operación de la biorrefinería Trongkai. Trongkai Feed (acuicultura + pet food) y Trongkai Food (humanos).',
  icons: {
    icon: '/icon-trongkai.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es-CL">
      <body className="bg-white font-sans text-ink antialiased">
        <CommandK />
        <NavMenu />

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
