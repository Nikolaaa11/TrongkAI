'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type TornadoEntry = {
  variable: string;
  delta_pct: number;
  tir_baja: number | null;
  tir_alta: number | null;
  van_baja: number;
  van_alta: number;
};

const PRETTY: Record<string, string> = {
  precio_promedio: 'Precio promedio',
  rendimiento_promedio: 'Rendimiento MMPP',
  costo_mmpp: 'Costo MMPP',
  opex_mensual: 'OpEx mensual',
  wacc_anual: 'WACC',
};

export function TornadoChart({
  entries,
  baseTir,
  height = 320,
}: {
  entries: TornadoEntry[];
  baseTir: number;
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    // Para tornado horizontal: cada variable es una categoría, mostramos delta TIR
    // como dos barras simétricas (baja → 0 y 0 → alta).
    const ordered = [...entries].sort((a, b) => {
      const ma = Math.abs((a.tir_alta ?? 0) - (a.tir_baja ?? 0));
      const mb = Math.abs((b.tir_alta ?? 0) - (b.tir_baja ?? 0));
      return ma - mb; // de menor a mayor para que el de mayor swing quede arriba
    });

    const categorias = ordered.map((e) => PRETTY[e.variable] ?? e.variable);
    const deltasBajos = ordered.map((e) => ((e.tir_baja ?? baseTir) - baseTir) * 100);
    const deltasAltos = ordered.map((e) => ((e.tir_alta ?? baseTir) - baseTir) * 100);

    chartRef.current.setOption({
      title: { text: 'Tornado: sensibilidad TIR a ±20%', textStyle: { fontSize: 13, color: '#3F4A2B' } },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const idx = params[0].dataIndex;
          const e = ordered[idx];
          return `<strong>${PRETTY[e.variable] ?? e.variable}</strong><br/>
                  Shock -20%: TIR ${((e.tir_baja ?? 0) * 100).toFixed(2)}% (Δ ${((e.tir_baja ?? baseTir) - baseTir) * 100 >= 0 ? '+' : ''}${(((e.tir_baja ?? baseTir) - baseTir) * 100).toFixed(2)} pp)<br/>
                  Shock +20%: TIR ${((e.tir_alta ?? 0) * 100).toFixed(2)}% (Δ ${((e.tir_alta ?? baseTir) - baseTir) * 100 >= 0 ? '+' : ''}${(((e.tir_alta ?? baseTir) - baseTir) * 100).toFixed(2)} pp)`;
        },
      },
      grid: { left: 110, right: 50, top: 40, bottom: 30 },
      xAxis: {
        type: 'value',
        name: 'Δ TIR vs base (pp)',
        nameLocation: 'middle',
        nameGap: 22,
        axisLabel: { formatter: '{value}' },
      },
      yAxis: { type: 'category', data: categorias, axisLabel: { color: '#3F4A2B', fontSize: 11 } },
      series: [
        {
          name: 'Shock -20%',
          type: 'bar',
          stack: 'tornado',
          data: deltasBajos,
          itemStyle: { color: '#8B5A3C' }, // borgoña (downside)
          barWidth: 18,
        },
        {
          name: 'Shock +20%',
          type: 'bar',
          stack: 'tornado',
          data: deltasAltos,
          itemStyle: { color: '#7C8857' }, // oliva (upside)
          barWidth: 18,
        },
      ],
    });

    const onResize = () => chartRef.current?.resize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [entries, baseTir]);

  useEffect(() => () => {
    chartRef.current?.dispose();
    chartRef.current = null;
  }, []);

  return <div ref={ref} style={{ height, width: '100%' }} />;
}
