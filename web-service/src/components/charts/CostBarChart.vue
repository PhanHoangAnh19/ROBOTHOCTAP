<script setup lang="ts">
// Biểu đồ cột chồng: token đầu vào / ảnh / đầu ra theo ngày; tooltip kèm chi phí (VND).
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { gridColor } from './setup'

const props = defineProps<{
  labels: string[]
  input: number[]
  image: number[]
  output: number[]
  costVnd: number[]
}>()

const data = computed(() => ({
  labels: props.labels,
  datasets: [
    { label: 'Prompt + câu hỏi', data: props.input, backgroundColor: '#7c5cff', borderRadius: 4, maxBarThickness: 36, stack: 't' },
    { label: 'Ảnh trang vở', data: props.image, backgroundColor: '#38bdf8', borderRadius: 4, maxBarThickness: 36, stack: 't' },
    { label: 'Câu trả lời', data: props.output, backgroundColor: '#34d399', borderRadius: 4, maxBarThickness: 36, stack: 't' },
  ],
}))

const vnd = (n: number) => `${Math.round(n).toLocaleString('vi-VN')} ₫`

const options = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { position: 'bottom' as const, labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } },
    tooltip: {
      callbacks: {
        label: (c: { dataset: { label?: string }; parsed: { y: number } }) =>
          ` ${c.dataset.label}: ${c.parsed.y.toLocaleString('vi-VN')} token`,
        footer: (items: Array<{ dataIndex: number }>) => `Chi phí: ${vnd(props.costVnd[items[0]?.dataIndex ?? 0] ?? 0)}`,
      },
    },
  },
  scales: {
    x: { stacked: true, grid: { display: false } },
    y: { stacked: true, beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0 } },
  },
}))
</script>

<template>
  <div class="h-64"><Bar :data="data" :options="options" /></div>
</template>
