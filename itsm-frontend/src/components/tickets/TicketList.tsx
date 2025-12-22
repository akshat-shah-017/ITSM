import { useCallback, useEffect, useState } from 'react';
import type { TicketSummary, TicketListParams } from '../../types/ticket';
import type { PaginatedResponse } from '../../types/api';
import { LoadingSpinner, ErrorMessage, EmptyState, Pagination, FilterBar, type TicketFilters } from '../common';
import { TicketRow } from './TicketRow';

interface TicketListProps {
    title?: string;
    fetchTickets: (params: TicketListParams) => Promise<PaginatedResponse<TicketSummary>>;
    emptyMessage?: string;
    emptyDescription?: string;
    defaultSort?: string;
    showFilters?: boolean;
    showPriorityFilter?: boolean;
}

export function TicketList({
    title,
    fetchTickets,
    emptyMessage = 'No tickets found',
    emptyDescription = 'There are no tickets to display.',
    defaultSort = '-created_at',
    showFilters = true,
    showPriorityFilter = false,
}: TicketListProps) {
    const [tickets, setTickets] = useState<TicketSummary[]>([]);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(25);
    const [totalCount, setTotalCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<unknown>(null);
    const [filters, setFilters] = useState<TicketFilters>({ sort: defaultSort });

    const loadTickets = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const response = await fetchTickets({
                page,
                page_size: pageSize,
                status: filters.status,
                sort: filters.sort || defaultSort,
            });
            setTickets(response.results);
            setTotalCount(response.total_count);
        } catch (err) {
            setError(err);
            setTickets([]);
        } finally {
            setIsLoading(false);
        }
    }, [fetchTickets, page, pageSize, filters, defaultSort]);

    useEffect(() => {
        loadTickets();
    }, [loadTickets]);

    const handlePageChange = (newPage: number) => {
        setPage(newPage);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const handleFilterChange = (newFilters: TicketFilters) => {
        setFilters(newFilters);
        setPage(1);
    };

    if (isLoading && tickets.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-surface-400">
                <LoadingSpinner />
            </div>
        );
    }

    if (error) {
        return (
            <ErrorMessage
                error={error}
                title="Failed to load tickets"
                onRetry={loadTickets}
            />
        );
    }

    return (
        <div className="space-y-4">
            {/* Header with title */}
            {title && (
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-surface-900 dark:text-white flex items-center gap-2">
                        {title}
                        <span className="text-xs font-normal text-surface-500 px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700">
                            {totalCount}
                        </span>
                    </h2>
                </div>
            )}

            {/* Filter Bar */}
            {showFilters && (
                <FilterBar
                    filters={filters}
                    onChange={handleFilterChange}
                    showPriority={showPriorityFilter}
                    showTimeElapsed={true}
                />
            )}

            {tickets.length === 0 ? (
                <EmptyState
                    icon="clipboard"
                    message={emptyMessage}
                    description={emptyDescription}
                />
            ) : (
                <div className="space-y-4 animate-fade-in">
                    {/* List Header */}
                    <div className="hidden md:flex items-center gap-4 px-3 py-2 text-[10px] uppercase tracking-wider font-bold text-surface-400 border-b border-surface-200 dark:border-surface-700">
                        <div className="w-28">Ticket #</div>
                        <div className="w-20">Status</div>
                        {showPriorityFilter && <div className="w-14">Priority</div>}
                        <div className="flex-1">Title</div>
                        <div className="w-24">Age</div>
                        <div className="w-28">Assignee</div>
                    </div>

                    {/* Ticket Rows */}
                    <div className="space-y-2">
                        {tickets.map((ticket) => (
                            <TicketRow
                                key={ticket.id}
                                ticket={ticket}
                                showPriority={showPriorityFilter}
                            />
                        ))}
                    </div>

                    <Pagination
                        page={page}
                        pageSize={pageSize}
                        totalCount={totalCount}
                        onPageChange={handlePageChange}
                    />
                </div>
            )}

            {isLoading && tickets.length > 0 && (
                <div className="flex justify-center p-4">
                    <LoadingSpinner size="small" />
                </div>
            )}
        </div>
    );
}
