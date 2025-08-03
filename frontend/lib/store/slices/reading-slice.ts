import { createSlice, PayloadAction } from '@reduxjs/toolkit'

// Types
export interface ReadingProgress {
  bookId: string
  currentPage: number
  totalPages: number
  percentage: number
  lastReadAt: string
  timeSpent: number // in minutes
  bookmarks: Bookmark[]
  highlights: Highlight[]
  notes: Note[]
}

export interface Bookmark {
  id: string
  bookId: string
  page: number
  position?: string
  title?: string
  createdAt: string
}

export interface Highlight {
  id: string
  bookId: string
  page: number
  startPosition: string
  endPosition: string
  text: string
  color: 'yellow' | 'green' | 'blue' | 'pink' | 'purple'
  note?: string
  createdAt: string
}

export interface Note {
  id: string
  bookId: string
  page: number
  position?: string
  content: string
  createdAt: string
  updatedAt: string
}

export interface ReadingSettings {
  fontSize: 'small' | 'medium' | 'large' | 'xl'
  fontFamily: 'serif' | 'sans-serif' | 'dyslexic'
  lineHeight: 'compact' | 'normal' | 'relaxed'
  backgroundColor: 'white' | 'cream' | 'dark'
  textColor: 'black' | 'dark-gray' | 'white'
  margin: 'narrow' | 'normal' | 'wide'
  autoScroll: boolean
  autoBookmark: boolean
  nightMode: boolean
  pageTransition: 'slide' | 'fade' | 'none'
}

export interface ReadingSession {
  bookId: string
  startTime: string
  endTime?: string
  duration: number // in minutes
  pagesRead: number
  startPage: number
  endPage: number
}

interface ReadingState {
  // Current reading
  currentBookId: string | null
  currentPage: number
  isReading: boolean
  
  // Reading progress for all books
  progress: Record<string, ReadingProgress>
  
  // Reading settings
  settings: ReadingSettings
  
  // Reading sessions
  currentSession: ReadingSession | null
  recentSessions: ReadingSession[]
  
  // Reader state
  isFullscreen: boolean
  showToolbar: boolean
  showToc: boolean // Table of Contents
  showBookmarks: boolean
  showNotes: boolean
  
  // Loading states
  isLoading: boolean
  isSaving: boolean
  
  // Error state
  error: string | null
}

// Initial state
const initialState: ReadingState = {
  currentBookId: null,
  currentPage: 1,
  isReading: false,
  progress: {},
  settings: {
    fontSize: 'medium',
    fontFamily: 'serif',
    lineHeight: 'normal',
    backgroundColor: 'cream',
    textColor: 'black',
    margin: 'normal',
    autoScroll: false,
    autoBookmark: true,
    nightMode: false,
    pageTransition: 'slide'
  },
  currentSession: null,
  recentSessions: [],
  isFullscreen: false,
  showToolbar: true,
  showToc: false,
  showBookmarks: false,
  showNotes: false,
  isLoading: false,
  isSaving: false,
  error: null
}

