<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BookOpen, Bot, ClipboardList, LayoutDashboard, Menu, Users, X } from 'lucide-vue-next'
import { STUDENTS, needsAttention } from '@/data/mock'
import { ui } from '@/stores/ui'
import { useRobotEvents } from '@/stores/robot'
import LessonDialog from '@/components/LessonDialog.vue'

const route = useRoute()
const { state } = useRobotEvents()

const attentionCount = computed(() => STUDENTS.filter(needsAttention).length)
const pendingHomework = computed(() => STUDENTS.filter((s) => s.homeworkDone < s.homeworkTotal).length)

const nav = computed(() => [
  { to: '/', label: 'Tổng quan lớp', icon: LayoutDashboard },
  { to: '/hoc-sinh', label: 'Học sinh', icon: Users, badge: attentionCount.value },
  { to: '/bai-hoc', label: 'Nội dung bài học', icon: BookOpen },
  { to: '/bai-tap', label: 'Bài tập', icon: ClipboardList, badge: pendingHomework.value },
  { to: '/ai-chi-phi', label: 'AI & Chi phí', icon: Bot },
])

function isActive(to: string) {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

// Đóng menu điện thoại khi chuyển trang
watch(() => route.fullPath, () => (ui.sidebarOpen = false))
</script>

<template>
  <div class="min-h-screen lg:flex">
    <!-- Thanh trên cùng cho điện thoại -->
    <header class="sticky top-0 z-30 flex items-center justify-between bg-sidebar px-4 py-3 text-white lg:hidden">
      <span class="font-semibold">Trợ lý học tập</span>
      <button class="rounded-lg p-1.5 hover:bg-sidebar-hover" aria-label="Mở menu" @click="ui.sidebarOpen = true">
        <Menu class="size-5" />
      </button>
    </header>

    <!-- Lớp phủ khi mở menu trên điện thoại -->
    <div v-if="ui.sidebarOpen" class="fixed inset-0 z-40 bg-black/40 lg:hidden" @click="ui.sidebarOpen = false" />

    <aside
      :class="ui.sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      class="fixed inset-y-0 left-0 z-50 flex w-60 flex-col bg-sidebar text-slate-300 transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0"
    >
      <div class="flex items-center justify-between px-5 py-5">
        <span class="text-base font-semibold text-white">Trợ lý học tập</span>
        <button class="rounded p-1 hover:bg-sidebar-hover lg:hidden" aria-label="Đóng menu" @click="ui.sidebarOpen = false">
          <X class="size-4" />
        </button>
      </div>

      <nav class="space-y-0.5 px-3">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="isActive(item.to) ? 'bg-sidebar-hover text-white' : 'hover:bg-sidebar-hover hover:text-white'"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm"
        >
          <component :is="item.icon" class="size-4" />
          <span class="flex-1">{{ item.label }}</span>
          <span v-if="item.badge" class="grid size-5 place-items-center rounded-full bg-rose-500 text-[11px] font-semibold text-white">
            {{ item.badge }}
          </span>
        </RouterLink>
      </nav>

      <p class="mt-6 px-6 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Của tôi</p>
      <div class="mt-2 space-y-0.5 px-3 text-sm">
        <button
          :class="ui.classFilter === 'all' ? 'bg-sidebar-hover text-white' : 'hover:bg-sidebar-hover'"
          class="flex w-full items-center justify-between rounded-lg px-3 py-2"
          @click="ui.classFilter = 'all'"
        >
          <span>Tất cả</span><span class="text-xs text-slate-500">{{ STUDENTS.length }}</span>
        </button>
        <button
          :class="ui.classFilter === '5A' ? 'bg-sidebar-hover text-white' : 'hover:bg-sidebar-hover'"
          class="flex w-full items-center justify-between rounded-lg px-3 py-2"
          @click="ui.classFilter = '5A'"
        >
          <span>Lớp 5A</span><span class="text-xs text-slate-500">{{ STUDENTS.length }} em</span>
        </button>
      </div>

      <!-- Trạng thái kết nối backend -->
      <div class="mt-auto border-t border-white/10 px-5 py-4 text-xs">
        <div class="flex items-center gap-2">
          <span :class="state.online ? 'bg-emerald-400' : 'bg-slate-500'" class="size-2 rounded-full" />
          <span>{{ state.online ? 'Đã kết nối backend' : 'Chưa kết nối backend' }}</span>
        </div>
        <p v-if="!state.online && state.loaded" class="mt-1 text-slate-500">Đang hiển thị dữ liệu mẫu</p>
      </div>
    </aside>

    <main class="min-w-0 flex-1">
      <slot />
    </main>

    <LessonDialog />
  </div>
</template>
