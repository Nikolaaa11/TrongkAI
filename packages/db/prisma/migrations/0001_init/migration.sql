-- Trongkai DB - migración inicial (0001_init)
-- Generada manualmente desde packages/db/prisma/schema.prisma para poder seedar
-- sin depender de la CLI de Prisma corriendo en local. Mantener sincronizada con
-- schema.prisma vía CI (futuro: usar `prisma migrate diff`).

-- =====================================================================
-- ENUMs
-- =====================================================================

CREATE TYPE "MMPPCodigo" AS ENUM ('ALPERUJO','TOMASA','POMASA','ORUJO_UVA','LEVADURA');
CREATE TYPE "CasoLogistico" AS ENUM ('CASO_1','CASO_2','CASO_3','CASO_4');
CREATE TYPE "SupplierStatus" AS ENUM ('ACTIVO','PROSPECT','INACTIVO');
CREATE TYPE "EstadoSupuesto" AS ENUM (
  'PD','OK_PROVISORIO','OK_VALIDADO_JOSE','OK_VALIDADO_CLAUDIO',
  'OK_VALIDADO_JAIME','OK_VALIDADO_DIRECTORIO','NO_APLICA'
);
CREATE TYPE "SensibilidadSupuesto" AS ENUM ('BAJA','MEDIA','ALTA','CRITICA');
CREATE TYPE "EtapaProceso" AS ENUM (
  'RECEPCION','ALIMENTACION','HOMOG_1','PEF','PRENSADO_MECANICO',
  'TRICANTER','EXTRACCION','SECADO','HOMOG_2','ENSACADO'
);
CREATE TYPE "TipoProducto" AS ENUM ('BASE','AGREGADO','PTEC');
CREATE TYPE "MarcaProducto" AS ENUM ('FEED','FOOD','SERVICIOS');
CREATE TYPE "BalanceMode" AS ENUM ('A_INITIAL_BASE','B_DEHYDRATED_BASE');
CREATE TYPE "EscenarioPlan" AS ENUM ('BASE','OPTIMISTA','PESIMISTA');
CREATE TYPE "TipoOpex" AS ENUM (
  'ENERGIA','MO','MANTENCION','ENVASE','ALMACEN',
  'CALIDAD','CERTIFICACIONES','ADMIN','TRANSPORTE_CLIENTE'
);

-- =====================================================================
-- Catálogos
-- =====================================================================

CREATE TABLE "MateriaPrima" (
  id                       SERIAL PRIMARY KEY,
  codigo                   "MMPPCodigo" UNIQUE NOT NULL,
  nombre                   TEXT NOT NULL,
  temporada_inicio_mes     INT  NOT NULL,
  temporada_fin_mes        INT  NOT NULL,
  humedad_inicial_pct      DOUBLE PRECISION,
  materia_solida_pct       DOUBLE PRECISION,
  aceite_extraible_pct     DOUBLE PRECISION DEFAULT 0,
  licopeno_pct             DOUBLE PRECISION DEFAULT 0,
  pectina_pct              DOUBLE PRECISION DEFAULT 0,
  tiempo_descomposicion_h  DOUBLE PRECISION,
  notas                    TEXT
);

