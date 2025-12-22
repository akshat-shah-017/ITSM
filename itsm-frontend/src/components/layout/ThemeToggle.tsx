// Theme Toggle Component
// Provides light/dark mode toggle with localStorage persistence
// Respects system preference on first load

import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

/**
 * Hook to manage theme state
 * - Reads initial preference from localStorage > system preference
 * - Persists changes to localStorage
 * - Toggles 'dark' class on document root
 */
function useTheme() {
    const [theme, setTheme] = useState<Theme>(() => {
        // Check if we're on the client side
        if (typeof window === 'undefined') return 'light';

        const stored = localStorage.getItem('theme') as Theme | null;
        if (stored) return stored;

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    });

    useEffect(() => {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.add('dark');
        } else {
            root.classList.remove('dark');
        }
        localStorage.setItem('theme', theme);
    }, [theme]);

    const toggle = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

    return { theme, toggle };
}

/**
 * Sun icon for light mode indication
 */
function SunIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
    );
}

/**
 * Moon icon for dark mode indication
 */
function MoonIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
    );
}

/**
 * Theme toggle button component
 * - Displays sun icon in dark mode (click to switch to light)
 * - Displays moon icon in light mode (click to switch to dark)
 * - Subtle hover/focus states for micro-interaction
 */
export function ThemeToggle() {
    const { theme, toggle } = useTheme();

    return (
        <button
            onClick={toggle}
            className="theme-toggle"
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
            {theme === 'light' ? <MoonIcon /> : <SunIcon />}
        </button>
    );
}
