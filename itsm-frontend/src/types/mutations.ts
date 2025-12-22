// Types - Mutation request/response types for Phase 2

import type { CategoryRef, ClosureCodeRef } from './ticket';
import type { UserRef } from './user';

// =============================================================================
// Create Ticket
// =============================================================================

/**
 * Request body for POST /api/tickets/
 * Note: Uses multipart/form-data when attachments included
 */
export interface CreateTicketRequest {
    title: string;
    description: string;
    category_id: string;
    subcategory_id: string;
    // Attachments handled separately via FormData
}

/**
 * Response from POST /api/tickets/
 */
export interface CreateTicketResponse {
    id: string;
    ticket_number: string;
    title: string;
    description: string;
    status: string;
    category: CategoryRef;
    subcategory: CategoryRef;
    created_by: UserRef;
    created_at: string;
    assigned_to: null;
}

// =============================================================================
// Assign Ticket
// =============================================================================

/**
 * Request body for POST /api/tickets/{id}/assign/
 */
export interface AssignTicketRequest {
    assigned_to?: string; // Optional: null = self-assign
}

/**
 * Response from POST /api/tickets/{id}/assign/
 */
export interface AssignTicketResponse {
    id: string;
    ticket_number: string;
    status: string;
    assigned_to: UserRef;
    assigned_at: string;
}

// =============================================================================
// Update Status
// =============================================================================

/**
 * Valid status values for PATCH /api/tickets/{id}/status/
 */
export const UPDATABLE_STATUSES = ['In Progress', 'Waiting', 'On Hold', 'Assigned'] as const;
export type UpdatableStatus = (typeof UPDATABLE_STATUSES)[number];

/**
 * Request body for PATCH /api/tickets/{id}/status/
 */
export interface UpdateStatusRequest {
    status: UpdatableStatus;
    note: string; // Required, non-empty
}

/**
 * Response from PATCH /api/tickets/{id}/status/
 */
export interface UpdateStatusResponse {
    id: string;
    ticket_number: string;
    status: string;
    updated_at: string;
}

// =============================================================================
// Close Ticket
// =============================================================================

/**
 * Request body for POST /api/tickets/{id}/close/
 */
export interface CloseTicketRequest {
    closure_code_id: string; // Required
    note: string; // Required, non-empty
}

/**
 * Response from POST /api/tickets/{id}/close/
 */
export interface CloseTicketResponse {
    id: string;
    ticket_number: string;
    status: 'Closed';
    is_closed: true;
    closure_code: ClosureCodeRef;
    closed_at: string;
}

// =============================================================================
// Update Priority
// =============================================================================

/**
 * Valid priority values (P1-P4)
 */
export const PRIORITY_VALUES = [1, 2, 3, 4] as const;
export type PriorityValue = (typeof PRIORITY_VALUES)[number];

/**
 * Request body for PATCH /api/tickets/{id}/priority/
 */
export interface UpdatePriorityRequest {
    priority: PriorityValue;
    note: string; // Required, non-empty
}

/**
 * Response from PATCH /api/tickets/{id}/priority/
 */
export interface UpdatePriorityResponse {
    id: string;
    ticket_number: string;
    priority: number;
    updated_at: string;
}

// =============================================================================
// Upload Attachment
// =============================================================================

/**
 * Response from POST /api/tickets/{id}/attachments/
 */
export interface UploadAttachmentResponse {
    id: string;
    file_name: string;
    file_type: string;
    file_size: number;
}

// =============================================================================
// Reassign Ticket
// =============================================================================

/**
 * Request body for POST /api/tickets/{id}/reassign/
 */
export interface ReassignTicketRequest {
    assigned_to: string; // Required - target user ID
    note: string; // Required, non-empty
}

/**
 * Response from POST /api/tickets/{id}/reassign/
 */
export interface ReassignTicketResponse {
    id: string;
    ticket_number: string;
    status: string;
    assigned_to: UserRef;
    assigned_at: string;
}

// =============================================================================
// Master Data Types
// =============================================================================

/**
 * Category from GET /api/categories/
 */
export interface Category {
    id: string;
    name: string;
    description?: string;
    is_active: boolean;
}

/**
 * Subcategory from GET /api/categories/{id}/subcategories/
 */
export interface Subcategory {
    id: string;
    name: string;
    description?: string;
    category_id: string;
    department_id: string;
    is_active: boolean;
}

/**
 * Closure code from GET /api/closure-codes/
 * Note: Backend already filters by is_active=True, so is_active is not returned
 */
export interface ClosureCode {
    id: string;
    code: string;
    description: string | null;
}

/**
 * Status from GET /api/statuses/
 */
export interface TicketStatusOption {
    value: string;
    label: string;
}
