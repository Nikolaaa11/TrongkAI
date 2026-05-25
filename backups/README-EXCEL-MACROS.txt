TRONGKAI — Excel con Macros VBA
================================

Archivos generados (25/05/2026 16:42):

  1. Trongkai-Master-VBA-20260525-1642.xlsm
     Excel con instrucciones, dashboard placeholder y macros buttons.

  2. TrongkaiAPI.bas
     Módulo VBA con 6 macros para importar al Excel.

INSTRUCCIONES DE USO
--------------------

PASO 1 - Abrir el .xlsm en Excel
  - Click derecho > Propiedades > Desbloquear (si Windows lo bloquea)
  - Doble-click para abrir
  - Habilitar contenido si aparece la barra amarilla

PASO 2 - Importar el módulo VBA
  - Alt+F11 (abre editor Visual Basic)
  - File > Import File...
  - Seleccionar TrongkaiAPI.bas
  - Alt+Q para cerrar el editor

PASO 3 - Ejecutar macros
  - Alt+F8 (lista de macros disponibles)
  - Doble-click en cualquier macro o seleccionar + Ejecutar

MACROS DISPONIBLES
------------------
  RefrescarDashboard       -> GET /api/snapshot
  DescargarTearsheetPDF    -> GET /api/tearsheet.pdf
  RecalcularReadiness      -> GET /readiness/score?n_sims_mc=500
  EjecutarHeatmap5x5       -> POST /sensitivity/heatmap (5x5=25 sims)
  RefrescarMacroChile      -> GET /macro/chile
  RefrescarTodo            -> Ejecuta las refrescadas en cadena

MOTOR EN VIVO
-------------
  Base URL:  https://trongkai-engine.fly.dev
  Swagger:   https://trongkai-engine.fly.dev/docs
  PDF live:  https://trongkai-engine.fly.dev/api/tearsheet.pdf

NOTAS
-----
- Las macros usan MSXML2.XMLHTTP (disponible en todas las versiones de Office Windows).
- El parser JSON es minimalista. Para casos avanzados, agregar referencia a Microsoft Script Control.
- Conexión sin auth — todos los endpoints son públicos en el engine prod.

GENERADO POR: TrongkAI Platform
