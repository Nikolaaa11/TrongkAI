import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Trongkai — Biorrefinería Agrosphere',
  description: 'Plataforma inteligente de planificación y operación.',
};

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
            <div className="font-serif text-xl tracking-tight">Trongkai</div>
            <nav className="flex gap-6 text-sm">
              <a href="/" className="hover:text-trigo">Operacional</a>
              <a href="/balance" className="hover:text-trigo">Balance de masa</a>
              <a href="/plan" className="hover:text-trigo">Plan 5 años</a>
              <a href="/whatif" className="hover:text-trigo">What-if</a>
              <a href="/supuestos" className="hover:text-trigo">Supuestos</a>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
