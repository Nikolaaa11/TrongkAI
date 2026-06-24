// Captura screenshots reales de cada pantalla para la guía de usuario (/guia).
// Uso:
//   node scripts/capturar-guia.mjs                  -> captura TODAS las secciones
//   node scripts/capturar-guia.mjs /riesgo /macro   -> captura solo esas rutas
//
// Requiere: npx playwright install chromium
// Salida: apps/web/public/guia/<seccion>.png  (1280x820, image-first de la guía)
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';

const BASE = process.env.GUIA_BASE_URL || 'https://trongkai-web.vercel.app';
const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = join(__dirname, '..', 'public', 'guia');
mkdirSync(OUT, { recursive: true });

// Todas las rutas que la guía puede ilustrar (deben existir en SCREENSHOTS de page.tsx).
const TODAS = [
  '/comando', '/plan', '/dashboard-directorio', '/riesgo', '/decisiones',
  '/planta', '/simulacion', '/balance-integral', '/balance-etapas', '/costeo',
  '/parametros', '/equipos', '/readiness', '/data-room', '/carbono',
  '/compliance', '/lp-pack', '/pipeline-lp', '/escalas', '/whatif-live',
  '/sensitivity', '/inteligencia', '/financiamiento', '/variables', '/inbox',
  '/audit', '/salud', '/mapa',
];

const args = process.argv.slice(2).filter((a) => a.startsWith('/'));
const rutas = args.length ? args : TODAS;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 1 });

let ok = 0;
let fail = 0;
for (const ruta of rutas) {
  const archivo = join(OUT, `${ruta.replace(/^\//, '')}.png`);
  try {
    await page.goto(`${BASE}${ruta}`, { waitUntil: 'networkidle', timeout: 45000 });
    // Dar tiempo a charts, fetch de datos y animaciones de entrada.
    await page.waitForTimeout(2800);
    await page.screenshot({ path: archivo, clip: { x: 0, y: 0, width: 1280, height: 820 } });
    console.log(`OK   ${ruta} -> ${archivo}`);
    ok++;
  } catch (e) {
    console.log(`FAIL ${ruta}: ${e.message}`);
    fail++;
  }
}

await browser.close();
console.log(`\nListo: ${ok} OK, ${fail} FAIL de ${rutas.length}`);
process.exit(fail > 0 ? 1 : 0);
