// Kết nối Backend FastAPI của nhóm BE (xem be/README.md — "Hợp đồng API tương thích").
// Vite proxy chuyển /events, /sensor-event, /ask-ai sang http://127.0.0.1:8000.

export type EventType =
  | 'TU_THE_CO'
  | 'TU_THE_VAI'
  | 'KHOANG_CACH_MAT'
  | 'MAT_TAP_TRUNG'
  | 'GIAI_TOAN'
  | 'DAY_HOC'
  | 'THAC_MAC'
  | (string & {})

export interface RobotEvent {
  id: number
  timestamp: string // "YYYY-MM-DD HH:MM:SS"
  event_type: EventType
  category_name: string
  detail: string
  duration_minutes: number
}

export interface EventsResponse {
  summary: {
    total_study_minutes: number
    posture_warnings: number
    attention_warnings: number
    ai_interactions: number
  }
  events: RobotEvent[]
}

export const POSTURE_TYPES = ['TU_THE_CO', 'TU_THE_VAI', 'KHOANG_CACH_MAT']
export const ATTENTION_TYPES = ['MAT_TAP_TRUNG']
export const AI_TYPES = ['GIAI_TOAN', 'DAY_HOC', 'THAC_MAC']

export async function fetchEvents(signal?: AbortSignal): Promise<EventsResponse> {
  const res = await fetch('/events', { signal })
  if (!res.ok) throw new Error(`GET /events → HTTP ${res.status}`)
  return res.json()
}

/** "2026-11-16 10:24:34" → Date (giờ địa phương) */
export function parseTimestamp(ts: string): Date {
  return new Date(ts.replace(' ', 'T'))
}
