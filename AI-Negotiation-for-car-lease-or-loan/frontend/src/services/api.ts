/**
 * Axios client + all API calls
 *
 * Token strategy:
 *  - Request interceptor: reads access token from Zustand store (in-memory).
 *  - Response interceptor: on 401, silently calls POST /auth/refresh once,
 *    updates the in-memory token, then retries the original request.
 *    If refresh also fails → logout + redirect to home.
 *
 * Multiple simultaneous 401s are handled by the subscriber queue so that
 * only one refresh call is ever in-flight at a time.
 */
import axios, { AxiosRequestConfig } from "axios";
import { UserRead } from "../types";
import { isAccessTokenValid, useAuthStore } from "../store/authStore";
import { API_BASE_URL } from "../config/apiBaseUrl";

const BASE_URL = API_BASE_URL;

export const axiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true, // send HTTP-only refresh_token cookie on every request
});

// ── Request interceptor — attach in-memory access token ──────────────────────
axiosInstance.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (isAccessTokenValid(token)) {
    config.headers.Authorization = `Bearer ${token}`;
  } else if (token) {
    useAuthStore.setState({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    });
  }
  return config;
});

// ── Refresh machinery ─────────────────────────────────────────────────────────
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function notifySubscribers(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// ── Response interceptor — silent refresh on 401 ─────────────────────────────
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest: AxiosRequestConfig & { _retry?: boolean } =
      error.config;

    const is401 = error.response?.status === 401;
    const isAuthEndpoint =
      originalRequest?.url?.includes("/auth/login") ||
      originalRequest?.url?.includes("/auth/refresh");

    if (!is401 || isAuthEndpoint || originalRequest._retry) {
      return Promise.reject(error);
    }

    // If another request is already refreshing, queue this one
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh((newToken) => {
          if (!newToken) {
            reject(error);
            return;
          }
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
          } else {
            originalRequest.headers = { Authorization: `Bearer ${newToken}` };
          }
          originalRequest._retry = true;
          resolve(axiosInstance(originalRequest));
        });
      });
    }

    // First request to hit a 401 — do the refresh
    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const newToken = await useAuthStore.getState().refreshAccessToken();

      if (!newToken) {
        // Refresh token has also expired — send user to home
        notifySubscribers("");
        window.location.href = "/";
        return Promise.reject(error);
      }

      notifySubscribers(newToken);
      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
      } else {
        originalRequest.headers = { Authorization: `Bearer ${newToken}` };
      }
      return axiosInstance(originalRequest);
    } catch {
      notifySubscribers("");
      window.location.href = "/";
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);

// ── API calls ─────────────────────────────────────────────────────────────────
export const api = {
  auth: {
    login: async (email: string, password: string) => {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);
      const res = await axiosInstance.post("/auth/login", params);
      return res.data as {
        access_token: string;
        token_type: string;
        user: UserRead;
      };
    },

    register: async (data: {
      email: string;
      password: string;
      full_name?: string;
    }) => {
      const res = await axiosInstance.post("/auth/register", data);
      return res.data;
    },

    me: async (): Promise<UserRead> => {
      const res = await axiosInstance.get("/auth/me");
      return res.data;
    },

    // POST /auth/refresh is called internally via fetch (see authStore).
    // Exposing a helper here for explicit use if needed.
    refresh: async () => {
      const res = await axiosInstance.post("/auth/refresh");
      return res.data as {
        access_token: string;
        token_type: string;
        user: UserRead;
      };
    },

    logout: async () => {
      await axiosInstance.post("/auth/logout");
    },

    forgotPassword: async (email: string) => {
      const res = await axiosInstance.post("/auth/forgot-password", { email });
      return res.data;
    },

    checkResetToken: async (token: string) => {
      const res = await axiosInstance.post("/auth/check-reset-token", {
        token,
      });
      return res.data;
    },

    resetPassword: async (token: string, new_password: string) => {
      const res = await axiosInstance.post("/auth/reset-password", {
        token,
        new_password,
      });
      return res.data;
    },
  },

  documents: {
    upload: async (formData: FormData) => {
      const res = await axiosInstance.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return res.data;
    },
    list: async () => {
      const res = await axiosInstance.get("/documents/list");
      return res.data;
    },
    getById: async (doc_id: string, _includeText?: boolean) => {
      const res = await axiosInstance.get(`/documents/${doc_id}`);
      return res.data;
    },
    getStatus: async (doc_id: string) => {
      const res = await axiosInstance.get(`/documents/${doc_id}/status`);
      return res.data;
    },
    delete: async (doc_id: string) => {
      await axiosInstance.delete(`/documents/${doc_id}`);
    },
    retrySLA: async (doc_id: string) => {
      const res = await axiosInstance.post(`/documents/${doc_id}/retry-sla`);
      return res.data;
    },
    analyseStream: async (doc_id: string) => {
      const token = useAuthStore.getState().accessToken;
      return fetch(`${BASE_URL}/documents/${doc_id}/analyse-stream`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
    },
  },

  chat: {
    newThread: async (doc_id: string) => {
      const res = await axiosInstance.post("/chat/new-thread", { doc_id });
      return res.data;
    },
    getHistory: async (thread_id: string, page: number = 1) => {
      const res = await axiosInstance.get(
        `/chat/history/${thread_id}?page=${page}`,
      );
      return res.data;
    },
    listThreads: async (doc_id: string) => {
      const res = await axiosInstance.get(`/chat/threads/${doc_id}`);
      return res.data;
    },
    deleteThread: async (thread_id: string) => {
      await axiosInstance.delete(`/chat/thread/${thread_id}`);
    },
  },

  vin: {
    lookup: async (vin: string, doc_id?: string) => {
      const url = doc_id
        ? `/vin/lookup/${vin}?doc_id=${doc_id}`
        : `/vin/lookup/${vin}`;
      const res = await axiosInstance.get(url);
      return res.data;
    },
    fromDocument: async (doc_id: string) => {
      const res = await axiosInstance.get(`/vin/from-document/${doc_id}`);
      return res.data;
    },
  },

  compare: {
    twoContracts: async (doc_id_1: string, doc_id_2: string) => {
      const res = await axiosInstance.get(
        `/compare/?doc_id_1=${encodeURIComponent(doc_id_1)}&doc_id_2=${encodeURIComponent(doc_id_2)}`,
      );
      return res.data;
    },
  },

  admin: {
    getStats: async () => {
      const res = await axiosInstance.get("/admin/stats");
      return res.data;
    },
    getLogs: async (limit: number = 20) => {
      const res = await axiosInstance.get(`/admin/logs?limit=${limit}`);
      return res.data;
    },
  },
};
