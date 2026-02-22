import { useThemeStore } from '@/stores/useThemeStore'

export function useChartTheme() {
  const isDark = useThemeStore((s) => s.isDark)

  return isDark
    ? {
        gridColor: '#374151',
        textColor: '#9ca3af',
        tooltipBg: '#1f2937',
        tooltipBorder: '#374151',
        priceStroke: '#d1d5db',
      }
    : {
        gridColor: '#f0f0f0',
        textColor: '#6b7280',
        tooltipBg: '#ffffff',
        tooltipBorder: '#e5e7eb',
        priceStroke: '#374151',
      }
}
