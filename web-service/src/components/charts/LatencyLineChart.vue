<script setup lang="ts">
// Độ trễ trung vị theo ngày (giây) so với mục tiêu Q8 ≤ 8 giây.
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { gridColor } from './setup'

const props = defineProps<{ labels: string[]; medianSeconds: Array<number | null>; target?: number }>()

const data = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Độ trễ trung vị (giây)',
      data: props.medianSeconds,
      borderColor: '#7c5cff',
      backgroundColor: 'rgba(124,92,255,0.12)',
      fill: true,
      tension: 0.35,
      cubicInterpolationMode: 'monotone' as const,
      pointRadius: 3,
      spanGaps: true,
    },
    {
      label: `Mục tiêu Q8 (≤ ${props.target ?? 8}s)`,
      data: props.labels.map(() => props.target ?? 8),
      borderColor: '#f43f5e',
      borderDash: [6, 4],
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
    },
  ],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { position: 'bottom' as const, labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } },
    tooltip: {
      callbacks: {
        label: (c: { dataset: { label?: string }; parsed: { y: number | null } }) =>
          c.parsed.y == null ? ` ${c.dataset.label}: —` : ` ${c.dataset.label}: ${c.parsed.y.toFixed(1)}s`,
      },
    },
  },
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, grid: { color: gridColor }, ticks: { callback: (v: string | number) => `${v}s` } },
  },
}
</script>

<template>
  <div class="h-64"><Line :data="data" :options="options" /></div>
</template>
