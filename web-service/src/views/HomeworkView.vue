<script setup lang="ts">
import { computed } from 'vue'
import { STUDENTS } from '@/data/mock'
import StudentAvatar from '@/components/StudentAvatar.vue'

const assigned = computed(() => STUDENTS.filter((s) => s.homeworkTotal > 0))
</script>

<template>
  <div class="mx-auto max-w-4xl p-4 sm:p-6 lg:p-8">
    <h1 class="text-2xl font-bold tracking-tight">Bài tập</h1>
    <p class="mt-1 text-sm text-slate-500">Tình trạng làm bài tập của các em (dữ liệu mẫu — chờ API bài tập).</p>

    <ul class="mt-5 divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white">
      <li v-for="s in assigned" :key="s.id" class="flex items-center gap-3 px-5 py-3">
        <StudentAvatar :name="s.name" />
        <span class="flex-1 font-medium">{{ s.name }}</span>
        <span
          :class="s.homeworkDone < s.homeworkTotal ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-700'"
          class="rounded-md px-2 py-0.5 text-xs font-semibold"
        >
          {{ s.homeworkDone < s.homeworkTotal ? `Còn ${s.homeworkTotal - s.homeworkDone} bài` : 'Đã xong' }}
        </span>
      </li>
      <li v-if="!assigned.length" class="px-5 py-10 text-center text-sm text-slate-400">Chưa giao bài tập nào.</li>
    </ul>
  </div>
</template>
