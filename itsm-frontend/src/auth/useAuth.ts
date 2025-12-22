// Auth - useAuth hook

import { useContext, useMemo } from 'react';
import { AuthContext } from './AuthContext';
import type { AuthContextValue } from './AuthContext';
import {
    Roles,
    hasRole,
    hasAnyRole,
    isAtLeastEmployee,
    isAtLeastManager,
    isAdmin,
} from './roles';

/**
 * Extended auth hook value with role helpers
 */
export interface UseAuthValue extends AuthContextValue {
    /** Check if user has a specific role by ID */
    hasRole: (roleId: number) => boolean;
    /** Check if user has any of the specified roles */
    hasAnyRole: (roleIds: number[]) => boolean;
    /** User is at least an employee (EMPLOYEE, MANAGER, or ADMIN) */
    isEmployee: boolean;
    /** User is at least a manager (MANAGER or ADMIN) */
    isManager: boolean;
    /** User is an admin */
    isAdmin: boolean;
    /** User's role names */
    roles: string[];
}

/**
 * Hook to access auth context with role helpers
 * Must be used within an AuthProvider
 */
export function useAuth(): UseAuthValue {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }

    const roles = context.user?.roles ?? [];

    // Memoize the extended value to prevent unnecessary re-renders
    return useMemo(() => ({
        ...context,
        roles,
        hasRole: (roleId: number) => hasRole(roles, roleId),
        hasAnyRole: (roleIds: number[]) => hasAnyRole(roles, roleIds),
        isEmployee: isAtLeastEmployee(roles),
        isManager: isAtLeastManager(roles),
        isAdmin: isAdmin(roles),
    }), [context, roles]);
}

// Re-export Roles constant for convenience
export { Roles };
