import { configureStore } from '@reduxjs/toolkit'
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import authSlice from './slices/auth-slice'
import catalogSlice from './slices/catalog-slice'
import readingSlice from './slices/reading-slice'
import billingSlice from './slices/billing-slice'
import uiSlice from './slices/ui-slice'

// Configure the Redux store
export const store = configureStore({
  reducer: {
    auth: authSlice,
    catalog: catalogSlice,
    reading: readingSlice,
    billing: billingSlice,
    ui: uiSlice
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for serialization checks
        ignoredActions: [
          'persist/PERSIST',
          'persist/REHYDRATE',
          'persist/PAUSE',
          'persist/PURGE',
          'persist/REGISTER'
        ],
        // Ignore these field paths in all actions
        ignoredActionsPaths: ['meta.arg', 'payload.timestamp'],
        // Ignore these paths in the state
        ignoredPaths: ['items.dates']
      },
      // Optimized for African networks - reduce middleware overhead
      immutableCheck: process.env.NODE_ENV === 'development',
      thunk: {
        extraArgument: {
          // Add any extra arguments for thunks here
        }
      }
    }),
  devTools: process.env.NODE_ENV === 'development' && {
    name: 'Coko App',
    trace: true,
    traceLimit: 25
  }
})

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector

// Export store for use in providers
export default store