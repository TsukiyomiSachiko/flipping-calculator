import axios from 'axios';
import { useAppStore } from '../stores/appStore';

// Use empty baseURL and explicit /api prefix for better proxy compatibility
const baseURL = '';

const api = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add X-Account-Id header and Authorization token
api.interceptors.request.use(
  (config) => {
    const { currentAccount, token } = useAppStore.getState();
    // Default to account ID 1 if none selected yet, to allow initial fetches
    config.headers['X-Account-Id'] = currentAccount?.id || 1;
    
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor for better error messages and token refresh handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized errors (expired token)
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      // If we failed refreshing itself, prevent loop and force logout
      if (originalRequest.url === '/api/auth/refresh') {
        const { logout } = useAppStore.getState();
        logout();
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { refreshToken, setToken, setRefreshToken, logout } = useAppStore.getState();

      if (!refreshToken) {
        logout();
        isRefreshing = false;
        return Promise.reject(error);
      }

      try {
        const response = await axios.post('/api/auth/refresh', { refresh_token: refreshToken });
        const { access_token, refresh_token } = response.data;

        setToken(access_token);
        setRefreshToken(refresh_token);

        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        processQueue(null, access_token);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        logout();
        isRefreshing = false;
        return Promise.reject(refreshErr);
      }
    }

    if (!error.response) {
      error.message = 'Cannot connect to API. Is the backend running?';
    } else if (error.response.status === 500) {
      const detail = error.response.data?.detail;
      error.message = detail || 'Server error. Please try again.';
    } else if (error.response.status === 400) {
      const detail = error.response.data?.detail;
      error.message = typeof detail === 'object' ? detail.error || JSON.stringify(detail) : detail || 'Invalid request.';
    } else if (error.response.status === 404) {
      error.message = 'Not found.';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/api/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  register: (name, password) => api.post('/api/auth/register', { name, password }),
};

// Accounts API
export const accountsApi = {
  getAll: () => api.get('/api/accounts'),
  create: (name) => api.post('/api/accounts', { name }),
  delete: (id) => api.delete(`/api/accounts/${id}`),
};

// Items API
export const itemsApi = {
  sync: () => api.post('/api/items/sync'),
  search: (query) => api.get('/api/items/search', { params: { q: query } }),
  getAll: () => api.get('/api/items'),
  getById: (id) => api.get(`/api/items/${id}`),
  getWithPrices: (id, cash) => api.get(`/api/items/${id}/prices`, { params: cash ? { cash } : {} }),
  clearCache: () => api.post('/api/items/clear-cache'),
  getPriceHistory: (itemId, timestep = '5m') => api.get(`/api/items/${itemId}/price-history`, { params: { timestep } }),
  getTrajectory: (itemId, timestep = '1h') => api.get(`/api/items/${itemId}/trajectory`, { params: { timestep } }),
};

// Flips API
export const flipsApi = {
  search: (params) => api.get('/api/flips/search', { params }),
  trending: (params) => api.get('/api/flips/trending', { params }),
  getStats: () => api.get('/api/flips/stats'),
};

// High-Alchemy API
export const alchApi = {
  getProfitable: (params) => api.get('/api/alch/profitable', { params }),
};

// Portfolio API
export const portfolioApi = {
  buy: (data) => api.post('/api/portfolio/buy', data),
  add: (data) => api.post('/api/portfolio/add', data),
  sell: (data) => api.post('/api/portfolio/sell', data),
  cancel: (flipId) => api.post('/api/portfolio/cancel', { flip_id: flipId }),
  deleteFlip: (flipId) => api.delete(`/api/portfolio/flip/${flipId}`),
  adjustIntended: (flipId) => api.patch(`/api/portfolio/flip/${flipId}/adjust-intended`),
  updateBuyPrice: (flipId, newPrice) => api.patch(`/api/portfolio/flip/${flipId}/buy-price`, { new_price: newPrice }),
  getPending: () => api.get('/api/portfolio/pending'),
  getPendingProjections: () => api.get('/api/portfolio/pending/projections'),
  getCompleted: () => api.get('/api/portfolio/completed'),
  getCancelled: () => api.get('/api/portfolio/cancelled'),
  getMutations: (limit = 50) => api.get('/api/portfolio/mutations', { params: { limit } }),
  getFlipDetails: (flipId) => api.get(`/api/portfolio/flips/${flipId}`),
  getSummary: () => api.get('/api/portfolio/summary'),
  getStatistics: () => api.get('/api/portfolio/statistics'),
  getRecoveryAnalysis: (flipId) => api.get(`/api/portfolio/recovery/${flipId}`),
  export: () => api.get('/api/portfolio/export', { responseType: 'blob' }),
  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/portfolio/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Settings API
export const settingsApi = {
  get: () => api.get('/api/settings'),
  setCash: (amount) => api.post('/api/settings/cash', { amount }),
  setCashflow: (data) => api.post('/api/settings/cashflow', data),
};

// Price History & Polling API
export const priceHistoryApi = {
  getStats: () => api.get('/api/price-history/stats'),
  triggerPoll: () => api.post('/api/price-history/poll/trigger'),
  setPollingEnabled: (enabled) => api.post(`/api/price-history/poll/enable?enabled=${enabled}`),
  cleanup: (days) => api.post(`/api/price-history/cleanup?days_to_keep=${days}`),
};

// Margins API
export const marginsApi = {
  getAnalysis: (itemId, hours = 168, interval = '1h') => 
    api.get(`/api/margins/item/${itemId}`, { params: { hours, interval } }),
};

  

  export default api;