CREATE TABLE "Supplier" (
  id                              SERIAL PRIMARY KEY,
  nombre                          TEXT UNIQUE NOT NULL,
  mmpp_id                         INT NOT NULL REFERENCES "MateriaPrima"(id),
  distancia_km                    DOUBLE PRECISION NOT NULL,
  tarifa_flete_clp_km             DOUBLE PRECISION NOT NULL,
  caso_logistico                  "CasoLogistico" NOT NULL,
  pago_recepcion_clp_kg           DOUBLE PRECISION NOT NULL DEFAULT 0,
  volumen_anual_comprometido_ton  DOUBLE PRECISION NOT NULL,
  capacidad_camion_ton            DOUBLE PRECISION NOT NULL DEFAULT 22.5,
  contacto                        TEXT,
  certificaciones                 TEXT[] NOT NULL DEFAULT '{}',
  status                          "SupplierStatus" NOT NULL DEFAULT 'ACTIVO',
  notas                           TEXT,
  created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE "Recepcion" (
  id                    SERIAL PRIMARY KEY,
  supplier_id           INT NOT NULL REFERENCES "Supplier"(id),
  mmpp_id               INT NOT NULL REFERENCES "MateriaPrima"(id),
  fecha_hora            TIMESTAMPTZ NOT NULL,
  peso_neto_ton         DOUBLE PRECISION NOT NULL,
  humedad_medida_pct    DOUBLE PRECISION,
  calidad_aceptada      BOOLEAN NOT NULL DEFAULT TRUE,
  motivo_rechazo        TEXT,
  costo_flete_clp       DOUBLE PRECISION NOT NULL,
  ingreso_recepcion_clp DOUBLE PRECISION NOT NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "Recepcion_fecha_idx"      ON "Recepcion"(fecha_hora);
CREATE INDEX "Recepcion_mmpp_fecha_idx" ON "Recepcion"(mmpp_id, fecha_hora);

CREATE TABLE "CapacidadEquipo" (
  id                          SERIAL PRIMARY KEY,
  etapa                       "EtapaProceso" UNIQUE NOT NULL,
  capacidad_ton_hora          DOUBLE PRECISION,
  tiempo_residencia_h         DOUBLE PRECISION,
  capacidad_kg_kwh            DOUBLE PRECISION,
  horas_entre_mantenciones    DOUBLE PRECISION,
  costo_mantencion_clp        DOUBLE PRECISION,
  costo_energia_unitario_clp  DOUBLE PRECISION,
  aplica_a_mmpp               "MMPPCodigo"[] NOT NULL DEFAULT '{}',
  opcional                    BOOLEAN NOT NULL DEFAULT FALSE,
  notas                       TEXT,
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE "Producto" (
  id                 SERIAL PRIMARY KEY,
  codigo             TEXT UNIQUE NOT NULL,
  nombre             TEXT NOT NULL,
  mmpp_origen_id     INT REFERENCES "MateriaPrima"(id),
  tipo               "TipoProducto" NOT NULL,
  marca              "MarcaProducto" NOT NULL DEFAULT 'FEED',
  precio_venta_clp_kg DOUBLE PRECISION,
  rendimiento_pct_ms DOUBLE PRECISION,
  ano_lanzamiento    INT NOT NULL,
  notas              TEXT
);

CREATE TABLE "Supuesto" (
  id                  SERIAL PRIMARY KEY,
  clave               TEXT UNIQUE NOT NULL,
  valor_actual        TEXT,
  unidad              TEXT,
  fuente              TEXT NOT NULL,
  estado              "EstadoSupuesto" NOT NULL,
  sensibilidad        "SensibilidadSupuesto" NOT NULL DEFAULT 'MEDIA',
  owner               TEXT,
  fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT now(),
  tag                 TEXT
);
CREATE INDEX "Supuesto_estado_idx"          ON "Supuesto"(estado);
CREATE INDEX "Supuesto_sens_estado_idx"     ON "Supuesto"(sensibilidad, estado);

CREATE TABLE "SupuestoAudit" (
  id              SERIAL PRIMARY KEY,
  supuesto_id     INT NOT NULL REFERENCES "Supuesto"(id),
  valor_anterior  TEXT,
  valor_nuevo     TEXT,
  razon           TEXT NOT NULL,
  changed_by      TEXT NOT NULL,
  changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Planificación
-- =====================================================================

CREATE TABLE "PlanAnual" (
  id              SERIAL PRIMARY KEY,
  ano             INT NOT NULL,
  escenario       "EscenarioPlan" NOT NULL DEFAULT 'BASE',
  balance_mode    "BalanceMode"   NOT NULL DEFAULT 'A_INITIAL_BASE',
  wacc_anual      DOUBLE PRECISION,
  aprobado_por    TEXT,
  fecha_creacion  TIMESTAMPTZ NOT NULL DEFAULT now(),
  fecha_aprobacion TIMESTAMPTZ,
  UNIQUE (ano, escenario)
);

CREATE TABLE "MixProduccionMensual" (
  id                SERIAL PRIMARY KEY,
  plan_anual_id     INT NOT NULL REFERENCES "PlanAnual"(id) ON DELETE CASCADE,
  mes               INT NOT NULL,
  producto_id       INT NOT NULL REFERENCES "Producto"(id),
  mmpp_codigo       "MMPPCodigo" NOT NULL,
  ton_procesadas    DOUBLE PRECISION NOT NULL,
  ton_producto_final DOUBLE PRECISION NOT NULL,
  detalles          JSONB
);

CREATE TABLE "CapEx" (
  id                         SERIAL PRIMARY KEY,
  plan_anual_id              INT NOT NULL REFERENCES "PlanAnual"(id) ON DELETE CASCADE,
  descripcion                TEXT NOT NULL,
  monto_clp                  DOUBLE PRECISION NOT NULL,
  ano                        INT NOT NULL,
  etapa_proceso_relacionada  "EtapaProceso",
  depreciacion_anos          INT NOT NULL DEFAULT 10,
  aace_clase                 INT NOT NULL DEFAULT 5
);

CREATE TABLE "OpEx" (
  id                 SERIAL PRIMARY KEY,
  plan_anual_id      INT NOT NULL REFERENCES "PlanAnual"(id) ON DELETE CASCADE,
  tipo               "TipoOpex" NOT NULL,
  ano                INT NOT NULL,
  mensual_clp        DOUBLE PRECISION NOT NULL,
  formula_referencia TEXT
);

CREATE TABLE "FlujoCaja" (
  id                       SERIAL PRIMARY KEY,
  plan_anual_id            INT NOT NULL REFERENCES "PlanAnual"(id) ON DELETE CASCADE,
  mes                      INT NOT NULL,
  ingresos_ventas          DOUBLE PRECISION NOT NULL DEFAULT 0,
  ingresos_maquilas        DOUBLE PRECISION NOT NULL DEFAULT 0,
  ingresos_recepcion       DOUBLE PRECISION NOT NULL DEFAULT 0,
  ingresos_transferencia_tec DOUBLE PRECISION NOT NULL DEFAULT 0,
  costos_directos          DOUBLE PRECISION NOT NULL DEFAULT 0,
  gastos_fijos             DOUBLE PRECISION NOT NULL DEFAULT 0,
  capex_periodo            DOUBLE PRECISION NOT NULL DEFAULT 0,
  ebitda                   DOUBLE PRECISION NOT NULL,
  flujo_neto               DOUBLE PRECISION NOT NULL,
  UNIQUE (plan_anual_id, mes)
);

-- =====================================================================
-- Trazabilidad
-- =====================================================================

CREATE TABLE "AuditLog" (
  id              SERIAL PRIMARY KEY,
  entidad         TEXT NOT NULL,
  entidad_id      TEXT NOT NULL,
  campo           TEXT NOT NULL,
  valor_anterior  TEXT,
  valor_nuevo     TEXT,
  razon           TEXT,
  usuario         TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX "AuditLog_entidad_idx" ON "AuditLog"(entidad, entidad_id);

CREATE TABLE "VersionPlan" (
  id              SERIAL PRIMARY KEY,
  plan_anual_id   INT NOT NULL REFERENCES "PlanAnual"(id),
  snapshot        JSONB NOT NULL,
  aprobado_por    TEXT NOT NULL,
  fecha_aprobacion TIMESTAMPTZ NOT NULL,
  hash            TEXT UNIQUE NOT NULL,
  comentario      TEXT
);

CREATE TABLE "TipoCambio" (
  id              SERIAL PRIMARY KEY,
  codigo          TEXT NOT NULL,
  valor_clp       DOUBLE PRECISION NOT NULL,
  vigencia_desde  TIMESTAMPTZ NOT NULL,
  vigencia_hasta  TIMESTAMPTZ
);
CREATE INDEX "TipoCambio_codigo_idx" ON "TipoCambio"(codigo, vigencia_desde);

-- =====================================================================
-- Trigger de inmutabilidad de VersionPlan
-- (ADR-005 — snapshot inmutable post-aprobación)
-- =====================================================================

CREATE OR REPLACE FUNCTION trongkai_block_versionplan_modify()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'VersionPlan es inmutable (ADR-005). Crear nueva versión en lugar de modificar.';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER versionplan_immutable
BEFORE UPDATE OR DELETE ON "VersionPlan"
FOR EACH ROW EXECUTE FUNCTION trongkai_block_versionplan_modify();
