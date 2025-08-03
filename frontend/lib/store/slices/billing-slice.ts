import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

// Types
export interface Subscription {
  id: string
  userId: string
  planId: string
  status: 'active' | 'inactive' | 'cancelled' | 'past_due' | 'trialing'
  currentPeriodStart: string
  currentPeriodEnd: string
  cancelAtPeriodEnd: boolean
  trialEnd?: string
  createdAt: string
  updatedAt: string
}

export interface Plan {
  id: string
  name: string
  description: string
  price: number
  currency: string
  interval: 'month' | 'year'
  features: string[]
  maxBooks: number
  maxDevices: number
  offlineAccess: boolean
  prioritySupport: boolean
  isPopular?: boolean
  isActive: boolean
  createdAt: string
}

export interface PaymentMethod {
  id: string
  type: 'card' | 'mobile_money' | 'bank_transfer'
  last4?: string
  brand?: string
  expiryMonth?: number
  expiryYear?: number
  phoneNumber?: string
  provider?: string // Orange Money, MTN Mobile Money, etc.
  isDefault: boolean
  createdAt: string
}

export interface Invoice {
  id: string
  subscriptionId: string
  amount: number
  currency: string
  status: 'paid' | 'pending' | 'failed' | 'cancelled'
  dueDate: string
  paidAt?: string
  paymentMethodId?: string
  downloadUrl?: string
  createdAt: string
}

export interface Transaction {
  id: string
  type: 'subscription' | 'book_purchase' | 'refund'
  amount: number
  currency: string
  status: 'completed' | 'pending' | 'failed' | 'cancelled'
  description: string
  paymentMethodId?: string
  invoiceId?: string
  createdAt: string
}

export interface UsageStats {
  booksRead: number
  timeSpent: number // in minutes
  devicesUsed: number
  lastActivity: string
  monthlyStats: {
    month: string
    booksRead: number
    timeSpent: number
  }[]
}

interface BillingState {
  // Subscription
  subscription: Subscription | null
  plans: Plan[]
  
  // Payment methods
  paymentMethods: PaymentMethod[]
  defaultPaymentMethod: PaymentMethod | null
  
  // Billing history
  invoices: Invoice[]
  transactions: Transaction[]
  
  // Usage
  usageStats: UsageStats | null
  
  // Loading states
  isLoading: boolean
  isProcessingPayment: boolean
  isUpdatingSubscription: boolean
  
  // Error states
  error: string | null
  paymentError: string | null
}

// Initial state
const initialState: BillingState = {
  subscription: null,
  plans: [],
  paymentMethods: [],
  defaultPaymentMethod: null,
  invoices: [],
  transactions: [],
  usageStats: null,
  isLoading: false,
  isProcessingPayment: false,
  isUpdatingSubscription: false,
  error: null,
  paymentError: null
}

