// Layout Components - AppLayout and AuthLayout
// Provides consistent page structure for authenticated and auth routes

import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { FAB } from '../pwa';

/**
 * Main application layout for authenticated users
 * Includes Navbar, Sidebar, and main content area
 */
export function AppLayout() {
    return (
        <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col">
            {/* Top Navigation */}
            <Navbar />

            <div className="flex flex-1 pt-16">
                {/* Side Navigation */}
                <Sidebar />

                {/* Main Content Area */}
                <main className="flex-1 p-6 overflow-auto">
                    <Outlet />
                </main>
            </div>

            {/* Floating Action Button for quick ticket creation */}
            <FAB />
        </div>
    );
}

/**
 * Auth layout for login, register, password reset pages
 * Simple centered layout without navigation
 */
export function AuthLayout() {
    return (
        <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex items-center justify-center">
            <Outlet />
        </div>
    );
}
