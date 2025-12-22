// Pages - Employee My Tickets Page

import { TicketList } from '../../components/tickets';
import { getEmployeeTickets } from '../../api/tickets';

/**
 * Employee assigned tickets page
 * Shows tickets assigned to the current employee
 * GET /api/employee/tickets/
 */
export function MyTicketsPage() {
    return (
        <div className="page my-tickets-page">
            <header className="page-header">
                <h1>My Assigned Tickets</h1>
                <p className="page-description">
                    Tickets currently assigned to you
                </p>
            </header>

            <TicketList
                fetchTickets={getEmployeeTickets}
                emptyMessage="No assigned tickets"
                emptyDescription="You don't have any tickets assigned to you."
                defaultSort="-assigned_at"
                showPriorityFilter={true}
            />
        </div>
    );
}
