// Auth - Protected Route component

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';
import { hasAnyRole as checkHasAnyRole } from './roles';

/**
 * Props for ProtectedRoute component
 */
interface ProtectedRouteProps {
    /** Child components to render when authorized */
    children: React.ReactNode;
    /** Required role IDs (user must have at least one) */
    requiredRoles?: number[];
    /** Redirect path for unauthenticated users (default: /login) */
    loginPath?: string;
    /** Redirect path for unauthorized users (default: /tickets) */
    fallbackPath?: string;
}

/**
 * Protected Route component
 * Redirects to login if not authenticated
 * Redirects to fallback if missing required roles
 */
export function ProtectedRoute({
    children,
    requiredRoles,
    loginPath = '/login',
    fallbackPath = '/tickets',
}: ProtectedRouteProps) {
    const { isAuthenticated, isLoading, user } = useAuth();
    const location = useLocation();

    // Show loading state while checking auth
    if (isLoading) {
        return (
            <div className="loading-container">
                <div className="loading-spinner" />
                <p>Loading...</p>
            </div>
        );
    }

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
        // Save the attempted URL for redirect after login
        return <Navigate to={loginPath} state={{ from: location }} replace />;
    }

    // Check role requirements if specified
    if (requiredRoles && requiredRoles.length > 0) {
        const userRoles = user?.roles ?? [];

        if (!checkHasAnyRole(userRoles, requiredRoles)) {
            // User doesn't have required role - redirect to fallback
            return <Navigate to={fallbackPath} replace />;
        }
    }

    // Authorized - render children
    return <>{children}</>;
}

/**
 * Higher-order component version of ProtectedRoute
 */
export function withProtectedRoute<P extends object>(
    Component: React.ComponentType<P>,
    requiredRoles?: number[]
) {
    return function WrappedComponent(props: P) {
        return (
            <ProtectedRoute requiredRoles={requiredRoles}>
                <Component {...props} />
            </ProtectedRoute>
        );
    };
}
