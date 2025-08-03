import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { toast } from 'react-hot-toast'

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
const API_TIMEOUT = 30000 // 30 seconds - optimized for African networks

// Extended config interface for metadata
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  metadata?: {
    startTime: Date
  }
  _retry?: boolean
}

// API response interface
interface ApiErrorResponse {
  message?: string
  errors?: Record<string, string[]>
}

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  // Optimizations for African networks
  maxRedirects: 3,
  validateStatus: (status) => status < 500, // Don't throw on 4xx errors
  transformRequest: [
    (data, headers) => {
      // Compress large payloads if possible
      if (data && typeof data === 'object' && JSON.stringify(data).length > 1024) {
        if (headers) {
          headers['Accept-Encoding'] = 'gzip, deflate'
        }
      }
      return JSON.stringify(data)
    }
  ]
})

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const extendedConfig = config as ExtendedAxiosRequestConfig
    
    // Add auth token if available
    const token = localStorage.getItem('coko_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request timestamp for debugging
    if (process.env.NODE_ENV === 'development') {
      extendedConfig.metadata = { startTime: new Date() }
    }

    // Add language header
    const language = localStorage.getItem('coko_language') || 'fr'
    if (config.headers) {
      config.headers['Accept-Language'] = language
    }

    // Add device info for analytics
    if (config.headers) {
      config.headers['X-Device-Type'] = /Mobile|Android|iPhone|iPad/.test(navigator.userAgent) ? 'mobile' : 'desktop'
      config.headers['X-User-Agent'] = navigator.userAgent
    }

    return config
  },
  (error) => {
    console.error('Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response time in development
    if (process.env.NODE_ENV === 'development') {
      const extendedConfig = response.config as ExtendedAxiosRequestConfig
      if (extendedConfig.metadata) {
        const endTime = new Date()
        const duration = endTime.getTime() - extendedConfig.metadata.startTime.getTime()
        console.log(`API ${response.config.method?.toUpperCase()} ${response.config.url}: ${duration}ms`)
      }
    }

    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as ExtendedAxiosRequestConfig

    // Handle network errors (common in African networks)
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        toast.error('Connexion lente. Veuillez réessayer.')
      } else if (error.message === 'Network Error') {
        toast.error('Erreur de réseau. Vérifiez votre connexion internet.')
      } else {
        toast.error('Erreur de connexion au serveur.')
      }
      return Promise.reject(error)
    }

    const status = error.response.status
    const data = error.response.data as ApiErrorResponse

    // Handle different HTTP status codes
    switch (status) {
      case 400:
        // Bad Request - show specific error message
        if (data?.message) {
          toast.error(data.message)
        } else {
          toast.error('Requête invalide')
        }
        break

      case 401:
        // Unauthorized - try to refresh token
        if (originalRequest && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('coko_refresh_token')
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken
              })

              const newToken = response.data.token
              localStorage.setItem('coko_token', newToken)

              // Retry original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`
              }
              return apiClient(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('coko_token')
            localStorage.removeItem('coko_refresh_token')
            localStorage.removeItem('coko_user')
            
            // Only redirect if not already on auth pages
            if (!window.location.pathname.includes('/auth/')) {
              window.location.href = '/auth/login'
            }
          }
        }
        break

      case 403:
        // Forbidden
        toast.error('Accès refusé. Vous n\'avez pas les permissions nécessaires.')
        break

      case 404:
        // Not Found
        if (data?.message) {
          toast.error(data.message)
        } else {
          toast.error('Ressource non trouvée')
        }
        break

      case 422:
        // Validation Error
        if (data?.errors) {
          // Show first validation error
          const firstError = Object.values(data.errors)[0]
          if (Array.isArray(firstError) && firstError.length > 0) {
            toast.error(firstError[0] as string)
          }
        } else if (data?.message) {
          toast.error(data.message)
        } else {
          toast.error('Données invalides')
        }
        break

      case 429:
        // Rate Limited
        toast.error('Trop de requêtes. Veuillez patienter avant de réessayer.')
        break

      case 500:
        // Internal Server Error
        toast.error('Erreur serveur. Veuillez réessayer plus tard.')
        break

      case 502:
      case 503:
      case 504:
        // Server unavailable
        toast.error('Service temporairement indisponible. Veuillez réessayer.')
        break

      default:
        // Generic error
        if (data?.message) {
          toast.error(data.message)
        } else {
          toast.error('Une erreur inattendue s\'est produite')
        }
    }

    return Promise.reject(error)
  }
)

// Utility functions
export const setAuthToken = (token: string | null) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('coko_token', token)
  } else {
    delete apiClient.defaults.headers.common['Authorization']
    localStorage.removeItem('coko_token')
  }
}

export const clearAuthToken = () => {
  delete apiClient.defaults.headers.common['Authorization']
  localStorage.removeItem('coko_token')
  localStorage.removeItem('coko_refresh_token')
  localStorage.removeItem('coko_user')
}

// Network status utilities
export const isOnline = () => navigator.onLine

export const getNetworkInfo = () => {
  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
  
  if (connection) {
    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData
    }
  }
  
  return null
}

// Request retry utility for poor network conditions
export const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error as Error
      
      if (i === maxRetries) {
        throw lastError
      }
      
      // Exponential backoff with jitter
      const backoffDelay = delay * Math.pow(2, i) + Math.random() * 1000
      await new Promise(resolve => setTimeout(resolve, backoffDelay))
    }
  }
  
  throw lastError!
}

// File upload utility with progress
export const uploadFile = async (
  file: File,
  endpoint: string,
  onProgress?: (progress: number) => void
): Promise<AxiosResponse> => {
  const formData = new FormData()
  formData.append('file', file)
  
  return apiClient.post(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    }
  })
}

// Export default client
export default apiClient