// Async thunks
export const fetchSubscription = createAsyncThunk(
  'billing/fetchSubscription',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/subscription')
      if (!response.ok) {
        throw new Error('Failed to fetch subscription')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const fetchPlans = createAsyncThunk(
  'billing/fetchPlans',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/plans')
      if (!response.ok) {
        throw new Error('Failed to fetch plans')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const fetchPaymentMethods = createAsyncThunk(
  'billing/fetchPaymentMethods',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/payment-methods')
      if (!response.ok) {
        throw new Error('Failed to fetch payment methods')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const addPaymentMethod = createAsyncThunk(
  'billing/addPaymentMethod',
  async (paymentData: any, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/payment-methods', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(paymentData)
      })
      if (!response.ok) {
        throw new Error('Failed to add payment method')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const removePaymentMethod = createAsyncThunk(
  'billing/removePaymentMethod',
  async (paymentMethodId: string, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch(`/api/billing/payment-methods/${paymentMethodId}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('Failed to remove payment method')
      }
      return paymentMethodId
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const setDefaultPaymentMethod = createAsyncThunk(
  'billing/setDefaultPaymentMethod',
  async (paymentMethodId: string, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch(`/api/billing/payment-methods/${paymentMethodId}/default`, {
        method: 'PUT'
      })
      if (!response.ok) {
        throw new Error('Failed to set default payment method')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const subscribeToPlan = createAsyncThunk(
  'billing/subscribeToPlan',
  async ({ planId, paymentMethodId }: { planId: string; paymentMethodId: string }, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planId, paymentMethodId })
      })
      if (!response.ok) {
        throw new Error('Failed to subscribe to plan')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const cancelSubscription = createAsyncThunk(
  'billing/cancelSubscription',
  async (cancelAtPeriodEnd: boolean = true, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/subscription/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cancelAtPeriodEnd })
      })
      if (!response.ok) {
        throw new Error('Failed to cancel subscription')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const fetchInvoices = createAsyncThunk(
  'billing/fetchInvoices',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/invoices')
      if (!response.ok) {
        throw new Error('Failed to fetch invoices')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const fetchTransactions = createAsyncThunk(
  'billing/fetchTransactions',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/transactions')
      if (!response.ok) {
        throw new Error('Failed to fetch transactions')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

export const fetchUsageStats = createAsyncThunk(
  'billing/fetchUsageStats',
  async (_, { rejectWithValue }) => {
    try {
      // TODO: Replace with actual API call
      const response = await fetch('/api/billing/usage')
      if (!response.ok) {
        throw new Error('Failed to fetch usage stats')
      }
      return await response.json()
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Unknown error')
    }
  }
)

// Billing slice
const billingSlice = createSlice({
  name: 'billing',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    
    clearPaymentError: (state) => {
      state.paymentError = null
    },
    
    setPaymentError: (state, action: PayloadAction<string>) => {
      state.paymentError = action.payload
    },
    
    updateSubscriptionStatus: (state, action: PayloadAction<Subscription['status']>) => {
      if (state.subscription) {
        state.subscription.status = action.payload
      }
    }
  },
  extraReducers: (builder) => {
    // Fetch subscription
    builder
      .addCase(fetchSubscription.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchSubscription.fulfilled, (state, action) => {
        state.isLoading = false
        state.subscription = action.payload
      })
      .addCase(fetchSubscription.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Fetch plans
    builder
      .addCase(fetchPlans.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPlans.fulfilled, (state, action) => {
        state.isLoading = false
        state.plans = action.payload
      })
      .addCase(fetchPlans.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Fetch payment methods
    builder
      .addCase(fetchPaymentMethods.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPaymentMethods.fulfilled, (state, action) => {
        state.isLoading = false
        state.paymentMethods = action.payload
        state.defaultPaymentMethod = action.payload.find((pm: PaymentMethod) => pm.isDefault) || null
      })
      .addCase(fetchPaymentMethods.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Add payment method
    builder
      .addCase(addPaymentMethod.pending, (state) => {
        state.isProcessingPayment = true
        state.paymentError = null
      })
      .addCase(addPaymentMethod.fulfilled, (state, action) => {
        state.isProcessingPayment = false
        state.paymentMethods.push(action.payload)
        if (action.payload.isDefault) {
          state.defaultPaymentMethod = action.payload
        }
      })
      .addCase(addPaymentMethod.rejected, (state, action) => {
        state.isProcessingPayment = false
        state.paymentError = action.payload as string
      })
    
    // Remove payment method
    builder
      .addCase(removePaymentMethod.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(removePaymentMethod.fulfilled, (state, action) => {
        state.isLoading = false
        state.paymentMethods = state.paymentMethods.filter(pm => pm.id !== action.payload)
        if (state.defaultPaymentMethod?.id === action.payload) {
          state.defaultPaymentMethod = null
        }
      })
      .addCase(removePaymentMethod.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Set default payment method
    builder
      .addCase(setDefaultPaymentMethod.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(setDefaultPaymentMethod.fulfilled, (state, action) => {
        state.isLoading = false
        // Update all payment methods
        state.paymentMethods = state.paymentMethods.map(pm => ({
          ...pm,
          isDefault: pm.id === action.payload.id
        }))
        state.defaultPaymentMethod = action.payload
      })
      .addCase(setDefaultPaymentMethod.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Subscribe to plan
    builder
      .addCase(subscribeToPlan.pending, (state) => {
        state.isUpdatingSubscription = true
        state.error = null
      })
      .addCase(subscribeToPlan.fulfilled, (state, action) => {
        state.isUpdatingSubscription = false
        state.subscription = action.payload
      })
      .addCase(subscribeToPlan.rejected, (state, action) => {
        state.isUpdatingSubscription = false
        state.error = action.payload as string
      })
    
    // Cancel subscription
    builder
      .addCase(cancelSubscription.pending, (state) => {
        state.isUpdatingSubscription = true
        state.error = null
      })
      .addCase(cancelSubscription.fulfilled, (state, action) => {
        state.isUpdatingSubscription = false
        state.subscription = action.payload
      })
      .addCase(cancelSubscription.rejected, (state, action) => {
        state.isUpdatingSubscription = false
        state.error = action.payload as string
      })
    
    // Fetch invoices
    builder
      .addCase(fetchInvoices.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchInvoices.fulfilled, (state, action) => {
        state.isLoading = false
        state.invoices = action.payload
      })
      .addCase(fetchInvoices.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Fetch transactions
    builder
      .addCase(fetchTransactions.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchTransactions.fulfilled, (state, action) => {
        state.isLoading = false
        state.transactions = action.payload
      })
      .addCase(fetchTransactions.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
    
    // Fetch usage stats
    builder
      .addCase(fetchUsageStats.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchUsageStats.fulfilled, (state, action) => {
        state.isLoading = false
        state.usageStats = action.payload
      })
      .addCase(fetchUsageStats.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.payload as string
      })
  }
})

// Export actions
export const {
  clearError,
  clearPaymentError,
  setPaymentError,
  updateSubscriptionStatus
} = billingSlice.actions

// Selectors
export const selectBilling = (state: { billing: BillingState }) => state.billing
export const selectSubscription = (state: { billing: BillingState }) => state.billing.subscription
export const selectPlans = (state: { billing: BillingState }) => state.billing.plans
export const selectPaymentMethods = (state: { billing: BillingState }) => state.billing.paymentMethods
export const selectDefaultPaymentMethod = (state: { billing: BillingState }) => state.billing.defaultPaymentMethod
export const selectInvoices = (state: { billing: BillingState }) => state.billing.invoices
export const selectTransactions = (state: { billing: BillingState }) => state.billing.transactions
export const selectUsageStats = (state: { billing: BillingState }) => state.billing.usageStats
export const selectBillingError = (state: { billing: BillingState }) => state.billing.error
export const selectPaymentError = (state: { billing: BillingState }) => state.billing.paymentError
export const selectIsProcessingPayment = (state: { billing: BillingState }) => state.billing.isProcessingPayment
export const selectIsUpdatingSubscription = (state: { billing: BillingState }) => state.billing.isUpdatingSubscription

// Export reducer
export default billingSlice.reducer