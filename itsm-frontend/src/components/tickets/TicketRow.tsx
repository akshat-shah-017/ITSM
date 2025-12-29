/**
 * TicketRow Component
 * Responsive ticket row - horizontal on desktop, stacked card on mobile
 */
import { Link } from 'react-router-dom';
import type { TicketSummary } from '../../types/ticket';
import { Clock, User, AlertTriangle, ArrowUpCircle } from 'lucide-react';
import { getTimeElapsedString } from '../../utils/dateFormat';

interface TicketRowProps {
    ticket: TicketSummary;
    showPriority?: boolean;
}

export function TicketRow({ ticket, showPriority = false }: TicketRowProps) {
    const getStatusStyle = (status: string) => {
        const styles: Record<string, string> = {
            'New': 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
            'Assigned': 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
            'In Progress': 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
            'Waiting': 'bg-gray-500/10 text-gray-600 dark:text-gray-400',
            'Pending': 'bg-gray-500/10 text-gray-600 dark:text-gray-400',
            'Resolved': 'bg-green-500/10 text-green-600 dark:text-green-400',
            'Closed': 'bg-surface-500/10 text-surface-500',
        };
        return styles[status] || styles['Pending'];
    };

    const getPriorityBadge = (priority: string | undefined) => {
        if (!priority) return null;
        const p = priority.toLowerCase();
        if (p === 'critical' || p === '1') {
            return <span className="px-1.5 py-0.5 text-[10px] font-bold bg-red-500/10 text-red-600 dark:text-red-400 rounded flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> CRIT
            </span>;
        }
        if (p === 'high' || p === '2') {
            return <span className="px-1.5 py-0.5 text-[10px] font-bold bg-orange-500/10 text-orange-600 dark:text-orange-400 rounded flex items-center gap-1">
                <ArrowUpCircle className="w-3 h-3" /> HIGH
            </span>;
        }
        return null;
    };

    return (
        <Link
            to={`/tickets/${ticket.id}`}
            className="block p-3 rounded-lg border border-surface-200 dark:border-surface-800 bg-white dark:bg-surface-900 hover:border-primary-300 dark:hover:border-primary-700 hover:bg-surface-50 dark:hover:bg-surface-800/80 transition-all group"
        >
            {/* Desktop Layout - Hidden on mobile */}
            <div className="hidden md:flex items-center gap-4">
                {/* Ticket Number */}
                <div className="w-28 shrink-0">
                    <span className="text-xs font-mono text-surface-500">{ticket.ticket_number}</span>
                </div>

                {/* Status Badge */}
                <div className="w-20 shrink-0">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getStatusStyle(ticket.status)}`}>
                        {ticket.status}
                    </span>
                </div>

                {/* Priority (optional) */}
                {showPriority && (
                    <div className="w-14 shrink-0">
                        {getPriorityBadge(ticket.priority)}
                    </div>
                )}

                {/* Title */}
                <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-surface-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors truncate block">
                        {ticket.title}
                    </span>
                </div>

                {/* Time Elapsed */}
                <div className="w-24 shrink-0 flex items-center gap-1 text-xs text-surface-400">
                    <Clock className="w-3 h-3" />
                    <span>{getTimeElapsedString(ticket.created_at)}</span>
                </div>

                {/* Assignee */}
                <div className="w-28 shrink-0 flex items-center gap-1.5 text-xs text-surface-500">
                    <User className="w-3 h-3" />
                    <span className="truncate">{ticket.assigned_to?.name || 'Unassigned'}</span>
                </div>
            </div>

            {/* Mobile Layout - Visible only on mobile */}
            <div className="md:hidden space-y-2">
                {/* Top row: Ticket # + Status */}
                <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-surface-500">{ticket.ticket_number}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${getStatusStyle(ticket.status)}`}>
                        {ticket.status}
                    </span>
                </div>

                {/* Title - Full width on mobile */}
                <div>
                    <span className="text-sm font-medium text-surface-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 line-clamp-2">
                        {ticket.title}
                    </span>
                </div>

                {/* Bottom row: Time + Priority + Assignee */}
                <div className="flex items-center justify-between text-xs text-surface-400">
                    <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{getTimeElapsedString(ticket.created_at)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        {showPriority && getPriorityBadge(ticket.priority)}
                        <div className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            <span className="truncate max-w-[80px]">{ticket.assigned_to?.name || 'Unassigned'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </Link>
    );
}
