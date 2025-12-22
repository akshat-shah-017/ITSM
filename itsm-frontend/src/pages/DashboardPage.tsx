// Pages - Dashboard Page
// Tabbed interface for Employee/Manager: My Work / Queue
// Enhanced ticket table with filters and sorting
// User dashboard with active tickets list

import { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { getEmployeeTickets, getEmployeeQueue, getManagerTeam, getTickets } from '../api/tickets';
import { assignTicket } from '../api/mutations';
import { getEmployeeAnalytics } from '../api/analytics';
import type { EmployeeAnalytics } from '../api/analytics';
import type { TicketSummary } from '../types/ticket';
import type { TeamMember } from '../types/user';
import { LoadingSpinner, ErrorMessage } from '../components/common';
import { getCurrentTimeIST, getTimeElapsedString } from '../utils/dateFormat';
import {
    Plus,
    FileText,
    Clock,
    ArrowRight,
    User,
    UserPlus,
    Inbox,
    AlertTriangle,
    ArrowUpCircle,
    Ticket,
    Briefcase,
    AlertOctagon,
    PlayCircle,
    Search,
    BarChart3,
    ChevronUp,
    ChevronDown,
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
} from 'recharts';

// Status colors for pie chart
const STATUS_COLORS: Record<string, string> = {
    'New': '#3b82f6',
    'Assigned': '#8b5cf6',
    'In Progress': '#f59e0b',
    'Waiting': '#6b7280',
    'On Hold': '#ef4444',
    'Closed': '#22c55e'
};

// =============================================================================
// SHARED COMPONENTS
// =============================================================================

// Status badge with color
function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, string> = {
        'New': 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30',
        'Assigned': 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30',
        'In Progress': 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
        'Pending': 'bg-gray-500/15 text-gray-600 dark:text-gray-400 border-gray-500/30',
        'Waiting': 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30',
        'On Hold': 'bg-orange-500/15 text-orange-600 dark:text-orange-400 border-orange-500/30',
        'Resolved': 'bg-green-500/15 text-green-600 dark:text-green-400 border-green-500/30',
        'Closed': 'bg-surface-500/15 text-surface-600 dark:text-surface-400 border-surface-500/30',
    };
    return (
        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${colors[status] || 'bg-gray-500/15 text-gray-600 border-gray-500/30'}`}>
            {status}
        </span>
    );
}

// Priority badge
function PriorityBadge({ priority }: { priority?: string | number }) {
    if (!priority) return <span className="text-xs text-surface-400">—</span>;
    const p = String(priority).toLowerCase();
    if (p === 'critical' || p === '1') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold bg-red-500/15 text-red-600 dark:text-red-400 rounded-full border border-red-500/30">
                <AlertTriangle className="w-3 h-3" /> Critical
            </span>
        );
    }
    if (p === 'high' || p === '2') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold bg-orange-500/15 text-orange-600 dark:text-orange-400 rounded-full border border-orange-500/30">
                <ArrowUpCircle className="w-3 h-3" /> High
            </span>
        );
    }
    if (p === 'medium' || p === '3') {
        return (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-blue-500/15 text-blue-600 dark:text-blue-400 rounded-full border border-blue-500/30">
                Medium
            </span>
        );
    }
    return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-surface-500/15 text-surface-600 dark:text-surface-400 rounded-full border border-surface-500/30">
            Low
        </span>
    );
}

// Stat card with icon
function StatCard({ icon: Icon, label, value, color }: {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    value: number | string;
    color: 'blue' | 'orange' | 'green' | 'red' | 'purple';
}) {
    const colors = {
        blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
        orange: 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20',
        green: 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20',
        red: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
        purple: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20',
    };

    return (
        <div className={`flex items-center gap-4 p-4 rounded-xl border ${colors[color]} transition-all hover:scale-[1.02]`}>
            <div className="p-2.5 rounded-lg bg-white/50 dark:bg-white/5">
                <Icon size={22} />
            </div>
            <div>
                <div className="text-2xl font-bold">{value}</div>
                <div className="text-xs font-medium opacity-80">{label}</div>
            </div>
        </div>
    );
}

// Tab button
function TabButton({ active, onClick, icon: Icon, label, count }: {
    active: boolean;
    onClick: () => void;
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    count?: number;
}) {
    return (
        <button
            onClick={onClick}
            className={`
                flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-all
                ${active
                    ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 border border-primary-500/30'
                    : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800'
                }
            `}
        >
            <Icon size={18} />
            {label}
            {typeof count === 'number' && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${active ? 'bg-primary-500/20' : 'bg-surface-200 dark:bg-surface-700'}`}>
                    {count}
                </span>
            )}
        </button>
    );
}

