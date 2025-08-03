import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Types
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

export interface Modal {
  id: string
  type: 'confirm' | 'alert' | 'custom'
  title: string
  content?: string
  component?: string
  props?: Record<string, any>
  onConfirm?: () => void
  onCancel?: () => void
  confirmText?: string
  cancelText?: string
  isDismissible?: boolean
}

export interface Sidebar {
  isOpen: boolean
  activeSection: 'library' | 'reading' | 'bookmarks' | 'notes' | 'settings' | null
}

export interface SearchState {
  isOpen: boolean
  query: string
  filters: {
    category?: string
    author?: string
    language?: string
    format?: string
    priceRange?: [number, number]
    rating?: number
  }
  recentSearches: string[]
}

export interface ViewPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: 'fr' | 'en' | 'wo' | 'ar'
  currency: 'XOF' | 'EUR' | 'USD'
  timezone: string
  dateFormat: 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD'
  numberFormat: 'french' | 'english'
}

export interface Layout {
  headerHeight: number
  sidebarWidth: number
  isCompact: boolean
  showBreadcrumbs: boolean
}

export interface NetworkStatus {
  isOnline: boolean
  connectionType: 'wifi' | 'cellular' | 'ethernet' | 'unknown'
  effectiveType: 'slow-2g' | '2g' | '3g' | '4g' | 'unknown'
  downlink: number
  rtt: number
  saveData: boolean
}

interface UIState {
  // Global loading
  isGlobalLoading: boolean
  globalLoadingMessage: string | undefined
  
  // Toasts
  toasts: Toast[]
  
  // Modals
  modals: Modal[]
  
  // Sidebar
  sidebar: Sidebar
  
  // Search
  search: SearchState
  
  // View preferences
  preferences: ViewPreferences
  
  // Layout
  layout: Layout
  
  // Network status
  network: NetworkStatus
  
  // Mobile specific
  isMobile: boolean
  orientation: 'portrait' | 'landscape'
  
  // Offline mode
  isOfflineMode: boolean
  offlineQueueCount: number
  
  // Performance
  performanceMode: 'auto' | 'optimized' | 'full'
  
  // Accessibility
  accessibility: {
    reduceMotion: boolean
    highContrast: boolean
    fontSize: 'small' | 'medium' | 'large' | 'xl'
    screenReader: boolean
  }
  
  // Debug mode (development only)
  debugMode: boolean
}

// Initial state
const initialState: UIState = {
  isGlobalLoading: false,
  globalLoadingMessage: undefined,
  toasts: [],
  modals: [],
  sidebar: {
    isOpen: false,
    activeSection: null
  },
  search: {
    isOpen: false,
    query: '',
    filters: {},
    recentSearches: []
  },
  preferences: {
    theme: 'auto',
    language: 'fr',
    currency: 'XOF',
    timezone: 'Africa/Dakar',
    dateFormat: 'DD/MM/YYYY',
    numberFormat: 'french'
  },
  layout: {
    headerHeight: 64,
    sidebarWidth: 280,
    isCompact: false,
    showBreadcrumbs: true
  },
  network: {
    isOnline: true,
    connectionType: 'unknown',
    effectiveType: 'unknown',
    downlink: 0,
    rtt: 0,
    saveData: false
  },
  isMobile: false,
  orientation: 'portrait',
  isOfflineMode: false,
  offlineQueueCount: 0,
  performanceMode: 'auto',
  accessibility: {
    reduceMotion: false,
    highContrast: false,
    fontSize: 'medium',
    screenReader: false
  },
  debugMode: false
}

