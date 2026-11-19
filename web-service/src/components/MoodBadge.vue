<script setup lang="ts">
import { Frown, Meh, Smile } from 'lucide-vue-next'
import { MOOD_LABEL, type Mood } from '@/data/mock'

defineProps<{ mood: Mood }>()
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 text-sm font-medium"
    :class="{ 'text-amber-600': mood === 'met', 'text-slate-600': mood === 'binh_thuong', 'text-emerald-600': mood === 'vui' }"
  >
    <Frown v-if="mood === 'met'" class="size-4" />
    <Smile v-else-if="mood === 'vui'" class="size-4" />
    <Meh v-else class="size-4" />
    {{ MOOD_LABEL[mood] }}
  </span>
</template>
