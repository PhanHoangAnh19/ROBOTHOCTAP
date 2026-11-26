<script setup lang="ts">
// Trang "AI & Chi phí" (tuần 5 — task 8): phản hồi LLM, lịch sử bài học, biểu đồ chi phí token.
import { computed, ref } from 'vue'
import { BookOpen, Bot, ChevronDown, Coins, Gauge, MessageCircleQuestion, RotateCcw, Search, WifiOff } from 'lucide-vue-next'
import { MODE_LABEL, costUsd, logDate, totalTokens, type LlmLog } from '@/api/llm'
import { pricing, resetPricing, useLlmLogs } from '@/stores/llm'
import { useLessons } from '@/stores/robot'
import { dayKey, dayLabel, hhmm, lastDays, shortDate } from '@/utils/stats'
import StatCard from '@/components/StatCard.vue'
import CostBarChart from '@/components/charts/CostBarChart.vue'
import LatencyLineChart from '@/components/charts/LatencyLineChart.vue'

const Q8_TARGET_S = 8

const { state } = useLlmLogs()
const { lessons } = useLessons()

const days = lastDays(7)
const since = days[0]
const recent = computed(() => state.logs.filter((l) => logDate(l) >= since))

const vnd = (usd: number) => usd * pricing.usdToVnd
const fmtVnd = (n: number) => `${n < 10 ? n.toLocaleString('vi-VN', { maximumFractionDigits: 1 }) : Math.round(n).toLocaleString('vi-VN')} ₫`
const fmtNum = (n: number) => n.toLocaleString('vi-VN')

function median(xs: number[]): number | null {
  if (!xs.length) return null
  const s = [...xs].sort((a, b) => a - b)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}
const latencies = (ls: readonly LlmLog[]) => ls.map((l) => l.latency_ms).filter((x): x is number => typeof x === 'number')

// ── Thẻ thống kê (7 ngày) ────────────────────────────────────────────────────
const stats = computed(() => {
  const ls = recent.value
  const answered = ls.filter((l) => l.status === 'ok')
  const cost = ls.reduce((a, l) => a + costUsd(l, pricing), 0)
  const med = median(latencies(ls))
  return {
    total: ls.length,
    offline: ls.filter((l) => l.status !== 'ok').length,
    tokens: ls.reduce((a, l) => a + totalTokens(l), 0),
    avgTokens: answered.length ? Math.round(answered.reduce((a, l) => a + totalTokens(l), 0) / answered.length) : 0,
    costVnd: vnd(cost),
    perCallVnd: answered.length ? vnd(cost) / answered.length : 0,
    medianS: med == null ? null : med / 1000,
  }
})

// ── Biểu đồ theo ngày ────────────────────────────────────────────────────────
const daily = computed(() =>
  days.map((d) => {
    const ls = recent.value.filter((l) => dayKey(logDate(l)) === dayKey(d))
    const med = median(latencies(ls))
    return {
      label: dayLabel(d),
      input: ls.reduce((a, l) => a + l.input_tokens, 0),
      image: ls.reduce((a, l) => a + (l.image_tokens ?? 0), 0),
      output: ls.reduce((a, l) => a + l.output_tokens, 0),
      costVnd: vnd(ls.reduce((a, l) => a + costUsd(l, pricing), 0)),
      medianS: med == null ? null : med / 1000,
    }
  }),
)
const hasLatency = computed(() => latencies(state.logs).length > 0)

// ── Theo chế độ học ──────────────────────────────────────────────────────────
const byMode = computed(() => {
  const m = new Map<string, number>()
  for (const l of recent.value) m.set(l.mode, (m.get(l.mode) ?? 0) + 1)
  return [...m].map(([mode, count]) => ({ mode, count })).sort((a, b) => b.count - a.count)
})

// ── Danh sách log ────────────────────────────────────────────────────────────
const search = ref('')
const mode = ref('all')
const status = ref<'all' | 'ok' | 'offline'>('all')
const expanded = ref<number | null>(null)
const limit = ref(20)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return state.logs.filter(
    (l) =>
      (mode.value === 'all' || l.mode === mode.value) &&
      (status.value === 'all' || (status.value === 'ok' ? l.status === 'ok' : l.status !== 'ok')) &&
      (!q || l.question.toLowerCase().includes(q) || l.answer.toLowerCase().includes(q)),
  )
})

