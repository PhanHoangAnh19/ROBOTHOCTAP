// Tính thống kê phía web từ danh sách sự kiện.
// Backend hiện chỉ trả 50 sự kiện gần nhất → khi BE có API thống kê theo ngày/tuần,
// thay các hàm ở đây bằng dữ liệu từ API.
import { AI_TYPES, ATTENTION_TYPES, POSTURE_TYPES, parseTimestamp, type RobotEvent } from '@/api/events'

export const isPosture = (e: RobotEvent) => POSTURE_TYPES.includes(e.event_type)
export const isAttention = (e: RobotEvent) => ATTENTION_TYPES.includes(e.event_type)
export const isAi = (e: RobotEvent) => AI_TYPES.includes(e.event_type)
export const isReminder = (e: RobotEvent) => isPosture(e) || isAttention(e)

export function dayKey(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export function shortDate(d: Date): string {
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}

const WEEKDAY = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

/** Danh sách N ngày gần nhất (cũ → mới) */
export function lastDays(n: number, now = new Date()): Date[] {
  return Array.from({ length: n }, (_, i) => {
    const d = new Date(now)
    d.setHours(0, 0, 0, 0)
    d.setDate(d.getDate() - (n - 1 - i))
    return d
  })
}

export function dayLabel(d: Date): string {
  return `${WEEKDAY[d.getDay()]} ${shortDate(d)}`
}

export interface DailyStat {
  date: Date
  studyMinutes: number
  posture: number
  attention: number
  ai: number
}

/** Gom sự kiện theo ngày cho N ngày gần nhất */
export function dailyStats(events: RobotEvent[], days = 7, now = new Date()): DailyStat[] {
  const buckets = new Map<string, DailyStat>()
  for (const d of lastDays(days, now)) {
    buckets.set(dayKey(d), { date: d, studyMinutes: 0, posture: 0, attention: 0, ai: 0 })
  }
  // Thời lượng học: cộng độ dài các phiên học, tính vào ngày bắt đầu phiên
  for (const s of splitSessions(events)) {
    const b = buckets.get(dayKey(s.start))
    if (b) b.studyMinutes += s.studyMinutes
  }
  for (const e of events) {
    const b = buckets.get(dayKey(parseTimestamp(e.timestamp)))
    if (!b) continue
    if (isPosture(e)) b.posture++
    else if (isAttention(e)) b.attention++
    else if (isAi(e)) b.ai++
  }
  return [...buckets.values()]
}

export interface WeeklyStat {
  label: string
  studyMinutes: number
  reminders: number
  ai: number
}

/** Gom theo tuần (thứ 2 → CN) cho N tuần gần nhất */
export function weeklyStats(events: RobotEvent[], weeks = 4, now = new Date()): WeeklyStat[] {
  const monday = new Date(now)
  monday.setHours(0, 0, 0, 0)
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7))
  const result: WeeklyStat[] = []
  for (let w = weeks - 1; w >= 0; w--) {
    const start = new Date(monday)
    start.setDate(monday.getDate() - w * 7)
    const end = new Date(start)
    end.setDate(start.getDate() + 7)
    const inWeek = events.filter((e) => {
      const t = parseTimestamp(e.timestamp)
      return t >= start && t < end
    })
    const last = new Date(end)
    last.setDate(end.getDate() - 1)
    result.push({
      label: `${shortDate(start)}–${shortDate(last)}`,
      studyMinutes: splitSessions(inWeek).reduce((a, s) => a + s.studyMinutes, 0),
      reminders: inWeek.filter(isReminder).length,
      ai: inWeek.filter(isAi).length,
    })
  }
  return result
}

export interface Session {
  start: Date
  end: Date
  events: RobotEvent[] // cũ → mới
  studyMinutes: number
  reminders: number
  ai: number
}

/**
 * Chia sự kiện thành phiên học: 2 sự kiện cách nhau > gapMinutes → phiên mới.
 * (Tạm thời cho tới khi BE có API phiên học.)
 */
export function splitSessions(events: RobotEvent[], gapMinutes = 30): Session[] {
  const sorted = [...events].sort(
    (a, b) => parseTimestamp(a.timestamp).getTime() - parseTimestamp(b.timestamp).getTime(),
  )
  const sessions: Session[] = []
  let cur: RobotEvent[] = []
  const flush = () => {
    if (!cur.length) return
    const start = parseTimestamp(cur[0].timestamp)
    const end = parseTimestamp(cur[cur.length - 1].timestamp)
    // Thời lượng phiên = từ sự kiện đầu → cuối; nếu ngắn hơn tổng phút backend ghi
    // (mỗi câu hỏi AI = 5 phút) thì lấy số lớn hơn. Tối thiểu 1 phút.
    const span = Math.round((end.getTime() - start.getTime()) / 60_000)
    sessions.push({
      start,
      end,
      events: cur,
      studyMinutes: Math.max(1, span, cur.reduce((s, e) => s + e.duration_minutes, 0)),
      reminders: cur.filter(isReminder).length,
      ai: cur.filter(isAi).length,
    })
    cur = []
  }
  for (const e of sorted) {
    const t = parseTimestamp(e.timestamp).getTime()
    const prev = cur.length ? parseTimestamp(cur[cur.length - 1].timestamp).getTime() : t
    if (t - prev > gapMinutes * 60_000) flush()
    cur.push(e)
  }
  flush()
  return sessions.reverse() // phiên mới nhất trước
}

/** Tách "Hỏi: ... ➔ Đáp: ..." của sự kiện AI */
export function splitQA(detail: string): { q: string; a: string } {
  const m = detail.match(/^Hỏi:\s*(.*?)\s*➔\s*Đáp:\s*(.*)$/s)
  return m ? { q: m[1], a: m[2] } : { q: detail, a: '' }
}

export function hhmm(d: Date): string {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
