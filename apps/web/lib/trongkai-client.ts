/**
 * Cliente TypeScript tipado para el motor Trongkai (21 endpoints).
 *
 * Uso:
 *   import { trongkai } from '@/lib/trongkai-client';
 *   const plan = await trongkai.plan();
 *   const mc = await trongkai.monteCarloIntegrado({ n_runs: 2000 });
 */

const BASE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type PlanRequest = {
  wacc_anual?: number;
  volumen_total_ton_ano?: number;
  opex_mensual_clp?: number;
  costo_mmpp_clp_kg?: number;
};

export type Kpis = {
  tir_proyecto_anual: number | null;
  van: number;
  payback_meses: number | null;
  ebitda_margin_promedio: number;
  ratio_capex_ventas: number;
};

export type PorMarca = {
  ingresos_anuales: number[];
  volumen_ton_anuales: number[];
  tam_clp_anual?: number;
  penetracion_pct_ano5?: number;
};

export type PlanResponse = {
  kpis: Kpis;
  resumen_anual: { ano: number; ingresos: number; ebitda: number; ebitda_margin: number; capex: number }[];
  por_marca?: Record<string, PorMarca>;
  nwc_anuales?: number[];
  delta_nwc_anuales?: number[];
};

export type TornadoEntry = {
  variable: string;
  delta_pct: number;
  tir_baja: number | null;
  tir_alta: number | null;
  van_baja: number;
  van_alta: number;
};

export type MonteCarloResponse = {
  n_runs: number;
  tir_p5: number | null;
  tir_p50: number | null;
  tir_p95: number | null;
  van_p5: number;
  van_p50: number;
  van_p95: number;
  prob_tir_supera_wacc: number;
  prob_van_positivo: number;
  histograma_tir?: { bin_start: number; bin_end: number; count: number; fraction: number }[];
  promedio_anos_critico_por_corrida?: number;
  incluye_clima?: boolean;
};

export type ValuationResponse = {
  ebitda_ano5_clp: number;
  multiple_base: number;
  multiple_low: number;
  multiple_high: number;
  ev_clp_base: number;
  ev_clp_low: number;
  ev_clp_high: number;
  moic_estimado: number | null;
  capex_total_5y_clp: number;
};

export type FinancingResponse = {
  estructura: {
    deuda_pct: number;
    tasa_deuda_anual: number;
    plazo_deuda_anos: number;
    tipo_amortizacion: string;
  };
  capex_total_clp: number;
  monto_deuda_clp: number;
  monto_equity_clp: number;
  intereses_anual: number[];
  principal_anual: number[];
  saldo_deuda_anual: number[];
  tax_shield: { anual: number[]; total_5y: number; utilidad_neta_anual: number[] };
  coverage: { dscr_anual: (number | null)[]; llcr: number; saludable: boolean; nota: string };
  tir_equity_apalancado: number | null;
};

export type RepCalendar = {
  total_hitos: number;
  por_estado: Record<string, RepHito[]>;
  proximos: RepHito[];
  costo_compliance_5y_clp: { total_clp: number; detalle: { nombre: string; costo_clp: number }[] };
};

export type RepHito = {
  nombre: string;
  fecha_vigor: string;
  fuente: string;
  severidad: 'CRITICA' | 'ALTA' | 'MEDIA' | 'INFORMATIVA';
  impacto_trongkai: string;
  accion_requerida: string;
  costo_estimado_clp: number | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => r.statusText);
    throw new Error(`HTTP ${r.status} ${path}: ${txt}`);
  }
  return r.json() as Promise<T>;
}

