import { Link } from 'react-router-dom';
import { TicketList } from '../../components/tickets';
import { getTickets } from '../../api/tickets';
import { Plus } from 'lucide-react';

/**
 * User's own tickets list page
 * GET /api/tickets/
 */
export function TicketListPage() {
    return (
        <div className="space-y-6">
            <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 dark:text-white tracking-tight flex items-center gap-2">
                        My Tickets
                    </h1>
                    <p className="text-surface-500 dark:text-surface-400 text-sm mt-1">
                        View and manage incidents you have reported
                    </p>
                </div>
                <Link
                    to="/tickets/new"
                    className="btn btn-accent shadow-lg shadow-primary-500/20 hover:shadow-primary-500/40 transition-all hover:-translate-y-0.5"
                >
                    <Plus className="w-4 h-4" />
                    Create Ticket
                </Link>
            </header>

            <TicketList
                fetchTickets={getTickets}
                emptyMessage="No tickets found"
                emptyDescription="You haven't created any tickets yet."
            />
        </div>
    );
}
