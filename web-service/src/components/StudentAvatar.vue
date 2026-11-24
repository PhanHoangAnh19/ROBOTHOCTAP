<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ name: string; size?: 'sm' | 'lg' }>()

const COLORS = ['bg-blue-500', 'bg-violet-500', 'bg-rose-500', 'bg-emerald-500', 'bg-amber-500', 'bg-cyan-500', 'bg-orange-500']
const color = computed(() => COLORS[[...props.name].reduce((a, c) => a + c.charCodeAt(0), 0) % COLORS.length])
</script>

<template>
  <div
    :class="[color, size === 'lg' ? 'size-14 text-xl' : 'size-9 text-sm']"
    class="grid shrink-0 place-items-center rounded-full font-semibold text-white"
  >
    {{ name.charAt(0).toUpperCase() }}
  </div>
</template>