const sourceInfo = computed(() => {
  switch (state.source) {
    case 'api':
      return { badge: '● Dữ liệu thật từ backend', cls: 'bg-emerald-50 text-emerald-700', note: '' }
    case 'events':
      return {
        badge: '● Câu hỏi thật · token ước tính',
        cls: 'bg-sky-50 text-sky-700',
        note: 'Câu hỏi và câu trả lời là dữ liệu thật từ GET /events. Backend chưa lưu token và độ trễ, nên token được ước tính (1 từ ≈ 1.6 token, giống llm_socratic.py) và chưa có biểu đồ độ trễ. Khi nhóm BE có API GET /llm-logs, trang tự chuyển sang số liệu thật.',
      }
    default:
      return { badge: 'Dữ liệu mẫu', cls: 'bg-amber-50 text-amber-700', note: 'Backend chưa chạy — đang hiển thị dữ liệu mẫu.' }
  }
})

const lessonsSorted = computed(() => [...lessons].sort((a, b) => b.createdAt.localeCompare(a.createdAt)))
const fmtDate = (d: string) => d.split('-').reverse().join('/')
</script>

<template>
  <div class="mx-auto max-w-7xl p-4 sm:p-6 lg:p-8">
    <!-- Tiêu đề -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">AI &amp; Chi phí</h1>
        <p class="mt-1 text-sm text-slate-500">Phản hồi của robot, token và chi phí LLM · 7 ngày {{ shortDate(days[0]) }} — {{ shortDate(days[6]) }}</p>
      </div>
      <span :class="sourceInfo.cls" class="rounded-full px-2.5 py-1 text-xs font-medium">{{ sourceInfo.badge }}</span>
    </div>
    <p v-if="sourceInfo.note" class="mt-3 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">{{ sourceInfo.note }}</p>

    <!-- Thẻ thống kê -->
    <div class="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        :icon="MessageCircleQuestion"
        icon-class="bg-brand-50 text-brand-600"
        label="Lượt hỏi robot"
        :value="fmtNum(stats.total)"
        :sub="stats.offline ? `${stats.offline} lượt robot trả lời offline` : 'Tất cả đều được LLM trả lời'"
        :sub-class="stats.offline ? 'text-amber-600 font-medium' : 'text-emerald-600'"
      />
      <StatCard :icon="Bot" icon-class="bg-sky-50 text-sky-600" label="Token đã dùng" :value="fmtNum(stats.tokens)" :sub="`Trung bình ${fmtNum(stats.avgTokens)} token / lượt`" />
      <StatCard :icon="Coins" icon-class="bg-emerald-50 text-emerald-600" label="Chi phí ước tính" :value="fmtVnd(stats.costVnd)" :sub="`≈ ${fmtVnd(stats.perCallVnd)} / lượt hỏi`" />
      <StatCard
        :icon="Gauge"
        icon-class="bg-rose-50 text-rose-500"
        label="Độ trễ trung vị (Q8)"
        :value="stats.medianS == null ? '—' : `${stats.medianS.toFixed(1)} giây`"
        :sub="stats.medianS == null ? 'Chờ BE ghi độ trễ' : stats.medianS <= Q8_TARGET_S ? `Đạt mục tiêu ≤ ${Q8_TARGET_S} giây` : `Chưa đạt mục tiêu ≤ ${Q8_TARGET_S} giây`"
        :sub-class="stats.medianS == null ? undefined : stats.medianS <= Q8_TARGET_S ? 'text-emerald-600 font-medium' : 'text-rose-500 font-medium'"
      />
    </div>

    <!-- Biểu đồ -->
    <div class="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
      <section class="min-w-0 rounded-2xl border border-slate-200 bg-white p-5">
        <h2 class="font-semibold">Token &amp; chi phí theo ngày</h2>
        <p class="mt-0.5 text-xs text-slate-500">Rê chuột vào cột để xem chi phí (VND)</p>
        <CostBarChart
          class="mt-3"
          :labels="daily.map((d) => d.label)"
          :input="daily.map((d) => d.input)"
          :image="daily.map((d) => d.image)"
          :output="daily.map((d) => d.output)"
          :cost-vnd="daily.map((d) => d.costVnd)"
        />
      </section>
      <section class="min-w-0 rounded-2xl border border-slate-200 bg-white p-5">
        <h2 class="font-semibold">Độ trễ phản hồi</h2>
        <p class="mt-0.5 text-xs text-slate-500">Từ lúc gửi câu hỏi tới lúc robot có câu trả lời</p>
        <LatencyLineChart v-if="hasLatency" class="mt-3" :labels="daily.map((d) => d.label)" :median-seconds="daily.map((d) => d.medianS)" :target="Q8_TARGET_S" />
        <div v-else class="mt-3 grid h-64 place-items-center rounded-xl border border-dashed border-slate-200 text-center text-sm text-slate-400">
          <div class="px-6">
            <Gauge class="mx-auto size-7 text-slate-300" />
            <p class="mt-2">Backend chưa ghi độ trễ LLM.</p>
            <p class="text-xs">Biểu đồ sẽ hiện khi có API GET /llm-logs (trường latency_ms).</p>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
      <!-- Log phản hồi LLM -->
      <section class="min-w-0 rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="font-semibold">Phản hồi của robot <span class="text-sm font-normal text-slate-400">({{ filtered.length }})</span></h2>
          <label class="relative w-full sm:w-56">
            <Search class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
            <input v-model="search" placeholder="Tìm câu hỏi..." class="w-full rounded-lg border border-slate-200 py-1.5 pl-9 pr-3 text-sm outline-none focus:border-brand-500" />
          </label>
        </div>
        <div class="mt-3 flex flex-wrap gap-2 text-sm">
          <select v-model="mode" class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 outline-none focus:border-brand-500">
            <option value="all">Mọi chế độ</option>
            <option v-for="(label, key) in MODE_LABEL" :key="key" :value="key">{{ label }}</option>
          </select>
          <select v-model="status" class="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 outline-none focus:border-brand-500">
            <option value="all">Mọi trạng thái</option>
            <option value="ok">LLM trả lời</option>
            <option value="offline">Offline / lỗi</option>
          </select>
        </div>

        <p v-if="!filtered.length" class="py-10 text-center text-sm text-slate-400">
          {{ state.logs.length ? 'Không có lượt hỏi nào khớp bộ lọc.' : 'Chưa có lượt hỏi robot nào.' }}
        </p>
        <ul class="mt-3 divide-y divide-slate-100">
          <li v-for="l in filtered.slice(0, limit)" :key="l.id">
            <button class="flex w-full items-start gap-3 py-3 text-left" @click="expanded = expanded === l.id ? null : l.id">
              <span class="w-14 shrink-0 text-xs tabular-nums text-slate-400">
                {{ shortDate(logDate(l)) }}<br />{{ hhmm(logDate(l)) }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="flex flex-wrap items-center gap-1.5">
                  <span class="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700">{{ MODE_LABEL[l.mode] ?? l.mode }}</span>
                  <span v-if="l.status !== 'ok'" class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-700">
                    <WifiOff class="size-3" /> Offline
                  </span>
                </span>
                <span :class="expanded === l.id ? '' : 'line-clamp-1'" class="mt-1 block text-sm font-medium text-slate-800">{{ l.question }}</span>
              </span>
              <span class="shrink-0 text-right text-xs text-slate-500">
                <span class="block tabular-nums">{{ fmtNum(totalTokens(l)) }} token</span>
                <span class="block tabular-nums">{{ fmtVnd(vnd(costUsd(l, pricing))) }}</span>
              </span>
              <ChevronDown :class="expanded === l.id ? 'rotate-180' : ''" class="mt-0.5 size-4 shrink-0 text-slate-400 transition-transform" />
            </button>
            <div v-if="expanded === l.id" class="mb-3 ml-0 space-y-2 rounded-xl bg-slate-50 p-3 text-sm sm:ml-[68px]">
              <p><span class="font-medium text-slate-500">Bé hỏi:</span> {{ l.question }}</p>
              <p><span class="font-medium text-brand-600">Robot:</span> {{ l.answer || '—' }}</p>
              <div class="flex flex-wrap gap-x-4 gap-y-1 border-t border-slate-200 pt-2 text-xs text-slate-500">
                <span>Vào: {{ fmtNum(l.input_tokens) }}</span>
                <span v-if="l.image_tokens">Ảnh: {{ fmtNum(l.image_tokens) }}</span>
                <span>Ra: {{ fmtNum(l.output_tokens) }}</span>
                <span>Độ trễ: {{ l.latency_ms == null ? '—' : `${(l.latency_ms / 1000).toFixed(1)}s` }}</span>
                <span v-if="l.model">Model: {{ l.provider ? `${l.provider} · ` : '' }}{{ l.model }}</span>
              </div>
            </div>
          </li>
        </ul>
        <button v-if="filtered.length > limit" class="mt-2 w-full rounded-lg border border-slate-200 py-2 text-sm text-slate-600 hover:bg-slate-50" @click="limit += 20">
          Xem thêm {{ Math.min(20, filtered.length - limit) }} lượt
        </button>
      </section>

      <!-- Cột phải -->
      <aside class="space-y-5">
        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 class="font-semibold">Theo chế độ học</h2>
          <p v-if="!byMode.length" class="mt-3 text-sm text-slate-400">Chưa có dữ liệu 7 ngày.</p>
          <ul class="mt-3 space-y-3">
            <li v-for="m in byMode" :key="m.mode">
              <div class="flex justify-between text-sm">
                <span>{{ MODE_LABEL[m.mode] ?? m.mode }}</span><span class="font-medium text-brand-600">{{ m.count }} lượt</span>
              </div>
              <div class="mt-1.5 h-1.5 rounded-full bg-brand-100">
                <div class="h-full rounded-full bg-brand-500" :style="{ width: `${(m.count / byMode[0].count) * 100}%` }" />
              </div>
            </li>
          </ul>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">Đơn giá tính chi phí</h2>
            <button class="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-900" @click="resetPricing">
              <RotateCcw class="size-3.5" /> Mặc định
            </button>
          </div>
          <div class="mt-3 space-y-2.5 text-sm">
            <label class="flex items-center justify-between gap-3">
              <span class="text-slate-600">Đầu vào (USD / 1M token)</span>
              <input v-model.number="pricing.inputPerM" type="number" min="0" step="0.01" class="w-24 rounded-lg border border-slate-200 px-2 py-1 text-right outline-none focus:border-brand-500" />
            </label>
            <label class="flex items-center justify-between gap-3">
              <span class="text-slate-600">Đầu ra (USD / 1M token)</span>
              <input v-model.number="pricing.outputPerM" type="number" min="0" step="0.01" class="w-24 rounded-lg border border-slate-200 px-2 py-1 text-right outline-none focus:border-brand-500" />
            </label>
            <label class="flex items-center justify-between gap-3">
              <span class="text-slate-600">Tỷ giá (VND / USD)</span>
              <input v-model.number="pricing.usdToVnd" type="number" min="0" step="100" class="w-24 rounded-lg border border-slate-200 px-2 py-1 text-right outline-none focus:border-brand-500" />
            </label>
          </div>
          <p class="mt-3 text-xs text-slate-400">Giá tham khảo — đối chiếu bảng giá của nhà cung cấp LLM nhóm đang dùng. Khi BE trả cost_usd, trang dùng số của BE.</p>
        </section>

        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="flex items-center gap-2 font-semibold"><BookOpen class="size-4 text-brand-600" /> Lịch sử bài học</h2>
            <RouterLink to="/bai-hoc" class="text-xs text-brand-600 hover:underline">Xem tất cả</RouterLink>
          </div>
          <p v-if="!lessonsSorted.length" class="mt-3 text-sm text-slate-400">Chưa nạp bài học nào.</p>
          <ul class="mt-3 space-y-2.5">
            <li v-for="l in lessonsSorted.slice(0, 5)" :key="l.id" class="rounded-lg bg-slate-50 px-3 py-2">
              <p class="truncate text-sm font-medium">{{ l.summary }}</p>
              <p class="text-xs text-slate-500">{{ l.subject }} · {{ fmtDate(l.date) }} · {{ l.received }} em đã nhận</p>
            </li>
          </ul>
        </section>
      </aside>
    </div>
  </div>
</template>
