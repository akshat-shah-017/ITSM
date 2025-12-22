/**
 * FilterBar Component
 * Provides status, priority, and time-elapsed sorting controls for ticket lists
 */
import { useCallback } from 'react';
import { Filter, X, ArrowUpDown, Clock } from 'lucide-react';

export interface TicketFilters {
    status?: string;
    priority?: string;
    sort?: string;
}

interface FilterBarProps {
    filters: TicketFilters;
    onChange: (filters: TicketFilters) => void;
    showPriority?: boolean;
    showTimeElapsed?: boolean;
}

const STATUS_OPTIONS = [
    { value: '', label: 'All Statuses' },
    { value: 'New', label: 'New' },
    { value: 'Assigned', label: 'Assigned' },
    { value: 'In Progress', label: 'In Progress' },
    { value: 'Waiting', label: 'Waiting' },
    { value: 'On Hold', label: 'On Hold' },
    { value: 'Closed', label: 'Closed' },
];

const PRIORITY_OPTIONS = [
    { value: '', label: 'All Priorities' },
    { value: '1', label: 'Critical' },
    { value: '2', label: 'High' },
    { value: '3', label: 'Medium' },
    { value: '4', label: 'Low' },
];

const SORT_OPTIONS = [
    { value: '-created_at', label: 'Newest First' },
    { value: 'created_at', label: 'Oldest First (Time Elapsed ↓)' },
    { value: 'priority', label: 'Priority' },
    { value: 'status', label: 'Status' },
];

export function FilterBar({
    filters,
    onChange,
    showPriority = false,
    showTimeElapsed = true,
}: FilterBarProps) {
    const hasActiveFilters = filters.status || filters.priority;

    const handleStatusChange = useCallback((status: string) => {
        onChange({ ...filters, status: status || undefined });
    }, [filters, onChange]);

    const handlePriorityChange = useCallback((priority: string) => {
        onChange({ ...filters, priority: priority || undefined });
    }, [filters, onChange]);

    const handleSortChange = useCallback((sort: string) => {
        onChange({ ...filters, sort: sort || undefined });
    }, [filters, onChange]);

    const handleClearFilters = useCallback(() => {
        onChange({ sort: filters.sort });
    }, [filters.sort, onChange]);

    return (
        <div className="flex flex-wrap items-center gap-3 p-4 glass-panel rounded-xl">
            {/* Filter Icon */}
            <div className="flex items-center gap-2 text-surface-500">
                <Filter size={16} />
                <span className="text-sm font-medium hidden sm:inline">Filters</span>
            </div>

            {/* Status Filter */}
            <div className="relative">
                <select
                    className="filter-select"
                    value={filters.status || ''}
                    onChange={(e) => handleStatusChange(e.target.value)}
                    aria-label="Filter by status"
                >
                    {STATUS_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>

            {/* Priority Filter (for employees/managers) */}
            {showPriority && (
                <div className="relative">
                    <select
                        className="filter-select"
                        value={filters.priority || ''}
                        onChange={(e) => handlePriorityChange(e.target.value)}
                        aria-label="Filter by priority"
                    >
                        {PRIORITY_OPTIONS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>
            )}

            {/* Divider */}
            <div className="w-px h-6 bg-surface-200 dark:bg-surface-700 hidden sm:block" />

            {/* Sort */}
            <div className="relative flex items-center gap-2">
                <ArrowUpDown size={14} className="text-surface-400" />
                <select
                    className="filter-select"
                    value={filters.sort || '-created_at'}
                    onChange={(e) => handleSortChange(e.target.value)}
                    aria-label="Sort tickets"
                >
                    {SORT_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            </div>

            {/* Time Elapsed Indicator */}
            {showTimeElapsed && filters.sort === 'created_at' && (
                <div className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-2 py-1 rounded-md">
                    <Clock size={12} />
                    <span>Showing oldest first</span>
                </div>
            )}

            {/* Clear Filters */}
            {hasActiveFilters && (
                <button
                    onClick={handleClearFilters}
                    className="flex items-center gap-1 text-xs text-surface-500 hover:text-primary-600 transition-colors px-2 py-1 rounded hover:bg-surface-100 dark:hover:bg-surface-800"
                >
                    <X size={12} />
                    Clear filters
                </button>
            )}
        </div>
    );
}
