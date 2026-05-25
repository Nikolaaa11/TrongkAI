'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type HistoryPoint = { timestamp: string; score: number };

export function ReadinessHistoryChart({
  data,
  height = 280,
}: {
  data: HistoryPoint[];
  height?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    if (data.length === 0) {
      // Mostrar vacío con mensaje
      chartRef.current.setOption(
        {
          title: {
            text: 'Aún no hay snapshots históricos',
            subtext: 'Click en "Marcar hito" para crear el primer snapshot',
            left: 'center',
            top: 'middle',
            textStyle: { fontSize: 14, color: '#86868B' },
            subtextStyle: { fontSize: 12, color: '#86868B' },
          },
          xAxis: { show: false, type: 'category', data: [] },
          yAxis: { show: false, type: 'value' },
          series: [],
        },
        true,
      );
      return;
    }

    chartRef.current.setOption(
      {
        tooltip: {
          trigger: 'axis',
          formatter: (params: any) => {
            const p = params[0];
            return `${p.axisValue}<br/>Score: <strong>${p.value.toFixed(1)}/100</strong>`;
          },
        },
        grid: { left: 40, right: 16, top: 24, bottom: 30 },
        xAxis: {
          type: 'category',
          data: data.map((p) => p.timestamp),
          axisLabel: { color: '#86868B', fontSize: 10 },
          axisLine: { lineStyle: { color: '#E8E8ED' } },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#86868B', fontSize: 10, formatter: '{value}' },
          splitLine: { lineStyle: { color: '#E8E8ED' } },
        },
        series: [
          {
            type: 'line',
            data: data.map((p) => p.score),
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { width: 2.5, color: '#1A8A1A' },
            itemStyle: { color: '#1A8A1A' },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(26,138,26,0.25)' },
                { offset: 1, color: 'rgba(26,138,26,0.02)' },
              ]),
            },
            markLine: {
              silent: true,
              symbol: 'none',
              data: [
                {
                  yAxis: 80,
                  lineStyle: { color: '#1A8A1A', type: 'dashed', width: 1 },
                  label: { formatter: 'BANKABLE 80', color: '#1A8A1A', fontSize: 10, position: 'insideEndTop' },
                },
                {
                  yAxis: 60,
                  lineStyle: { color: '#FF9500', type: 'dashed', width: 1 },
                  label: { formatter: 'PROMETEDOR 60', color: '#FF9500', fontSize: 10, position: 'insideEndTop' },
                },
              ],
            },
          },
        ],
      },
      true,
    );

    const onResize = () => chartRef.current?.resize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [data]);

  useEffect(() => {
    return () => {
      chartRef.current?.dispose();
      chartRef.current = null;
    };
  }, []);

  return <div ref={ref} style={{ height, width: '100%' }} />;
}
