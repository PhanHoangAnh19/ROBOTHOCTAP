// Log LLM & chi phí token (tuần 5 — task 8).
//
// Nguồn dữ liệu, theo thứ tự ưu tiên:
//   1. GET /llm-logs  — API nhóm BE sẽ làm ở task 5 tuần 5 (hợp đồng ở web-service/README.md).
//                       Có token thật, độ trễ thật, model thật.
//   2. GET /events    — đang có: lấy các câu hỏi AI (GIAI_TOAN / DAY_HOC / THAC_MAC),
//                       token ƯỚC TÍNH từ độ dài văn bản, chưa có độ trễ.
//   3. Dữ liệu mẫu    — khi backend không chạy.
import { AI_TYPES, parseTimestamp, type RobotEvent } from '@/api/events'
import { splitQA } from '@/utils/stats'

export type LlmStatus = 'ok' | 'offline' | 'error'

export interface LlmLog {
  id: number
  timestamp: string // "YYYY-MM-DD HH:MM:SS"
  mode: string // GIAI_TOAN | DAY_HOC | THAC_MAC
  question: string
  answer: string
  status: LlmStatus
  provider?: string
  model?: string
  input_tokens: number
  output_tokens: number
  image_tokens?: number
  latency_ms?: number | null
  /** Chi phí BE tự tính (nếu có); không có thì web tự tính theo đơn giá */
  cost_usd?: number | null
}

export type LlmSource = 'api' | 'events' | 'mock'

export const MODE_LABEL: Record<string, string> = {
  GIAI_TOAN: 'Giải Toán',
  DAY_HOC: 'Dạy học gợi mở',
  THAC_MAC: 'Giải đáp thắc mắc',
}

/** Ước lượng token tiếng Việt — cùng công thức với ai/prompts/llm_socratic.py (1 từ ≈ 1.6 token) */
export function estimateTokens(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length
  return Math.ceil(words * 1.6)
}

/** Prompt hệ thống được gửi kèm mỗi lượt hỏi — ước lượng khi chưa có số thật từ BE */
const SYSTEM_PROMPT_TOKENS = 120

const OFFLINE_MARK = '[Chế độ Offline]'

/** Chuyển 1 sự kiện AI trong /events thành log LLM (token ước tính) */
export function logFromEvent(e: RobotEvent): LlmLog {
  const { q, a } = splitQA(e.detail)
  const offline = a.startsWith(OFFLINE_MARK)
  return {
    id: e.id,
    timestamp: e.timestamp,
    mode: e.event_type,
    question: q,
    answer: a,
    status: offline ? 'offline' : 'ok',
    input_tokens: offline ? 0 : SYSTEM_PROMPT_TOKENS + estimateTokens(q),
    output_tokens: offline ? 0 : estimateTokens(a),
    latency_ms: null,
  }
}

export async function fetchLlmLogs(signal?: AbortSignal): Promise<{ logs: LlmLog[]; source: LlmSource }> {
  // 1. API log LLM của BE
  try {
    const res = await fetch('/llm-logs', { signal })
    if (res.ok && res.headers.get('content-type')?.includes('json')) {
      const body = await res.json()
      if (Array.isArray(body?.logs)) return { logs: body.logs, source: 'api' }
    }
  } catch {
    /* chưa có API → thử nguồn tiếp theo */
  }
  // 2. Câu hỏi AI trong /events
  try {
    const res = await fetch('/events', { signal })
    if (res.ok) {
      const body = await res.json()
      const events: RobotEvent[] = body.events ?? []
      return { logs: events.filter((e) => AI_TYPES.includes(e.event_type)).map(logFromEvent), source: 'events' }
    }
  } catch {
    /* backend tắt */
  }
  // 3. Dữ liệu mẫu
  return { logs: mockLlmLogs(), source: 'mock' }
}

export function logDate(l: LlmLog): Date {
  return parseTimestamp(l.timestamp)
}

