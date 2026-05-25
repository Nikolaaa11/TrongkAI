'use client';

import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export type GraphNodo = {
  id: string;
  label: string;
  tipo: string;
  descripcion: string;
  plataforma_url: string;
};

export type GraphEdge = {
  desde: string;
  hacia: string;
  tipo: string;
  peso: number;
  descripcion: string;
};

export type GraphData = {
  nodos: GraphNodo[];
  edges: GraphEdge[];
};

// Colores por tipo de nodo
const TIPO_COLOR: Record<string, string> = {
  input: '#86868B',       // ink-400 gris
  matriz: '#1A8A1A',      // brand verde
  calculo: '#FF9500',     // orange
  decision: '#FF3B30',    // Apple red
  output: '#3FB23F',      // brand-400 verde claro
};

const TIPO_TAMANO: Record<string, number> = {
  input: 30,
  matriz: 50,
  calculo: 40,
  decision: 60,    // El cerebro destacado
  output: 35,
};

export function NetworkGraph({ data, height = 540 }: { data: GraphData; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current);

    const echartsNodes = data.nodos.map((n) => ({
      id: n.id,
      name: n.label,
      symbolSize: TIPO_TAMANO[n.tipo] ?? 30,
      itemStyle: { color: TIPO_COLOR[n.tipo] ?? '#86868B' },
      label: {
        show: true,
        fontSize: 11,
        color: '#1D1D1F',
        position: 'right',
        formatter: n.label,
      },
      tooltipExtra: `<strong>${n.label}</strong> <em>(${n.tipo})</em><br/>${n.descripcion}${
        n.plataforma_url ? `<br/><small>→ ${n.plataforma_url}</small>` : ''
      }`,
      category: n.tipo,
    }));

    const echartsEdges = data.edges.map((e) => ({
      source: e.desde,
      target: e.hacia,
      lineStyle: {
        width: Math.max(1, e.peso * 3),
        opacity: 0.5,
        curveness: 0.15,
        color: '#D2D2D7',
      },
      label: { show: false },
      value: e.peso,
      tooltipExtra: `${e.desde} → ${e.hacia}<br/><em>${e.tipo}</em>: ${e.descripcion}`,
    }));

    const categories = Object.keys(TIPO_COLOR).map((t) => ({
      name: t,
      itemStyle: { color: TIPO_COLOR[t] },
    }));

    chartRef.current.setOption(
      {
        backgroundColor: '#FFFFFF',
        tooltip: {
          formatter: (params: any) => {
            return params.data.tooltipExtra ?? params.name;
          },
          backgroundColor: 'rgba(255,255,255,0.95)',
          borderColor: '#E8E8ED',
          borderWidth: 1,
          textStyle: { color: '#1D1D1F', fontSize: 12 },
        },
        legend: {
          data: categories.map((c) => c.name),
          bottom: 0,
          textStyle: { color: '#86868B', fontSize: 11 },
          itemWidth: 12,
          itemHeight: 12,
        },
        series: [
          {
            type: 'graph',
            layout: 'force',
            data: echartsNodes,
            links: echartsEdges,
            categories,
            roam: true,
            draggable: true,
            focusNodeAdjacency: true,
            force: {
              repulsion: 200,
              edgeLength: [80, 180],
              gravity: 0.1,
              friction: 0.6,
            },
            emphasis: {
              focus: 'adjacency',
              lineStyle: { width: 3, opacity: 1, color: '#1A8A1A' },
            },
            labelLayout: { hideOverlap: true },
          },
        ],
      },
      true,
    );

    chartRef.current.on('click', (params: any) => {
      if (params.dataType === 'node') {
        const url = data.nodos.find((n) => n.id === params.data.id)?.plataforma_url;
        if (url) window.location.href = url;
      }
    });

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
