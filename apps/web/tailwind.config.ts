import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  safelist: [
    // Colores semánticos usados dinámicamente en /datos y otras
    'bg-red-50', 'text-red-600', 'ring-red-200',
    'bg-orange-50', 'text-orange-600', 'ring-orange-200',
    'bg-yellow-50', 'text-yellow-700', 'ring-yellow-200',
    'bg-brand-50', 'text-brand', 'ring-brand/20', 'ring-brand/30',
    'bg-brand', 'text-brand-700', 'from-brand', 'to-brand-700',
    'bg-ink-50', 'bg-ink-100', 'bg-ink', 'text-ink', 'text-ink-400', 'text-ink-600',
  ],
  theme: {
    extend: {
      colors: {
        // ===== Paleta Apple-inspired =====
        // Base
        white: '#FFFFFF',
        ink: {
          DEFAULT: '#1D1D1F',   // texto principal Apple
          50: '#F5F5F7',          // fondo gris muy claro (Apple sections)
          100: '#E8E8ED',         // borde sutil
          200: '#D2D2D7',         // gris claro
          400: '#86868B',         // gris medio (subtítulos)
          600: '#515154',         // gris oscuro
          900: '#1D1D1F',         // texto principal
        },
        // Acento Trongkai (verde brand)
        brand: {
          DEFAULT: '#1A8A1A',    // verde Trongkai vivo (del logo)
          50: '#EAF6EA',
          100: '#C8E7C8',
          400: '#3FB23F',
          600: '#1A8A1A',
          700: '#136913',
          900: '#0B3D0B',
        },
        // Mantener paleta clásica disponible (legacy)
        oliva: {
          DEFAULT: '#3F4A2B',
          50: '#F5F1E8',
          100: '#E6E2D5',
          400: '#7C8857',
          600: '#3F4A2B',
          700: '#2A311E',
          900: '#2A311E',
        },
        trigo: '#C8A961',
        tierra: '#8B5A3C',
        borgoña: '#7A1F1F',
        crema: '#F5F1E8',
        papel: '#FEFCF6',
      },
      fontFamily: {
        // SF Pro stack — fallback Inter
        sans: [
          '"SF Pro Display"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Inter"',
          'system-ui',
          'sans-serif',
        ],
        serif: [
          '"SF Pro Display"',
          '"Source Serif Pro"',
          'Georgia',
          'serif',
        ],
      },
      letterSpacing: {
        apple: '-0.022em',     // Apple-tight tracking para títulos
        appleNormal: '-0.011em',
      },
      borderRadius: {
        apple: '18px',
        appleLg: '24px',
        appleXl: '32px',
      },
      boxShadow: {
        apple: '0 1px 3px 0 rgba(0,0,0,0.04), 0 1px 2px 0 rgba(0,0,0,0.02)',
        appleHover: '0 6px 24px -4px rgba(0,0,0,0.08), 0 2px 6px 0 rgba(0,0,0,0.04)',
        appleLg: '0 12px 40px -8px rgba(0,0,0,0.08)',
      },
      spacing: {
        row: '2rem',
      },
    },
  },
  plugins: [],
};

export default config;
