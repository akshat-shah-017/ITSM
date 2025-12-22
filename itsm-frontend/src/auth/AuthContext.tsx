// Auth - Context and Provider

import { createContext, useCallback, useEffect, useState } from 'react';
import type { User } from '../types/user';
import { login as apiLogin, logout as apiLogout, getMe, refreshToken as apiRefresh } from '../api/auth';
import { getAccessToken, clearTokens, hasPersistedSession, setAccessToken } from './tokenStorage';

/**
 * Auth context value interface
 */
export interface AuthContextValue {
    /** Current authenticated user, or null if not logged in */
    user: User | null;
    /** Whether user is currently authenticated */
    isAuthenticated: boolean;
    /** Whether auth state is being loaded */
    isLoading: boolean;
    /** Login with email and password */
    login: (email: string, password: string) => Promise<void>;
    /** Logout and clear session */
    logout: () => Promise<void>;
    /** Force refresh user data from server */
    refreshUser: () => Promise<void>;
}

/**
 * Auth context - provides authentication state and actions
 */
export const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Auth provider props
 */
interface AuthProviderProps {
    children: React.ReactNode;
}

/**
 * Auth provider component
 * Wraps the app and provides authentication state
 */
export function AuthProvider({ children }: AuthProviderProps) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    /**
     * Load user data from API using stored token
     */
    const loadUser = useCallback(async () => {
        const token = getAccessToken();

        if (!token) {
            setUser(null);
            setIsLoading(false);
            return;
        }

        try {
            const userData = await getMe();
            setUser(userData);
        } catch (error) {
            // Token invalid or expired - clear everything
            console.error('Failed to load user:', error);
            clearTokens();
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    /**
     * Attempt to restore session from persisted refresh token
     * Called on app load to enable session persistence across page refresh
     */
    const tryRestoreSession = useCallback(async () => {
        // Check if we already have a valid access token in memory
        if (getAccessToken()) {
            await loadUser();
            return;
        }

        // Check if there's a persisted refresh token
        if (!hasPersistedSession()) {
            setIsLoading(false);
            return;
        }

        // Attempt silent token refresh
        try {
            const response = await apiRefresh();
            setAccessToken(response.access_token, response.expires_in);
            await loadUser();
        } catch (error) {
            // Refresh failed - session expired, clear tokens
            console.log('Session expired, please login again');
            clearTokens();
            setUser(null);
            setIsLoading(false);
        }
    }, [loadUser]);

    /**
     * Login with email and password
     */
    const login = useCallback(async (email: string, password: string) => {
        setIsLoading(true);
        try {
            const response = await apiLogin(email, password);
            // Set user from login response initially
            setUser({
                id: response.user.id,
                name: response.user.name,
                email: response.user.email,
                roles: response.user.roles,
                alias: null,
                phone: null,
                is_active: true,
                last_login: null,
                team: null,
                department: null,
                company: null,
                business_group: null,
            });
            // Then fetch full user profile
            await loadUser();
        } catch (error) {
            clearTokens();
            setUser(null);
            throw error;
        } finally {
            setIsLoading(false);
        }
    }, [loadUser]);

    /**
     * Logout and clear session
     */
    const logout = useCallback(async () => {
        setIsLoading(true);
        try {
            await apiLogout();
        } finally {
            setUser(null);
            setIsLoading(false);
        }
    }, []);

    /**
     * Force refresh user data
     */
    const refreshUser = useCallback(async () => {
        await loadUser();
    }, [loadUser]);

    // Attempt to restore session on mount (handles page refresh)
    useEffect(() => {
        tryRestoreSession();
    }, [tryRestoreSession]);

    // Listen for 401 errors and trigger logout
    useEffect(() => {
        const handleUnauthorized = () => {
            clearTokens();
            setUser(null);
        };

        // Add global event listener for unauthorized events
        window.addEventListener('auth:unauthorized', handleUnauthorized);

        return () => {
            window.removeEventListener('auth:unauthorized', handleUnauthorized);
        };
    }, []);

    const value: AuthContextValue = {
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}
