// Pages - Create Ticket Page

import { Link } from 'react-router-dom';
import { CreateTicketForm } from '../../components/tickets';

/**
 * Create new ticket page
 * POST /api/tickets/
 */
export function CreateTicketPage() {
    return (
        <div className="page create-ticket-page">
            <nav className="page-breadcrumb">
                <Link to="/tickets">← Back to Tickets</Link>
            </nav>

            <CreateTicketForm />
        </div>
    );
}