// ── Đơn giá (USD / 1 triệu token) ─────────────────────────────────────────────
// Giá tham khảo, có thể chỉnh trên trang. Luôn đối chiếu bảng giá chính thức của nhà cung cấp.
export interface Pricing {
  inputPerM: number
  outputPerM: number
  usdToVnd: number
}

export const DEFAULT_PRICING: Pricing = { inputPerM: 0.1, outputPerM: 0.4, usdToVnd: 26000 }

export function costUsd(l: LlmLog, p: Pricing): number {
  if (typeof l.cost_usd === 'number') return l.cost_usd
  const input = l.input_tokens + (l.image_tokens ?? 0)
  return (input * p.inputPerM + l.output_tokens * p.outputPerM) / 1_000_000
}

export const totalTokens = (l: LlmLog) => l.input_tokens + l.output_tokens + (l.image_tokens ?? 0)

// ── Dữ liệu mẫu ───────────────────────────────────────────────────────────────
const SAMPLE: Array<[string, string, string]> = [
  ['GIAI_TOAN', '3/4 + 1/2 bằng bao nhiêu?', 'Con thử quy đồng mẫu số trước nhé! Mẫu số chung của 4 và 2 là mấy?'],
  ['DAY_HOC', 'Chu vi hình chữ nhật tính sao ạ?', 'Con cộng chiều dài với chiều rộng, rồi nhân với mấy nhỉ? Con thử đo quyển vở xem!'],
  ['THAC_MAC', 'Vì sao có cầu vồng?', 'Câu hỏi hay quá! Con nghĩ khi ánh nắng đi qua giọt mưa thì điều gì xảy ra?'],
  ['GIAI_TOAN', '125 x 8 bằng mấy?', 'Con thử tách 125 x 8 thành 100 x 8 và 25 x 8 xem nào!'],
  ['DAY_HOC', 'Từ "chăm chỉ" là từ loại gì?', 'Con thử đặt một câu có từ "chăm chỉ" nhé. Nó tả người hay chỉ hành động?'],
  ['GIAI_TOAN', '21 phần 7 cộng 21 phần 8 bằng bao nhiêu?', 'Mình rút gọn 21/7 trước được không con? 21 chia 7 bằng mấy?'],
]

function pad(n: number) {
  return String(n).padStart(2, '0')
}

export function mockLlmLogs(now = new Date()): LlmLog[] {
  let seed = 7
  const rand = () => ((seed = (seed * 9301 + 49297) % 233280) / 233280)
  const logs: LlmLog[] = []
  let id = 1
  for (let d = 6; d >= 0; d--) {
    const count = 2 + Math.floor(rand() * 5)
    for (let i = 0; i < count; i++) {
      const t = new Date(now)
      t.setDate(now.getDate() - d)
      t.setHours(15 + Math.floor(rand() * 6), Math.floor(rand() * 60), Math.floor(rand() * 60))
      if (t > now) continue
      const [mode, question, answer] = SAMPLE[Math.floor(rand() * SAMPLE.length)]
      const offline = rand() < 0.08
      const withImage = mode === 'GIAI_TOAN' && rand() < 0.6
      logs.push({
        id: id++,
        timestamp: `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}:${pad(t.getSeconds())}`,
        mode,
        question,
        answer: offline ? `${OFFLINE_MARK} Đã nhận câu hỏi '${question}'.` : answer,
        status: offline ? 'offline' : 'ok',
        provider: 'Gemini',
        model: 'gemini-2.0-flash',
        input_tokens: offline ? 0 : SYSTEM_PROMPT_TOKENS + estimateTokens(question),
        output_tokens: offline ? 0 : estimateTokens(answer) + Math.floor(rand() * 40),
        image_tokens: offline || !withImage ? 0 : 250 + Math.floor(rand() * 200),
        latency_ms: offline ? null : Math.round(1800 + rand() * 5500),
      })
    }
  }
  return logs.sort((a, b) => logDate(b).getTime() - logDate(a).getTime())
}
