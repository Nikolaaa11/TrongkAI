import { z } from 'zod';

// MMPP catálogo
export const MMPPCodigo = z.enum([
  'ALPERUJO',
  'TOMASA',
  'POMASA',
  'ORUJO_UVA',
  'LEVADURA',
]);
export type MMPPCodigo = z.infer<typeof MMPPCodigo>;

// Balance de masa — request/response del motor
export const MassBalanceRequest = z.object({
  mmpp_codigo: z.string(),
  humedad_inicial_pct: z.number().min(0).lt(1),
  materia_solida_pct: z.number().min(0).max(1),
  aceite_extraible_pct: z.number().min(0).max(1).default(0),
  licopeno_pct: z.number().min(0).max(1).default(0),
  pectina_pct: z.number().min(0).max(1).default(0),
  input_ton: z.number().positive(),
  mode: z.enum(['A', 'B']).default('A'),
  humedad_final_pct: z.number().min(0).lt(1).default(0.1),
  perdidas_pct: z.number().min(0).lt(1).default(0.031),
});
export type MassBalanceRequest = z.infer<typeof MassBalanceRequest>;

export const SankeyNode = z.object({ name: z.string() });
export const SankeyLink = z.object({
  source: z.string(),
  target: z.string(),
  value: z.number(),
});

export const MassBalanceResponse = z.object({
  mmpp: z.string(),
  mode: z.string(),
  input_ton: z.number(),
  materia_seca_pura_ton: z.number(),
  aceite_extraido_ton: z.number(),
  licopeno_extraido_ton: z.number(),
  pectina_extraida_ton: z.number(),
  harina_final_ton: z.number(),
  agua_evaporada_ton: z.number(),
  perdidas_ton: z.number(),
  materia_seca_neta_pct: z.number(),
  delta_balance_pct: z.number(),
  sankey: z.object({
    nodes: z.array(SankeyNode),
    links: z.array(SankeyLink),
  }),
});
export type MassBalanceResponse = z.infer<typeof MassBalanceResponse>;

// Bottleneck
export const EtapaProceso = z.enum([
  'RECEPCION',
  'ALIMENTACION',
  'HOMOG_1',
  'PEF',
  'PRENSADO_MECANICO',
  'TRICANTER',
  'EXTRACCION',
  'SECADO',
  'HOMOG_2',
  'ENSACADO',
]);
export type EtapaProceso = z.infer<typeof EtapaProceso>;

export const CapacidadInput = z.object({
  etapa: EtapaProceso,
  ton_por_hora: z.number().nullable(),
  tiempo_residencia_h: z.number().default(0),
  aplica: z.boolean().default(true),
});

export const BottleneckRequest = z.object({
  capacidades: z.array(CapacidadInput),
  tiempo_descomposicion_h: z.number().positive(),
  capacidad_camion_ton: z.number().positive().default(22.5),
  horas_operativas_dia: z.number().positive().max(24).default(24),
});

export const Alerta = z.enum(['VERDE', 'AMARILLA', 'ROJA']);
export const BottleneckResponse = z.object({
  flujo_max_ton_h: z.number(),
  etapa_bottleneck: EtapaProceso,
  tiempo_proceso_total_h: z.number(),
  tiempo_descomposicion_h: z.number(),
  ventana_segura_h: z.number(),
  puede_recibir: z.boolean(),
  camiones_max_dia: z.number(),
  horas_operativas_dia: z.number(),
  incertidumbres: z.array(z.string()),
  alerta: Alerta,
});

// Estados de Supuesto (espejado de Prisma)
export const EstadoSupuesto = z.enum([
  'PD',
  'OK_PROVISORIO',
  'OK_VALIDADO_JOSE',
  'OK_VALIDADO_CLAUDIO',
  'OK_VALIDADO_JAIME',
  'OK_VALIDADO_DIRECTORIO',
  'NO_APLICA',
]);
export type EstadoSupuesto = z.infer<typeof EstadoSupuesto>;

export const SensibilidadSupuesto = z.enum(['BAJA', 'MEDIA', 'ALTA', 'CRITICA']);
export type SensibilidadSupuesto = z.infer<typeof SensibilidadSupuesto>;
