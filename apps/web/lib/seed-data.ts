/**
 * Datos derivados del seed (scripts/seed_dryrun.json). Para Fase 2-3 leemos
 * del JSON statico; en Fase 4+ migramos a tRPC contra DB real.
 */

import seedRaw from './seed-data.json';

export type MMPP = {
  codigo: string;
  nombre: string;
  temporadaInicioMes: number;
  temporadaFinMes: number;
  humedadInicialPct: number | null;
  materiaSolidaPct: number | null;
  aceiteExtraiblePct?: number;
  tiempoDescomposicionH?: number | null;
};

export type Supplier = {
  nombre: string;
  mmppCodigo: string;
  distanciaKm: number;
  tarifaFleteClpKm: number;
  casoLogistico: string;
  pagoRecepcionClpKg: number;
  volumenAnualComprometidoTon: number;
  capacidadCamionTon: number;
  status: 'ACTIVO' | 'PROSPECT' | 'INACTIVO';
};

export type Producto = {
  codigo: string;
  nombre: string;
  mmppOrigen: string | null;
  tipo: 'BASE' | 'AGREGADO' | 'PTEC';
  marca: 'FEED' | 'FOOD' | 'SERVICIOS';
  anoLanzamiento: number;
};

export type Supuesto = {
  clave: string;
  valorActual: string | null;
  unidad: string | null;
  fuente: string;
  estado: string;
  sensibilidad: string;
  owner: string | null;
};

export type Capacidad = {
  etapa: string;
  capacidadTonHora: number | null;
  tiempoResidenciaH: number | null;
  opcional: boolean;
};

type Seed = {
  materias_primas: MMPP[];
  suppliers: Supplier[];
  productos: Producto[];
  supuestos: Supuesto[];
  capacidades: Capacidad[];
};

export const seed: Seed = seedRaw as unknown as Seed;

export const productosPorMarca = (marca: 'FEED' | 'FOOD' | 'SERVICIOS') =>
  seed.productos.filter((p) => p.marca === marca);

export const suppliersActivos = () => seed.suppliers.filter((s) => s.status === 'ACTIVO');

export const supuestosCriticosPD = () =>
  seed.supuestos.filter((s) => s.estado === 'PD').slice(0, 25);

export const stats = {
  mmpp: seed.materias_primas.length,
  suppliersActivos: seed.suppliers.filter((s) => s.status === 'ACTIVO').length,
  suppliersTotal: seed.suppliers.length,
  productos: seed.productos.length,
  productosFeed: seed.productos.filter((p) => p.marca === 'FEED').length,
  productosFood: seed.productos.filter((p) => p.marca === 'FOOD').length,
  supuestosPD: seed.supuestos.filter((s) => s.estado === 'PD').length,
  supuestosOK: seed.supuestos.filter((s) => s.estado.startsWith('OK')).length,
  capacidadesPD: seed.capacidades.filter((c) => c.capacidadTonHora == null).length,
  capacidadesOK: seed.capacidades.filter((c) => c.capacidadTonHora != null).length,
  volumenContratoTon: 50_000,
  volumenComprometidoActual: seed.suppliers
    .filter((s) => s.status === 'ACTIVO')
    .reduce((acc, s) => acc + s.volumenAnualComprometidoTon, 0),
};
