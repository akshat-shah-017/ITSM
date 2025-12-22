// API - Ticket endpoints

import { get } from './client';
import type { PaginatedResponse } from '../types/api';
import type {
    TicketSummary,
    TicketDetail,
    TicketHistoryEntry,
    TicketListParams,
    EmployeeQueueParams,
    ManagerTeamTicketsParams,
} from '../types/ticket';
import type { TeamMember } from '../types/user';

/**
 * Get list of user's own tickets
 * GET /api/tickets/
 */
export async function getTickets(
    params?: TicketListParams
): Promise<PaginatedResponse<TicketSummary>> {
    return get<PaginatedResponse<TicketSummary>>('/api/tickets/', params);
}

/**
 * Get ticket details by ID
 * GET /api/tickets/{id}/
 * 
 * Note: Returns 404 if ticket doesn't exist or user doesn't have access
 * Note: `priority` field is only present for EMPLOYEE+ roles
 */
export async function getTicket(id: string): Promise<TicketDetail> {
    return get<TicketDetail>(`/api/tickets/${id}/`);
}

/**
 * Get ticket history
 * GET /api/tickets/{id}/history/
 */
export async function getTicketHistory(
    id: string,
    params?: { page?: number; page_size?: number }
): Promise<PaginatedResponse<TicketHistoryEntry>> {
    return get<PaginatedResponse<TicketHistoryEntry>>(
        `/api/tickets/${id}/history/`,
        params
    );
}

/**
 * Get employee department queue (unassigned tickets)
 * GET /api/employee/queue/
 * Requires: EMPLOYEE, MANAGER, or ADMIN role
 */
export async function getEmployeeQueue(
    params?: EmployeeQueueParams
): Promise<PaginatedResponse<TicketSummary>> {
    return get<PaginatedResponse<TicketSummary>>('/api/employee/queue/', params);
}

/**
 * Get employee's assigned tickets
 * GET /api/employee/tickets/
 * Requires: EMPLOYEE, MANAGER, or ADMIN role
 */
export async function getEmployeeTickets(
    params?: TicketListParams
): Promise<PaginatedResponse<TicketSummary>> {
    return get<PaginatedResponse<TicketSummary>>('/api/employee/tickets/', params);
}

/**
 * Get manager's team members
 * GET /api/manager/team/
 * Requires: MANAGER or ADMIN role
 */
export async function getManagerTeam(): Promise<TeamMember[]> {
    return get<TeamMember[]>('/api/manager/team/');
}

/**
 * Get all tickets for manager's team
 * GET /api/manager/team/tickets/
 * Requires: MANAGER or ADMIN role
 */
export async function getManagerTeamTickets(
    params?: ManagerTeamTicketsParams
): Promise<PaginatedResponse<TicketSummary>> {
    return get<PaginatedResponse<TicketSummary>>(
        '/api/manager/team/tickets/',
        params
    );
}
