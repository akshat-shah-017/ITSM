// Pages - User Ticket Detail Page

import { useParams, Link } from 'react-router-dom';
import { TicketDetail } from '../../components/tickets';

/**
 * Ticket detail page
 * GET /api/tickets/{id}/
 */
export function TicketDetailPage() {
    const { id } = useParams<{ id: string }>();

    if (!id) {
        return (
            <div className="page error-page">
                <h1>Invalid Ticket</h1>
                <p>No ticket ID provided.</p>
                <Link to="/tickets">Back to Tickets</Link>
            </div>
        );
    }

    return (
        <div className="page ticket-detail-page">
            <nav className="page-breadcrumb">
                <Link to="/tickets">← Back to Tickets</Link>
            </nav>

            <TicketDetail ticketId={id} />
        </div>
    );
}
