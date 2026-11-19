<script setup lang="ts">
// Timeline sự kiện trong 1 phiên học (cũ → mới).
import { AlertTriangle, Bot, EyeOff, Ruler, UserRound } from 'lucide-vue-next'
import { parseTimestamp, type RobotEvent } from '@/api/events'
import { hhmm, isAi, splitQA } from '@/utils/stats'

defineProps<{ events: RobotEvent[] }>()

function style(e: RobotEvent) {
  switch (e.event_type) {
    case 'TU_THE_CO':
      return { icon: UserRound, dot: 'bg-rose-100 text-rose-600' }
    case 'TU_THE_VAI':
      return { icon: AlertTriangle, dot: 'bg-orange-100 text-orange-600' }
    case 'KHOANG_CACH_MAT':
      return { icon: Ruler, dot: 'bg-violet-100 text-violet-600' }
    case 'MAT_TAP_TRUNG':
      return { icon: EyeOff, dot: 'bg-amber-100 text-amber-600' }
    default:
      return { icon: Bot, dot: 'bg-emerald-100 text-emerald-600' }
  }
}
</script>

<template>
  <ol class="relative space-y-4 border-l border-slate-200 pl-6">
    <li v-for="e in events" :key="e.id" class="relative">
      <span :class="style(e).dot" class="absolute -left-[37px] grid size-7 place-items-center rounded-full ring-4 ring-white">
        <component :is="style(e).icon" class="size-3.5" />
      </span>
      <div class="flex flex-wrap items-baseline gap-x-2">
        <span class="text-xs tabular-nums text-slate-400">{{ hhmm(parseTimestamp(e.timestamp)) }}</span>
        <span class="text-sm font-medium">{{ e.category_name }}</span>
      </div>
      <!-- Câu hỏi AI: tách Hỏi / Đáp cho dễ đọc. Dùng {{ }} để Vue tự escape nội dung -->
      <div v-if="isAi(e)" class="mt-1.5 space-y-1.5 rounded-xl bg-slate-50 p-3 text-sm">
        <p><span class="font-medium text-slate-500">Bé hỏi:</span> {{ splitQA(e.detail).q }}</p>
        <p v-if="splitQA(e.detail).a"><span class="font-medium text-brand-600">Robot:</span> {{ splitQA(e.detail).a }}</p>
      </div>
      <p v-else class="mt-0.5 text-sm text-slate-600">{{ e.detail }}</p>
    </li>
  </ol>
</template>
