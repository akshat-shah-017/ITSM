// Types - User domain types

/**
 * Reference to a user (minimal embedded object)
 * Used when a user is referenced within another resource
 */
export interface UserRef {
    id: string;
    name: string;
    email?: string;
}

/**
 * Full user profile returned by /api/auth/me/
 * Contains complete user information including roles and organization
 */
export interface User {
    id: string;
    name: string;
    email: string;
    alias: string | null;
    phone: string | null;
    roles: string[]; // Array of role names: "USER", "EMPLOYEE", etc.
    is_active: boolean;
    last_login: string | null;
    // Organization hierarchy
    team: { id: string; name: string } | null;
    department: { id: string; name: string } | null;
    company: { id: string; name: string } | null;
    business_group: { id: string; name: string } | null;
}

/**
 * Login response from POST /api/auth/login/
 */
export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    expires_in: number; // In seconds (900 = 15 min)
    user: {
        id: string;
        name: string;
        email: string;
        roles: string[];
    };
}

/**
 * Token refresh response from POST /api/auth/refresh/
 */
export interface RefreshResponse {
    access_token: string;
    expires_in: number;
}

/**
 * Team member info for manager views
 */
export interface TeamMember {
    id: string;
    name: string;
    email: string;
}