export const trongkai = {
  health: () => request<{ status: string; version: string }>('/health'),

  plan: (base: PlanRequest = {}) =>
    request<PlanResponse>('/plan', { method: 'POST', body: JSON.stringify(base) }),

  tornado: (base: PlanRequest = {}) =>
    request<{ tornado: TornadoEntry[] }>('/plan/tornado', {
      method: 'POST',
      body: JSON.stringify(base),
    }).then((r) => (Array.isArray(r) ? r : r.tornado)),

  escenariosEstrategicos: () =>
    request<{
      escenarios: {
        nombre: string;
        descripcion: string;
        volumen_objetivo_ton_ano: number;
        kpis: Kpis & { tir: number };
        capex_total: number;
        ingresos_anuales: number[];
        ebitda_anuales: number[];
        capex_anuales: number[];
      }[];
      recomendacion: { elegido: string; razon: string; vans_b_clp: Record<string, number>; tirs_pct: Record<string, number> };
    }>('/plan/escenarios-estrategicos'),

  valuation: (base: PlanRequest = {}) =>
    request<ValuationResponse>('/plan/valuation', { method: 'POST', body: JSON.stringify(base) }),

  monteCarlo: (params: { n_runs?: number; seed?: number; base?: PlanRequest } = {}) =>
    request<MonteCarloResponse>('/plan/monte-carlo', {
      method: 'POST',
      body: JSON.stringify({ n_runs: 2000, seed: 42, base: {}, ...params }),
    }),

  monteCarloIntegrado: (params: { n_runs?: number; seed?: number; incluir_clima?: boolean; base?: PlanRequest } = {}) =>
    request<MonteCarloResponse>('/plan/monte-carlo-integrado', {
      method: 'POST',
      body: JSON.stringify({ n_runs: 2000, seed: 42, incluir_clima: true, base: {}, ...params }),
    }),

  depreciation: (params: { metodo?: string; regimen?: string; base?: PlanRequest } = {}) =>
    request<any>('/plan/depreciation', {
      method: 'POST',
      body: JSON.stringify({ metodo: 'NORMAL', regimen: 'GENERAL', base: {}, ...params }),
    }),

  learningCurve: (params: { learning_rate?: number; base?: PlanRequest } = {}) =>
    request<{
      learning_rate: number;
      costo_sin_curva_clp: number;
      costo_con_curva_clp: number;
      ahorro_total_clp: number;
      ahorro_pct: number;
      costo_unitario_ano1_clp_kg: number;
      costo_unitario_ano5_clp_kg: number;
    }>('/plan/learning-curve', {
      method: 'POST',
      body: JSON.stringify({ learning_rate: 0.9, base: {}, ...params }),
    }),

  financing: (
    params: {
      deuda_pct?: number;
      tasa_deuda_anual?: number;
      plazo_deuda_anos?: number;
      grace_anos?: number;
      tasa_equity_required?: number;
      base?: PlanRequest;
    } = {},
  ) =>
    request<FinancingResponse>('/plan/financing', {
      method: 'POST',
      body: JSON.stringify({
        deuda_pct: 0.5,
        tasa_deuda_anual: 0.095,
        plazo_deuda_anos: 10,
        grace_anos: 2,
        tasa_equity_required: 0.2,
        base: {},
        ...params,
      }),
    }),

  slbSimulation: (params: { monto_clp?: number; tasa_base_anual?: number; plazo_anos?: number } = {}) =>
    request<any>('/plan/slb-simulation', {
      method: 'POST',
      body: JSON.stringify({ monto_clp: 5e9, tasa_base_anual: 0.085, plazo_anos: 7, ...params }),
    }),

  climateRisk: (params: { n_runs?: number; seed?: number; base?: PlanRequest } = {}) =>
    request<any>('/plan/climate-risk', {
      method: 'POST',
      body: JSON.stringify({ n_runs: 1000, seed: 42, base: {}, ...params }),
    }),

  repCalendar: () => request<RepCalendar>('/compliance/rep-calendar'),

  massBalance: (params: {
    mmpp_codigo: string;
    humedad_inicial_pct: number;
    materia_solida_pct: number;
    input_ton: number;
    mode?: 'A' | 'B';
    aceite_extraible_pct?: number;
    licopeno_pct?: number;
    pectina_pct?: number;
  }) =>
    request<any>('/mass-balance', { method: 'POST', body: JSON.stringify(params) }),
};
