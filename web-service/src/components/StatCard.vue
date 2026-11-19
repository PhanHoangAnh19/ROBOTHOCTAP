<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  iconClass: string
  label: string
  value: string
  sub?: string
  subClass?: string
}>()
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5">
    <div class="flex items-center gap-3">
      <div :class="iconClass" class="grid size-9 place-items-center rounded-xl">
        <component :is="icon" class="size-4.5" />
      </div>
      <span class="text-sm text-slate-500">{{ label }}</span>
    </div>
    <p class="mt-3 text-3xl font-bold tracking-tight">{{ value }}</p>
    <p v-if="sub" :class="subClass ?? 'text-slate-500'" class="mt-1 text-xs">{{ sub }}</p>
    <slot />
  </div>
</template>
