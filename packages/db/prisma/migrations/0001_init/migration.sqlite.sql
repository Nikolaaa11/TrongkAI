-- Trongkai DB - migración inicial para SQLite local (sin Postgres).
-- ENUMs convertidos a TEXT con CHECK. JSONB/ARRAY convertidos a TEXT JSON.
-- Mantener sincronizada con migration.sql (versión Postgres canónica).

-- =====================================================================
-- Catálogos
-- =====================================================================

CREATE TABLE IF NOT EXISTS "MateriaPrima" (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo                   TEXT UNIQUE NOT NULL CHECK (codigo IN ('ALPERUJO','TOMASA','POMASA','ORUJO_UVA','LEVADURA')),
  nombre                   TEXT NOT NULL,
  temporada_inicio_mes     INTEGER NOT NULL,
  temporada_fin_mes        INTEGER NOT NULL,
  humedad_inicial_pct      REAL,
  materia_solida_pct       REAL,
  aceite_extraible_pct     REAL DEFAULT 0,
  licopeno_pct             REAL DEFAULT 0,
  pectina_pct              REAL DEFAULT 0,
  tiempo_descomposicion_h  REAL,
  notas                    TEXT
);

CREATE TABLE IF NOT EXISTS "Supplier" (
  id                              INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre                          TEXT UNIQUE NOT NULL,
  mmpp_id                         INTEGER NOT NULL REFERENCES "MateriaPrima"(id),
  distancia_km                    REAL NOT NULL,
  tarifa_flete_clp_km             REAL NOT NULL,
  caso_logistico                  TEXT NOT NULL CHECK (caso_logistico IN ('CASO_1','CASO_2','CASO_3','CASO_4')),
  pago_recepcion_clp_kg           REAL NOT NULL DEFAULT 0,
  volumen_anual_comprometido_ton  REAL NOT NULL,
  capacidad_camion_ton            REAL NOT NULL DEFAULT 22.5,
  contacto                        TEXT,
  certificaciones                 TEXT NOT NULL DEFAULT '[]',  -- JSON array
  status                          TEXT NOT NULL DEFAULT 'ACTIVO' CHECK (status IN ('ACTIVO','PROSPECT','INACTIVO')),
  notas                           TEXT,
  created_at                      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Recepcion" (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  supplier_id           INTEGER NOT NULL REFERENCES "Supplier"(id),
  mmpp_id               INTEGER NOT NULL REFERENCES "MateriaPrima"(id),
  fecha_hora            TEXT NOT NULL,
  peso_neto_ton         REAL NOT NULL,
  humedad_medida_pct    REAL,
  calidad_aceptada      INTEGER NOT NULL DEFAULT 1,
  motivo_rechazo        TEXT,
  costo_flete_clp       REAL NOT NULL,
  ingreso_recepcion_clp REAL NOT NULL,
  created_at            TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "Recepcion_fecha_idx" ON "Recepcion"(fecha_hora);
CREATE INDEX IF NOT EXISTS "Recepcion_mmpp_fecha_idx" ON "Recepcion"(mmpp_id, fecha_hora);

CREATE TABLE IF NOT EXISTS "CapacidadEquipo" (
  id                          INTEGER PRIMARY KEY AUTOINCREMENT,
  etapa                       TEXT UNIQUE NOT NULL CHECK (etapa IN
    ('RECEPCION','ALIMENTACION','HOMOG_1','PEF','PRENSADO_MECANICO','TRICANTER','EXTRACCION','SECADO','HOMOG_2','ENSACADO')),
  capacidad_ton_hora          REAL,
  tiempo_residencia_h         REAL,
  capacidad_kg_kwh            REAL,
  horas_entre_mantenciones    REAL,
  costo_mantencion_clp        REAL,
  costo_energia_unitario_clp  REAL,
  aplica_a_mmpp               TEXT NOT NULL DEFAULT '[]',  -- JSON array
  opcional                    INTEGER NOT NULL DEFAULT 0,
  notas                       TEXT,
  updated_at                  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Producto" (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo             TEXT UNIQUE NOT NULL,
  nombre             TEXT NOT NULL,
  mmpp_origen_id     INTEGER REFERENCES "MateriaPrima"(id),
  tipo               TEXT NOT NULL CHECK (tipo IN ('BASE','AGREGADO','PTEC')),
  marca              TEXT NOT NULL DEFAULT 'FEED' CHECK (marca IN ('FEED','FOOD','SERVICIOS')),
  precio_venta_clp_kg REAL,
  rendimiento_pct_ms REAL,
  ano_lanzamiento    INTEGER NOT NULL,
  notas              TEXT
);

CREATE TABLE IF NOT EXISTS "Supuesto" (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  clave               TEXT UNIQUE NOT NULL,
  valor_actual        TEXT,
  unidad              TEXT,
  fuente              TEXT NOT NULL,
  estado              TEXT NOT NULL CHECK (estado IN
    ('PD','OK_PROVISORIO','OK_VALIDADO_JOSE','OK_VALIDADO_CLAUDIO','OK_VALIDADO_JAIME','OK_VALIDADO_DIRECTORIO','NO_APLICA')),
  sensibilidad        TEXT NOT NULL DEFAULT 'MEDIA' CHECK (sensibilidad IN ('BAJA','MEDIA','ALTA','CRITICA')),
  owner               TEXT,
  fecha_actualizacion TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tag                 TEXT
);
CREATE INDEX IF NOT EXISTS "Supuesto_estado_idx"      ON "Supuesto"(estado);
CREATE INDEX IF NOT EXISTS "Supuesto_sens_estado_idx" ON "Supuesto"(sensibilidad, estado);

CREATE TABLE IF NOT EXISTS "SupuestoAudit" (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  supuesto_id     INTEGER NOT NULL REFERENCES "Supuesto"(id),
  valor_anterior  TEXT,
  valor_nuevo     TEXT,
  razon           TEXT NOT NULL,
  changed_by      TEXT NOT NULL,
  changed_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================================
-- Planificación
-- =====================================================================

CREATE TABLE IF NOT EXISTS "PlanAnual" (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  ano             INTEGER NOT NULL,
  escenario       TEXT NOT NULL DEFAULT 'BASE' CHECK (escenario IN ('BASE','OPTIMISTA','PESIMISTA')),
  balance_mode    TEXT NOT NULL DEFAULT 'A_INITIAL_BASE' CHECK (balance_mode IN ('A_INITIAL_BASE','B_DEHYDRATED_BASE')),
  wacc_anual      REAL,
  aprobado_por    TEXT,
  fecha_creacion  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_aprobacion TEXT,
  UNIQUE (ano, escenario)
);

CREATE TABLE IF NOT EXISTS "FlujoCaja" (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_anual_id            INTEGER NOT NULL REFERENCES "PlanAnual"(id) ON DELETE CASCADE,
  mes                      INTEGER NOT NULL,
  ingresos_ventas          REAL NOT NULL DEFAULT 0,
  ingresos_maquilas        REAL NOT NULL DEFAULT 0,
  ingresos_recepcion       REAL NOT NULL DEFAULT 0,
  ingresos_transferencia_tec REAL NOT NULL DEFAULT 0,
  costos_directos          REAL NOT NULL DEFAULT 0,
  gastos_fijos             REAL NOT NULL DEFAULT 0,
  capex_periodo            REAL NOT NULL DEFAULT 0,
  ebitda                   REAL NOT NULL,
  flujo_neto               REAL NOT NULL,
  UNIQUE (plan_anual_id, mes)
);

-- Trazabilidad
CREATE TABLE IF NOT EXISTS "AuditLog" (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  entidad         TEXT NOT NULL,
  entidad_id      TEXT NOT NULL,
  campo           TEXT NOT NULL,
  valor_anterior  TEXT,
  valor_nuevo     TEXT,
  razon           TEXT,
  usuario         TEXT NOT NULL,
  created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "AuditLog_entidad_idx" ON "AuditLog"(entidad, entidad_id);
