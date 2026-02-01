import { create } from 'zustand'
import type { StockFilter, SortOption } from '@/types'

interface StockStore {
  // Filter state
  filter: StockFilter
  setFilter: (filter: Partial<StockFilter>) => void
  resetFilter: () => void

  // Sort state
  sort: SortOption
  setSort: (sort: SortOption) => void

  // Search state
  searchQuery: string
  setSearchQuery: (query: string) => void

  // Pagination
  page: number
  pageSize: number
  setPage: (page: number) => void
  setPageSize: (size: number) => void

  // Selected stocks for comparison
  selectedStocks: string[]
  toggleStock: (code: string) => void
  clearSelection: () => void
}

const defaultFilter: StockFilter = {
  sector: undefined,
  minScore: undefined,
  maxScore: undefined,
  grades: undefined,
  excludeLoss: false,
  market: 'all',
}

const defaultSort: SortOption = {
  field: 'totalScore',
  direction: 'desc',
}

export const useStockStore = create<StockStore>((set) => ({
  // Filter
  filter: defaultFilter,
  setFilter: (newFilter) =>
    set((state) => ({
      filter: { ...state.filter, ...newFilter },
      page: 1, // Reset page on filter change
    })),
  resetFilter: () => set({ filter: defaultFilter, page: 1 }),

  // Sort
  sort: defaultSort,
  setSort: (sort) => set({ sort, page: 1 }),

  // Search
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query, page: 1 }),

  // Pagination
  page: 1,
  pageSize: 20,
  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),

  // Selection
  selectedStocks: [],
  toggleStock: (code) =>
    set((state) => {
      const isSelected = state.selectedStocks.includes(code)
      if (isSelected) {
        return { selectedStocks: state.selectedStocks.filter((c) => c !== code) }
      }
      if (state.selectedStocks.length >= 5) {
        return state // Max 5 stocks for comparison
      }
      return { selectedStocks: [...state.selectedStocks, code] }
    }),
  clearSelection: () => set({ selectedStocks: [] }),
}))

// Selectors
export const selectFilter = (state: StockStore) => state.filter
export const selectSort = (state: StockStore) => state.sort
export const selectPagination = (state: StockStore) => ({
  page: state.page,
  pageSize: state.pageSize,
})