// Sortable table header
function SortableHeader({
    field,
    label,
    sortField,
    sortOrder,
    onSort
}: {
    field: string;
    label: string;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    onSort: (field: string) => void;
}) {
    const isActive = sortField === field;
    return (
        <th
            onClick={() => onSort(field)}
            className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500 dark:text-surface-400 cursor-pointer hover:text-primary-600 dark:hover:text-primary-400 transition-colors select-none"
        >
            <span className="inline-flex items-center gap-1">
                {label}
                {isActive && (
                    sortOrder === 'asc'
                        ? <ChevronUp className="w-3.5 h-3.5" />
                        : <ChevronDown className="w-3.5 h-3.5" />
                )}
            </span>
        </th>
    );
}

// =============================================================================
// EMPLOYEE/MANAGER TICKET TABLE
// =============================================================================

interface TicketTableRowProps {
    ticket: TicketSummary;
    onAssign?: () => void;
    isAssigning?: boolean;
    showAssignee?: boolean;
    teamMembers?: TeamMember[];
    onAssignTo?: (memberId: string) => void;
}

function TicketTableRow({ ticket, onAssign, isAssigning, showAssignee, teamMembers, onAssignTo }: TicketTableRowProps) {
    const navigate = useNavigate();
    const hasTeamDropdown = teamMembers && teamMembers.length > 0;

    const handleRowClick = (e: React.MouseEvent) => {
        const target = e.target as HTMLElement;
        if (target.closest('button') || target.closest('select')) return;
        navigate(`/tickets/${ticket.id}`);
    };

    return (
        <tr
            onClick={handleRowClick}
            className="border-b border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800/50 cursor-pointer transition-colors"
        >
            {/* Ticket # */}
            <td className="py-3 px-4">
                <span className="text-xs font-mono text-surface-500 dark:text-surface-400">
                    {ticket.ticket_number}
                </span>
            </td>

            {/* Status */}
            <td className="py-3 px-4">
                <StatusBadge status={ticket.status} />
            </td>

            {/* Priority */}
            <td className="py-3 px-4">
                <PriorityBadge priority={ticket.priority} />
            </td>

            {/* Title */}
            <td className="py-3 px-4 max-w-[300px]">
                <span className="text-sm font-medium text-surface-900 dark:text-surface-100 line-clamp-1">
                    {ticket.title}
                </span>
            </td>

            {/* Category */}
            <td className="py-3 px-4">
                <span className="text-xs text-surface-500 dark:text-surface-400">
                    {ticket.category?.name || '—'}
                </span>
            </td>

            {/* Requester */}
            <td className="py-3 px-4">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-surface-200 dark:bg-surface-700 flex items-center justify-center">
                        <User className="w-3.5 h-3.5 text-surface-500" />
                    </div>
                    <span className="text-xs text-surface-600 dark:text-surface-400 truncate max-w-[100px]">
                        {ticket.created_by?.name || '—'}
                    </span>
                </div>
            </td>

            {/* Age */}
            <td className="py-3 px-4">
                <div className="flex items-center gap-1 text-xs text-surface-500 dark:text-surface-400">
                    <Clock className="w-3.5 h-3.5" />
                    {getTimeElapsedString(ticket.created_at)}
                </div>
            </td>

            {/* Assignee / Action */}
            <td className="py-3 px-4">
                {showAssignee && ticket.assigned_to ? (
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-primary-500/10 flex items-center justify-center">
                            <User className="w-3.5 h-3.5 text-primary-500" />
                        </div>
                        <span className="text-xs text-surface-600 dark:text-surface-400 truncate">
                            {ticket.assigned_to.name}
                        </span>
                    </div>
                ) : hasTeamDropdown ? (
                    <select
                        className="px-2 py-1.5 text-xs bg-surface-100 dark:bg-surface-700 border border-surface-300 dark:border-surface-600 rounded-lg cursor-pointer text-surface-700 dark:text-surface-300"
                        onChange={(e) => {
                            e.stopPropagation();
                            if (e.target.value === 'self' && onAssign) {
                                onAssign();
                            } else if (e.target.value && onAssignTo) {
                                onAssignTo(e.target.value);
                            }
                            e.target.value = '';
                        }}
                        onClick={(e) => e.stopPropagation()}
                        defaultValue=""
                        disabled={isAssigning}
                    >
                        <option value="" disabled>{isAssigning ? 'Assigning...' : 'Assign...'}</option>
                        <option value="self">Assign to Me</option>
                        {teamMembers.map((m) => (
                            <option key={m.id} value={m.id}>{m.name}</option>
                        ))}
                    </select>
                ) : onAssign ? (
                    <button
                        onClick={(e) => { e.stopPropagation(); onAssign(); }}
                        disabled={isAssigning}
                        className="px-3 py-1.5 text-xs font-medium bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded-lg hover:bg-primary-500/20 transition-colors flex items-center gap-1 disabled:opacity-50"
                    >
                        <UserPlus size={14} /> {isAssigning ? 'Assigning...' : 'Assign to Me'}
                    </button>
                ) : null}
            </td>
        </tr>
    );
}

