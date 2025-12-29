// API - Central axios client with token refresh
// Implements single-flight pattern for refresh and request queuing

import axios from 'axios';
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import {
    getAccessToken,
    getRefreshToken,
    setAccessToken,
    clearTokens,
    isTokenExpiringSoon,
} from '../auth/tokenStorage';

// Get base URL from environment variable
// In production, VITE_API_BASE_URL must be set - localhost fallback only for dev
const BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:5003' : (() => { throw new Error('VITE_API_BASE_URL is required in production'); })());

/**
 * Create the axios instance with base configuration
 */
const apiClient: AxiosInstance = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Token refresh state
let isRefreshing = false;
let refreshQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
}> = [];

/**
 * Process queued requests after refresh completes
 */
function processQueue(error: unknown, token: string | null): void {
    refreshQueue.forEach((promise) => {
        if (error) {
            promise.reject(error);
        } else if (token) {
            promise.resolve(token);
        }
    });
    refreshQueue = [];
}

/**
 * Perform token refresh
 * Called when access token is expired or expiring soon
 */
async function refreshAccessToken(): Promise<string> {
    const refreshToken = getRefreshToken();

    if (!refreshToken) {
        throw new Error('No refresh token available');
    }

    try {
        // Use a separate axios instance to avoid interceptor loops
        const response = await axios.post(`${BASE_URL}/api/auth/refresh/`, {
            refresh_token: refreshToken,
        });

        const { access_token, expires_in } = response.data;
        setAccessToken(access_token, expires_in);
        return access_token;
    } catch (error) {
        // Refresh failed - clear all tokens
        clearTokens();
        throw error;
    }
}

/**
 * Request interceptor - inject authorization header
 */
apiClient.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
        // Skip auth header for auth endpoints
        const isAuthEndpoint =
            config.url?.includes('/api/auth/login') ||
            config.url?.includes('/api/auth/refresh');

        if (isAuthEndpoint) {
            return config;
        }

        let token = getAccessToken();

        // Proactively refresh if token is expiring soon (within 60s)
        if (token && isTokenExpiringSoon(60)) {
            if (!isRefreshing) {
                isRefreshing = true;
                try {
                    token = await refreshAccessToken();
                    processQueue(null, token);
                } catch (error) {
                    processQueue(error, null);
                    throw error;
                } finally {
                    isRefreshing = false;
                }
            } else {
                // Wait for ongoing refresh
                token = await new Promise<string>((resolve, reject) => {
                    refreshQueue.push({ resolve, reject });
                });
            }
        }

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

/**
 * Response interceptor - handle 401 errors with token refresh
 */
apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Only handle 401 errors
        if (error.response?.status !== 401 || !originalRequest) {
            return Promise.reject(error);
        }

        // Don't retry auth endpoints
        const isAuthEndpoint =
            originalRequest.url?.includes('/api/auth/login') ||
            originalRequest.url?.includes('/api/auth/refresh') ||
            originalRequest.url?.includes('/api/auth/logout');

        if (isAuthEndpoint) {
            return Promise.reject(error);
        }

        // Don't retry if we already retried
        if (originalRequest._retry) {
            clearTokens();
            // Redirect to login will be handled by AuthContext
            return Promise.reject(error);
        }

        originalRequest._retry = true;

        // Single-flight pattern: only one refresh at a time
        if (!isRefreshing) {
            isRefreshing = true;

            try {
                const newToken = await refreshAccessToken();
                processQueue(null, newToken);

                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return apiClient(originalRequest);
            } catch (refreshError) {
                processQueue(refreshError, null);
                clearTokens();
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        // Wait for ongoing refresh, then retry
        return new Promise((resolve, reject) => {
            refreshQueue.push({
                resolve: (token: string) => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    resolve(apiClient(originalRequest));
                },
                reject: (err: unknown) => {
                    reject(err);
                },
            });
        });
    }
);

export default apiClient;

/**
 * Type-safe GET request
 */
export async function get<T>(url: string, params?: object): Promise<T> {
    const response = await apiClient.get<T>(url, { params });
    return response.data;
}

/**
 * Type-safe POST request
 */
export async function post<T>(url: string, data?: unknown): Promise<T> {
    const response = await apiClient.post<T>(url, data);
    return response.data;
}

/**
 * Type-safe PATCH request
 */
export async function patch<T>(url: string, data?: unknown): Promise<T> {
    const response = await apiClient.patch<T>(url, data);
    return response.data;
}

/**
 * Type-safe DELETE request
 */
export async function del<T>(url: string): Promise<T> {
    const response = await apiClient.delete<T>(url);
    return response.data;
}
