<script setup lang="ts">
// Trang chi tiết học sinh / phiên học (tuần 4 — task 9):
// thống kê theo ngày/tuần, danh sách phiên học, timeline sự kiện của từng phiên.
import { computed, ref, watch } from 'vue'
import { ArrowLeft, Bell, Clock, MessageCircleQuestion, Timer } from 'lucide-vue-next'
import { STUDENTS, currentFocus } from '@/data/mock'
import { eventsForStudent, useRobotEvents } from '@/stores/robot'
import { dailyStats, dayLabel, hhmm, shortDate, splitSessions, weeklyStats } from '@/utils/stats'
import StudentAvatar from '@/components/StudentAvatar.vue'
import MoodBadge from '@/components/MoodBadge.vue'
import FocusBar from '@/components/FocusBar.vue'
import StatCard from '@/components/StatCard.vue'
import EventTimeline from '@/components/EventTimeline.vue'
import StudyBarChart from '@/components/charts/StudyBarChart.vue'
import ReminderLineChart from '@/components/charts/ReminderLineChart.vue'

const props = defineProps<{ id: string }>()
const { state } = useRobotEvents()

const student = computed(() => STUDENTS.find((s) => s.id === props.id))
const source = computed(() => {
  state.events // tự cập nhật khi robot gửi sự kiện mới
  return student.value ? eventsForStudent(student.value) : { events: [], isReal: false }
})

const period = ref<'day' | 'week'>('day')

const chart = computed(() => {
  if (period.value === 'day') {
    const d = dailyStats(source.value.events, 7)
    return { labels: d.map((x) => dayLabel(x.date)), minutes: d.map((x) => x.studyMinutes), posture: d.map((x) => x.posture), attention: d.map((x) => x.attention) }
  }
  const w = weeklyStats(source.value.events, 4)
  // Theo tuần: gộp tư thế + tập trung vào cùng đường "nhắc nhở"
  return { labels: w.map((x) => x.label), minutes: w.map((x) => x.studyMinutes), posture: w.map((x) => x.reminders), attention: undefined }
})

const sessions = computed(() => splitSessions(source.value.events))
const totals = computed(() => ({
  minutes: sessions.value.reduce((a, s) => a + s.studyMinutes, 0),
  reminders: sessions.value.reduce((a, s) => a + s.reminders, 0),
  ai: sessions.value.reduce((a, s) => a + s.ai, 0),
}))

const selected = ref(0)
watch(() => props.id, () => (selected.value = 0))
const current = computed(() => sessions.value[selected.value] ?? sessions.value[0])

const durationLabel = (start: Date, end: Date) => {
  const m = Math.max(1, Math.round((end.getTime() - start.getTime()) / 60000))
  return m >= 60 ? `${Math.floor(m / 60)} giờ ${m % 60} phút` : `${m} phút`
}
</script>

