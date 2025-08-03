import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { CatalogAPI } from '@/lib/api/catalog'
import {
  Book,
  Author,
  Category,
  SearchFilters,
  PaginationMeta,
  Publisher
} from '@/lib/types/catalog'

interface CatalogState {
  // Books
  books: Book[]
  featuredBooks: Book[]
  recentBooks: Book[]
  popularBooks: Book[]
  currentBook: Book | null
  
  // Metadata
  authors: Author[]
  categories: Category[]
  publishers: Publisher[]
  
  // Search & Filters
  searchQuery: string
  filters: SearchFilters
  searchResults: Book[]
  searchPagination: PaginationMeta | null
  
  // Pagination
  pagination: PaginationMeta | null
  
  // Loading states
  isLoading: boolean
  isSearching: boolean
  isFeaturedLoading: boolean
  isBookLoading: boolean
  
  // Error states
  error: string | null
  searchError: string | null
}

// Initial state
const initialState: CatalogState = {
  books: [],
  featuredBooks: [],
  recentBooks: [],
  popularBooks: [],
  currentBook: null,
  authors: [],
  categories: [],
  publishers: [],
  searchQuery: '',
  filters: {},
  searchResults: [],
  searchPagination: null,
  pagination: null,
  isLoading: false,
  isSearching: false,
  isFeaturedLoading: false,
  isBookLoading: false,
  error: null,
  searchError: null
}

// Async thunks
export const fetchBooks = createAsyncThunk(
  'catalog/fetchBooks',
  async (params: { page?: number; limit?: number; filters?: SearchFilters }, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.getBooks(params)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur lors du chargement des livres')
    }
  }
)

export const fetchFeaturedBooks = createAsyncThunk(
  'catalog/fetchFeaturedBooks',
  async (_, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.getFeaturedBooks()
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur lors du chargement des livres en vedette')
    }
  }
)

export const fetchBookById = createAsyncThunk(
  'catalog/fetchBookById',
  async (bookId: string, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.getBookById(bookId)
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur lors du chargement du livre')
    }
  }
)

export const searchBooks = createAsyncThunk(
  'catalog/searchBooks',
  async (filters: SearchFilters, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.searchBooks(filters)
      return response.data
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Search failed')
    }
  }
)

export const fetchAuthors = createAsyncThunk(
  'catalog/fetchAuthors',
  async (_, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.getAuthors()
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur lors du chargement des auteurs')
    }
  }
)

export const fetchCategories = createAsyncThunk(
  'catalog/fetchCategories',
  async (_, { rejectWithValue }) => {
    try {
      const response = await CatalogAPI.getCategories()
      return response
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur lors du chargement des catégories')
    }
  }
)

