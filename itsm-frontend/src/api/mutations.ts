// API - Ticket mutations for Phase 2

import apiClient, { get, post, patch } from './client';
import type {
    CreateTicketRequest,
    CreateTicketResponse,
    AssignTicketRequest,
    AssignTicketResponse,
    UpdateStatusRequest,
    UpdateStatusResponse,
    CloseTicketRequest,
    CloseTicketResponse,
    UpdatePriorityRequest,
    UpdatePriorityResponse,
    UploadAttachmentResponse,
    ReassignTicketRequest,
    ReassignTicketResponse,
    Category,
    Subcategory,
    ClosureCode,
} from '../types/mutations';

// =============================================================================
// Master Data APIs (for forms)
// =============================================================================

/**
 * Get list of active categories
 * GET /api/categories/
 */
export async function getCategories(): Promise<Category[]> {
    return get<Category[]>('/api/categories/');
}

/**
 * Get subcategories for a category
 * GET /api/categories/{id}/subcategories/
 */
export async function getSubcategories(categoryId: string): Promise<Subcategory[]> {
    return get<Subcategory[]>(`/api/categories/${categoryId}/subcategories/`);
}

/**
 * Get list of active closure codes
 * GET /api/closure-codes/
 */
export async function getClosureCodes(): Promise<ClosureCode[]> {
    return get<ClosureCode[]>('/api/closure-codes/');
}

// =============================================================================
// Ticket Mutations
// =============================================================================

/**
 * Create a new ticket
 * POST /api/tickets/
 * 
 * Uses multipart/form-data when attachments are included
 */
export async function createTicket(
    data: CreateTicketRequest,
    attachments?: File[]
): Promise<CreateTicketResponse> {
    if (attachments && attachments.length > 0) {
        // Use FormData for multipart upload
        const formData = new FormData();
        formData.append('title', data.title);
        formData.append('description', data.description);
        formData.append('category_id', data.category_id);
        formData.append('subcategory_id', data.subcategory_id);

        attachments.forEach((file) => {
            formData.append('attachments', file);
        });

        const response = await apiClient.post<CreateTicketResponse>('/api/tickets/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    // JSON request without attachments
    return post<CreateTicketResponse>('/api/tickets/', data);
}

/**
 * Assign ticket (self-assign or to specific user)
 * POST /api/tickets/{id}/assign/
 * 
 * @param id - Ticket ID
 * @param assignedTo - Target user ID (optional, null = self-assign)
 */
export async function assignTicket(
    id: string,
    assignedTo?: string
): Promise<AssignTicketResponse> {
    const data: AssignTicketRequest = {};
    if (assignedTo) {
        data.assigned_to = assignedTo;
    }
    return post<AssignTicketResponse>(`/api/tickets/${id}/assign/`, data);
}

/**
 * Update ticket status
 * PATCH /api/tickets/{id}/status/
 * 
 * @param id - Ticket ID
 * @param status - New status (In Progress, Waiting, On Hold, Assigned)
 * @param note - Required note for status change
 */
export async function updateTicketStatus(
    id: string,
    status: string,
    note: string
): Promise<UpdateStatusResponse> {
    const data: UpdateStatusRequest = {
        status: status as UpdateStatusRequest['status'],
        note,
    };
    return patch<UpdateStatusResponse>(`/api/tickets/${id}/status/`, data);
}

/**
 * Close ticket
 * POST /api/tickets/{id}/close/
 * 
 * @param id - Ticket ID
 * @param closureCodeId - ID of the closure code
 * @param note - Required closure note
 */
export async function closeTicket(
    id: string,
    closureCodeId: string,
    note: string
): Promise<CloseTicketResponse> {
    const data: CloseTicketRequest = {
        closure_code_id: closureCodeId,
        note,
    };
    return post<CloseTicketResponse>(`/api/tickets/${id}/close/`, data);
}

/**
 * Update ticket priority
 * PATCH /api/tickets/{id}/priority/
 * 
 * @param id - Ticket ID
 * @param priority - Priority value (1-4)
 * @param note - Required note for priority change
 */
export async function updateTicketPriority(
    id: string,
    priority: number,
    note: string
): Promise<UpdatePriorityResponse> {
    const data: UpdatePriorityRequest = {
        priority: priority as UpdatePriorityRequest['priority'],
        note,
    };
    return patch<UpdatePriorityResponse>(`/api/tickets/${id}/priority/`, data);
}

/**
 * Upload attachment to ticket
 * POST /api/tickets/{id}/attachments/
 * 
 * @param id - Ticket ID
 * @param file - File to upload
 */
export async function uploadAttachment(
    id: string,
    file: File
): Promise<UploadAttachmentResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<UploadAttachmentResponse>(
        `/api/tickets/${id}/attachments/`,
        formData,
        {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        }
    );
    return response.data;
}

/**
 * Reassign ticket to another team member
 * POST /api/tickets/{id}/reassign/
 * 
 * @param id - Ticket ID
 * @param assignedTo - Target user ID
 * @param note - Required note for reassignment
 */
export async function reassignTicket(
    id: string,
    assignedTo: string,
    note: string
): Promise<ReassignTicketResponse> {
    const data: ReassignTicketRequest = {
        assigned_to: assignedTo,
        note,
    };
    return post<ReassignTicketResponse>(`/api/tickets/${id}/reassign/`, data);
}
