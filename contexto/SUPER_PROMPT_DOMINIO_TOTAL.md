# SUPER PROMPT — DOMINIO TOTAL EN LA APP (v1, 03-jul-2026)

> **Misión:** que la plataforma sea *realmente útil* sin manual externo. El conocimiento de la
> guía (/guia) deja de vivir solo en una página aparte y pasa a estar **dentro de cada pantalla**:
> qué hace, qué funciones tiene, qué parámetros la mueven, de dónde salen los datos y cómo
> reemplazarlos. Un usuario nuevo debe poder dominar cualquier sección sin salir de ella.

## 1. El problema que esto resuelve

- `/guia` es completa (29 secciones, 28 capturas reales, funciones + parámetros + fuentes),
  pero es **pull**: el usuario tiene que ir a buscarla. En el uso real nadie interrumpe su
  flujo para abrir un manual.
- Resultado: el equipo usa 5 pantallas de 29 y pregunta "¿de dónde sale este número?" por WhatsApp.
- La utilidad real = contexto **push**: la explicación vive al lado del dato, un click, sin navegar.

## 2. Arquitectura de la solución (implementada en esta ola)

| Pieza | Qué es | Archivo |
|---|---|---|
| **Fuente única** | Los datos de la guía (tipos + GUIA + SCREENSHOTS) extraídos a un módulo compartido. La guía y la ayuda contextual leen EL MISMO objeto → cero divergencia. | `apps/web/lib/guia-data.ts` |
| **Ayuda contextual global** | Botón flotante "?" en TODAS las páginas (montado en layout). Abre un panel lateral con: qué es · para qué sirve · funciones · cómo usarla · parámetros que influyen (nombre → dónde se trabaja → efecto) · 📡 de dónde salen los datos · cómo reemplazarlos · captura real · link a /guia. | `apps/web/components/AyudaSeccion.tsx` |
| **Guía refactorizada** | /guia importa de lib/guia-data.ts (ya no duplica). | `apps/web/app/guia/page.tsx` |

Reglas de diseño:
1. El panel se resuelve por `usePathname()` → lookup en GUIA. Si la ruta no está documentada,
   el botón no aparece (nunca ayuda vacía).
2. print:hidden — no contamina PDFs ni board packs.
3. Apple-style: drawer blanco, backdrop blur, misma tipografía ink/brand de la casa.
4. Cada nueva página DEBE agregar su entrada en `lib/guia-data.ts` — así gana guía + ayuda
   contextual + Cmd+K de una sola vez. (Regla para trongkai-improver y todo agente.)

## 3. Estándar de contenido por sección (contrato de calidad)

Toda entrada de GUIA debe tener, sin excepción:
- `queEs` (1 frase) + `paraQue` (1 frase de valor de negocio)
- `funciones[]` — TODAS las capacidades visibles de la pantalla
- `pasos[]` — cómo trabajarla (numerado, accionable)
- `parametros[]` — {nombre, donde, efecto}: qué mueve el resultado, EN QUÉ PANTALLA se trabaja
  y qué pasa al cambiarlo. "donde" debe ser una ruta real de la app o una acción concreta.
- `fuente` — endpoint del engine / módulo Python / cálculo, con nombre exacto
- `reemplazar` — el camino concreto para pasar de estimación a dato real (quién, dónde, cómo)

## 4. Verificación (auditoría multi-agente de esta ola)

- Endpoints citados en `fuente` existen en `apps/engine/trongkai_engine/main.py`.
- Rutas citadas en `donde` existen en `apps/web/app/*/page.tsx`.
- Ninguna sección con funciones/parametros vacíos.
- Números citados coherentes con el canon vigente (V3: 270 CLP/kWh, 19.114 CLP/kg OPEX,
  194.723/77.938 CLP/ton MP seca — ver [[SUPER_PROMPT_COSTOS_PROCESOS_V3]]).
- Capturas de /guia frescas tras cada cambio visual (script `apps/web/scripts/capturar-guia.mjs`).

## 5. Roadmap de utilidad real — ESTADO 03-jul-2026

1. ✅ **Provenance por número** — `components/NivelDato.tsx` en /simulacion, /costeo, /plan
   (derivado en vivo de GET /parametros; peor driver manda).
2. ✅ **Acciones sugeridas por pantalla** — `SIGUIENTES` en guia-data (56 acciones, 28 secciones),
   bloque "¿Y ahora qué?" en el panel de ayuda.
3. ✅ **Tour de primer uso** — "▶ Tour guiado" recorre los `pasos[]` sobre la página real.
4. ⏳ **Telemetría de secciones** (qué pantallas nadie abre) — pendiente, requiere usuarios activos.

## 6. Definition of done de esta ola

- [x] lib/guia-data.ts como fuente única
- [x] AyudaSeccion global en layout con panel completo
- [x] /guia consumiendo el módulo compartido
- [x] Auditoría multi-agente de las 29 entradas (endpoints/rutas/completitud)
- [x] tsc verde + build verde + deploy + verificación live
- [x] Capturas re-generadas si cambió el aspecto de páginas
