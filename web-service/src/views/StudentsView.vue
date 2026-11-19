<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search } from 'lucide-vue-next'
import { STUDENTS } from '@/data/mock'
import StudentTable from '@/components/StudentTable.vue'

const search = ref('')
const students = computed(() => STUDENTS.filter((s) => s.name.toLowerCase().includes(search.value.trim().toLowerCase())))
</script>

<template>
  <div class="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Học sinh</h1>
        <p class="mt-1 text-sm text-slate-500">Bấm “Xem” để mở thống kê và các phiên học của từng em.</p>
      </div>
      <label class="relative">
        <Search class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
        <input v-model="search" placeholder="Tìm học sinh..." class="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-500 sm:w-56" />
      </label>
    </div>
    <StudentTable class="mt-5" :students="students" />
  </div>
</template>
