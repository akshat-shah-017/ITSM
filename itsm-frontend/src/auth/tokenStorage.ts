// Auth - Token storage abstraction
// Hybrid approach: refresh token in localStorage, access token in memory
// This balances security (access token protected from XSS) with usability (survives refresh)

const REFRESH_TOKEN_KEY = 'itsm_refresh_token';

/**
 * In-memory access token storage.
 * Access tokens are kept in memory for XSS protection.
 */
let accessToken: string | null = null;
let tokenExpiresAt: number | null = null;

/**
 * Get the current access token
 */
export function getAccessToken(): string | null {
    return accessToken;
}

/**
 * Set the access token with expiry time
 * @param token - The JWT access token
 * @param expiresIn - Token lifetime in seconds
 */
export function setAccessToken(token: string, expiresIn: number): void {
    accessToken = token;
    // Store absolute expiry time
    tokenExpiresAt = Date.now() + expiresIn * 1000;
}

/**
 * Get the refresh token from localStorage
 */
export function getRefreshToken(): string | null {
    try {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch {
        // localStorage may be unavailable (private browsing, etc.)
        return null;
    }
}

/**
 * Set the refresh token in localStorage
 */
export function setRefreshToken(token: string): void {
    try {
        localStorage.setItem(REFRESH_TOKEN_KEY, token);
    } catch {
        // localStorage may be unavailable - token will only persist in memory
        console.warn('localStorage unavailable, refresh token will not persist');
    }
}

/**
 * Clear all tokens (on logout or auth failure)
 */
export function clearTokens(): void {
    accessToken = null;
    tokenExpiresAt = null;
    try {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    } catch {
        // Ignore localStorage errors
    }
}

/**
 * Check if the access token is about to expire
 * Returns true if token will expire within the threshold
 * @param thresholdSeconds - Seconds before expiry to consider "expiring soon" (default: 60)
 */
export function isTokenExpiringSoon(thresholdSeconds: number = 60): boolean {
    if (!tokenExpiresAt) return true;
    const thresholdMs = thresholdSeconds * 1000;
    return Date.now() >= tokenExpiresAt - thresholdMs;
}

/**
 * Check if we have a valid (non-expired) access token
 */
export function hasValidToken(): boolean {
    return accessToken !== null && !isTokenExpiringSoon(0);
}

/**
 * Get time until token expires in milliseconds
 * Returns 0 if no token or already expired
 */
export function getTokenTTL(): number {
    if (!tokenExpiresAt) return 0;
    const ttl = tokenExpiresAt - Date.now();
    return Math.max(0, ttl);
}

/**
 * Check if there's a persisted refresh token available
 * Used on app load to determine if we can attempt silent re-authentication
 */
export function hasPersistedSession(): boolean {
    return getRefreshToken() !== null;
}
