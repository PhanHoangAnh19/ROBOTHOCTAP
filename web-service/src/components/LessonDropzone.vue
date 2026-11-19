<script setup lang="ts">
// Ô kéo thả slide / ảnh bài học → mở hộp thoại Nạp bài học.
import { ref } from 'vue'
import { Pencil, Upload } from 'lucide-vue-next'
import { openLessonDialog } from '@/stores/ui'

const dragging = ref(false)
const input = ref<HTMLInputElement>()

// Chỉ lấy TÊN file — không đọc, không lưu nội dung ảnh (nguyên tắc 0 byte ảnh)
function pick(files: FileList | null | undefined) {
  const f = files?.[0]
  if (f) openLessonDialog(f.name)
}
</script>

<template>
  <div>
    <button
      type="button"
      :class="dragging ? 'border-brand-500 bg-brand-50' : 'border-brand-200 bg-brand-50/40'"
      class="flex w-full flex-col items-center rounded-xl border-2 border-dashed px-4 py-6 text-center transition"
      @click="input?.click()"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="dragging = false; pick($event.dataTransfer?.files)"
    >
      <Upload class="size-5 text-brand-600" />
      <span class="mt-2 text-sm font-semibold text-brand-700">Kéo slide / ảnh bài học vào đây</span>
      <span class="mt-1 text-xs text-slate-500">hoặc bấm để chọn file, rồi điền tóm tắt và câu hỏi ôn trước khi gửi</span>
    </button>
    <input ref="input" type="file" accept=".pdf,.ppt,.pptx,image/*" class="hidden" @change="pick(($event.target as HTMLInputElement).files)" />
    <button type="button" class="mx-auto mt-2 flex items-center gap-1.5 text-sm text-brand-600 hover:underline" @click="openLessonDialog()">
      <Pencil class="size-3.5" /> Hoặc nhập tay
    </button>
  </div>
</template>