<template>
  <div v-if="student" class="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
    <RouterLink to="/" class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900">
      <ArrowLeft class="size-4" /> Tổng quan lớp
    </RouterLink>

    <!-- Thông tin học sinh -->
    <div class="mt-4 flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5">
      <StudentAvatar :name="student.name" size="lg" />
      <div class="min-w-0 flex-1">
        <h1 class="text-xl font-bold">{{ student.name }}</h1>
        <p class="text-sm text-slate-500">{{ student.className }} · {{ student.group }}</p>
        <p v-if="student.note" class="mt-1 text-sm italic text-slate-600">“{{ student.note }}”</p>
      </div>
      <div class="flex flex-wrap items-center gap-5">
        <div><p class="text-xs text-slate-400">Tập trung hôm nay</p><FocusBar :value="currentFocus(student)" /></div>
        <div><p class="text-xs text-slate-400">Tâm trạng</p><MoodBadge :mood="student.mood" /></div>
        <span
          :class="source.isReal ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
          class="rounded-full px-2.5 py-1 text-xs font-medium"
        >
          {{ source.isReal ? '● Dữ liệu thật từ robot' : 'Dữ liệu mẫu' }}
        </span>
      </div>
    </div>

    <!-- Tổng quan -->
    <div class="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard :icon="Timer" icon-class="bg-brand-50 text-brand-600" label="Thời lượng học" :value="`${totals.minutes} phút`" sub="Tổng độ dài các phiên học" />
      <StatCard :icon="Clock" icon-class="bg-sky-50 text-sky-600" label="Phiên học" :value="`${sessions.length}`" sub="Cách nhau > 30 phút là phiên mới" />
      <StatCard :icon="Bell" icon-class="bg-rose-50 text-rose-500" label="Robot nhắc nhở" :value="`${totals.reminders} lần`" sub="Tư thế + tập trung" />
      <StatCard :icon="MessageCircleQuestion" icon-class="bg-emerald-50 text-emerald-600" label="Câu hỏi cho robot" :value="`${totals.ai}`" />
    </div>

    <!-- Biểu đồ theo ngày / tuần -->
    <section class="mt-5 rounded-2xl border border-slate-200 bg-white p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="font-semibold">Thống kê {{ period === 'day' ? '7 ngày' : '4 tuần' }}</h2>
        <div class="flex rounded-lg border border-slate-200 p-0.5 text-sm">
          <button :class="period === 'day' ? 'bg-slate-900 text-white' : 'text-slate-600'" class="rounded-md px-3 py-1" @click="period = 'day'">Theo ngày</button>
          <button :class="period === 'week' ? 'bg-slate-900 text-white' : 'text-slate-600'" class="rounded-md px-3 py-1" @click="period = 'week'">Theo tuần</button>
        </div>
      </div>
      <div class="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <p class="mb-2 text-sm text-slate-500">Thời lượng học (phút)</p>
          <StudyBarChart :labels="chart.labels" :minutes="chart.minutes" />
        </div>
        <div>
          <p class="mb-2 text-sm text-slate-500">Tần suất nhắc nhở (lần)</p>
          <ReminderLineChart :labels="chart.labels" :posture="chart.posture" :attention="chart.attention" />
        </div>
      </div>
      <p v-if="source.isReal" class="mt-3 text-xs text-slate-400">
        Backend hiện chỉ trả 50 sự kiện gần nhất — số liệu ngày/tuần cũ hơn sẽ đầy đủ khi nhóm BE có API thống kê.
      </p>
    </section>

    <!-- Phiên học + timeline -->
    <div class="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
      <section class="rounded-2xl border border-slate-200 bg-white p-3">
        <h2 class="px-2 pb-2 pt-1 font-semibold">Phiên học</h2>
        <p v-if="!sessions.length" class="px-2 py-6 text-center text-sm text-slate-400">Chưa có phiên học nào.</p>
        <ul class="max-h-[520px] space-y-1 overflow-y-auto">
          <li v-for="(s, i) in sessions" :key="s.start.getTime()">
            <button
              :class="i === selected ? 'bg-brand-50 ring-1 ring-brand-200' : 'hover:bg-slate-50'"
              class="w-full rounded-xl px-3 py-2.5 text-left"
              @click="selected = i"
            >
              <p class="text-sm font-medium">{{ dayLabel(s.start) }} · {{ hhmm(s.start) }}–{{ hhmm(s.end) }}</p>
              <p class="mt-0.5 text-xs text-slate-500">
                {{ s.events.length }} sự kiện · {{ s.reminders }} lần nhắc · {{ s.ai }} câu hỏi
              </p>
            </button>
          </li>
        </ul>
      </section>

      <section class="min-w-0 rounded-2xl border border-slate-200 bg-white p-5">
        <template v-if="current">
          <h2 class="font-semibold">Phiên {{ shortDate(current.start) }} · {{ hhmm(current.start) }}–{{ hhmm(current.end) }}</h2>
          <p class="mt-0.5 text-sm text-slate-500">
            Kéo dài {{ durationLabel(current.start, current.end) }} · {{ current.events.length }} sự kiện
          </p>
          <EventTimeline class="mt-5" :events="current.events" />
        </template>
        <p v-else class="py-10 text-center text-sm text-slate-400">Chọn một phiên học để xem chi tiết.</p>
      </section>
    </div>
  </div>

  <div v-else class="p-10 text-center text-slate-500">
    Không tìm thấy học sinh. <RouterLink to="/" class="text-brand-600 underline">Về tổng quan</RouterLink>
  </div>
</template>