// Reading slice
const readingSlice = createSlice({
  name: 'reading',
  initialState,
  reducers: {
    // Book reading actions
    startReading: (state, action: PayloadAction<{ bookId: string; page?: number }>) => {
      const { bookId, page = 1 } = action.payload
      state.currentBookId = bookId
      state.currentPage = page
      state.isReading = true
      
      // Start new reading session
      state.currentSession = {
        bookId,
        startTime: new Date().toISOString(),
        duration: 0,
        pagesRead: 0,
        startPage: page,
        endPage: page
      }
      
      // Initialize progress if not exists
      if (!state.progress[bookId]) {
        state.progress[bookId] = {
          bookId,
          currentPage: page,
          totalPages: 0,
          percentage: 0,
          lastReadAt: new Date().toISOString(),
          timeSpent: 0,
          bookmarks: [],
          highlights: [],
          notes: []
        }
      }
    },
    
    stopReading: (state) => {
      if (state.currentSession) {
        // End current session
        const endTime = new Date().toISOString()
        const duration = Math.round(
          (new Date(endTime).getTime() - new Date(state.currentSession.startTime).getTime()) / 60000
        )
        
        const completedSession: ReadingSession = {
          ...state.currentSession,
          endTime,
          duration
        }
        
        // Add to recent sessions
        state.recentSessions.unshift(completedSession)
        if (state.recentSessions.length > 50) {
          state.recentSessions = state.recentSessions.slice(0, 50)
        }
        
        // Update total time spent
        if (state.currentBookId && state.progress[state.currentBookId]) {
          const progress = state.progress[state.currentBookId]
          if (progress) {
            progress.timeSpent += duration
          }
        }
        
        state.currentSession = null
      }
      
      state.isReading = false
    },
    
    setCurrentPage: (state, action: PayloadAction<number>) => {
      const page = action.payload
      state.currentPage = page
      
      // Update progress
      if (state.currentBookId && state.progress[state.currentBookId]) {
        const progress = state.progress[state.currentBookId]
        if (progress) {
          progress.currentPage = page
          progress.lastReadAt = new Date().toISOString()
          
          if (progress.totalPages > 0) {
            progress.percentage = Math.round((page / progress.totalPages) * 100)
          }
          
          // Auto-bookmark if enabled
          if (state.settings.autoBookmark) {
            const existingBookmark = progress.bookmarks.find(b => b.page === page)
            if (!existingBookmark) {
              progress.bookmarks.push({
                id: `auto-${Date.now()}`,
                bookId: state.currentBookId,
                page,
                title: `Page ${page}`,
                createdAt: new Date().toISOString()
              })
            }
          }
        }
      }
      
      // Update current session
      if (state.currentSession) {
        state.currentSession.endPage = page
        state.currentSession.pagesRead = Math.abs(page - state.currentSession.startPage) + 1
      }
    },
    
    setTotalPages: (state, action: PayloadAction<{ bookId: string; totalPages: number }>) => {
      const { bookId, totalPages } = action.payload
      
      if (state.progress[bookId]) {
        const progress = state.progress[bookId]
        if (progress) {
          progress.totalPages = totalPages
          
          // Recalculate percentage
          const currentPage = progress.currentPage
          progress.percentage = Math.round((currentPage / totalPages) * 100)
        }
      }
    },
    
    // Bookmark actions
    addBookmark: (state, action: PayloadAction<Omit<Bookmark, 'id' | 'createdAt'>>) => {
      const bookmark: Bookmark = {
        ...action.payload,
        id: `bookmark-${Date.now()}`,
        createdAt: new Date().toISOString()
      }
      
      const progress = state.progress[bookmark.bookId]
      if (progress) {
        progress.bookmarks.push(bookmark)
      }
    },
    
    removeBookmark: (state, action: PayloadAction<{ bookId: string; bookmarkId: string }>) => {
      const { bookId, bookmarkId } = action.payload
      
      const progress = state.progress[bookId]
      if (progress) {
        progress.bookmarks = progress.bookmarks.filter(
          bookmark => bookmark.id !== bookmarkId
        )
      }
    },
    
    // Highlight actions
    addHighlight: (state, action: PayloadAction<Omit<Highlight, 'id' | 'createdAt'>>) => {
      const highlight: Highlight = {
        id: `highlight-${Date.now()}`,
        bookId: action.payload.bookId,
        page: action.payload.page,
        startPosition: action.payload.startPosition,
        endPosition: action.payload.endPosition,
        text: action.payload.text,
        color: action.payload.color,
        ...(action.payload.note && { note: action.payload.note }),
        createdAt: new Date().toISOString()
      }
      
      const progress = state.progress[highlight.bookId]
      if (progress) {
        progress.highlights.push(highlight)
      }
    },
    
    removeHighlight: (state, action: PayloadAction<{ bookId: string; highlightId: string }>) => {
      const { bookId, highlightId } = action.payload
      
      const progress = state.progress[bookId]
      if (progress) {
        progress.highlights = progress.highlights.filter(
          highlight => highlight.id !== highlightId
        )
      }
    },
    
    updateHighlight: (state, action: PayloadAction<{ bookId: string; highlightId: string; updates: Partial<Highlight> }>) => {
      const { bookId, highlightId, updates } = action.payload
      
      const progress = state.progress[bookId]
      if (progress) {
        const highlightIndex = progress.highlights.findIndex(
          highlight => highlight.id === highlightId
        )
        
        if (highlightIndex !== -1) {
          const highlight = progress.highlights[highlightIndex]
          if (highlight) {
            progress.highlights[highlightIndex] = {
              ...highlight,
              ...updates
            }
          }
        }
      }
    },
    
    // Note actions
    addNote: (state, action: PayloadAction<Omit<Note, 'id' | 'createdAt' | 'updatedAt'>>) => {
      const now = new Date().toISOString()
      const note: Note = {
        ...action.payload,
        id: `note-${Date.now()}`,
        createdAt: now,
        updatedAt: now
      }
      
      const progress = state.progress[note.bookId]
      if (progress) {
        progress.notes.push(note)
      }
    },
    
    updateNote: (state, action: PayloadAction<{ bookId: string; noteId: string; content: string }>) => {
      const { bookId, noteId, content } = action.payload
      
      const progress = state.progress[bookId]
      if (progress) {
        const noteIndex = progress.notes.findIndex(
          note => note.id === noteId
        )
        
        if (noteIndex !== -1) {
          const note = progress.notes[noteIndex]
          if (note) {
            note.content = content
            note.updatedAt = new Date().toISOString()
          }
        }
      }
    },
    
    removeNote: (state, action: PayloadAction<{ bookId: string; noteId: string }>) => {
      const { bookId, noteId } = action.payload
      
      const progress = state.progress[bookId]
      if (progress) {
        progress.notes = progress.notes.filter(
          note => note.id !== noteId
        )
      }
    },
    
    // Settings actions
    updateSettings: (state, action: PayloadAction<Partial<ReadingSettings>>) => {
      state.settings = { ...state.settings, ...action.payload }
    },
    
    // UI actions
    toggleFullscreen: (state) => {
      state.isFullscreen = !state.isFullscreen
    },
    
    toggleToolbar: (state) => {
      state.showToolbar = !state.showToolbar
    },
    
    toggleToc: (state) => {
      state.showToc = !state.showToc
      state.showBookmarks = false
      state.showNotes = false
    },
    
    toggleBookmarks: (state) => {
      state.showBookmarks = !state.showBookmarks
      state.showToc = false
      state.showNotes = false
    },
    
    toggleNotes: (state) => {
      state.showNotes = !state.showNotes
      state.showToc = false
      state.showBookmarks = false
    },
    
    closePanels: (state) => {
      state.showToc = false
      state.showBookmarks = false
      state.showNotes = false
    },
    
    // Error handling
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    
    clearError: (state) => {
      state.error = null
    },
    
    // Loading states
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    
    setSaving: (state, action: PayloadAction<boolean>) => {
      state.isSaving = action.payload
    }
  }
})

