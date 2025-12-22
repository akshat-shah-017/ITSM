// Pages - Employee Queue Page

import { TicketList } from '../../components/tickets';
import { getEmployeeQueue } from '../../api/tickets';

/**
 * Employee department queue page
 * Shows unassigned tickets in the employee's department
 * GET /api/employee/queue/
 */
export function QueuePage() {
    return (
        <div className="page queue-page">
            <header className="page-header">
                <h1>Department Queue</h1>
                <p className="page-description">
                    Unassigned tickets in your department
                </p>
            </header>

            <TicketList
                fetchTickets={getEmployeeQueue}
                emptyMessage="Queue is empty"
                emptyDescription="There are no unassigned tickets in your department."
                defaultSort="created_at"
                showPriorityFilter={true}
            />
        </div>
    );
}
