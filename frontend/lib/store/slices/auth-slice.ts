import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authApi } from '@/lib/api/auth'
import type { User, LoginCredentials, RegisterData } from '@/lib/types/auth'

// Types
interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  lastActivity: number | null
  sessionExpiry: number | null
}

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  lastActivity: null,
  sessionExpiry: null
}

// Async thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials)
      
      // Store token in localStorage for persistence
      if (response.token) {
        localStorage.setItem('coko_token', response.token)
        localStorage.setItem('coko_user', JSON.stringify(response.user))
      }
      
      return response
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || 'Erreur de connexion'
      )
    }
  }
)

export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData: RegisterData, { rejectWithValue }) => {
    try {
      const response = await authApi.register(userData)
      
      // Store token in localStorage for persistence
      if (response.token) {
        localStorage.setItem('coko_token', response.token)
        localStorage.setItem('coko_user', JSON.stringify(response.user))
      }
      
      return response
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || 'Erreur lors de l\'inscription'
      )
    }
  }
)

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { rejectWithValue }) => {
    try {
      const response = await authApi.refreshToken()
      
      if (response.token) {
        localStorage.setItem('coko_token', response.token)
      }
      
      return response
    } catch (error: any) {
      return rejectWithValue(
        error.response?.data?.message || 'Erreur de rafraîchissement du token'
      )
    }
  }
)

export const logoutUser = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await authApi.logout()
      
      // Clear localStorage
      localStorage.removeItem('coko_token')
      localStorage.removeItem('coko_user')
      
      return null
    } catch (error: any) {
      // Even if logout fails on server, clear local storage
      localStorage.removeItem('coko_token')
      localStorage.removeItem('coko_user')
      
      return rejectWithValue(
        error.response?.data?.message || 'Erreur lors de la déconnexion'
      )
    }
  }
)

export const verifyToken = createAsyncThunk(
  'auth/verifyToken',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('coko_token')
      if (!token) {
        throw new Error('No token found')
      }
      
      const response = await authApi.verifyToken()
      return response
    } catch (error: any) {
      // Clear invalid token
      localStorage.removeItem('coko_token')
      localStorage.removeItem('coko_user')
      
      return rejectWithValue(
        error.response?.data?.message || 'Token invalide'
      )
    }
  }
)

// Auth slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    updateLastActivity: (state) => {
      state.lastActivity = Date.now()
    },
    setSessionExpiry: (state, action: PayloadAction<number>) => {
      state.sessionExpiry = action.payload
    },
    restoreSession: (state) => {
      // Restore session from localStorage on app start
      const token = localStorage.getItem('coko_token')
      const userStr = localStorage.getItem('coko_user')
      
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr)
          state.token = token
          state.user = user
          state.isAuthenticated = true
          state.lastActivity = Date.now()
        } catch (error) {
          // Clear corrupted data
          localStorage.removeItem('coko_token')
          localStorage.removeItem('coko_user')
        }
      }
    },
    clearSession: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.error = null
      state.lastActivity = null
      state.sessionExpiry = null
      
      // Clear localStorage
      localStorage.removeItem('coko_token')
      localStorage.removeItem('coko_user')
    }
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.token
        state.isAuthenticated = true
        state.error = null
        state.lastActivity = Date.now()
        state.sessionExpiry = action.payload.expiresAt || Date.now() + (24 * 60 * 60 * 1000) // 24h default
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
        state.isAuthenticated = false
        state.user = null
        state.token = null
      })
    
    // Register
    builder
      .addCase(registerUser.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.token
        state.isAuthenticated = true
        state.error = null
        state.lastActivity = Date.now()
        state.sessionExpiry = action.payload.expiresAt || Date.now() + (24 * 60 * 60 * 1000)
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
        state.isAuthenticated = false
        state.user = null
        state.token = null
      })
    
    // Refresh token
    builder
      .addCase(refreshToken.pending, (state) => {
        state.isLoading = true
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.isLoading = false
        state.token = action.payload.token
        state.lastActivity = Date.now()
        state.sessionExpiry = action.payload.expiresAt || Date.now() + (24 * 60 * 60 * 1000)
        state.error = null
      })
      .addCase(refreshToken.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
        // Don't clear session on refresh failure, let user try again
      })
    
    // Logout
    builder
      .addCase(logoutUser.pending, (state) => {
        state.isLoading = true
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.isLoading = false
        state.user = null
        state.token = null
        state.isAuthenticated = false
        state.error = null
        state.lastActivity = null
        state.sessionExpiry = null
      })
      .addCase(logoutUser.rejected, (state, action) => {
        state.isLoading = false
        // Still clear session even if logout failed
        state.user = null
        state.token = null
        state.isAuthenticated = false
        state.lastActivity = null
        state.sessionExpiry = null
        state.error = action.payload as string
      })
    
    // Verify token
    builder
      .addCase(verifyToken.pending, (state) => {
        state.isLoading = true
      })
      .addCase(verifyToken.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload.user
        state.isAuthenticated = true
        state.lastActivity = Date.now()
        state.error = null
      })
      .addCase(verifyToken.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
        state.isAuthenticated = false
        state.user = null
        state.token = null
        state.lastActivity = null
        state.sessionExpiry = null
      })
  }
})

// Export actions
export const {
  clearError,
  updateLastActivity,
  setSessionExpiry,
  restoreSession,
  clearSession
} = authSlice.actions

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth
export const selectUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.isLoading
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error
export const selectToken = (state: { auth: AuthState }) => state.auth.token
export const selectSessionExpiry = (state: { auth: AuthState }) => state.auth.sessionExpiry
export const selectLastActivity = (state: { auth: AuthState }) => state.auth.lastActivity

// Export reducer
export default authSlice.reducer