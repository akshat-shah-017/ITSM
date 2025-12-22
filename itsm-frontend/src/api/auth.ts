// API - Authentication endpoints

import axios from 'axios';
import { post, get } from './client';
import type { User, LoginResponse, RefreshResponse } from '../types/user';
import {
    setAccessToken,
    setRefreshToken,
    getRefreshToken,
    clearTokens,
} from '../auth/tokenStorage';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5003';

/**
 * Login with email and password
 * Stores tokens and returns user data
 */
export async function login(email: string, password: string): Promise<LoginResponse> {
    // Use direct axios call to avoid interceptors for login
    const response = await axios.post<LoginResponse>(`${BASE_URL}/api/auth/login/`, {
        email,
        password,
    });

    const { access_token, refresh_token, expires_in } = response.data;

    // Store tokens
    setAccessToken(access_token, expires_in);
    setRefreshToken(refresh_token);

    return response.data;
}

/**
 * Refresh the access token
 * Uses the stored refresh token
 */
export async function refreshToken(): Promise<RefreshResponse> {
    const currentRefreshToken = getRefreshToken();

    if (!currentRefreshToken) {
        throw new Error('No refresh token available');
    }

    const response = await axios.post<RefreshResponse>(`${BASE_URL}/api/auth/refresh/`, {
        refresh_token: currentRefreshToken,
    });

    const { access_token, expires_in } = response.data;
    setAccessToken(access_token, expires_in);

    return response.data;
}

/**
 * Logout - invalidate the refresh token
 * Clears all stored tokens regardless of API response
 */
export async function logout(): Promise<void> {
    try {
        await post('/api/auth/logout/', {});
    } catch {
        // Ignore logout errors - we clear tokens anyway
    } finally {
        clearTokens();
    }
}

/**
 * Get current user profile
 */
export async function getMe(): Promise<User> {
    return get<User>('/api/auth/me/');
}
