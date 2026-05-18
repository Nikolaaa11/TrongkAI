import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        oliva: {
          DEFAULT: '#3F4A2B',
          50: '#F5F1E8',
          100: '#E6E2D5',
          400: '#7C8857',
          600: '#3F4A2B',
          900: '#2A311E',
        },
        trigo: '#C8A961',
        tierra: '#8B5A3C',
        borgoña: '#7A1F1F',
        crema: '#F5F1E8',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['"Source Serif Pro"', 'Georgia', 'serif'],
      },
      spacing: {
        row: '2rem',
      },
    },
  },
  plugins: [],
};

export default config;