// =============================================================================
// USER TICKET TABLE ROW
// =============================================================================

function UserTicketRow({ ticket }: { ticket: TicketSummary }) {
    const navigate = useNavigate();

    return (
        <tr
            onClick={() => navigate(`/tickets/${ticket.id}`)}
            className="border-b border-surface-200 dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800/50 cursor-pointer transition-colors"
        >
            <td className="py-3 px-4">
                <span className="text-xs font-mono text-surface-500 dark:text-surface-400">
                    {ticket.ticket_number}
                </span>
            </td>
            <td className="py-3 px-4">
                <StatusBadge status={ticket.status} />
            </td>
            <td className="py-3 px-4">
                <PriorityBadge priority={ticket.priority} />
            </td>
            <td className="py-3 px-4 max-w-[300px]">
                <span className="text-sm font-medium text-surface-900 dark:text-surface-100 line-clamp-1">
                    {ticket.title}
                </span>
            </td>
            <td className="py-3 px-4">
                {ticket.assigned_to ? (
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-primary-500/10 flex items-center justify-center">
                            <User className="w-3.5 h-3.5 text-primary-500" />
                        </div>
                        <span className="text-xs text-surface-600 dark:text-surface-400">
                            {ticket.assigned_to.name}
                        </span>
                    </div>
                ) : (
                    <span className="text-xs text-surface-400">Unassigned</span>
                )}
            </td>
            <td className="py-3 px-4">
                <div className="flex items-center gap-1 text-xs text-surface-500 dark:text-surface-400">
                    <Clock className="w-3.5 h-3.5" />
                    {getTimeElapsedString(ticket.created_at)}
                </div>
            </td>
            <td className="py-3 px-4">
                <ArrowRight className="w-4 h-4 text-surface-400" />
            </td>
        </tr>
    );
}

// =============================================================================
// MAIN DASHBOARD COMPONENT
// =============================================================================

type EmployeeTab = 'my-work' | 'queue';

