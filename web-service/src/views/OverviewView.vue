<script setup lang="ts">
import { computed, ref } from 'vue'
import { Bot, ChartColumn, CheckCircle2, Download, Heart, Plus, Search, Sparkles, Target, TrendingDown, TrendingUp } from 'lucide-vue-next'
import { GROUPS, STUDENTS, SAMPLE_QUESTIONS, currentFocus, needsAttention } from '@/data/mock'
import { eventsForStudent, isRobotOnline, useLessons, useRobotEvents } from '@/stores/robot'
import { openLessonDialog, ui } from '@/stores/ui'
import { dailyStats, dayLabel, isAi, lastDays, shortDate, splitQA } from '@/utils/stats'
import StatCard from '@/components/StatCard.vue'
import StudentTable from '@/components/StudentTable.vue'
import LessonDropzone from '@/components/LessonDropzone.vue'
import StudyBarChart from '@/components/charts/StudyBarChart.vue'
import ReminderLineChart from '@/components/charts/ReminderLineChart.vue'

const { state } = useRobotEvents()
const { lessons } = useLessons()

const search = ref('')
const group = ref<string>('all')

const days = lastDays(7)
const rangeLabel = `${shortDate(days[0])} — ${shortDate(days[6])}`

const students = computed(() =>
  STUDENTS.filter((s) => (group.value === 'all' || s.group === group.value) && s.name.toLowerCase().includes(search.value.trim().toLowerCase())),
)

// ── 4 thẻ thống kê ───────────────────────────────────────────────────────────
const avg = (xs: number[]) => (xs.length ? Math.round(xs.reduce((a, b) => a + b, 0) / xs.length) : 0)
const avgFocus = computed(() => avg(students.value.map(currentFocus)))
// Trung bình cả lớp theo từng ngày (7 ô nhỏ dưới thẻ tập trung)
const focusByDay = computed(() => days.map((_, i) => avg(students.value.map((s) => s.focusHistory[i]))))
const focusDelta = computed(() => focusByDay.value[6] - focusByDay.value[0])

const homeworkTotal = computed(() => students.value.reduce((a, s) => a + s.homeworkTotal, 0))
const homeworkDone = computed(() => students.value.reduce((a, s) => a + s.homeworkDone, 0))
const homeworkMissing = computed(() => students.value.filter((s) => s.homeworkDone < s.homeworkTotal).length)

const attention = computed(() => students.value.filter(needsAttention))
const lowFocus = computed(() => students.value.filter((s) => currentFocus(s) < 50).length)
const negativeMood = computed(() => students.value.filter((s) => s.mood === 'met').length)

const robotsOnline = computed(() => (state.online && isRobotOnline() ? students.value.filter((s) => s.linkedToRobot).length : 0))

// ── Biểu đồ 7 ngày cả lớp (tuần 4) ───────────────────────────────────────────
const classEvents = computed(() => {
  state.events // phụ thuộc để tự cập nhật khi có sự kiện mới
  return students.value.flatMap((s) => eventsForStudent(s).events)
})
const daily = computed(() => dailyStats(classEvents.value, 7))
const chartLabels = computed(() => daily.value.map((d) => dayLabel(d.date)))

// ── Cả lớp hay hỏi robot ─────────────────────────────────────────────────────
const topQuestions = computed(() => {
  const counts = new Map<string, number>()
  for (const e of state.events.filter(isAi)) {
    const q = splitQA(e.detail).q
    counts.set(q, (counts.get(q) ?? 0) + 1)
  }
  const real = [...counts].map(([text, count]) => ({ text, count })).sort((a, b) => b.count - a.count)
  return (real.length ? real : SAMPLE_QUESTIONS).slice(0, 4)
})

const todayLessons = computed(() => lessons.filter((l) => l.date === new Date().toISOString().slice(0, 10)))

