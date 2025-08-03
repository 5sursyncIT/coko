import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/auth-slice'
import uiReducer from './slices/ui-slice'
import catalogReducer from './slices/catalog-slice'
import readingReducer from './slices/reading-slice'
import billingReducer from './slices/billing-slice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    catalog: catalogReducer,
    reading: readingReducer,
    billing: billingReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export default store