// Export actions
export const {
  startReading,
  stopReading,
  setCurrentPage,
  setTotalPages,
  addBookmark,
  removeBookmark,
  addHighlight,
  removeHighlight,
  updateHighlight,
  addNote,
  updateNote,
  removeNote,
  updateSettings,
  toggleFullscreen,
  toggleToolbar,
  toggleToc,
  toggleBookmarks,
  toggleNotes,
  closePanels,
  setError,
  clearError,
  setLoading,
  setSaving
} = readingSlice.actions

// Selectors
export const selectReading = (state: { reading: ReadingState }) => state.reading
export const selectCurrentBookId = (state: { reading: ReadingState }) => state.reading.currentBookId
export const selectCurrentPage = (state: { reading: ReadingState }) => state.reading.currentPage
export const selectIsReading = (state: { reading: ReadingState }) => state.reading.isReading
export const selectReadingProgress = (state: { reading: ReadingState }, bookId: string) => 
  state.reading.progress[bookId]
export const selectReadingSettings = (state: { reading: ReadingState }) => state.reading.settings
export const selectCurrentSession = (state: { reading: ReadingState }) => state.reading.currentSession
export const selectRecentSessions = (state: { reading: ReadingState }) => state.reading.recentSessions
export const selectIsFullscreen = (state: { reading: ReadingState }) => state.reading.isFullscreen
export const selectShowToolbar = (state: { reading: ReadingState }) => state.reading.showToolbar
export const selectReadingError = (state: { reading: ReadingState }) => state.reading.error

// Export reducer
export default readingSlice.reducer