'use client';

import dynamic from 'next/dynamic';
import type { EChartsOption } from 'echarts';

const ReactECharts = dynamic(() => import('echarts-for-react'), { ssr: false });

export type SankeyData = {
  nodes: { name: string }[];
  links: { source: string; target: string; value: number }[];
};

export function SankeyChart({ data, height = 420, title }: { data: SankeyData; height?: number; title?: string }) {
  const option: EChartsOption = {
    title: title ? { text: title, left: 'center', textStyle: { fontSize: 14, color: '#3F4A2B' } } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/><strong>${params.data.value.toFixed(3)} ton</strong>`;
        }
        return params.data.name;
      },
    },
    series: [
      {
        type: 'sankey',
        data: data.nodes,
        links: data.links,
        emphasis: { focus: 'adjacency' },
        nodeAlign: 'left',
        lineStyle: { color: 'gradient', curveness: 0.5 },
        label: {
          color: '#3F4A2B',
          fontSize: 11,
        },
        levels: [
          { depth: 0, itemStyle: { color: '#3F4A2B' } },
          { depth: 1, itemStyle: { color: '#7C8857' } },
          { depth: 2, itemStyle: { color: '#C8A961' } },
          { depth: 3, itemStyle: { color: '#8B5A3C' } },
        ],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height, width: '100%' }} />;
}
