<script setup lang="ts">
// Hộp thoại "Nạp bài học" — theo ảnh mẫu.
import { computed, onMounted, onUnmounted, reactive, watch } from 'vue'
import { BookOpen, Paperclip, Send, Users } from 'lucide-vue-next'
import { STUDENTS } from '@/data/mock'
import { useLessons } from '@/stores/robot'
import { ui } from '@/stores/ui'

const { add } = useLessons()

const today = () => new Date().toISOString().slice(0, 10)

const form = reactive({
  sendTo: 'class' as 'class' | 'all',
  date: today(),
  subject: 'Toán',
  summary: '',
  keyPoints: '',
  questions: '',
})
const errors = reactive({ summary: '' })

const lines = (s: string) => s.split('\n').map((l) => l.trim()).filter(Boolean)
const canSubmit = computed(() => form.summary.trim().length > 0)

// Mỗi lần mở: làm trống form; nếu có file kéo thả thì lấy tên file làm gợi ý tóm tắt
watch(
  () => ui.lessonDialogOpen,
  (open) => {
    if (!open) return
    Object.assign(form, { sendTo: 'class', date: today(), subject: 'Toán', summary: '', keyPoints: '', questions: '' })
    errors.summary = ''
    if (ui.lessonAttachment) form.summary = ui.lessonAttachment.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ')
  },
)

function close() {
  ui.lessonDialogOpen = false
  ui.lessonAttachment = ''
}

// Nhấn Esc để đóng
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && ui.lessonDialogOpen) close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))

function submit() {
  if (!canSubmit.value) {
    errors.summary = 'Cô/thầy nhập tóm tắt bài học nhé'
    return
  }
  add({
    sendTo: form.sendTo,
    date: form.date,
    subject: form.subject.trim() || 'Khác',
    summary: form.summary.trim(),
    keyPoints: lines(form.keyPoints),
    questions: lines(form.questions),
    attachment: ui.lessonAttachment || undefined,
  })
  close()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="ui.lessonDialogOpen"
      class="fixed inset-0 z-[60] grid place-items-center bg-slate-900/50 p-4"
      @click.self="close"
    >
      <form
        class="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
        role="dialog"
        aria-labelledby="lesson-title"
        @submit.prevent="submit"
      >
        <h2 id="lesson-title" class="flex items-center gap-2 text-lg font-semibold">
          <BookOpen class="size-5 text-brand-600" /> Nạp bài học
        </h2>

        <p class="mt-4 text-xs font-medium text-slate-500">Gửi cho</p>
        <div class="mt-1.5 flex flex-wrap gap-2">
          <button
            type="button"
            :class="form.sendTo === 'class' ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-600'"
            class="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm"
            @click="form.sendTo = 'class'"
          >
            <Users class="size-4" /> Lớp 5A ({{ STUDENTS.length }})
          </button>
          <button
            type="button"
            :class="form.sendTo === 'all' ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-slate-200 text-slate-600'"
            class="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm"
            @click="form.sendTo = 'all'"
          >
            <Users class="size-4" /> Tất cả học sinh của tôi ({{ STUDENTS.length }})
          </button>
        </div>

        <div v-if="ui.lessonAttachment" class="mt-4 flex items-start gap-2 rounded-lg bg-brand-50 px-3 py-2 text-xs text-brand-700">
          <Paperclip class="mt-0.5 size-3.5 shrink-0" />
          <span>
            Đã đính kèm <b>{{ ui.lessonAttachment }}</b>. Robot tự đọc slide sẽ có khi backend hỗ trợ — hiện cô/thầy điền
            nội dung bên dưới nhé.
          </span>
        </div>

        <div class="mt-4 grid grid-cols-2 gap-3">
          <label class="text-xs font-medium text-slate-500">
            Ngày
            <input v-model="form.date" type="date" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900" />
          </label>
          <label class="text-xs font-medium text-slate-500">
            Môn
            <input v-model="form.subject" list="subjects" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900" />
            <datalist id="subjects">
              <option value="Toán" /><option value="Tiếng Việt" /><option value="Tiếng Anh" /><option value="Khoa học" />
            </datalist>
          </label>
        </div>

        <label class="mt-3 block text-xs font-medium text-slate-500">
          Tóm tắt bài học
          <input
            v-model="form.summary"
            placeholder="VD: Cộng hai phân số khác mẫu số"
            :class="errors.summary ? 'border-rose-400' : 'border-slate-200'"
            class="mt-1 w-full rounded-lg border px-3 py-2 text-sm text-slate-900"
            @input="errors.summary = ''"
          />
          <span v-if="errors.summary" class="mt-1 block text-rose-500">{{ errors.summary }}</span>
        </label>

        <label class="mt-3 block text-xs font-medium text-slate-500">
          Ý chính (mỗi dòng một ý)
          <textarea
            v-model="form.keyPoints"
            rows="3"
            placeholder="Quy đồng mẫu số hai phân số&#10;Cộng các tử số, giữ nguyên mẫu số chung"
            class="mt-1 w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900"
          />
        </label>

        <label class="mt-3 block text-xs font-medium text-slate-500">
          Câu hỏi ôn ở nhà (mỗi dòng một câu)
          <textarea
            v-model="form.questions"
            rows="3"
            placeholder="21/7 + 21/8 = ?&#10;2/3 + 1/4 = ?"
            class="mt-1 w-full resize-y rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900"
          />
        </label>

        <div class="mt-5 grid grid-cols-[1fr_2fr] gap-3">
          <button type="button" class="rounded-lg border border-slate-200 py-2.5 text-sm font-medium hover:bg-slate-50" @click="close">
            Huỷ
          </button>
          <button
            type="submit"
            class="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-brand-500 to-brand-700 py-2.5 text-sm font-semibold text-white hover:opacity-90"
          >
            <Send class="size-4" /> Gửi cho các em
          </button>
        </div>
      </form>
    </div>
  </Teleport>
</template>
