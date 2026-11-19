// Trạng thái dùng chung: sự kiện thật từ robot + danh sách bài học đã nạp.
import { reactive, readonly } from 'vue'
import { fetchEvents, type RobotEvent } from '@/api/events'
import { mockEventsFor, type Student } from '@/data/mock'

// ── Sự kiện từ robot (GET /events), tự làm mới mỗi 5 giây ────────────────────
const state = reactive({
  events: [] as RobotEvent[],
  online: false, // backend có phản hồi không
  loaded: false,
  lastUpdated: null as Date | null,
})

let timer: number | undefined

async function refresh() {
  try {
    const data = await fetchEvents()
    state.events = data.events
    state.online = true
    state.lastUpdated = new Date()
  } catch {
    state.online = false
  } finally {
    state.loaded = true
  }
}

export function useRobotEvents() {
  if (timer === undefined) {
    refresh()
    timer = window.setInterval(refresh, 5000)
  }
  return { state: readonly(state), refresh }
}

/** Robot coi là online nếu backend phản hồi và có sự kiện trong 10 phút gần đây */
export function isRobotOnline(): boolean {
  if (!state.online || !state.events.length) return false
  const latest = new Date(state.events[0].timestamp.replace(' ', 'T')).getTime()
  return Date.now() - latest < 10 * 60_000
}

/**
 * Sự kiện của 1 học sinh: học sinh gắn robot thật + backend online → dữ liệu thật,
 * ngược lại → dữ liệu mẫu.
 */
export function eventsForStudent(student: Student): { events: RobotEvent[]; isReal: boolean } {
  if (student.linkedToRobot && state.online) return { events: state.events as RobotEvent[], isReal: true }
  return { events: mockEventsFor(student), isReal: false }
}

// ── Bài học đã nạp (tạm lưu trên trình duyệt, chưa có API bài học) ───────────
export interface Lesson {
  id: string
  sendTo: 'class' | 'all'
  date: string // yyyy-mm-dd
  subject: string
  summary: string
  keyPoints: string[]
  questions: string[]
  attachment?: string
  createdAt: string
  received: number // số em đã nhận
}

const LESSON_KEY = 'robothoctap.lessons'

function loadLessons(): Lesson[] {
  try {
    return JSON.parse(localStorage.getItem(LESSON_KEY) || '[]')
  } catch {
    return []
  }
}

const lessons = reactive<Lesson[]>(loadLessons())

function persist() {
  try {
    localStorage.setItem(LESSON_KEY, JSON.stringify(lessons))
  } catch {
    /* trình duyệt chặn lưu trữ → chỉ giữ trong phiên */
  }
}

export function useLessons() {
  return {
    lessons: readonly(lessons),
    add(lesson: Omit<Lesson, 'id' | 'createdAt' | 'received'>) {
      lessons.unshift({
        ...lesson,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        received: 1,
      })
      persist()
    },
    remove(id: string) {
      const i = lessons.findIndex((l) => l.id === id)
      if (i >= 0) lessons.splice(i, 1)
      persist()
    },
  }
}
