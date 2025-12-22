/**
 * Date formatting utilities with IST timezone
 * All dates displayed in Indian Standard Time (Asia/Kolkata)
 */

/**
 * Format a date string in IST timezone
 * @param dateString - ISO date string or null
 * @returns Formatted date string in IST
 */
export function formatDateIST(dateString: string | null): string {
    if (!dateString) return '—';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-IN', {
            timeZone: 'Asia/Kolkata',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return dateString;
    }
}

/**
 * Format a date string in IST without time (date only)
 * @param dateString - ISO date string or null
 * @returns Formatted date string in IST
 */
export function formatDateOnlyIST(dateString: string | null): string {
    if (!dateString) return '—';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            timeZone: 'Asia/Kolkata',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    } catch {
        return dateString;
    }
}

/**
 * Get time elapsed as a readable string
 * @param dateString - ISO date string
 * @returns Human readable elapsed time (e.g., "2d 5h ago", "30m ago")
 */
export function getTimeElapsedString(dateString: string): string {
    const now = new Date();
    const then = new Date(dateString);
    const diffMs = now.getTime() - then.getTime();

    if (diffMs < 0) return 'Just now';

    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays > 0) {
        const remainingHours = diffHours % 24;
        return remainingHours > 0 ? `${diffDays}d ${remainingHours}h ago` : `${diffDays}d ago`;
    }

    if (diffHours > 0) {
        const remainingMins = diffMins % 60;
        return remainingMins > 0 ? `${diffHours}h ${remainingMins}m ago` : `${diffHours}h ago`;
    }

    if (diffMins > 0) {
        return `${diffMins}m ago`;
    }

    return 'Just now';
}

/**
 * Get time elapsed in milliseconds
 * @param dateString - ISO date string
 * @returns Elapsed time in milliseconds
 */
export function getTimeElapsedMs(dateString: string): number {
    return Date.now() - new Date(dateString).getTime();
}

/**
 * Sort tickets by time elapsed (oldest first = longest wait time)
 * @param items - Array of items with created_at property
 * @returns Sorted array (oldest first)
 */
export function sortByAgeDescending<T extends { created_at: string }>(items: T[]): T[] {
    return [...items].sort((a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
}

/**
 * Get current time in IST formatted nicely
 * @returns Current time in IST
 */
export function getCurrentTimeIST(): string {
    return new Date().toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });
}
