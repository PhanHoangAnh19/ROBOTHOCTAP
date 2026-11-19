<script setup lang="ts">
// Biểu đồ đường: tần suất robot nhắc nhở (tư thế / mất tập trung) theo ngày/tuần.
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import { gridColor } from './setup'

// Không truyền `attention` → chỉ vẽ 1 đường "Nhắc nhở" (dùng cho thống kê theo tuần)
const props = defineProps<{ labels: string[]; posture: number[]; attention?: number[] }>()

const line = (label: string, data: number[], color: string, bg: string) => ({
  // monotone: đường cong không vọt quá số liệu thật (không bị âm giữa 2 điểm)
  label, data, borderColor: color, backgroundColor: bg, fill: true, cubicInterpolationMode: 'monotone' as const, pointRadius: 3,
})

const data = computed(() => ({
  labels: props.labels,
  datasets: props.attention
    ? [
        line('Nhắc tư thế', props.posture, '#f43f5e', 'rgba(244,63,94,0.08)'),
        line('Nhắc tập trung', props.attention, '#f59e0b', 'rgba(245,158,11,0.08)'),
      ]
    : [line('Nhắc nhở', props.posture, '#f43f5e', 'rgba(244,63,94,0.08)')],
}))

const options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: { legend: { position: 'bottom' as const, labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true } } },
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, grid: { color: gridColor }, ticks: { precision: 0 } },
  },
}
</script>

<template>
  <div class="h-56"><Line :data="data" :options="options" /></div>
</template>
