// User types
export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
  username?: string
  avatar?: string
  phoneNumber?: string
  country?: string
  language: 'fr' | 'en' | 'wo' | 'ar'
  timezone?: string
  isEmailVerified: boolean
  isPhoneVerified: boolean
  role: 'user' | 'author' | 'publisher' | 'admin'
  subscription?: UserSubscription
  preferences: UserPreferences
  createdAt: string
  updatedAt: string
  lastLoginAt?: string
}

// User subscription
export interface UserSubscription {
  id: string
  plan: 'free' | 'basic' | 'premium' | 'unlimited'
  status: 'active' | 'inactive' | 'cancelled' | 'expired'
  startDate: string
  endDate?: string
  autoRenew: boolean
  paymentMethod?: string
}

// User preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'system'
  language: 'fr' | 'en' | 'wo' | 'ar'
  notifications: {
    email: boolean
    push: boolean
    sms: boolean
    marketing: boolean
  }
  reading: {
    fontSize: 'small' | 'medium' | 'large' | 'xl'
    fontFamily: 'serif' | 'sans-serif' | 'dyslexic'
    lineHeight: 'compact' | 'normal' | 'relaxed'
    backgroundColor: 'white' | 'cream' | 'dark'
    autoBookmark: boolean
    readingGoal?: number // books per month
  }
  privacy: {
    profileVisibility: 'public' | 'friends' | 'private'
    readingActivity: 'public' | 'friends' | 'private'
    allowRecommendations: boolean
  }
}

// Authentication credentials
export interface LoginCredentials {
  email: string
  password: string
  rememberMe?: boolean
}

// Registration data
export interface RegisterData {
  email: string
  password: string
  confirmPassword: string
  firstName: string
  lastName: string
  phoneNumber?: string
  country?: string
  language: 'fr' | 'en' | 'wo' | 'ar'
  acceptTerms: boolean
  acceptMarketing?: boolean
}

// Password reset
export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirm {
  token: string
  newPassword: string
  confirmPassword: string
}

// Change password
export interface ChangePasswordData {
  currentPassword: string
  newPassword: string
  confirmPassword: string
}

// Update profile
export interface UpdateProfileData {
  firstName?: string
  lastName?: string
  username?: string
  phoneNumber?: string
  country?: string
  language?: 'fr' | 'en' | 'wo' | 'ar'
  timezone?: string
}

// API response types
export interface AuthResponse {
  user: User
  token: string
  refreshToken?: string
  expiresAt?: number
  message?: string
}

export interface TokenRefreshResponse {
  token: string
  expiresAt?: number
}

export interface VerifyTokenResponse {
  user: User
  valid: boolean
}

// Error types
export interface AuthError {
  message: string
  code?: string
  field?: string
  details?: Record<string, string[]>
}

// Session types
export interface Session {
  id: string
  userId: string
  deviceInfo: {
    userAgent: string
    ip: string
    location?: string
    device: string
  }
  createdAt: string
  lastActivity: string
  expiresAt: string
  isActive: boolean
}

// Two-factor authentication
export interface TwoFactorSetup {
  secret: string
  qrCode: string
  backupCodes: string[]
}

export interface TwoFactorVerification {
  code: string
  backupCode?: string
}

// Social login
export interface SocialLoginData {
  provider: 'google' | 'facebook' | 'apple'
  token: string
  email?: string
  firstName?: string
  lastName?: string
  avatar?: string
}

// Email verification
export interface EmailVerificationRequest {
  email: string
}

export interface EmailVerificationConfirm {
  token: string
}

// Phone verification
export interface PhoneVerificationRequest {
  phoneNumber: string
}

export interface PhoneVerificationConfirm {
  phoneNumber: string
  code: string
}

// Account deletion
export interface AccountDeletionRequest {
  password: string
  reason?: string
  feedback?: string
}

// API endpoints
export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  LOGOUT: '/auth/logout',
  REFRESH_TOKEN: '/auth/refresh',
  VERIFY_TOKEN: '/auth/verify',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
  CHANGE_PASSWORD: '/auth/change-password',
  UPDATE_PROFILE: '/auth/profile',
  VERIFY_EMAIL: '/auth/verify-email',
  RESEND_EMAIL: '/auth/resend-email',
  VERIFY_PHONE: '/auth/verify-phone',
  RESEND_PHONE: '/auth/resend-phone',
  SETUP_2FA: '/auth/2fa/setup',
  VERIFY_2FA: '/auth/2fa/verify',
  DISABLE_2FA: '/auth/2fa/disable',
  SOCIAL_LOGIN: '/auth/social',
  SESSIONS: '/auth/sessions',
  DELETE_ACCOUNT: '/auth/delete-account'
} as const

// Validation schemas (for use with zod)
export const PASSWORD_REQUIREMENTS = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: false
} as const

export const USERNAME_REQUIREMENTS = {
  minLength: 3,
  maxLength: 30,
  allowedChars: /^[a-zA-Z0-9_-]+$/
} as const

// Helper types
export type AuthStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated' | 'error'
export type UserRole = User['role']
export type Language = User['language']
export type SubscriptionPlan = UserSubscription['plan']
export type SubscriptionStatus = UserSubscription['status']