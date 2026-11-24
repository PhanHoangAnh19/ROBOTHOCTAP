// Trạng thái giao diện dùng chung: hộp thoại "Nạp bài học", bộ lọc lớp.
import { reactive } from 'vue'

export const ui = reactive({
  lessonDialogOpen: false,
  lessonAttachment: '' as string, // tên file kéo thả vào
  classFilter: 'all' as 'all' | '5A',
  sidebarOpen: false, // menu trên điện thoại
})

export function openLessonDialog(attachment = '') {
  ui.lessonAttachment = attachment
  ui.lessonDialogOpen = true
}
