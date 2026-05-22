import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useAppStore = create(
  persist(
    (set) => ({
      // Account state
      accounts: [],
      currentAccount: null,
      token: null,
      refreshToken: null,
      setAccounts: (accounts) => set({ accounts }),
      setCurrentAccount: (account) => set({ currentAccount: account }),
      setToken: (token) => set({ token }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      logout: () => set({ token: null, refreshToken: null, currentAccount: null }),
      
      // Filter state
      filters: {
        minProfit: 0,
        minLimitProfit: null,
        minVolume: 0,
        minRoi: null,
        maxRoi: null,
        sortBy: 'profit',
        limit: 20,
        enableQualityFilter: false,
      },
      setFilters: (filters) => set((state) => ({ 
        filters: { ...state.filters, ...filters } 
      })),
      resetFilters: () => set({ 
        filters: {
          minProfit: 0,
          minLimitProfit: null,
          minVolume: 0,
          minRoi: null,
          maxRoi: null,
          sortBy: 'profit',
          limit: 20,
          enableQualityFilter: false,
        }
      }),

      // Active view
      activeView: 'flips', // 'flips', 'portfolio', 'history'
      setActiveView: (view) => set({ activeView: view }),

      // Alert settings
      alertSettings: {
        enableAlerts: true,
        lossThresholdPct: 10,
        enableSound: true,
        enableTabFlashing: true,
        enableInAppModal: true,
        alertPollInterval: 60,
      },
      setAlertSettings: (settings) => set((state) => ({
        alertSettings: { ...state.alertSettings, ...settings }
      })),
    }),
    {
      name: 'flipping-calculator-storage',
    }
  )
);