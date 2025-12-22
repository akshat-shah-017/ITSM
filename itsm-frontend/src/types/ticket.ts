// Types - Ticket domain types

import type { UserRef } from './user';

/**
 * Ticket list item (summary view)
 * Returned by GET /api/tickets/, /api/employee/queue/, etc.
 */
export interface TicketSummary {
    id: string;
    ticket_number: string;
    title: string;
    status: string;
    priority?: string; // Optional - may not be returned for all roles/endpoints
    created_at: string;
    assigned_to: UserRef | null;
    category?: { id: string; name: string }; // For dashboard display
    created_by?: UserRef; // Requester for dashboard display
}

/**
 * Attachment info embedded in ticket detail
 */
export interface Attachment {
    id: string;
    file_name: string;
    file_type: string;
    file_size: number;
}

/**
 * Category reference
 */
export interface CategoryRef {
    id: string;
    name: string;
}

/**
 * Closure code reference
 */
export interface ClosureCodeRef {
    code: string;
    description: string;
}

/**
 * Full ticket detail
 * Returned by GET /api/tickets/{id}/
 * Note: `priority` field is ONLY returned for EMPLOYEE/MANAGER/ADMIN roles
 */
export interface TicketDetail {
    id: string;
    ticket_number: string;
    title: string;
    description: string;
    status: string;
    is_closed: boolean;
    priority?: number; // Only for EMPLOYEE+ roles - HIDDEN for USER role
    category: CategoryRef;
    subcategory: CategoryRef;
    department: { id: string; name: string };
    created_by: UserRef & { email: string };
    created_at: string;
    assigned_to: (UserRef & { email: string }) | null;
    assigned_at: string | null;
    closure_code: ClosureCodeRef | null;
    closed_at: string | null;
    attachments: Attachment[];
}

/**
 * Ticket history entry
 * Returned by GET /api/tickets/{id}/history/
 */
export interface TicketHistoryEntry {
    id: string;
    old_status: string;
    new_status: string;
    note: string;
    changed_by: UserRef;
    changed_at: string;
}

/**
 * Query parameters for ticket list endpoints
 */
export interface TicketListParams {
    page?: number;
    page_size?: number;
    status?: string;
    sort?: string;
}

/**
 * Query parameters for employee queue
 */
export interface EmployeeQueueParams {
    page?: number;
    page_size?: number;
    category_id?: string;
    subcategory_id?: string;
    priority?: number;
    sort?: string;
}

/**
 * Query parameters for manager team tickets
 */
export interface ManagerTeamTicketsParams {
    page?: number;
    page_size?: number;
    status?: string;
    priority?: number;
    assigned_to?: string;
    created_after?: string;
    sort?: string;
}

/**
 * Valid ticket statuses
 * Note: Backend enforces valid status transitions
 */
export const TICKET_STATUSES = [
    'New',
    'Assigned',
    'In Progress',
    'Waiting',
    'On Hold',
    'Closed',
] as const;

export type TicketStatus = (typeof TICKET_STATUSES)[number];
