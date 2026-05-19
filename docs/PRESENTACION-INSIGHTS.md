# Insights de la presentación corporativa Trongkai (2025-10-22)

> Extraído de `contexto/Presentacion_Trongkai_2026-10.pdf` y `contexto/Presentacion_Trongkai_2025-10-22.pptx` por `scripts/extract_presentation.py`. Versión normalizada del pitch que el equipo usa para inversionistas y partners.

## 1. Posicionamiento (la tesis comercial)

> **"En la naturaleza no existen los residuos, solo recursos."**

Trongkai acelera la transición a una **bioeconomía circular** transformando subproductos agroindustriales en **nutrición regenerativa para el planeta, los animales y las personas**.

## 2. Mercado y oportunidad

| Variable | Valor | Fuente |
|---|---|---|
| Subproductos agroindustriales en Chile (mercado total) | **>800.000 ton/año** | Presentación slide 3 |
| Cuota contractual Trongkai (50.000 ton) | ~6,25% del mercado total | Cálculo |
| Marco regulatorio | Hoja de Ruta Circular Chile 2040 + prohibición de quemas agrícolas | Slide 3 |

**Triple impacto negativo del modelo actual** (que Trongkai mitiga):
1. Contaminación de suelos y aguas.
2. Costos crecientes de disposición para productores.
3. Desecho de compuestos valiosos.

## 3. Tres líneas de negocio (B2B)

### A. **TRONGKAI FEED** — Nutrición animal sostenible
- Target: **acuicultura y mascotas (pet food)**.
- Propuesta: ingredientes funcionales que reemplazan **harina de pescado** y aditivos sintéticos.
- Productos: proteínas sostenibles + compuestos bioactivos de alto valor.
- Driver de precio: precio mayorista de harina de pescado en Chile + premium por sostenibilidad.

### B. **TRONGKAI FOOD** — Ingredientes circulares para humanos
- Target: panadería, snacks, alimentos saludables.
- Propuesta: harinas funcionales 100% vegetales de **tomate y oliva**.
- Atributos clave: ricas en fibra y antioxidantes.

### C. **Servicios de plataforma tecnológica**
- Maquila de ingredientes (procesar MMPP de terceros).
- Licenciamiento de biorefinerías.
- Transferencia tecnológica.
- Alianzas con tecnologías de vanguardia: **Opticept** (PEF) y **Axolot**.

## 4. Modelo operativo en 3 fases (el viaje circular)

1. **Recepción y Estabilización** — recolección planificada + estabilizar biomasa preservando bioactivos.
2. **Fraccionamiento Inteligente** — separar líquidos/sólidos, dirigir cada componente a su ruta de valorización óptima.
3. **Valorización en cascada** — extracción verde + fermentación controlada para producir ingredientes funcionales de alto valor.

**Concepto rector**: "residuo cero". Cada flujo encuentra su valor óptimo antes de descartarse.

## 5. Equipo

### Liderazgo ejecutivo

| Persona | Cargo | Background |
|---|---|---|
| **José Cuevas** | Fundador & Gerente Técnico | Innovación, valorización de biomasa, spin-offs tecnológicos. Ex Concha y Toro, ex The Not Company. |
| **Jaime Echeverría** | Gerente General | Industria alimentaria senior. Ex Traverso, Parmalat, Danone. Especialista en escalamiento y alianzas globales. |
| **Claudia Gotschlich** | Gerenta de Logística & Administración | Ingeniera Civil Química. Experta en innovación y financiamiento público (ex CORFO). |

### Red de asesores

| Persona | Área |
|---|---|
| Felipe Ugalde | Estrategia |
| Rodrigo Morales | Ciencia |
| Ricardo Pérez Correa | Desarrollo de negocio |
| Guillermo Reyes | Desarrollo de negocio |

### Directorio

| Persona | Rol |
|---|---|
| **Guido Rietta** | Presidente del Directorio |
| Juan Pablo Velasco | Director |
| Ester Sáez | Directora |
| Andrés Fernández | Director |

> **Nota**: Guido Rietta (presidente) está vinculado a [[user_nicolas]] (COO de Cehta Capital y AFIS del FIP dueño de Trongkai). El usuario es stakeholder con visibilidad directa sobre el plan.

## 6. Compromisos de validación

- **ACV** (Análisis de Ciclo de Vida) — cuantificar impacto ambiental positivo end-to-end. Aporta credibilidad en mercados ESG.
- **SOPs** (Protocolos de Calidad Estandarizados) — operación y calidad por etapa, asegurando consistencia para mercados globales.

## 7. Beneficios proyectados (3 ejes)

1. **Mitigación de emisiones** — evitar descomposición en vertederos.
2. **Sostenibilidad de cadena de valor** — reducir dependencia de harina de pescado y aditivos sintéticos.
3. **Reducción de residuos** — solución a escala de las 800k ton/año chilenas.

## 8. Impacto en el modelo de la plataforma

Esta info **modifica supuestos y prioridades** del SUPER_PROMPT:

1. **Precio de harina de pescado** entra al top 10 de [`RIESGO-SUPUESTOS.md`](RIESGO-SUPUESTOS.md) como benchmark de TRONGKAI FEED.
2. **Los 5 SKUs base** del Excel se reagrupan en marcas comerciales (FEED / FOOD).
3. **Mercado total = 800.000 ton/año** entra como `supuesto.mercado.subproductos_total_chile_ton`.
4. **ACV + SOPs** son nuevos artefactos a producir desde la plataforma (etapa Fase 6 o aparte).
5. **Opticept** es la marca del PEF — actualizamos GLOSARIO. **Axolot** es alianza tecnológica adicional.
6. **Equipo del directorio** se carga en `Supuesto` para que VersionPlan referencie quién aprobó (auditoría CMF).

## 9. ADR derivado

- [ADR-009] Estrategia de marca dual: **Trongkai Feed** y **Trongkai Food** son sub-marcas comerciales. La plataforma interna mantiene SKU codes técnicos (`HARINA_TOMASA`, etc.) pero la UI muestra agrupación por marca en /plan y exports.
