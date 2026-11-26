import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: () => import('@/views/OverviewView.vue') },
    { path: '/hoc-sinh', name: 'students', component: () => import('@/views/StudentsView.vue') },
    { path: '/hoc-sinh/:id', name: 'student', component: () => import('@/views/StudentDetailView.vue'), props: true },
    { path: '/bai-hoc', name: 'lessons', component: () => import('@/views/LessonsView.vue') },
    { path: '/bai-tap', name: 'homework', component: () => import('@/views/HomeworkView.vue') },
    { path: '/ai-chi-phi', name: 'ai-cost', component: () => import('@/views/AiLogView.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