// ── Xuất báo cáo CSV ─────────────────────────────────────────────────────────
function exportReport() {
  const header = ['Học sinh', 'Lớp', 'Nhóm', 'Tập trung (%)', 'Bài tập', 'Tâm trạng']
  const rows = students.value.map((s) => [s.name, s.className, s.group, currentFocus(s), `${s.homeworkDone}/${s.homeworkTotal}`, s.mood])
  const csv = [header, ...rows].map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `bao-cao-lop-${new Date().toISOString().slice(0, 10)}.csv` })
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
    <!-- Tiêu đề + hành động -->
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ ui.classFilter === '5A' ? 'Lớp 5A' : 'Tất cả học sinh' }}</h1>
        <p class="mt-1 text-sm text-slate-500">{{ STUDENTS.length }} học sinh · 7 ngày {{ rangeLabel }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <label class="relative">
          <Search class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
          <input
            v-model="search"
            placeholder="Tìm học sinh..."
            class="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-500 sm:w-56"
          />
        </label>
        <button class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50" @click="exportReport">
          <Download class="size-4" /> Xuất báo cáo
        </button>
        <button
          class="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-500 to-brand-700 px-3 py-2 text-sm font-semibold text-white hover:opacity-90"
          @click="openLessonDialog()"
        >
          <Plus class="size-4" /> Nạp bài học
        </button>
      </div>
    </div>

    <!-- Lọc theo nhóm -->
    <div class="mt-5 flex flex-wrap gap-2">
      <button
        v-for="g in ['all', ...GROUPS]"
        :key="g"
        :class="group === g ? 'bg-brand-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'"
        class="rounded-full px-3.5 py-1.5 text-sm font-medium"
        @click="group = g"
      >
        {{ g === 'all' ? 'Cả lớp' : g }}
      </button>
    </div>

    <!-- 4 thẻ thống kê -->
    <div class="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard :icon="Target" icon-class="bg-brand-50 text-brand-600" label="Tập trung trung bình" :value="`${avgFocus}%`">
        <p :class="focusDelta >= 0 ? 'text-emerald-600' : 'text-rose-600'" class="mt-1 flex items-center gap-1 text-xs font-medium">
          <TrendingUp v-if="focusDelta >= 0" class="size-3.5" /><TrendingDown v-else class="size-3.5" />
          {{ Math.abs(focusDelta) }}% so với đầu tuần
        </p>
        <div class="mt-3 flex gap-1">
          <div
            v-for="(v, i) in focusByDay"
            :key="i"
            :title="`${dayLabel(days[i])}: ${v}%`"
            :class="i === 6 ? 'bg-brand-600' : 'bg-brand-100'"
            class="h-5 flex-1 rounded"
          />
        </div>
      </StatCard>
      <StatCard
        :icon="CheckCircle2"
        icon-class="bg-emerald-50 text-emerald-600"
        label="Đã làm xong bài tập"
        :value="`${homeworkDone}/${homeworkTotal} em`"
        :sub="homeworkMissing ? `${homeworkMissing} em còn bài chưa làm` : 'Cả lớp đã làm xong'"
        :sub-class="homeworkMissing ? 'text-rose-500 font-medium' : 'text-emerald-600'"
      />
      <StatCard
        :icon="Heart"
        icon-class="bg-rose-50 text-rose-500"
        label="Cần quan tâm"
        :value="`${attention.length} em`"
        :sub="`${negativeMood} có cảm xúc tiêu cực · ${lowFocus} ít tập trung`"
      />
      <StatCard
        :icon="Bot"
        icon-class="bg-violet-50 text-violet-500"
        label="Robot đang online"
        :value="`${robotsOnline}/${students.length}`"
        :sub="`${students.length - robotsOnline} em chưa kết nối robot`"
      />
    </div>

    <div class="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div class="min-w-0 space-y-5">
        <StudentTable :students="students" />

        <!-- Biểu đồ tuần 4 -->
        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h2 class="flex items-center gap-2 font-semibold"><ChartColumn class="size-4.5 text-brand-600" /> Thống kê 7 ngày</h2>
            <span v-if="!state.online" class="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs text-amber-700">Dữ liệu mẫu</span>
          </div>
          <div class="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div>
              <p class="mb-2 text-sm text-slate-500">Thời lượng học cả lớp (phút)</p>
              <StudyBarChart :labels="chartLabels" :minutes="daily.map((d) => d.studyMinutes)" />
            </div>
            <div>
              <p class="mb-2 text-sm text-slate-500">Tần suất robot nhắc nhở (lần)</p>
              <ReminderLineChart :labels="chartLabels" :posture="daily.map((d) => d.posture)" :attention="daily.map((d) => d.attention)" />
            </div>
          </div>
        </section>
      </div>

      <!-- Cột phải -->
      <aside class="space-y-5">
        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">Nạp bài học hôm nay</h2>
            <span class="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">Tất cả học sinh</span>
          </div>
          <LessonDropzone class="mt-4" />
          <div
            v-for="l in todayLessons.slice(0, 3)"
            :key="l.id"
            class="mt-3 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-xs text-emerald-800"
          >
            <CheckCircle2 class="size-4 shrink-0" />
            <span class="min-w-0 flex-1 truncate">{{ l.subject }} · {{ l.summary }}</span>
            <b class="shrink-0">{{ l.received }} em đã nhận</b>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="flex items-center gap-2 font-semibold"><Sparkles class="size-4 text-brand-600" /> Cả lớp hay hỏi robot</h2>
            <span class="text-xs text-slate-400">7 ngày</span>
          </div>
          <ul class="mt-3 space-y-3">
            <li v-for="q in topQuestions" :key="q.text">
              <div class="flex items-start justify-between gap-3 text-sm">
                <span class="text-slate-700">“{{ q.text }}”</span>
                <span class="shrink-0 font-medium text-brand-600">{{ q.count }} em</span>
              </div>
              <div class="mt-1.5 h-1.5 rounded-full bg-brand-100">
                <div class="h-full rounded-full bg-brand-500" :style="{ width: `${(q.count / topQuestions[0].count) * 100}%` }" />
              </div>
            </li>
          </ul>
        </section>
      </aside>
    </div>
  </div>
</template>
