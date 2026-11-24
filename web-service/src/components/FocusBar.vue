<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: number }>()
// ≥ 70% xanh lá, 50–69% cam, < 50% đỏ
const color = computed(() => (props.value >= 70 ? 'bg-emerald-500' : props.value >= 50 ? 'bg-orange-400' : 'bg-rose-500'))
</script>

<template>
  <div class="flex items-center gap-3">
    <div class="h-2 w-28 overflow-hidden rounded-full bg-slate-100">
      <div :class="color" class="h-full rounded-full transition-all" :style="{ width: `${value}%` }" />
    </div>
    <span class="w-10 text-sm tabular-nums text-slate-600">{{ value }}%</span>
  </div>
</template>
