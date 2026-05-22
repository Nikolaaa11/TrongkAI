'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type HistogramaBin = {
  bin_start: number;
  bin_end: number;
  count: number;
  fraction: number;
};

export function HistogramaChart({
  bins,
  p5,
  p50,
  p95,
  baseValue,
  title,
  height = 280,
  xAxisFormatter,
}: {
  bins: HistogramaBin[];
  p5?: number | null;
  p50?: number | null;
  p95?: number | null;
  baseValue?: number;
  title?: string;
  height?: number;
  xAxisFormatter?: (v: number) => string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    const fmt = xAxisFormatter ?? ((v: number) => `${(v * 100).toFixed(0)}%`);

    const categoryAxis = bins.map((b) => fmt((b.bin_start + b.bin_end) / 2));
    const counts = bins.map((b) => b.count);

    // Mark lines en P5/P50/P95
    const markLines: any[] = [];
    if (p5 != null) markLines.push({ name: 'P5', xAxis: fmt(p5), label: { formatter: 'P5', color: '#8B5A3C' }, lineStyle: { color: '#8B5A3C', type: 'dashed' } });
    if (p50 != null) markLines.push({ name: 'P50', xAxis: fmt(p50), label: { formatter: 'P50', color: '#3F4A2B' }, lineStyle: { color: '#3F4A2B', type: 'solid', width: 2 } });
    if (p95 != null) markLines.push({ name: 'P95', xAxis: fmt(p95), label: { formatter: 'P95', color: '#7C8857' }, lineStyle: { color: '#7C8857', type: 'dashed' } });
    if (baseValue != null) markLines.push({ name: 'Base', xAxis: fmt(baseValue), label: { formatter: 'Base', color: '#C8A961' }, lineStyle: { color: '#C8A961', type: 'dotted' } });

    chartRef.current.setOption({
      title: title ? { text: title, textStyle: { fontSize: 13, color: '#3F4A2B' } } : undefined,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const idx = params[0].dataIndex;
          const b = bins[idx];
          return `<strong>${fmt(b.bin_start)} – ${fmt(b.bin_end)}</strong><br/>
                  Conteo: ${b.count}<br/>
                  Fracción: ${(b.fraction * 100).toFixed(1)}%`;
        },
      },
      grid: { left: 40, right: 20, top: 35, bottom: 35 },
      xAxis: {
        type: 'category',
        data: categoryAxis,
        axisLabel: { fontSize: 9, color: '#3F4A2B', interval: Math.max(1, Math.floor(bins.length / 10)) },
      },
      yAxis: { type: 'value', name: 'Frecuencia', nameTextStyle: { fontSize: 10 } },
      series: [
        {
          name: 'Corridas',
          type: 'bar',
          data: counts,
          itemStyle: { color: '#7C8857' },
          markLine: markLines.length > 0 ? { silent: false, symbol: 'none', data: markLines } : undefined,
        },
      ],
    });

    const onResize = () => chartRef.current?.resize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [bins, p5, p50, p95, baseValue, title, xAxisFormatter]);

  useEffect(() => () => {
    chartRef.current?.dispose();
    chartRef.current = null;
  }, []);

  return <div ref={ref} style={{ height, width: '100%' }} />;
}