// UI slice
const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Global loading
    setGlobalLoading: (state, action: PayloadAction<{ isLoading: boolean; message?: string }>) => {
      state.isGlobalLoading = action.payload.isLoading
      state.globalLoadingMessage = action.payload.message || undefined
    },
    
    // Toast management
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const toast: Toast = {
        ...action.payload,
        id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }
      state.toasts.push(toast)
      
      // Limit to 5 toasts
      if (state.toasts.length > 5) {
        state.toasts = state.toasts.slice(-5)
      }
    },
    
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload)
    },
    
    clearToasts: (state) => {
      state.toasts = []
    },
    
    // Modal management
    openModal: (state, action: PayloadAction<Omit<Modal, 'id'>>) => {
      const modal: Modal = {
        ...action.payload,
        id: `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      }
      state.modals.push(modal)
    },
    
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter(modal => modal.id !== action.payload)
    },
    
    closeTopModal: (state) => {
      if (state.modals.length > 0) {
        state.modals.pop()
      }
    },
    
    clearModals: (state) => {
      state.modals = []
    },
    
    // Sidebar management
    toggleSidebar: (state) => {
      state.sidebar.isOpen = !state.sidebar.isOpen
    },
    
    openSidebar: (state, action: PayloadAction<Sidebar['activeSection']>) => {
      state.sidebar.isOpen = true
      state.sidebar.activeSection = action.payload
    },
    
    closeSidebar: (state) => {
      state.sidebar.isOpen = false
      state.sidebar.activeSection = null
    },
    
    setSidebarSection: (state, action: PayloadAction<Sidebar['activeSection']>) => {
      state.sidebar.activeSection = action.payload
    },
    
    // Search management
    openSearch: (state) => {
      state.search.isOpen = true
    },
    
    closeSearch: (state) => {
      state.search.isOpen = false
      state.search.query = ''
    },
    
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.search.query = action.payload
    },
    
    setSearchFilters: (state, action: PayloadAction<SearchState['filters']>) => {
      state.search.filters = { ...state.search.filters, ...action.payload }
    },
    
    clearSearchFilters: (state) => {
      state.search.filters = {}
    },
    
    addRecentSearch: (state, action: PayloadAction<string>) => {
      const query = action.payload.trim()
      if (query && !state.search.recentSearches.includes(query)) {
        state.search.recentSearches.unshift(query)
        // Keep only last 10 searches
        if (state.search.recentSearches.length > 10) {
          state.search.recentSearches = state.search.recentSearches.slice(0, 10)
        }
      }
    },
    
    clearRecentSearches: (state) => {
      state.search.recentSearches = []
    },
    
    // Preferences
    updatePreferences: (state, action: PayloadAction<Partial<ViewPreferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload }
    },
    
    setTheme: (state, action: PayloadAction<ViewPreferences['theme']>) => {
      state.preferences.theme = action.payload
    },
    
    setLanguage: (state, action: PayloadAction<ViewPreferences['language']>) => {
      state.preferences.language = action.payload
    },
    
    setCurrency: (state, action: PayloadAction<ViewPreferences['currency']>) => {
      state.preferences.currency = action.payload
    },
    
    // Layout
    updateLayout: (state, action: PayloadAction<Partial<Layout>>) => {
      state.layout = { ...state.layout, ...action.payload }
    },
    
    toggleCompactMode: (state) => {
      state.layout.isCompact = !state.layout.isCompact
    },
    
    // Network status
    updateNetworkStatus: (state, action: PayloadAction<Partial<NetworkStatus>>) => {
      state.network = { ...state.network, ...action.payload }
    },
    
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.network.isOnline = action.payload
    },
    
    // Mobile and orientation
    setMobileStatus: (state, action: PayloadAction<boolean>) => {
      state.isMobile = action.payload
    },
    
    setOrientation: (state, action: PayloadAction<'portrait' | 'landscape'>) => {
      state.orientation = action.payload
    },
    
    // Offline mode
    setOfflineMode: (state, action: PayloadAction<boolean>) => {
      state.isOfflineMode = action.payload
    },
    
    updateOfflineQueue: (state, action: PayloadAction<number>) => {
      state.offlineQueueCount = action.payload
    },
    
    // Performance mode
    setPerformanceMode: (state, action: PayloadAction<UIState['performanceMode']>) => {
      state.performanceMode = action.payload
    },
    
    // Accessibility
    updateAccessibility: (state, action: PayloadAction<Partial<UIState['accessibility']>>) => {
      state.accessibility = { ...state.accessibility, ...action.payload }
    },
    
    toggleReduceMotion: (state) => {
      state.accessibility.reduceMotion = !state.accessibility.reduceMotion
    },
    
    toggleHighContrast: (state) => {
      state.accessibility.highContrast = !state.accessibility.highContrast
    },
    
    setFontSize: (state, action: PayloadAction<UIState['accessibility']['fontSize']>) => {
      state.accessibility.fontSize = action.payload
    },
    
    // Debug mode
    toggleDebugMode: (state) => {
      state.debugMode = !state.debugMode
    },
    
    // Utility actions
    resetUI: (state) => {
      // Reset to initial state but keep preferences and accessibility settings
      const { preferences, accessibility } = state
      Object.assign(state, {
        ...initialState,
        preferences,
        accessibility
      })
    }
  }
})

// Export actions
export const {
  setGlobalLoading,
  addToast,
  removeToast,
  clearToasts,
  openModal,
  closeModal,
  closeTopModal,
  clearModals,
  toggleSidebar,
  openSidebar,
  closeSidebar,
  setSidebarSection,
  openSearch,
  closeSearch,
  setSearchQuery,
  setSearchFilters,
  clearSearchFilters,
  addRecentSearch,
  clearRecentSearches,
  updatePreferences,
  setTheme,
  setLanguage,
  setCurrency,
  updateLayout,
  toggleCompactMode,
  updateNetworkStatus,
  setOnlineStatus,
  setMobileStatus,
  setOrientation,
  setOfflineMode,
  updateOfflineQueue,
  setPerformanceMode,
  updateAccessibility,
  toggleReduceMotion,
  toggleHighContrast,
  setFontSize,
  toggleDebugMode,
  resetUI
} = uiSlice.actions

// Selectors
export const selectUI = (state: { ui: UIState }) => state.ui
export const selectIsGlobalLoading = (state: { ui: UIState }) => state.ui.isGlobalLoading
export const selectGlobalLoadingMessage = (state: { ui: UIState }) => state.ui.globalLoadingMessage
export const selectToasts = (state: { ui: UIState }) => state.ui.toasts
export const selectModals = (state: { ui: UIState }) => state.ui.modals
export const selectTopModal = (state: { ui: UIState }) => 
  state.ui.modals.length > 0 ? state.ui.modals[state.ui.modals.length - 1] : null
export const selectSidebar = (state: { ui: UIState }) => state.ui.sidebar
export const selectSearch = (state: { ui: UIState }) => state.ui.search
export const selectPreferences = (state: { ui: UIState }) => state.ui.preferences
export const selectTheme = (state: { ui: UIState }) => state.ui.preferences.theme
export const selectLanguage = (state: { ui: UIState }) => state.ui.preferences.language
export const selectCurrency = (state: { ui: UIState }) => state.ui.preferences.currency
export const selectLayout = (state: { ui: UIState }) => state.ui.layout
export const selectNetworkStatus = (state: { ui: UIState }) => state.ui.network
export const selectIsOnline = (state: { ui: UIState }) => state.ui.network.isOnline
export const selectIsMobile = (state: { ui: UIState }) => state.ui.isMobile
export const selectOrientation = (state: { ui: UIState }) => state.ui.orientation
export const selectIsOfflineMode = (state: { ui: UIState }) => state.ui.isOfflineMode
export const selectOfflineQueueCount = (state: { ui: UIState }) => state.ui.offlineQueueCount
export const selectPerformanceMode = (state: { ui: UIState }) => state.ui.performanceMode
export const selectAccessibility = (state: { ui: UIState }) => state.ui.accessibility
export const selectDebugMode = (state: { ui: UIState }) => state.ui.debugMode

// Export reducer
export default uiSlice.reducer