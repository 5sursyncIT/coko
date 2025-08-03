import { AxiosResponse } from 'axios'
import type {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  TokenRefreshResponse,
  VerifyTokenResponse,
  PasswordResetRequest,
  PasswordResetConfirm,
  ChangePasswordData,
  UpdateProfileData,
  EmailVerificationRequest,
  EmailVerificationConfirm,
  PhoneVerificationRequest,
  PhoneVerificationConfirm,
  TwoFactorSetup,
  TwoFactorVerification,
  SocialLoginData,
  AccountDeletionRequest,
  Session
} from '@/lib/types/auth'
import { apiClient } from './client'

// Auth API class
class AuthAPI {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      '/auth/login',
      credentials
    )
    return response.data
  }

  /**
   * Register new user
   */
  async register(userData: RegisterData): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      '/auth/register',
      userData
    )
    return response.data
  }

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout')
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<TokenRefreshResponse> {
    const response: AxiosResponse<TokenRefreshResponse> = await apiClient.post(
      '/auth/refresh'
    )
    return response.data
  }

  /**
   * Verify current token validity
   */
  async verifyToken(): Promise<VerifyTokenResponse> {
    const response: AxiosResponse<VerifyTokenResponse> = await apiClient.get(
      '/auth/verify'
    )
    return response.data
  }

  /**
   * Request password reset
   */
  async forgotPassword(data: PasswordResetRequest): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/forgot-password',
      data
    )
    return response.data
  }

  /**
   * Confirm password reset with token
   */
  async resetPassword(data: PasswordResetConfirm): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/reset-password',
      data
    )
    return response.data
  }

  /**
   * Change user password
   */
  async changePassword(data: ChangePasswordData): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/change-password',
      data
    )
    return response.data
  }

  /**
   * Update user profile
   */
  async updateProfile(data: UpdateProfileData): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.patch(
      '/auth/profile',
      data
    )
    return response.data
  }

  /**
   * Request email verification
   */
  async requestEmailVerification(data: EmailVerificationRequest): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/verify-email',
      data
    )
    return response.data
  }

  /**
   * Confirm email verification
   */
  async confirmEmailVerification(data: EmailVerificationConfirm): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/verify-email/confirm',
      data
    )
    return response.data
  }

  /**
   * Resend email verification
   */
  async resendEmailVerification(): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/resend-email'
    )
    return response.data
  }

  /**
   * Request phone verification
   */
  async requestPhoneVerification(data: PhoneVerificationRequest): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/verify-phone',
      data
    )
    return response.data
  }

  /**
   * Confirm phone verification
   */
  async confirmPhoneVerification(data: PhoneVerificationConfirm): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/verify-phone/confirm',
      data
    )
    return response.data
  }

  /**
   * Resend phone verification
   */
  async resendPhoneVerification(phoneNumber: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/resend-phone',
      { phoneNumber }
    )
    return response.data
  }

  /**
   * Setup two-factor authentication
   */
  async setup2FA(): Promise<TwoFactorSetup> {
    const response: AxiosResponse<TwoFactorSetup> = await apiClient.post(
      '/auth/2fa/setup'
    )
    return response.data
  }

  /**
   * Verify two-factor authentication
   */
  async verify2FA(data: TwoFactorVerification): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/2fa/verify',
      data
    )
    return response.data
  }

  /**
   * Disable two-factor authentication
   */
  async disable2FA(password: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.post(
      '/auth/2fa/disable',
      { password }
    )
    return response.data
  }

  /**
   * Social login (Google, Facebook, Apple)
   */
  async socialLogin(data: SocialLoginData): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await apiClient.post(
      '/auth/social',
      data
    )
    return response.data
  }

  /**
   * Get user sessions
   */
  async getSessions(): Promise<Session[]> {
    const response: AxiosResponse<Session[]> = await apiClient.get(
      '/auth/sessions'
    )
    return response.data
  }

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.delete(
      `/auth/sessions/${sessionId}`
    )
    return response.data
  }

  /**
   * Revoke all sessions except current
   */
  async revokeAllSessions(): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.delete(
      '/auth/sessions'
    )
    return response.data
  }

  /**
   * Delete user account
   */
  async deleteAccount(data: AccountDeletionRequest): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await apiClient.delete(
      '/auth/delete-account',
      { data }
    )
    return response.data
  }

  /**
   * Check if email is available
   */
  async checkEmailAvailability(email: string): Promise<{ available: boolean }> {
    const response: AxiosResponse<{ available: boolean }> = await apiClient.get(
      `/auth/check-email?email=${encodeURIComponent(email)}`
    )
    return response.data
  }

  /**
   * Check if username is available
   */
  async checkUsernameAvailability(username: string): Promise<{ available: boolean }> {
    const response: AxiosResponse<{ available: boolean }> = await apiClient.get(
      `/auth/check-username?username=${encodeURIComponent(username)}`
    )
    return response.data
  }
}

// Create and export auth API instance
export const authApi = new AuthAPI()

// Export individual methods for convenience
export const {
  login,
  register,
  logout,
  refreshToken,
  verifyToken,
  forgotPassword,
  resetPassword,
  changePassword,
  updateProfile,
  requestEmailVerification,
  confirmEmailVerification,
  resendEmailVerification,
  requestPhoneVerification,
  confirmPhoneVerification,
  resendPhoneVerification,
  setup2FA,
  verify2FA,
  disable2FA,
  socialLogin,
  getSessions,
  revokeSession,
  revokeAllSessions,
  deleteAccount,
  checkEmailAvailability,
  checkUsernameAvailability
} = authApi