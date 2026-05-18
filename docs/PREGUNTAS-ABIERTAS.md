# Preguntas abiertas — Fase 0

> Convención: `[BLOQUEANTE]` impide avanzar de fase. `[NO BLOQUEANTE]` se puede diferir.
> Cada pregunta lleva: dueño sugerido para responder, fase a la que bloquea, y referencia al supuesto.

## Bloqueantes para Fase 2 (Módulo 1 — Recepción + Capacidades)

1. `[BLOQUEANTE]` **Capacidad nominal del secador** (`cap.secado_ton_h`).
   - Dueño: Matías (con ingeniería conceptual del proveedor de equipo)
   - Sin esto el motor de cuello de botella no responde el entregable M1 ("¿cuántos camiones de tomasa puedo recibir el 15-Feb-2027?").
   - Mínimo aceptable: rango ±20%.

2. `[BLOQUEANTE]` **Tiempo de descomposición real de tomasa, pomasa, alperujo y orujo en silo** (`<mmpp>.tiempo_descomposicion_h`).
   - Dueño: José (medición en planta piloto)
   - Mínimo aceptable: rango ±1 h por MMPP.

3. `[BLOQUEANTE]` **¿La planta piloto tiene una o dos líneas de PEF?** (capacidad y costo se duplican).
   - Dueño: Jaime
   - Trongkai L96-97 sugiere "una línea y el óptice pasa perfecto" pero "capacidad de pensado quizá no está muy comprensa".

4. `[NO BLOQUEANTE]` **¿Prensado mecánico, tricánter o ambos en paralelo?**
   - Dueño: Jaime + ingeniería
   - Jaime: "es muy probable que terminemos con dos prensados". Por defecto modelamos ambos paralelo.

## Bloqueantes para Fase 3 (Módulo 2 — Balance de masa)

5. `[BLOQUEANTE]` **¿Modo A o modo B como default para reportes oficiales?**
   - Dueño: José + Claudio (validan; Jaime aprueba)
   - Sin firma de uno de los dos, no se promueve `OK_VALIDADO_*`. Mientras tanto, el motor muestra los dos lado a lado.

6. `[BLOQUEANTE]` **Pérdidas reales por etapa** (8 supuestos en `SUPUESTOS.md` §7).
   - Dueño: José + planta piloto.
   - Sin esto, el balance "cuadra" pero las pérdidas son inventadas y pueden esconder problemas reales.

7. `[NO BLOQUEANTE]` **Humedad inicial de pomasa, orujo y levadura** (sólo alperujo y tomasa están).
   - Dueño: José.

## Bloqueantes para Fase 4 (Módulo 3 — Plan 5 años)

8. `[BLOQUEANTE]` **Precios de venta de los 12 SKUs**. Hoy la columna "Precio de Venta" del Excel está vacía.
   - Dueño: Jaime + comercial.
   - Mínimo aceptable: rango por SKU (precio piso, target, techo) + fuente comparable.
   - Sin esto no hay EERR. Jaime mencionó "aceite 1.200 $/kg" como dato suelto — necesitamos los 12.

9. `[BLOQUEANTE]` **Costo real del secador por etapa** (`costo_etapa.secado_clp_kg`).
   - Dueño: Matías + cotización equipo + tarifa eléctrica real.
   - Es el "caro" según Jaime y el principal driver del bottleneck financiero.

10. `[BLOQUEANTE]` **WACC del FIP CEHTA ESG para descontar flujos**.
    - Dueño: Directorio / AFIS.
    - Sin esto no hay VAN ni payback descontado.

11. `[BLOQUEANTE]` **Tarifa eléctrica + UF base + USD/CLP base**.
    - Dueño: Tesorería + Matías.
    - Reajustables en UF según ADR-001.

12. `[BLOQUEANTE]` **¿CapEx por año o por hito?** y monto de planta piloto vs planta industrial.
    - Dueño: Jaime + ingeniería.
    - Hoy en `Datos x Plan 5 años` toda la columna OpEx/CapEx está PD.

13. `[NO BLOQUEANTE]` **¿Régimen de depreciación acelerada art. 31 N°5 LIR aplica a equipos importados desde China bajo TLC?**
    - Dueño: Tax (KPMG/Cehta).

## Bloqueantes para Fase 5 (What-If)

14. `[NO BLOQUEANTE]` **¿Las 5 preguntas tipo del SUPER_PROMPT §4.4 son las correctas?** ¿O hay otras prioritarias que el directorio pide?
    - Dueño: Jaime + directorio CEHTA.

## Operacionales / institucionales

15. `[BLOQUEANTE para deploy]` **Server destino de producción** (Fly.io, On-prem en planta, AWS, etc.) y backup policy.
    - Dueño: Nicolás (COO Cehta) + IT Trongkai.

16. `[BLOQUEANTE para deploy]` **Lista de usuarios (4-6) con email y rol**: operador planta, analista, gerente, directorio (solo lectura).
    - Dueño: Jaime + Nicolás.

17. `[NO BLOQUEANTE]` **¿Política CMF de valorización de FIP CEHTA ESG aplica algún formato específico de reporte trimestral?**
    - Dueño: Compliance Cehta (FIP CEHTA ESG es regulado).

18. `[NO BLOQUEANTE]` **¿Las certificaciones (más allá de B Corp) qué incluyen y cuánto cuestan al año?**
    - Dueño: Calidad Trongkai.

---

**Orden de respuesta sugerido para destrabar la plataforma**:
Pregunta 8 (precios) > 1 (cap secador) > 5 (modo balance) > 2 (descomposición) > 10 (WACC) > resto.

Sin las preguntas 1, 2, 8 y 10 no se entrega un MVP defendible a directorio.
