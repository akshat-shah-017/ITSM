import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TicketDetail as TicketDetailType } from '../../types/ticket';
import { getTicket } from '../../api/tickets';
import { getAccessToken } from '../../auth/tokenStorage';
import { getErrorCode } from '../../types/api';
import { useAuth } from '../../auth';
import { LoadingSpinner, ErrorMessage } from '../common';
import { TicketHistory } from './TicketHistory';
import { TicketActions } from './TicketActions';
import { formatDateIST } from '../../utils/dateFormat';
import {
    Clock,
    User,
    Hash,
    FileText,
    Paperclip,
    Download,
    AlertTriangle,
    CheckCircle2,
    ArrowUpCircle,
    Info,
    Calendar,
    Briefcase,
    Tag,
    XCircle
} from 'lucide-react';

interface TicketDetailProps {
    ticketId: string;
}

export function TicketDetail({ ticketId }: TicketDetailProps) {
    const [ticket, setTicket] = useState<TicketDetailType | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<unknown>(null);
    const { isEmployee } = useAuth();
    const navigate = useNavigate();

    const loadTicket = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await getTicket(ticketId);
            setTicket(data);
        } catch (err) {
            setError(err);
            setTicket(null);
        } finally {
            setIsLoading(false);
        }
    }, [ticketId]);

    useEffect(() => {
        loadTicket();
    }, [loadTicket]);

    const handleTicketUpdate = useCallback(async () => {
        await loadTicket();
    }, [loadTicket]);

    const getStatusStyle = (status: string) => {
        const styles: Record<string, string> = {
            'New': 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
            'Assigned': 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20',
            'In Progress': 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
            'Pending': 'bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20',
            'Resolved': 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20',
            'Closed': 'bg-surface-500/10 text-surface-600 dark:text-surface-400 border-surface-500/20',
        };
        return styles[status] || styles['Pending'];
    };

    const getPriorityBadge = (priority: number) => {
        const config: Record<number, { label: string, color: string, icon: any }> = {
            1: { label: 'Critical', color: 'text-red-500 bg-red-500/10 border-red-500/20', icon: AlertTriangle },
            2: { label: 'High', color: 'text-orange-500 bg-orange-500/10 border-orange-500/20', icon: ArrowUpCircle },
            3: { label: 'Medium', color: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20', icon: Info },
            4: { label: 'Low', color: 'text-blue-500 bg-blue-500/10 border-blue-500/20', icon: CheckCircle2 },
        };
        const { label, color, icon: Icon } = config[priority] || config[3];

        return (
            <span className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${color}`}>
                <Icon className="w-3.5 h-3.5" />
                {label} Priorty
            </span>
        );
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    if (isLoading) {
        return <div className="flex justify-center p-12"><LoadingSpinner message="Loading ticket details..." /></div>;
    }

    if (error) {
        const errorCode = getErrorCode(error);
        if (errorCode === 'NOT_FOUND' || errorCode === 'FORBIDDEN') {
            return (
                <div className="flex flex-col items-center justify-center p-12 text-center">
                    <div className="w-16 h-16 bg-surface-100 dark:bg-surface-800 rounded-full flex items-center justify-center mb-4">
                        <XCircle className="w-8 h-8 text-surface-400" />
                    </div>
                    <h2 className="text-xl font-bold text-surface-900 dark:text-white mb-2">Ticket Not Found</h2>
                    <p className="text-surface-500 max-w-md mb-6">The ticket you are looking for does not exist or you do not have permission to view it.</p>
                    <button onClick={() => navigate('/tickets')} className="btn btn-secondary">Return to Tickets</button>
                </div>
            );
        }
        return <ErrorMessage error={error} title="Failed to load ticket" onRetry={loadTicket} />;
    }

    if (!ticket) return null;

    return (
        <div className="animate-fade-in space-y-6 pb-12">
            {/* Header */}
            <header className="glass-panel p-6 md:p-8 rounded-2xl relative overflow-hidden">
                <div className="relative z-10">
                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                        <div className="flex items-center gap-3">
                            <span className="flex items-center gap-1.5 px-2.5 py-1 bg-surface-100 dark:bg-surface-800/50 rounded-lg text-sm font-mono font-medium text-surface-600 dark:text-surface-400 border border-surface-200 dark:border-surface-700/50">
                                <Hash className="w-4 h-4" />
                                {ticket.ticket_number}
                            </span>
                            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${getStatusStyle(ticket.status)}`}>
                                {ticket.status}
                            </span>
                        </div>
                        {ticket.is_closed && (
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-100 dark:bg-surface-800 rounded-lg text-sm text-surface-500 border border-surface-200 dark:border-surface-700">
                                <CheckCircle2 className="w-4 h-4" />
                                <span>Closed on {formatDateIST(ticket.closed_at)}</span>
                            </div>
                        )}
                    </div>

                    <h1 className="text-2xl md:text-3xl font-bold text-surface-900 dark:text-white mb-4 leading-tight">
                        {ticket.title}
                    </h1>

                    <div className="flex flex-wrap items-center gap-4 text-sm text-surface-500 dark:text-surface-400">
                        <div className="flex items-center gap-1.5">
                            <User className="w-4 h-4" />
                            <span>Created by <span className="text-surface-900 dark:text-white font-medium">{ticket.created_by.name}</span></span>
                        </div>
                        <div className="w-1 h-1 rounded-full bg-surface-300 dark:bg-surface-700" />
                        <div className="flex items-center gap-1.5">
                            <Clock className="w-4 h-4" />
                            <span>{formatDateIST(ticket.created_at)}</span>
                        </div>
                        {isEmployee && ticket.priority !== undefined && (
                            <>
                                <div className="w-1 h-1 rounded-full bg-surface-300 dark:bg-surface-700" />
                                {getPriorityBadge(ticket.priority)}
                            </>
                        )}
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Description */}
                    <div className="card">
                        <h2 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                            <FileText className="w-5 h-5 text-surface-400" />
                            Description
                        </h2>
                        <div className="prose dark:prose-invert max-w-none text-surface-600 dark:text-surface-300 leading-relaxed whitespace-pre-wrap">
                            {ticket.description || <em className="text-surface-400">No description provided</em>}
                        </div>
                    </div>

                    {/* Attachments */}
                    <div className="card">
                        <h2 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                            <Paperclip className="w-5 h-5 text-surface-400" />
                            Attachments
                            <span className="text-sm font-normal text-surface-500 ml-1">({ticket.attachments.length})</span>
                        </h2>
                        {ticket.attachments.length === 0 ? (
                            <div className="text-center py-8 text-surface-500 bg-surface-50 dark:bg-surface-800/50 rounded-lg border border-dashed border-surface-200 dark:border-surface-700">
                                <p>No files attached to this ticket.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {ticket.attachments.map((attachment) => (
                                    <div key={attachment.id} className="group p-3 rounded-lg border border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/30 hover:bg-white dark:hover:bg-surface-800 transition-colors flex items-center justify-between">
                                        <div className="flex items-center gap-3 min-w-0">
                                            <div className="p-2 rounded bg-surface-200 dark:bg-surface-700 text-surface-600 dark:text-surface-300">
                                                <FileText className="w-5 h-5" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="text-sm font-medium text-surface-900 dark:text-white truncate" title={attachment.file_name}>
                                                    {attachment.file_name}
                                                </p>
                                                <p className="text-xs text-surface-500">
                                                    {formatFileSize(attachment.file_size)} • {attachment.file_type}
                                                </p>
                                            </div>
                                        </div>
                                        <button
                                            className="p-2 text-surface-400 hover:text-primary-500 transition-colors"
                                            title="Download"
                                            onClick={async () => {
                                                try {
                                                    const token = getAccessToken();
                                                    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:5003';
                                                    const downloadUrl = `${baseUrl}/api/tickets/${ticketId}/attachments/${attachment.id}/download/`;

                                                    const response = await fetch(downloadUrl, {
                                                        headers: {
                                                            'Authorization': `Bearer ${token}`,
                                                        },
                                                    });

                                                    if (!response.ok) {
                                                        throw new Error('Download failed');
                                                    }

                                                    const blob = await response.blob();
                                                    const url = window.URL.createObjectURL(blob);
                                                    const a = document.createElement('a');
                                                    a.href = url;
                                                    a.download = attachment.file_name;
                                                    document.body.appendChild(a);
                                                    a.click();
                                                    window.URL.revokeObjectURL(url);
                                                    document.body.removeChild(a);
                                                } catch (err) {
                                                    console.error('Download error:', err);
                                                    alert('Failed to download file');
                                                }
                                            }}
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* History */}
                    <div className="card">
                        <TicketHistory ticketId={ticketId} />
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Actions */}
                    <TicketActions ticket={ticket} onTicketUpdate={handleTicketUpdate} />

                    {/* Metadata Card */}
                    <div className="card space-y-6">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-surface-400 mb-4">Ticket Details</h3>

                        <div className="space-y-4">
                            <div className="group">
                                <div className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                                    <User className="w-3.5 h-3.5" /> Assigned To
                                </div>
                                <div className="flex items-center gap-3">
                                    {ticket.assigned_to ? (
                                        <>
                                            <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-700 dark:text-primary-400 font-bold text-xs ring-2 ring-white dark:ring-surface-900">
                                                {ticket.assigned_to.name.charAt(0)}
                                            </div>
                                            <div>
                                                <div className="text-sm font-medium text-surface-900 dark:text-white">{ticket.assigned_to.name}</div>
                                                <div className="text-xs text-surface-500">{ticket.assigned_to.email}</div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="text-sm text-surface-400 italic flex items-center gap-2">
                                            <div className="w-8 h-8 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center">
                                                <User className="w-4 h-4" />
                                            </div>
                                            Unassigned
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="h-px bg-surface-100 dark:bg-surface-800" />

                            <div className="grid grid-cols-1 gap-4">
                                <div>
                                    <div className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                                        <Tag className="w-3.5 h-3.5" /> Category
                                    </div>
                                    <div className="text-sm text-surface-900 dark:text-white">{ticket.category.name}</div>
                                    <div className="text-xs text-surface-500 mt-0.5">{ticket.subcategory.name}</div>
                                </div>

                                <div>
                                    <div className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                                        <Briefcase className="w-3.5 h-3.5" /> Department
                                    </div>
                                    <div className="text-sm text-surface-900 dark:text-white">{ticket.department.name}</div>
                                </div>

                                {(ticket.assigned_at || ticket.closed_at) && (
                                    <>
                                        {ticket.assigned_at && (
                                            <div>
                                                <div className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                                                    <Calendar className="w-3.5 h-3.5" /> Assigned Date
                                                </div>
                                                <div className="text-sm text-surface-700 dark:text-surface-300">{formatDateIST(ticket.assigned_at)}</div>
                                            </div>
                                        )}
                                        {ticket.is_closed && ticket.closure_code && (
                                            <div className="p-3 rounded-lg bg-surface-50 dark:bg-surface-800/50 border border-surface-100 dark:border-surface-700">
                                                <div className="text-xs font-semibold text-surface-500 uppercase tracking-wide mb-1">
                                                    Closure Code
                                                </div>
                                                <div className="text-sm font-medium text-surface-900 dark:text-white">
                                                    {ticket.closure_code.code}
                                                </div>
                                                <div className="text-xs text-surface-500 mt-0.5">
                                                    {ticket.closure_code.description}
                                                </div>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
