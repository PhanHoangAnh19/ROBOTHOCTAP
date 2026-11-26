// Trạng thái dùng chung cho trang "AI & Chi phí": log LLM (làm mới mỗi 10 giây) + đơn giá.
import { reactive, readonly, watch } from 'vue'
import { DEFAULT_PRICING, fetchLlmLogs, type LlmLog, type LlmSource, type Pricing } from '@/api/llm'

const state = reactive({
  logs: [] as LlmLog[],
  source: 'mock' as LlmSource,
  loaded: false,
})

let timer: number | undefined

async function refresh() {
  const { logs, source } = await fetchLlmLogs()
  state.logs = logs
  state.source = source
  state.loaded = true
}

export function useLlmLogs() {
  if (timer === undefined) {
    refresh()
    timer = window.setInterval(refresh, 10_000)
  }
  return { state: readonly(state), refresh }
}

// ── Đơn giá: lưu trên trình duyệt để lần sau mở lại vẫn giữ ──────────────────
const PRICING_KEY = 'robothoctap.pricing'

function loadPricing(): Pricing {
  try {
    return { ...DEFAULT_PRICING, ...JSON.parse(localStorage.getItem(PRICING_KEY) || '{}') }
  } catch {
    return { ...DEFAULT_PRICING }
  }
}

export const pricing = reactive<Pricing>(loadPricing())

watch(pricing, (p) => {
  try {
    localStorage.setItem(PRICING_KEY, JSON.stringify(p))
  } catch {
    /* trình duyệt chặn lưu trữ */
  }
})

export function resetPricing() {
  Object.assign(pricing, DEFAULT_PRICING)
}
