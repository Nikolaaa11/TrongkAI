'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type HeatmapCelda = {
  x_pct: number;
  y_pct: number;
  tir: number | null;
  van_clp: number;
  supera_hurdle: boolean;
};

export type HeatmapData = {
  driver_x: string;
  driver_y: string;
  rango_x: number[];
  rango_y: number[];
  hurdle_pct: number;
  celdas: HeatmapCelda[];
};

const LABEL_DRIVER: Record<string, string> = {
  precio: 'Shock precios SKU (%)',
  costo_mmpp: 'Shock costo MMPP (%)',
  wacc: 'Shock WACC (pp abs)',
  opex: 'Shock OpEx (%)',
};

const fmtPctShock = (driver: string, v: number) =>
  driver === 'wacc' ? `${(v * 10000).toFixed(0)}bps` : `${(v * 100).toFixed(0)}%`;

export function HeatmapChart({
  data,
  height = 480,
  title,
}: {
  data: HeatmapData;
  height?: number;
  title?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    // Etiquetas de ejes
    const xLabels = data.rango_x.map((v) => fmtPctShock(data.driver_x, v));
    const yLabels = data.rango_y.map((v) => fmtPctShock(data.driver_y, v));

    // Datos heatmap: [xIdx, yIdx, valor]
    const xIdx = new Map(data.rango_x.map((v, i) => [v, i]));
    const yIdx = new Map(data.rango_y.map((v, i) => [v, i]));
    const series = data.celdas.map((c) => [
      xIdx.get(c.x_pct) ?? 0,
      yIdx.get(c.y_pct) ?? 0,
      c.tir !== null ? +(c.tir * 100).toFixed(2) : null,
    ]);

    const tirsValid = data.celdas
      .map((c) => c.tir)
      .filter((t): t is number => t !== null);
    const minTir = Math.min(...tirsValid) * 100;
    const maxTir = Math.max(...tirsValid) * 100;
    const hurdle = data.hurdle_pct * 100;

    chartRef.current.setOption(
      {
        title: title
          ? {
              text: title,
              left: 'center',
              textStyle: { fontSize: 14, color: '#3F4A2B', fontWeight: 'normal' },
            }
          : undefined,
        tooltip: {
          position: 'top',
          formatter: (p: any) => {
            const c = data.celdas[p.dataIndex];
            const tirStr = c.tir !== null ? `${(c.tir * 100).toFixed(2)}%` : '—';
            const vanStr = `$${(c.van_clp / 1e9).toFixed(2)}B`;
            const safe = c.supera_hurdle ? '✓ supera hurdle' : '✗ NO supera hurdle';
            return `
              <strong>${LABEL_DRIVER[data.driver_x] ?? data.driver_x}</strong>: ${fmtPctShock(data.driver_x, c.x_pct)}<br/>
              <strong>${LABEL_DRIVER[data.driver_y] ?? data.driver_y}</strong>: ${fmtPctShock(data.driver_y, c.y_pct)}<br/>
              <hr style="margin:4px 0;border:none;border-top:1px solid #ccc"/>
              TIR: <strong>${tirStr}</strong><br/>
              VAN: ${vanStr}<br/>
              <span style="color:${c.supera_hurdle ? '#3F4A2B' : '#7A1F1F'}">${safe}</span>
            `;
          },
        },
        grid: { left: 80, right: 30, top: title ? 50 : 20, bottom: 60 },
        xAxis: {
          type: 'category',
          data: xLabels,
          name: LABEL_DRIVER[data.driver_x] ?? data.driver_x,
          nameLocation: 'middle',
          nameGap: 30,
          axisLabel: { color: '#5C6440', fontSize: 11 },
          nameTextStyle: { color: '#3F4A2B', fontSize: 12, fontWeight: 'bold' },
        },
        yAxis: {
          type: 'category',
          data: yLabels,
          name: LABEL_DRIVER[data.driver_y] ?? data.driver_y,
          nameLocation: 'middle',
          nameGap: 50,
          axisLabel: { color: '#5C6440', fontSize: 11 },
          nameTextStyle: { color: '#3F4A2B', fontSize: 12, fontWeight: 'bold' },
        },
        visualMap: {
          min: minTir,
          max: maxTir,
          left: 'right',
          top: 'middle',
          orient: 'vertical',
          calculable: true,
          text: ['TIR alta', 'TIR baja'],
          textStyle: { color: '#3F4A2B', fontSize: 10 },
          // Paleta Trongkai: borgoña (rojo malo) → trigo → oliva (verde bueno)
          inRange: {
            color: ['#7A1F1F', '#B8736C', '#E0C896', '#C8A961', '#7C8857', '#3F4A2B'],
          },
          // Marcar el hurdle como split visual
          pieces: [
            { lt: hurdle, color: '#B8736C', label: `< ${hurdle}% (rechazo)` },
            { gte: hurdle, lt: 25, color: '#C8A961', label: `${hurdle}-25% (aceptable)` },
            { gte: 25, color: '#3F4A2B', label: `≥ 25% (excelente)` },
          ],
          itemSymbol: 'rect',
        },
        series: [
          {
            type: 'heatmap',
            data: series,
            label: {
              show: true,
              color: '#FEFCF6',
              fontSize: 10,
              fontWeight: 'bold',
              formatter: (p: any) => (p.value[2] !== null ? `${p.value[2]}%` : '—'),
            },
            emphasis: {
              itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.3)' },
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
  }, [data, title]);

  useEffect(() => {
    return () => {
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  return <div ref={ref} style={{ height, width: '100%' }} />;
}
