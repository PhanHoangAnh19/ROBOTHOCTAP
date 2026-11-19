// Đăng ký các thành phần Chart.js dùng trong dự án (1 lần).
import {
  BarElement, CategoryScale, Chart, Filler, Legend, LinearScale, LineElement, PointElement, Tooltip,
} from 'chart.js'

Chart.register(BarElement, CategoryScale, LinearScale, LineElement, PointElement, Filler, Legend, Tooltip)
Chart.defaults.font.family = 'Inter, "Segoe UI", system-ui, sans-serif'
Chart.defaults.color = '#64748b'

export const gridColor = '#eef2f7'
