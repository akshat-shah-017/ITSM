// Components - Loading Spinner

interface LoadingSpinnerProps {
    /** Size of the spinner */
    size?: 'small' | 'medium' | 'large';
    /** Optional message to display */
    message?: string;
}

/**
 * Simple loading spinner component
 */
export function LoadingSpinner({ size = 'medium', message }: LoadingSpinnerProps) {
    const sizeClass = `spinner-${size}`;

    return (
        <div className="loading-spinner-container">
            <div className={`loading-spinner ${sizeClass}`} />
            {message && <p className="loading-message">{message}</p>}
        </div>
    );
}
