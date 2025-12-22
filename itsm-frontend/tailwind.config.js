/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Primary Brand (Blackbox Red)
                primary: {
                    50: '#fef2f2',
                    100: '#fee2e2',
                    200: '#fecaca',
                    300: '#fca5a5',
                    400: '#f87171',
                    500: '#ef4444',
                    600: '#dc2626',
                    700: '#b91c1c',
                    800: '#991b1b',
                    900: '#7f1d1d',
                    950: '#450a0a',
                    DEFAULT: '#ed1c24',
                },
                // Surface (Pure Neutrals - no blue tint)
                surface: {
                    50: '#fafafa',
                    100: '#f5f5f5',
                    200: '#e5e5e5',
                    300: '#d4d4d4',
                    400: '#a3a3a3',
                    500: '#737373',
                    600: '#525252',
                    700: '#404040',
                    800: '#262626',
                    900: '#171717',
                    950: '#0a0a0a',
                },
                // Semantic Colors
                success: {
                    DEFAULT: '#22c55e',
                    light: '#dcfce7',
                    dark: 'rgba(34, 197, 94, 0.15)',
                },
                warning: {
                    DEFAULT: '#f59e0b',
                    light: '#fef3c7',
                    dark: 'rgba(245, 158, 11, 0.15)',
                },
                error: {
                    DEFAULT: '#ef4444',
                    light: '#fee2e2',
                    dark: 'rgba(239, 68, 68, 0.15)',
                },
                info: {
                    DEFAULT: '#3b82f6',
                    light: '#dbeafe',
                    dark: 'rgba(59, 130, 246, 0.15)',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            borderRadius: {
                'xl': '12px',
                '2xl': '16px',
                '3xl': '20px',
            },
            boxShadow: {
                'glass': '0 8px 32px rgba(0, 0, 0, 0.12)',
                'glass-dark': '0 8px 32px rgba(0, 0, 0, 0.4)',
                'glow': '0 0 20px rgba(237, 28, 36, 0.4)',
                'glow-sm': '0 0 10px rgba(237, 28, 36, 0.3)',
                'card': '0 4px 20px rgba(0, 0, 0, 0.08)',
                'card-dark': '0 4px 20px rgba(0, 0, 0, 0.3)',
            },
            backdropBlur: {
                'glass': '16px',
            },
            keyframes: {
                'fade-in': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'slide-up': {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-5px)' },
                },
            },
            animation: {
                'fade-in': 'fade-in 0.3s ease-out',
                'slide-up': 'slide-up 0.3s ease-out',
                'float': 'float 3s ease-in-out infinite',
            },
        },
    },
    plugins: [],
}
