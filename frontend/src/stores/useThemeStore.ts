import { create } from 'zustand'

type ThemeMode = 'light' | 'dark' | 'system'

interface ThemeStore {
  mode: ThemeMode
  isDark: boolean
  setMode: (mode: ThemeMode) => void
}

function getSystemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyThemeToDOM(isDark: boolean) {
  const html = document.documentElement
  if (isDark) {
    html.classList.add('dark')
    html.setAttribute('data-theme', 'dark')
    html.style.colorScheme = 'dark'
  } else {
    html.classList.remove('dark')
    html.setAttribute('data-theme', 'light')
    html.style.colorScheme = 'light'
  }
  // Force browser style recalculation
  void html.offsetHeight
}

function resolveIsDark(mode: ThemeMode): boolean {
  if (mode === 'system') return getSystemDark()
  return mode === 'dark'
}

const stored = (localStorage.getItem('stock_analysis_theme') as ThemeMode) || 'light'
const initialIsDark = resolveIsDark(stored)
applyThemeToDOM(initialIsDark)

export const useThemeStore = create<ThemeStore>((set) => ({
  mode: stored,
  isDark: initialIsDark,
  setMode: (mode) => {
    const isDark = resolveIsDark(mode)
    localStorage.setItem('stock_analysis_theme', mode)
    applyThemeToDOM(isDark)
    set({ mode, isDark })
  },
}))

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  const state = useThemeStore.getState()
  if (state.mode === 'system') {
    const isDark = getSystemDark()
    applyThemeToDOM(isDark)
    useThemeStore.setState({ isDark })
  }
})
