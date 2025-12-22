// Components - Error Message

import { getErrorCode, getErrorMessage } from '../../types/api';

interface ErrorMessageProps {
    /** The error object or message */
    error: unknown;
    /** Optional title */
    title?: string;
    /** Optional retry callback */
    onRetry?: () => void;
}

/**
 * Error message component
 * Displays user-friendly error messages based on error.code
 */
export function ErrorMessage({ error, title, onRetry }: ErrorMessageProps) {
    const errorCode = getErrorCode(error);
    const errorMessage = getErrorMessage(error);

    // Map error codes to user-friendly messages
    const friendlyMessages: Record<string, string> = {
        UNAUTHORIZED: 'Your session has expired. Please log in again.',
        FORBIDDEN: 'You do not have permission to access this resource.',
        NOT_FOUND: 'The requested resource was not found.',
        VALIDATION_ERROR: 'Please check your input and try again.',
        RATE_LIMITED: 'Too many requests. Please wait a moment and try again.',
        UNKNOWN_ERROR: 'An unexpected error occurred.',
    };

    const displayMessage = friendlyMessages[errorCode] || errorMessage;

    return (
        <div className="error-message" role="alert">
            {title && <h3 className="error-title">{title}</h3>}
            <p className="error-text">{displayMessage}</p>
            {errorCode !== 'UNKNOWN_ERROR' && (
                <p className="error-code">Error code: {errorCode}</p>
            )}
            {onRetry && (
                <button className="error-retry-button" onClick={onRetry}>
                    Try Again
                </button>
            )}
        </div>
    );
}

/**
 * Inline error message for forms
 */
export function InlineError({ message }: { message: string }) {
    return <span className="inline-error">{message}</span>;
}
