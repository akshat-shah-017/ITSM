// Components - Time Elapsed
// Displays relative time since a given date

interface TimeElapsedProps {
    /** ISO date string */
    date: string;
    /** Show as badge style */
    badge?: boolean;
    /** Show clock icon */
    showIcon?: boolean;
}

/**
 * Calculate and display time elapsed since a date
 * Shows "X hours/days ago" format
 * Highlights urgent (>7 days) and warning (>3 days) states
 */
export function TimeElapsed({ date, badge = false, showIcon = false }: TimeElapsedProps) {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now.getTime() - then.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    let text: string;
    let urgency: 'normal' | 'warning' | 'urgent' = 'normal';

    if (diffDays > 0) {
        text = `${diffDays}d ago`;
        if (diffDays >= 7) {
            urgency = 'urgent';
        } else if (diffDays >= 3) {
            urgency = 'warning';
        }
    } else if (diffHours > 0) {
        text = `${diffHours}h ago`;
    } else {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        text = diffMins <= 0 ? 'Just now' : `${diffMins}m ago`;
    }

    const className = badge
        ? `time-elapsed-badge ${urgency}`
        : `time-elapsed ${urgency}`;

    return (
        <span className={className}>
            {showIcon && <span className="time-elapsed-icon">⏱</span>}
            {text}
        </span>
    );
}

/**
 * Format time elapsed as just a string (for use in other components)
 */
export function formatTimeElapsed(date: string): string {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now.getTime() - then.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return diffMins <= 0 ? 'Just now' : `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    }
}
