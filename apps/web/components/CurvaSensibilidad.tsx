'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type PuntoCurva = {
  shock: number;
  tir: number | null;
  van_clp: number;
};

export type CurvaData = {
  driver: string;
  tir_base: number | null;
  puntos: PuntoCurva[];
};

const DRIVER_LABEL: Record<string, string> = {
  precio: 'Precio SKUs',
  costo_mmpp: 'Costo MMPP',
  wacc: 'WACC',
  opex: 'OpEx',
};

const fmtShock = (driver: string, v: number) =>
  driver === 'wacc' ? `${(v * 10000).toFixed(0)}bps` : `${(v * 100).toFixed(0)}%`;

export function CurvaSensibilidadChart({
  data,
  hurdlePct = 0.15,
  height = 220,
}: {
  data: CurvaData;
  hurdlePct?: number;
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    const xLabels = data.puntos.map((p) => fmtShock(data.driver, p.shock));
    const series = data.puntos.map((p) => (p.tir !== null ? +(p.tir * 100).toFixed(2) : null));

    chartRef.current.setOption(
      {
        title: {
          text: DRIVER_LABEL[data.driver] ?? data.driver,
          left: 'center',
          top: 4,
          textStyle: { fontSize: 12, color: '#3F4A2B', fontWeight: 'normal' },
        },
        tooltip: {
          trigger: 'axis',
          formatter: (p: any) => {
            const idx = p[0].dataIndex;
            const pt = data.puntos[idx];
            const tirStr = pt.tir !== null ? `${(pt.tir * 100).toFixed(2)}%` : '—';
            return `Shock: ${fmtShock(data.driver, pt.shock)}<br/>TIR: <strong>${tirStr}</strong>`;
          },
        },
        grid: { left: 38, right: 12, top: 32, bottom: 24 },
        xAxis: {
          type: 'category',
          data: xLabels,
          axisLabel: { color: '#7C8857', fontSize: 9 },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#7C8857', fontSize: 9, formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E0DBC9' } },
        },
        series: [
          {
            type: 'line',
            data: series,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2, color: '#3F4A2B' },
            itemStyle: { color: '#3F4A2B' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(63,74,43,0.3)' },
                { offset: 1, color: 'rgba(63,74,43,0.05)' },
              ]),
            },
            markLine: {
              silent: true,
              symbol: 'none',
              data: [
                {
                  yAxis: hurdlePct * 100,
                  lineStyle: { color: '#7A1F1F', type: 'dashed', width: 1 },
                  label: {
                    formatter: `hurdle ${(hurdlePct * 100).toFixed(0)}%`,
                    color: '#7A1F1F',
                    fontSize: 9,
                    position: 'insideEndTop',
                  },
                },
              ],
            },
          },
        ],
      },
      true
    );

    const onResize = () => chartRef.current?.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
    };
  }, [data, hurdlePct]);

  useEffect(() => {
    return () => {
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  return <div ref={ref} style={{ height, width: '100%' }} />;
}
