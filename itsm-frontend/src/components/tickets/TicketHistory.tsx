// Components - Ticket History

import { useCallback, useEffect, useState } from 'react';
import type { TicketHistoryEntry } from '../../types/ticket';
import type { PaginatedResponse } from '../../types/api';
import { getTicketHistory } from '../../api/tickets';
import { LoadingSpinner, ErrorMessage, EmptyState, Pagination } from '../common';
import { formatDateIST } from '../../utils/dateFormat';

interface TicketHistoryProps {
    /** Ticket ID */
    ticketId: string;
}

/**
 * Ticket history timeline component
 */
export function TicketHistory({ ticketId }: TicketHistoryProps) {
    const [history, setHistory] = useState<TicketHistoryEntry[]>([]);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalCount, setTotalCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<unknown>(null);

    const loadHistory = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response: PaginatedResponse<TicketHistoryEntry> = await getTicketHistory(
                ticketId,
                { page, page_size: pageSize }
            );
            setHistory(response.results);
            setTotalCount(response.total_count);
        } catch (err) {
            setError(err);
            setHistory([]);
        } finally {
            setIsLoading(false);
        }
    }, [ticketId, page, pageSize]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);


    if (isLoading && history.length === 0) {
        return <LoadingSpinner size="small" message="Loading history..." />;
    }

    if (error) {
        return (
            <ErrorMessage
                error={error}
                title="Failed to load history"
                onRetry={loadHistory}
            />
        );
    }

    if (history.length === 0) {
        return (
            <EmptyState
                icon="📜"
                message="No history"
                description="This ticket has no status change history yet."
            />
        );
    }

    return (
        <div className="ticket-history">
            <h3 className="ticket-history-title">History</h3>

            <div className="ticket-history-timeline">
                {history.map((entry) => (
                    <div key={entry.id} className="history-entry">
                        <div className="history-entry-header">
                            <span className="history-status-change">
                                <span className="history-old-status">{entry.old_status}</span>
                                <span className="history-arrow">→</span>
                                <span className="history-new-status">{entry.new_status}</span>
                            </span>
                            <span className="history-date">{formatDateIST(entry.changed_at)}</span>
                        </div>

                        <div className="history-entry-body">
                            <span className="history-user">
                                by {entry.changed_by.name}
                            </span>
                            {entry.note && (
                                <p className="history-note">{entry.note}</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <Pagination
                page={page}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={setPage}
            />
        </div>
    );
}
