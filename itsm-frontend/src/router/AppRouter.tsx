// Router - Application routes configuration

import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { AuthProvider, ProtectedRoute, Roles } from '../auth';
import { AppLayout, AuthLayout } from '../components/layout';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { TicketListPage, TicketDetailPage, CreateTicketPage } from '../pages/user';
import { QueuePage, MyTicketsPage, EmailInboxPage, MyPerformancePage } from '../pages/employee';
import { TeamPage, AdvancedAnalyticsPage } from '../pages/manager';

/**
 * Role requirements for protected routes
 */
const EMPLOYEE_ROLES = [Roles.EMPLOYEE, Roles.MANAGER, Roles.ADMIN];
const MANAGER_ROLES = [Roles.MANAGER, Roles.ADMIN];

/**
 * Application router configuration
 */
const router = createBrowserRouter([
    {
        // Auth layout (login, etc.)
        element: <AuthLayout />,
        children: [
            {
                path: '/login',
                element: <LoginPage />,
            },
        ],
    },
    {
        // Main app layout (authenticated)
        element: <AppLayout />,
        children: [
            // Default redirect to dashboard
            {
                path: '/',
                element: <Navigate to="/dashboard" replace />,
            },

            // Dashboard (default landing page)
            {
                path: '/dashboard',
                element: (
                    <ProtectedRoute>
                        <DashboardPage />
                    </ProtectedRoute>
                ),
            },

            // User routes (any authenticated user)
            {
                path: '/tickets',
                element: (
                    <ProtectedRoute>
                        <TicketListPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/tickets/new',
                element: (
                    <ProtectedRoute>
                        <CreateTicketPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/tickets/:id',
                element: (
                    <ProtectedRoute>
                        <TicketDetailPage />
                    </ProtectedRoute>
                ),
            },

            // Employee routes (EMPLOYEE, MANAGER, ADMIN)
            {
                path: '/employee/queue',
                element: (
                    <ProtectedRoute requiredRoles={EMPLOYEE_ROLES}>
                        <QueuePage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/employee/tickets',
                element: (
                    <ProtectedRoute requiredRoles={EMPLOYEE_ROLES}>
                        <MyTicketsPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/employee/emails',
                element: (
                    <ProtectedRoute requiredRoles={EMPLOYEE_ROLES}>
                        <EmailInboxPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/employee/performance',
                element: (
                    <ProtectedRoute requiredRoles={EMPLOYEE_ROLES}>
                        <MyPerformancePage />
                    </ProtectedRoute>
                ),
            },

            // Manager routes (MANAGER, ADMIN)
            {
                path: '/manager/team',
                element: (
                    <ProtectedRoute requiredRoles={MANAGER_ROLES}>
                        <TeamPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: '/manager/analytics',
                element: (
                    <ProtectedRoute requiredRoles={MANAGER_ROLES}>
                        <AdvancedAnalyticsPage />
                    </ProtectedRoute>
                ),
            },

            // 404 fallback
            {
                path: '*',
                element: (
                    <div className="page not-found-page">
                        <h1>404 - Page Not Found</h1>
                        <p>The page you're looking for doesn't exist.</p>
                        <a href="/dashboard">Go to Dashboard</a>
                    </div>
                ),
            },
        ],
    },
]);

/**
 * App Router component
 * Wraps router with AuthProvider
 */
export function AppRouter() {
    return (
        <AuthProvider>
            <RouterProvider router={router} />
        </AuthProvider>
    );
}
