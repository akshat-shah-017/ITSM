/**
 * Email API Client
 * Functions for email intake endpoints
 */
import { get, post } from './client';
import type { PaginatedResponse, PaginationParams } from '../types/api';

/**
 * Ingested email with extracted content
 */
export interface EmailIngest {
    id: string;
    message_id: string;
    subject: string;
    sender_email: string;
    sender_name: string | null;
    body_text: string;
    body_html: string | null;
    received_at: string;
    status: 'PENDING' | 'PROCESSED' | 'DISCARDED';
    created_at: string;
    attachments: EmailAttachment[];
}

/**
 * Email attachment info
 */
export interface EmailAttachment {
    id: string;
    file_name: string;
    file_type: string;
    file_size: number;
}

/**
 * Request to process email into a ticket
 */
export interface ProcessEmailRequest {
    title: string;
    category_id: string;
    subcategory_id: string;
    priority?: number;
}

/**
 * Upload/ingest an email file (.eml or .msg)
 * POST /api/email/ingest/
 */
export async function ingestEmail(file: File): Promise<EmailIngest> {
    const formData = new FormData();
    formData.append('file', file);

    // Use the client module's apiClient which handles auth
    const apiClient = (await import('./client')).default;

    const response = await apiClient.post<EmailIngest>('/api/email/ingest/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
}

/**
 * Get list of pending emails
 * GET /api/email/pending/
 */
export async function getPendingEmails(
    params?: PaginationParams
): Promise<PaginatedResponse<EmailIngest>> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.page_size) searchParams.set('page_size', params.page_size.toString());

    const query = searchParams.toString();
    return get<PaginatedResponse<EmailIngest>>(`/api/email/pending/${query ? '?' + query : ''}`);
}

/**
 * Get email details
 * GET /api/email/{id}/
 */
export async function getEmailDetail(id: string): Promise<EmailIngest> {
    return get<EmailIngest>(`/api/email/${id}/`);
}

/**
 * Process email to create a ticket
 * POST /api/email/{id}/process/
 */
export async function processEmail(
    id: string,
    data: ProcessEmailRequest
): Promise<{ ticket_id: string; ticket_number: string }> {
    return post<{ ticket_id: string; ticket_number: string }>(`/api/email/${id}/process/`, data);
}

/**
 * Discard an email
 * POST /api/email/{id}/discard/
 */
export async function discardEmail(id: string, reason: string): Promise<void> {
    return post<void>(`/api/email/${id}/discard/`, { reason });
}
