'use client'

import React, { createContext, useContext, useEffect, ReactNode } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { verifyToken, logoutUser, clearError } from '@/lib/store/slices/auth-slice'
import { AppDispatch } from '@/lib/store/store'
import { User } from '@/lib/types/auth'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (userData: any) => Promise<void>
  logout: () => void
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const dispatch = useDispatch<AppDispatch>()
  const { user, isAuthenticated, isLoading, error } = useSelector((state: any) => state.auth)

  useEffect(() => {
    // Validate token on app start
    const token = localStorage.getItem('coko_token')
    if (token) {
      dispatch(verifyToken())
    }
  }, [dispatch])

  const handleLogin = async () => {
    // This will be handled by the auth slice
    // dispatch(login({ email, password }))
  }

  const handleRegister = async () => {
    // This will be handled by the auth slice
    // dispatch(register(userData))
  }

  const handleLogout = () => {
    dispatch(logoutUser())
  }

  const handleClearError = () => {
    dispatch(clearError())
  }

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    clearError: handleClearError
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext