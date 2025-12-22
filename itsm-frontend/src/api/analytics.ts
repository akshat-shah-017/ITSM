// API - Analytics endpoints

import { get } from './client';

/**
 * Employee analytics response
 * GET /api/analytics/employee/
 */
export interface EmployeeAnalytics {
    total_assigned: number;
    total_open: number;
    total_closed: number;
    closed_today: number;
    closed_last_7_days: number;
    closed_last_30_days: number;
    by_status: Record<string, number>;
    avg_resolution_hours: number | null;
    oldest_open_ticket: {
        id: string;
        ticket_number: string;
        title: string;
        created_at: string;
    } | null;
}

/**
 * Manager analytics response
 * GET /api/analytics/manager/
 */
export interface ManagerAnalytics {
    team_total_tickets: number;
    team_open: number;
    team_closed: number;
    per_employee_stats: Array<{
        employee_id: string;
        employee_name: string;
        employee_email: string;
        total: number;
        open: number;
        closed: number;
    }>;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
    aging_tickets: Array<{
        id: string;
        ticket_number: string;
        title: string;
        status: string;
        created_at: string;
        assigned_to_name: string;
        age_days: number;
    }>;
    volume_trend: Array<{
        date: string;
        count: number;
    }>;
}

/**
 * Detailed analytics response (with org breakdown)
 * GET /api/analytics/manager/detailed/
 */
export interface DetailedAnalytics {
    summary: {
        total: number;
        open: number;
        closed: number;
        avg_resolution_hours: number | null;
    };
    by_company: Array<{
        id: string | null;
        name: string;
        total: number;
        open: number;
        closed: number;
    }>;
    by_business_group: Array<{
        id: string | null;
        name: string;
        total: number;
        open: number;
        closed: number;
    }>;
    by_status: Record<string, number>;
    by_priority: Record<string, number>;
    by_category: Array<{ name: string; count: number }>;
    volume_trend: Array<{ date: string; created: number; closed: number }>;
    resolution_trend: Array<{ date: string; avg_hours: number }>;
}

/**
 * Employee detailed analytics response
 * GET /api/analytics/employee/detailed/ or /api/analytics/employee/{id}/detailed/
 */
export interface EmployeeDetailedAnalytics {
    employee: {
        id: string;
        name: string;
        email: string;
    };
    summary: {
        total: number;
        open: number;
        closed: number;
        avg_resolution_hours: number | null;
    };
    by_week: Array<{
        week_start: string;
        assigned: number;
        resolved: number;
    }>;
    by_status: Record<string, number>;
    by_category: Array<{ name: string; count: number }>;
}

/**
 * Get employee analytics
 * Requires: EMPLOYEE, MANAGER, or ADMIN role
 */
export async function getEmployeeAnalytics(): Promise<EmployeeAnalytics> {
    return get<EmployeeAnalytics>('/api/analytics/employee/summary/');
}

/**
 * Get manager analytics
 * Requires: MANAGER or ADMIN role
 */
export async function getManagerAnalytics(): Promise<ManagerAnalytics> {
    return get<ManagerAnalytics>('/api/analytics/manager/team-summary/');
}

/**
 * Get detailed manager analytics with date range and org breakdown
 * Requires: MANAGER or ADMIN role
 */
export async function getDetailedAnalytics(
    startDate: string,
    endDate: string,
    groupBy: 'auto' | 'day' | 'week' | 'month' = 'auto'
): Promise<DetailedAnalytics> {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        group_by: groupBy,
    });
    return get<DetailedAnalytics>(`/api/analytics/manager/detailed/?${params}`);
}

/**
 * Get employee's own detailed analytics (self-view)
 * Requires: EMPLOYEE, MANAGER, or ADMIN role
 */
export async function getMyDetailedAnalytics(
    startDate: string,
    endDate: string
): Promise<EmployeeDetailedAnalytics> {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    return get<EmployeeDetailedAnalytics>(`/api/analytics/employee/detailed/?${params}`);
}

/**
 * Get detailed analytics for a specific employee
 * Requires: MANAGER/ADMIN viewing team member, OR employee viewing self
 */
export async function getEmployeeDetailedAnalytics(
    employeeId: string,
    startDate: string,
    endDate: string
): Promise<EmployeeDetailedAnalytics> {
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
    });
    return get<EmployeeDetailedAnalytics>(`/api/analytics/employee/${employeeId}/detailed/?${params}`);
}

