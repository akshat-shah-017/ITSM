import { Link } from 'react-router-dom';
import type { TicketSummary } from '../../types/ticket';
import { Clock, Hash, AlertTriangle, ArrowUpCircle, CheckCircle2 } from 'lucide-react';

interface TicketListItemProps {
    ticket: TicketSummary;
}

export function TicketListItem({ ticket }: TicketListItemProps) {
    const formatDate = (dateString: string): string => {
        try {
            const date = new Date(dateString);
            return new Intl.DateTimeFormat('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: 'numeric',
            }).format(date);
        } catch {
            return dateString;
        }
    };

    const getStatusStyle = (status: string) => {
        const styles: Record<string, string> = {
            'New': 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20 shadow-[0_0_8px_rgba(59,130,246,0.15)]',
            'Assigned': 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20 shadow-[0_0_8px_rgba(168,85,247,0.15)]',
            'In Progress': 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 shadow-[0_0_8px_rgba(245,158,11,0.15)]',
            'Pending': 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20',
            'Resolved': 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 shadow-[0_0_8px_rgba(34,197,94,0.15)]',
            'Closed': 'bg-surface-500/10 text-surface-600 dark:text-surface-400 border-surface-500/20',
        };
        return styles[status] || styles['Pending'];
    };

    const getPriorityIcon = (priority: string | undefined) => {
        switch (priority?.toLowerCase()) {
            case 'critical': return <AlertTriangle className="w-4 h-4 text-red-500 drop-shadow-[0_0_4px_rgba(239,68,68,0.5)]" />;
            case 'high': return <ArrowUpCircle className="w-4 h-4 text-orange-500 drop-shadow-[0_0_4px_rgba(249,115,22,0.4)]" />;
            case 'medium': return <ArrowUpCircle className="w-4 h-4 text-yellow-500" />;
            default: return <CheckCircle2 className="w-4 h-4 text-blue-500" />;
        }
    };

    return (
        <Link
            to={`/tickets/${ticket.id}`}
            className="group card card-hover relative overflow-hidden flex flex-col h-full interactive-border"
        >
            {/* Hover Glow Effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-primary-500/3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

            {/* Top highlight line */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

            <div className="flex items-start justify-between mb-3 relative">
                <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 text-xs font-mono font-medium text-surface-500 bg-surface-100 dark:bg-surface-800 px-2 py-1 rounded shadow-depth-1">
                        <Hash className="w-3 h-3" />
                        {ticket.ticket_number}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-1 rounded-full border uppercase tracking-wide ${getStatusStyle(ticket.status)}`}>
                        {ticket.status}
                    </span>
                </div>
                <div className="transition-transform duration-200 group-hover:scale-110">
                    {getPriorityIcon(ticket.priority)}
                </div>
            </div>

            <h3 className="text-base font-semibold text-surface-900 dark:text-white mb-2 line-clamp-2 leading-snug group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors text-emphasis">
                {ticket.title}
            </h3>

            <div className="mt-auto pt-4 flex items-center justify-between border-t border-surface-100 dark:border-surface-800/50">
                <div className="flex items-center gap-2 text-xs text-surface-500">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{formatDate(ticket.created_at)}</span>
                </div>

                {ticket.assigned_to ? (
                    <div className="flex items-center gap-1.5 text-xs font-medium text-surface-600 dark:text-surface-300">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center text-white text-[10px] font-bold">
                            {ticket.assigned_to.name?.charAt(0)}
                        </div>
                        <span className="truncate max-w-24">{ticket.assigned_to.name}</span>
                    </div>
                ) : (
                    <span className="text-xs text-surface-400 italic">Unassigned</span>
                )}
            </div>
        </Link>
    );
}

