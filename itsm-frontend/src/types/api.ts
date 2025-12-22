// Types - API envelope types

/**
 * Standard paginated response format from the backend.
 * All list endpoints return this structure.
 */
export interface PaginatedResponse<T> {
    page: number;
    page_size: number;
    total_count: number;
    results: T[];
}

/**
 * Standard error response envelope.
 * Frontend logic must depend ONLY on error.code, not message text.
 */
export interface ApiError {
    error: {
        code: string;
        message: string;
        details?: Array<{ field: string; message: string }>;
    };
}

/**
 * Standard query parameters for paginated list endpoints
 */
export interface PaginationParams {
    page?: number;
    page_size?: number;
    sort?: string;
}

/**
 * Check if an error response matches our ApiError shape
 */
export function isApiError(error: unknown): error is { response: { data: ApiError } } {
    return (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as { response: unknown }).response === 'object' &&
        (error as { response: { data: unknown } }).response !== null &&
        'data' in (error as { response: { data: unknown } }).response &&
        typeof (error as { response: { data: { error?: unknown } } }).response.data === 'object' &&
        (error as { response: { data: { error?: unknown } } }).response.data !== null &&
        'error' in (error as { response: { data: { error?: unknown } } }).response.data
    );
}

/**
 * Extract error code from API error response
 */
export function getErrorCode(error: unknown): string {
    if (isApiError(error)) {
        return error.response.data.error.code;
    }
    return 'UNKNOWN_ERROR';
}

/**
 * Extract human-readable error message from API error
 * Note: Use only for display, not for logic branching
 */
export function getErrorMessage(error: unknown): string {
    if (isApiError(error)) {
        return error.response.data.error.message;
    }
    if (error instanceof Error) {
        return error.message;
    }
    return 'An unexpected error occurred';
}