// Catalog slice
const catalogSlice = createSlice({
  name: 'catalog',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
      state.searchError = null
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload
    },
    setFilters: (state, action: PayloadAction<SearchFilters>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: (state) => {
      state.filters = {}
      state.searchQuery = ''
    },
    clearSearchResults: (state) => {
      state.searchResults = []
      state.searchError = null
    },
    setCurrentBook: (state, action: PayloadAction<Book | null>) => {
      state.currentBook = action.payload
    },
    updateBookRating: (state, action: PayloadAction<{ bookId: string; rating: number; reviewCount: number }>) => {
      const { bookId, rating, reviewCount } = action.payload
      
      // Update in books array
      const bookIndex = state.books.findIndex(book => book.id === bookId)
      if (bookIndex !== -1) {
        const book = state.books[bookIndex]
        if (book) {
          book.rating = rating
          book.reviewCount = reviewCount
        }
      }
      
      // Update in featured books
      const featuredIndex = state.featuredBooks.findIndex(book => book.id === bookId)
      if (featuredIndex !== -1) {
        const featuredBook = state.featuredBooks[featuredIndex]
        if (featuredBook) {
          featuredBook.rating = rating
          featuredBook.reviewCount = reviewCount
        }
      }
      
      // Update current book
      if (state.currentBook && state.currentBook.id === bookId) {
        state.currentBook.rating = rating
        state.currentBook.reviewCount = reviewCount
      }
    },
    incrementDownloadCount: (state, action: PayloadAction<string>) => {
      const bookId = action.payload
      
      // Update in books array
      const bookIndex = state.books.findIndex(book => book.id === bookId)
      if (bookIndex !== -1) {
        const book = state.books[bookIndex]
        if (book) {
          book.downloadCount += 1
        }
      }
      
      // Update current book
      if (state.currentBook && state.currentBook.id === bookId) {
        state.currentBook.downloadCount += 1
      }
    }
  },
  extraReducers: (builder) => {
    // Fetch books
    builder
      .addCase(fetchBooks.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchBooks.fulfilled, (state, action) => {
        state.isLoading = false
        if (action.payload && action.payload.data) {
          state.books = action.payload.data
          state.pagination = action.payload.pagination || null
        }
      })
      .addCase(fetchBooks.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || 'Failed to fetch books'
      })
    
    // Fetch featured books
    builder
      .addCase(fetchFeaturedBooks.pending, (state) => {
        state.isFeaturedLoading = true
      })
      .addCase(fetchFeaturedBooks.fulfilled, (state, action) => {
        state.isFeaturedLoading = false
        if (action.payload && action.payload.data) {
          state.featuredBooks = action.payload.data
        }
      })
      .addCase(fetchFeaturedBooks.rejected, (state, action) => {
        state.isFeaturedLoading = false
        state.error = action.payload as string || 'Failed to fetch featured books'
      })
    
    // Fetch book by ID
    builder
      .addCase(fetchBookById.pending, (state) => {
        state.isBookLoading = true
        state.error = null
      })
      .addCase(fetchBookById.fulfilled, (state, action) => {
        state.isBookLoading = false
        if (action.payload) {
          state.currentBook = action.payload.data || null
        }
      })
      .addCase(fetchBookById.rejected, (state, action) => {
        state.isBookLoading = false
        state.error = action.payload as string || 'Failed to fetch book'
      })
    
    // Search books
    builder
      .addCase(searchBooks.pending, (state) => {
        state.isSearching = true
        state.searchError = null
      })
      .addCase(searchBooks.fulfilled, (state, action) => {
        state.isSearching = false
        if (action.payload && action.payload.books) {
          state.searchResults = action.payload.books
          state.searchPagination = action.payload.pagination || null
        }
      })
      .addCase(searchBooks.rejected, (state, action) => {
        state.isSearching = false
        state.error = action.payload as string || 'Search failed'
      })
    
    // Fetch authors
    builder
      .addCase(fetchAuthors.fulfilled, (state, action) => {
        state.isLoading = false
        if (action.payload && action.payload.data) {
          state.authors = action.payload.data
        }
      })
      .addCase(fetchAuthors.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || 'Failed to fetch authors'
      })
    
    // Fetch categories
    builder
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.isLoading = false
        if (action.payload && action.payload.data) {
          state.categories = action.payload.data
        }
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string || 'Failed to fetch categories'
      })
  }
})

// Export actions
export const {
  clearError,
  setSearchQuery,
  setFilters,
  clearFilters,
  clearSearchResults,
  setCurrentBook,
  updateBookRating,
  incrementDownloadCount
} = catalogSlice.actions

// Selectors
export const selectCatalog = (state: { catalog: CatalogState }) => state.catalog
export const selectBooks = (state: { catalog: CatalogState }) => state.catalog.books
export const selectFeaturedBooks = (state: { catalog: CatalogState }) => state.catalog.featuredBooks
export const selectCurrentBook = (state: { catalog: CatalogState }) => state.catalog.currentBook
export const selectSearchResults = (state: { catalog: CatalogState }) => state.catalog.searchResults
export const selectAuthors = (state: { catalog: CatalogState }) => state.catalog.authors
export const selectCategories = (state: { catalog: CatalogState }) => state.catalog.categories
export const selectFilters = (state: { catalog: CatalogState }) => state.catalog.filters
export const selectPagination = (state: { catalog: CatalogState }) => state.catalog.pagination
export const selectCatalogLoading = (state: { catalog: CatalogState }) => state.catalog.isLoading
export const selectSearchLoading = (state: { catalog: CatalogState }) => state.catalog.isSearching
export const selectCatalogError = (state: { catalog: CatalogState }) => state.catalog.error

// Export reducer
export default catalogSlice.reducer