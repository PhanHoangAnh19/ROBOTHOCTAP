<script setup lang="ts">
import { computed, ref } from 'vue'
import { AlertTriangle, ChevronRight, Users } from 'lucide-vue-next'
import { currentFocus, needsAttention, type Student } from '@/data/mock'
import StudentAvatar from './StudentAvatar.vue'
import FocusBar from './FocusBar.vue'
import MoodBadge from './MoodBadge.vue'

const props = defineProps<{ students: Student[] }>()

const sortBy = ref<'attention' | 'name'>('attention')

const sorted = computed(() =>
  [...props.students].sort((a, b) =>
    sortBy.value === 'name'
      ? a.name.localeCompare(b.name, 'vi')
      : Number(needsAttention(b)) - Number(needsAttention(a)) || currentFocus(a) - currentFocus(b),
  ),
)
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white">
    <div class="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
      <h2 class="flex items-center gap-2 font-semibold"><Users class="size-4.5 text-slate-500" /> Học sinh</h2>
      <div class="flex rounded-lg border border-slate-200 p-0.5 text-sm">
        <button
          :class="sortBy === 'attention' ? 'bg-slate-900 text-white' : 'text-slate-600'"
          class="inline-flex items-center gap-1.5 rounded-md px-3 py-1"
          @click="sortBy = 'attention'"
        >
          <AlertTriangle class="size-3.5" /> Cần chú ý trước
        </button>
        <button :class="sortBy === 'name' ? 'bg-slate-900 text-white' : 'text-slate-600'" class="rounded-md px-3 py-1" @click="sortBy = 'name'">
          Tên A–Z
        </button>
      </div>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full min-w-[640px] text-left">
        <thead>
          <tr class="border-y border-slate-100 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            <th class="px-5 py-2.5">Học sinh</th>
            <th class="px-3 py-2.5">Tập trung</th>
            <th class="px-3 py-2.5">Bài tập</th>
            <th class="px-3 py-2.5">Tâm trạng</th>
            <th class="px-5 py-2.5" />
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in sorted" :key="s.id" class="border-b border-slate-100 last:border-0 hover:bg-slate-50/60">
            <td class="px-5 py-3">
              <div class="flex items-center gap-3">
                <StudentAvatar :name="s.name" />
                <div>
                  <p class="font-medium">{{ s.name }}</p>
                  <p class="text-xs text-slate-400">{{ s.note ? `“${s.note}”` : s.className }}</p>
                </div>
              </div>
            </td>
            <td class="px-3 py-3"><FocusBar :value="currentFocus(s)" /></td>
            <td class="px-3 py-3 text-sm">
              <span
                v-if="s.homeworkTotal"
                :class="s.homeworkDone < s.homeworkTotal ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-700'"
                class="rounded-md px-2 py-0.5 text-xs font-semibold"
              >
                {{ s.homeworkDone }}/{{ s.homeworkTotal }}
              </span>
              <span v-else class="text-slate-300">—</span>
            </td>
            <td class="px-3 py-3"><MoodBadge :mood="s.mood" /></td>
            <td class="px-5 py-3 text-right">
              <RouterLink :to="`/hoc-sinh/${s.id}`" class="inline-flex items-center gap-0.5 text-sm font-medium text-slate-600 hover:text-brand-600">
                Xem <ChevronRight class="size-4" />
              </RouterLink>
            </td>
          </tr>
          <tr v-if="!sorted.length">
            <td colspan="5" class="px-5 py-10 text-center text-sm text-slate-400">Không tìm thấy học sinh phù hợp.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
