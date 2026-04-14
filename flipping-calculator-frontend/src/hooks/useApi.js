import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { itemsApi, flipsApi, portfolioApi, settingsApi, priceHistoryApi, conversionsApi, marginsApi } from '../services/api';
import { useAppStore } from '../stores/appStore';
import api from '../services/api';

// Helper to get account ID for query keys
const getAccountId = () => useAppStore.getState().currentAccount?.id || 0;

// Margins hooks
export const useMargins = (itemId, period = '168', interval = '1h') => {
  return useQuery({
    queryKey: ['margins', itemId, period, interval],
    queryFn: async () => {
      const response = await marginsApi.getAnalysis(itemId, period, interval);
      return response.data;
    },
    enabled: !!itemId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Items hooks
export const useItems = () => {
  return useQuery({
    queryKey: ['items'],
    queryFn: async () => {
      const response = await itemsApi.getAll();
      return response.data;
    },
  });
};

export const useItemSearch = (query) => {
  return useQuery({
    queryKey: ['items', 'search', query],
    queryFn: async () => {
      const response = await itemsApi.search(query);
      return response.data;
    },
    enabled: !!query && query.length > 0,
  });
};

export const usePriceHistory = (itemId, timestep = '5m') => {
  return useQuery({
    queryKey: ['items', 'price-history', itemId, timestep],
    queryFn: async () => {
      const response = await itemsApi.getPriceHistory(itemId, timestep);
      return response.data;
    },
    enabled: !!itemId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useTrajectory = (itemId, timestep = '1h') => {
  return useQuery({
    queryKey: ['items', 'trajectory', itemId, timestep],
    queryFn: async () => {
      const response = await itemsApi.getTrajectory(itemId, timestep);
      return response.data;
    },
    enabled: !!itemId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Don't retry aggressively - 422 means not enough data
  });
};

export const useItemSync = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: itemsApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
  });
};

export const useItemWithPrices = (itemId, cash) => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['items', 'prices', itemId, cash, accountId],
    queryFn: async () => {
      const response = await itemsApi.getWithPrices(itemId, cash);
      return response.data;
    },
    enabled: !!itemId,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
};

// Flips hooks
export const useFlipSearch = (params) => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['flips', 'search', params, accountId],
    queryFn: async () => {
      const response = await flipsApi.search(params);
      return response.data;
    },
    enabled: !!params,
  });
};

export const useTrendingFlips = (params) => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['flips', 'trending', params, accountId],
    queryFn: async () => {
      const response = await flipsApi.trending(params);
      return response.data;
    },
    enabled: !!params,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useFlipStats = () => {
  return useQuery({
    queryKey: ['flips', 'stats'],
    queryFn: async () => {
      const response = await flipsApi.getStats();
      return response.data;
    },
  });
};

// Portfolio hooks
export const usePortfolioSummary = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'summary', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getSummary();
      return response.data;
    },
    staleTime: 1000 * 30, // 30 seconds - portfolio data changes on user action
  });
};

export const usePortfolioStatistics = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'statistics', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getStatistics();
      return response.data;
    },
    staleTime: 1000 * 60, // 1 minute
  });
};

export const useRecoveryAnalysis = (flipId) => {
  return useQuery({
    queryKey: ['portfolio', 'recovery', flipId],
    queryFn: async () => {
      const response = await portfolioApi.getRecoveryAnalysis(flipId);
      return response.data;
    },
    enabled: !!flipId,
    staleTime: 1000 * 60 * 5, // 5 minutes - 6h data doesn't change fast
  });
};

export const usePendingFlips = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'pending', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getPending();
      return response.data;
    },
  });
};

export const usePendingProjections = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'pending', 'projections', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getPendingProjections();
      return response.data;
    },
    staleTime: 1000 * 60, // 1 minute - live prices don't need constant refresh
  });
};

export const useCompletedFlips = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'completed', accountId],
    queryFn: async () => {
      const response = await portfolioApi.getCompleted();
      return response.data;
    },
  });
};

export const useMutations = (limit = 50) => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['portfolio', 'mutations', accountId, limit],
    queryFn: async () => {
      const response = await portfolioApi.getMutations(limit);
      return response.data;
    },
  });
};

export const useFlipDetails = (flipId) => {
  return useQuery({
    queryKey: ['portfolio', 'flip', flipId],
    queryFn: async () => {
      const response = await portfolioApi.getFlipDetails(flipId);
      return response.data;
    },
    enabled: !!flipId,
  });
};

// Portfolio mutations
export const useBuyFlip = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.buy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
    },
  });
};

export const useAddToFlip = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.add,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
    },
  });
};

export const useSellFlip = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.sell,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
    },
  });
};

export const useAddBuy = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.add,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

export const useCancelFlip = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

export const useAdjustIntended = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: portfolioApi.adjustIntended,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

export const useUpdateBuyPrice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ flipId, newPrice }) => portfolioApi.updateBuyPrice(flipId, newPrice),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'mutations'] });
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
  });
};

// Liquidity insights
export const useLiquidityInsights = (itemId, hours = 168) => {
  return useQuery({
    queryKey: ['liquidity', itemId, hours],
    queryFn: async () => {
      const response = await api.get(`/api/items/${itemId}/liquidity`, {
        params: { hours }
      });
      return response.data;
    },
    enabled: !!itemId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Settings
export const useSettings = () => {
  const accountId = getAccountId();
  return useQuery({
    queryKey: ['settings', accountId],
    queryFn: async () => {
      const response = await settingsApi.get();
      return response.data;
    },
    staleTime: 10 * 1000, // 10 seconds
    refetchOnMount: 'always', // Always refetch when component mounts
  });
};

export const useSetCash = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: settingsApi.setCash,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });
};

// Price History & Polling Hooks
export const usePriceHistoryStats = () => {
  return useQuery({
    queryKey: ['price-history', 'stats'],
    queryFn: async () => {
      const response = await priceHistoryApi.getStats();
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds to see polling progress
  });
};

export const useTriggerPoll = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: priceHistoryApi.triggerPoll,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-history', 'stats'] });
    },
  });
};

// Conversions hooks
export const useConversions = () => {
  return useQuery({
    queryKey: ['conversions'],
    queryFn: async () => {
      const response = await conversionsApi.getAll();
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useConversionSync = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: conversionsApi.sync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversions'] });
    },
  });
};

export const useSetPollingEnabled = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enabled) => priceHistoryApi.setPollingEnabled(enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['price-history', 'stats'] });
    },
  });
};