export function DashboardPage() {
    const { user, isEmployee, isManager } = useAuth();
    const [activeTab, setActiveTab] = useState<EmployeeTab>('my-work');
    const [assignedTickets, setAssignedTickets] = useState<TicketSummary[]>([]);
    const [queueTickets, setQueueTickets] = useState<TicketSummary[]>([]);
    const [userTickets, setUserTickets] = useState<TicketSummary[]>([]);
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
    const [employeeAnalytics, setEmployeeAnalytics] = useState<EmployeeAnalytics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<unknown>(null);
    const [assigningTicketId, setAssigningTicketId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortField, setSortField] = useState<string>('created_at');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

    const loadDashboardData = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            if (isEmployee) {
                const [assignedRes, queueRes, analytics] = await Promise.all([
                    getEmployeeTickets({ page_size: 50 }),
                    getEmployeeQueue({ page_size: 50 }),
                    getEmployeeAnalytics(),
                ]);
                setAssignedTickets(assignedRes.results.filter(t => t.status !== 'Closed'));
                setQueueTickets(queueRes.results);
                setEmployeeAnalytics(analytics);
            } else {
                const ticketsRes = await getTickets({ page_size: 50 });
                setUserTickets(ticketsRes.results);
            }

            if (isManager) {
                try {
                    const team = await getManagerTeam();
                    setTeamMembers(team);
                } catch { /* ignore */ }
            }
        } catch (err) {
            setError(err);
        } finally {
            setIsLoading(false);
        }
    }, [isEmployee, isManager]);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    const handleSelfAssign = async (ticketId: string) => {
        setAssigningTicketId(ticketId);
        try {
            await assignTicket(ticketId);
            await loadDashboardData();
        } catch (err) {
            console.error('Failed to assign ticket:', err);
            alert('Failed to assign ticket. Please try again.');
        } finally {
            setAssigningTicketId(null);
        }
    };

    const handleAssignTo = async (ticketId: string, memberId: string) => {
        setAssigningTicketId(ticketId);
        try {
            await assignTicket(ticketId, memberId);
            await loadDashboardData();
        } catch (err) {
            console.error('Failed to assign ticket:', err);
            alert('Failed to assign ticket. Please try again.');
        } finally {
            setAssigningTicketId(null);
        }
    };

    // Filter tickets by search
    const filterTickets = (tickets: TicketSummary[]) => {
        if (!searchQuery.trim()) return tickets;
        const q = searchQuery.toLowerCase();
        return tickets.filter(t =>
            t.title.toLowerCase().includes(q) ||
            t.ticket_number.toLowerCase().includes(q)
        );
    };

    // Sort tickets
    const sortTickets = (tickets: TicketSummary[]) => {
        return [...tickets].sort((a, b) => {
            let aVal: string | number = '';
            let bVal: string | number = '';

            switch (sortField) {
                case 'ticket_number':
                    aVal = a.ticket_number;
                    bVal = b.ticket_number;
                    break;
                case 'status':
                    aVal = a.status;
                    bVal = b.status;
                    break;
                case 'title':
                    aVal = a.title.toLowerCase();
                    bVal = b.title.toLowerCase();
                    break;
                case 'category':
                    aVal = a.category?.name?.toLowerCase() || '';
                    bVal = b.category?.name?.toLowerCase() || '';
                    break;
                case 'created_by':
                    aVal = a.created_by?.name?.toLowerCase() || '';
                    bVal = b.created_by?.name?.toLowerCase() || '';
                    break;
                case 'created_at':
                default:
                    aVal = new Date(a.created_at).getTime();
                    bVal = new Date(b.created_at).getTime();
                    break;
            }

            if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
            return 0;
        });
    };

    // Handle sort toggle
    const handleSort = (field: string) => {
        if (sortField === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortOrder('asc');
        }
    };

    // Compute stats
    const queueCount = queueTickets.length;
    const myWorkCount = assignedTickets.length;
    const inProgressCount = assignedTickets.filter(t => t.status === 'In Progress').length;
    const overdueCount = 0; // TODO: Calculate based on SLA if available

    if (isLoading) {
        return <LoadingSpinner message="Loading dashboard..." />;
    }

    if (error) {
        return <ErrorMessage error={error} title="Failed to load dashboard" onRetry={loadDashboardData} />;
    }

    // Current tickets based on active tab (filtered and sorted)
    const currentTickets = sortTickets(
        activeTab === 'my-work'
            ? filterTickets(assignedTickets)
            : filterTickets(queueTickets)
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 dark:text-white">
                        Welcome, <span className="text-primary-600 dark:text-primary-400">{user?.name?.split(' ')[0]}</span>
                    </h1>
                    <p className="text-sm text-surface-500 dark:text-surface-400 mt-1">{getCurrentTimeIST()}</p>
                </div>
                <Link to="/tickets/new" className="btn btn-primary">
                    <Plus size={18} /> New Ticket
                </Link>
            </header>

            {/* Stats Widgets - Employee/Manager */}
            {isEmployee && (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatCard icon={Inbox} label="Queue" value={queueCount} color="blue" />
                    <StatCard icon={Briefcase} label="My Work" value={myWorkCount} color="orange" />
                    <StatCard icon={PlayCircle} label="In Progress" value={inProgressCount} color="green" />
                    <StatCard icon={AlertOctagon} label="Overdue" value={overdueCount} color="red" />
                </div>
            )}

            {/* Status Breakdown Chart - Employee/Manager */}
            {isEmployee && employeeAnalytics && employeeAnalytics.by_status && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="card p-6">
                        <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                            <BarChart3 className="w-5 h-5 text-surface-400" />
                            My Status Breakdown
                        </h3>
                        <ResponsiveContainer width="100%" height={200}>
                            <PieChart>
                                <Pie
                                    data={Object.entries(employeeAnalytics.by_status).map(([name, value]) => ({ name, value }))}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={2}
                                    dataKey="value"
                                    label={({ name, percent }) => percent !== undefined ? `${name} (${(percent * 100).toFixed(0)}%)` : name}
                                >
                                    {Object.entries(employeeAnalytics.by_status).map(([name], index) => (
                                        <Cell key={`cell-${index}`} fill={STATUS_COLORS[name] || '#6b7280'} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Quick Stats Card */}
                    <div className="card p-6">
                        <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4">Performance</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="text-center p-4 bg-surface-50 dark:bg-surface-800/50 rounded-lg">
                                <div className="text-3xl font-bold text-surface-900 dark:text-white">{employeeAnalytics.closed_today}</div>
                                <div className="text-xs text-surface-500">Closed Today</div>
                            </div>
                            <div className="text-center p-4 bg-surface-50 dark:bg-surface-800/50 rounded-lg">
                                <div className="text-3xl font-bold text-surface-900 dark:text-white">{employeeAnalytics.closed_last_7_days}</div>
                                <div className="text-xs text-surface-500">Closed This Week</div>
                            </div>
                            <div className="text-center p-4 bg-surface-50 dark:bg-surface-800/50 rounded-lg">
                                <div className="text-3xl font-bold text-surface-900 dark:text-white">{employeeAnalytics.total_open}</div>
                                <div className="text-xs text-surface-500">Total Open</div>
                            </div>
                            <div className="text-center p-4 bg-surface-50 dark:bg-surface-800/50 rounded-lg">
                                <div className="text-3xl font-bold text-surface-900 dark:text-white">
                                    {employeeAnalytics.avg_resolution_hours ? `${employeeAnalytics.avg_resolution_hours.toFixed(1)}h` : 'N/A'}
                                </div>
                                <div className="text-xs text-surface-500">Avg Resolution</div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Tabbed Interface - Employee/Manager */}
            {isEmployee && (
                <div className="bg-white/80 dark:bg-surface-900/80 backdrop-blur-xl border border-surface-200/50 dark:border-surface-700/50 rounded-2xl overflow-hidden">
                    {/* Tab Bar */}
                    <div className="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-700">
                        <div className="flex gap-2">
                            <TabButton
                                active={activeTab === 'my-work'}
                                onClick={() => setActiveTab('my-work')}
                                icon={Briefcase}
                                label="My Work"
                                count={myWorkCount}
                            />
                            <TabButton
                                active={activeTab === 'queue'}
                                onClick={() => setActiveTab('queue')}
                                icon={Inbox}
                                label="Queue"
                                count={queueCount}
                            />
                        </div>

                        {/* Search */}
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                            <input
                                type="text"
                                placeholder="Search tickets..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 pr-4 py-2 text-sm bg-surface-100 dark:bg-surface-800 border border-surface-200 dark:border-surface-700 rounded-lg w-64 focus:outline-none focus:ring-2 focus:ring-primary-500/30"
                            />
                        </div>
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="bg-surface-50 dark:bg-surface-800/50 text-left">
                                    <SortableHeader field="ticket_number" label="Ticket #" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <SortableHeader field="status" label="Status" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500 dark:text-surface-400">Priority</th>
                                    <SortableHeader field="title" label="Title" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <SortableHeader field="category" label="Category" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <SortableHeader field="created_by" label="Requester" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <SortableHeader field="created_at" label="Age" sortField={sortField} sortOrder={sortOrder} onSort={handleSort} />
                                    <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500 dark:text-surface-400">
                                        {activeTab === 'queue' ? 'Action' : 'Assignee'}
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {currentTickets.length === 0 ? (
                                    <tr>
                                        <td colSpan={8} className="py-12 text-center text-surface-400">
                                            <Inbox className="w-12 h-12 mx-auto mb-3 opacity-50" />
                                            <p>No tickets found</p>
                                        </td>
                                    </tr>
                                ) : (
                                    currentTickets.map((ticket) => (
                                        <TicketTableRow
                                            key={ticket.id}
                                            ticket={ticket}
                                            showAssignee={activeTab === 'my-work'}
                                            onAssign={activeTab === 'queue' ? () => handleSelfAssign(ticket.id) : undefined}
                                            isAssigning={assigningTicketId === ticket.id}
                                            teamMembers={isManager && activeTab === 'queue' ? teamMembers : undefined}
                                            onAssignTo={activeTab === 'queue' ? (memberId) => handleAssignTo(ticket.id, memberId) : undefined}
                                        />
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* User Dashboard */}
            {!isEmployee && (
                <div className="bg-white/80 dark:bg-surface-900/80 backdrop-blur-xl border border-surface-200/50 dark:border-surface-700/50 rounded-2xl overflow-hidden">
                    <div className="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-700">
                        <h2 className="text-lg font-bold text-surface-900 dark:text-white flex items-center gap-2">
                            <Ticket size={20} className="text-primary-500" />
                            Your Tickets
                            <span className="text-sm font-normal text-surface-500">({userTickets.length})</span>
                        </h2>
                        <Link to="/tickets" className="text-sm font-medium text-primary-600 dark:text-primary-400 hover:text-primary-500 flex items-center gap-1">
                            View All <ArrowRight size={14} />
                        </Link>
                    </div>

                    {userTickets.length === 0 ? (
                        <div className="text-center py-12">
                            <FileText size={48} className="mx-auto text-surface-400 mb-4" />
                            <h3 className="text-lg font-bold text-surface-900 dark:text-white mb-2">Welcome to ITSM</h3>
                            <p className="text-surface-500 dark:text-surface-400 mb-6">Create tickets to get support from our team</p>
                            <Link to="/tickets/new" className="btn btn-primary">
                                <Plus size={18} /> Create Your First Ticket
                            </Link>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="bg-surface-50 dark:bg-surface-800/50 text-left">
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Ticket #</th>
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Status</th>
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Priority</th>
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Title</th>
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Assigned To</th>
                                        <th className="py-3 px-4 text-xs font-bold uppercase tracking-wider text-surface-500">Age</th>
                                        <th className="py-3 px-4"></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {userTickets.map((ticket) => (
                                        <UserTicketRow key={ticket.id} ticket={ticket} />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
