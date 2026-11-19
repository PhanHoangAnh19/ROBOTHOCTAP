<script setup lang="ts">
// Biểu đồ cột: thời lượng học (phút) theo ngày/tuần.
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import { gridColor } from './setup'

const props = defineProps<{ labels: string[]; minutes: number[] }>()

const data = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      label: 'Thời lượng học (phút)',
      data: props.minutes,
      backgroundColor: '#7c5cff',
      hoverBackgroundColor: '#5a35dd',
      borderRadius: 6,
      maxBarThickness: 36,
    },
  ],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: { callbacks: { label: (c: { parsed: { y: number } }) => ` ${c.parsed.y} phút` } },
  },
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0 } },
  },
}
</script>

<template>
  <div class="h-56"><Bar :data="data" :options="options" /></div>
</template>
