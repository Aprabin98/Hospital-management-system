import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { clearStoredAuthState, getStoredAuthState, setStoredAuthState } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface ApiError {
  message: string;
  status: number;
  data?: any;
}

interface ApiErrorResponse {
  message?: string;
  detail?: string;
  error?: string;
}

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

class APIClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor to add authentication token
    this.client.interceptors.request.use(
      (config) => {
        const { token } = getStoredAuthState();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as RetriableRequestConfig | undefined;
        const isUnauthorized = error.response?.status === 401;
        const requestUrl = originalRequest?.url || '';
        const isAuthRequest =
          requestUrl.includes('/auth/login/') ||
          requestUrl.includes('/auth/2fa-verify/') ||
          requestUrl.includes('/auth/refresh/');

        if (isUnauthorized && originalRequest && !originalRequest._retry && !isAuthRequest) {
          originalRequest._retry = true;
          const refreshedToken = await this.refreshAccessToken();

          if (refreshedToken) {
            originalRequest.headers.Authorization = `Bearer ${refreshedToken}`;
            return this.client(originalRequest);
          }
        }

        if (isUnauthorized) {
          this.handleExpiredSession();
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  private async refreshAccessToken(): Promise<string | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      const { refreshToken, userRole, user } = getStoredAuthState();
      if (!refreshToken) {
        return null;
      }

      try {
        const response = await axios.post<{ access: string; refresh?: string }>(
          `${API_BASE_URL}/auth/refresh/`,
          { refresh: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
            },
            timeout: 30000,
          }
        );

        const nextToken = response.data.access;
        const nextRefreshToken = response.data.refresh || refreshToken;
        setStoredAuthState({
          token: nextToken,
          refreshToken: nextRefreshToken,
          role: userRole,
          user,
        });

        return nextToken;
      } catch {
        this.handleExpiredSession();
        return null;
      } finally {
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  private handleExpiredSession() {
    clearStoredAuthState();
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  private formatError(error: AxiosError): ApiError {
    const responseData = error.response?.data as ApiErrorResponse;
    const message =
      responseData?.message ||
      responseData?.detail ||
      responseData?.error ||
      error.message ||
      'An error occurred';
    return {
      message,
      status: error.response?.status || 500,
      data: error.response?.data,
    };
  }

  // GET request
  async get<T = any>(url: string, config = {}): Promise<T> {
    try {
      const response = await this.client.get<T>(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // POST request
  async post<T = any>(url: string, data?: any, config = {}): Promise<T> {
    try {
      const response = await this.client.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // PUT request
  async put<T = any>(url: string, data?: any, config = {}): Promise<T> {
    try {
      const response = await this.client.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // PATCH request
  async patch<T = any>(url: string, data?: any, config = {}): Promise<T> {
    try {
      const response = await this.client.patch<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  // DELETE request
  async delete<T = any>(url: string, config = {}): Promise<T> {
    try {
      const response = await this.client.delete<T>(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

export const apiClient = new APIClient();
export type { ApiError };

