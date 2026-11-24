<script setup lang="ts">
// Danh sách bài học đã nạp (tuần 4 — "danh sách bài").
import { BookOpen, Paperclip, Plus, Trash2 } from 'lucide-vue-next'
import { useLessons } from '@/stores/robot'
import { openLessonDialog } from '@/stores/ui'

const { lessons, remove } = useLessons()
const fmt = (d: string) => d.split('-').reverse().join('/')
</script>

<template>
  <div class="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Nội dung bài học</h1>
        <p class="mt-1 text-sm text-slate-500">Bài đã gửi cho robot của các em · {{ lessons.length }} bài</p>
      </div>
      <button
        class="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-brand-500 to-brand-700 px-3 py-2 text-sm font-semibold text-white hover:opacity-90"
        @click="openLessonDialog()"
      >
        <Plus class="size-4" /> Nạp bài học
      </button>
    </div>

    <p class="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
      Bài học tạm lưu trên trình duyệt này — sẽ đồng bộ khi nhóm BE có API bài học.
    </p>

    <div v-if="!lessons.length" class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <BookOpen class="mx-auto size-8 text-slate-300" />
      <p class="mt-3 font-medium">Chưa có bài học nào</p>
      <p class="mt-1 text-sm text-slate-500">Bấm “Nạp bài học” để gửi bài đầu tiên cho các em.</p>
    </div>

    <div class="mt-5 grid gap-4 md:grid-cols-2">
      <article v-for="l in lessons" :key="l.id" class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <span class="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">{{ l.subject }}</span>
            <h2 class="mt-2 font-semibold">{{ l.summary }}</h2>
            <p class="mt-0.5 text-xs text-slate-500">
              {{ fmt(l.date) }} · {{ l.sendTo === 'class' ? 'Lớp 5A' : 'Tất cả học sinh' }} · {{ l.received }} em đã nhận
            </p>
          </div>
          <button class="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-500" title="Xoá bài" @click="remove(l.id)">
            <Trash2 class="size-4" />
          </button>
        </div>
        <div v-if="l.keyPoints.length" class="mt-3">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">Ý chính</p>
          <ul class="mt-1 list-disc space-y-0.5 pl-5 text-sm text-slate-700">
            <li v-for="k in l.keyPoints" :key="k">{{ k }}</li>
          </ul>
        </div>
        <div v-if="l.questions.length" class="mt-3">
          <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">Câu hỏi ôn ở nhà</p>
          <ul class="mt-1 space-y-0.5 text-sm text-slate-700">
            <li v-for="q in l.questions" :key="q">• {{ q }}</li>
          </ul>
        </div>
        <p v-if="l.attachment" class="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
          <Paperclip class="size-3.5" /> {{ l.attachment }}
        </p>
      </article>
    </div>
  </div>
</template>
