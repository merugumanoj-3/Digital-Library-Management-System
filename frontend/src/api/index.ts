import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach access token to every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return apiClient(original);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ─── API functions ────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; username: string; full_name: string; password: string }) =>
    apiClient.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    apiClient.post('/auth/login', data),
  refresh: (refresh_token: string) =>
    apiClient.post('/auth/refresh', { refresh_token }),
  me: () => apiClient.get('/auth/me'),
  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) =>
    apiClient.post('/auth/reset-password', { token, new_password }),
  changePassword: (current_password: string, new_password: string) =>
    apiClient.post('/auth/change-password', { current_password, new_password }),
};

export const booksApi = {
  list: (params?: Record<string, unknown>) => apiClient.get('/books', { params }),
  get: (id: string) => apiClient.get(`/books/${id}`),
  featured: () => apiClient.get('/books/featured'),
  trending: () => apiClient.get('/books/trending'),
  newArrivals: () => apiClient.get('/books/new-arrivals'),
  create: (data: unknown) => apiClient.post('/books', data),
  update: (id: string, data: unknown) => apiClient.put(`/books/${id}`, data),
  delete: (id: string) => apiClient.delete(`/books/${id}`),
  getReviews: (id: string) => apiClient.get(`/books/${id}/reviews`),
  addReview: (id: string, data: { rating: number; comment?: string }) =>
    apiClient.post(`/books/${id}/reviews`, data),
  addFavourite: (id: string) => apiClient.post(`/books/${id}/favourite`),
  removeFavourite: (id: string) => apiClient.delete(`/books/${id}/favourite`),
};

export const usersApi = {
  getProfile: () => apiClient.get('/users/me'),
  updateProfile: (data: unknown) => apiClient.put('/users/me', data),
  getDashboard: () => apiClient.get('/users/me/dashboard'),
  getReadingHistory: () => apiClient.get('/users/me/reading-history'),
  updateProgress: (bookId: string, data: { current_page: number; total_pages?: number }) =>
    apiClient.post(`/users/me/reading-progress/${bookId}`, data),
  getBookmarks: (bookId?: string) =>
    apiClient.get('/users/me/bookmarks', { params: bookId ? { book_id: bookId } : {} }),
  addBookmark: (data: { book_id: string; page_number: number; label?: string }) =>
    apiClient.post('/users/me/bookmarks', data),
  deleteBookmark: (id: string) => apiClient.delete(`/users/me/bookmarks/${id}`),
  getHighlights: (bookId?: string) =>
    apiClient.get('/users/me/highlights', { params: bookId ? { book_id: bookId } : {} }),
  addHighlight: (data: unknown) => apiClient.post('/users/me/highlights', data),
  getNotifications: () => apiClient.get('/users/me/notifications'),
  markNotificationRead: (id: string) =>
    apiClient.post(`/users/me/notifications/${id}/read`),
};

export const adminApi = {
  getStats: () => apiClient.get('/admin/stats'),
  listUsers: () => apiClient.get('/admin/users'),
  activateUser: (id: string) => apiClient.put(`/admin/users/${id}/activate`),
  deactivateUser: (id: string) => apiClient.put(`/admin/users/${id}/deactivate`),
  listAuthors: () => apiClient.get('/admin/authors'),
  createAuthor: (data: unknown) => apiClient.post('/admin/authors', data),
  deleteAuthor: (id: string) => apiClient.delete(`/admin/authors/${id}`),
  listCategories: () => apiClient.get('/admin/categories'),
  createCategory: (data: unknown) => apiClient.post('/admin/categories', data),
  getActivityLogs: () => apiClient.get('/admin/activity-logs'),
};

export const aiApi = {
  chat: (data: { book_id?: string; question: string; conversation_history?: unknown[] }) =>
    apiClient.post('/ai/chat', data),
  summarize: (book_id: string) => apiClient.post('/ai/summarize', { book_id }),
  generateMCQ: (book_id: string, num_questions = 5) =>
    apiClient.post('/ai/generate-mcq', { book_id, num_questions }),
  extractDefinitions: (book_id: string) =>
    apiClient.post('/ai/extract-definitions', { book_id }),
};

export const uploadApi = {
  uploadCover: (bookId: string, file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return apiClient.post(`/upload/cover/${bookId}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadPdf: (bookId: string, file: File) => {
    const fd = new FormData();
    fd.append('file', file);
    return apiClient.post(`/upload/pdf/${bookId}`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  processPdf: (bookId: string) => apiClient.post(`/upload/process-pdf/${bookId}`),
};

export const recommendationsApi = {
  personalized: () => apiClient.get('/recommendations/personalized'),
  similar: (bookId: string) => apiClient.get(`/recommendations/similar/${bookId}`),
  trending: () => apiClient.get('/recommendations/trending'),
};
