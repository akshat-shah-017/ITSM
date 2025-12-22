// Pages - Manager Team Page (Enhanced)
// Team statistics with charts, employee-wise ticket filtering

import { useCallback, useEffect, useState } from 'react';
import { getManagerTeam, getManagerTeamTickets } from '../../api/tickets';
import { getManagerAnalytics } from '../../api/analytics';
import type { ManagerAnalytics } from '../../api/analytics';
import type { TeamMember } from '../../types/user';
import { TicketList } from '../../components/tickets';
import { LoadingSpinner, ErrorMessage } from '../../components/common';
import {
    Users,
    Mail,
    TrendingUp,
    CheckCircle,
    Clock,
    AlertTriangle,
    BarChart3,
    Ticket,
    ChevronRight,
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
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

const PRIORITY_COLORS: Record<string, string> = {
    '1': '#ef4444',
    '2': '#f97316',
    '3': '#eab308',
    '4': '#22c55e'
};

type ViewType = 'overview' | 'team' | 'employee-tickets';

export function TeamPage() {
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
    const [analytics, setAnalytics] = useState<ManagerAnalytics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);
    const [view, setView] = useState<ViewType>('overview');
    const [selectedEmployee, setSelectedEmployee] = useState<{ id: string; name: string } | null>(null);

    const loadData = useCallback(async () => {
        setIsLoading(true);
        setError(null);

        try {
            const [members, stats] = await Promise.all([
                getManagerTeam(),
                getManagerAnalytics()
            ]);
            setTeamMembers(members);
            setAnalytics(stats);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to load data'));
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // Prepare chart data
    const statusChartData = analytics?.by_status
        ? Object.entries(analytics.by_status).map(([name, value]) => ({ name, value }))
        : [];

    const priorityChartData = analytics?.by_priority
        ? Object.entries(analytics.by_priority).map(([key, value]) => ({
            name: key === '1' ? 'Critical' : key === '2' ? 'High' : key === '3' ? 'Medium' : 'Low',
            value,
            key
        }))
        : [];

    const trendData = analytics?.volume_trend || [];

    // Handler to view employee tickets
    const handleViewEmployeeTickets = (employee: { id: string; name: string }) => {
        setSelectedEmployee(employee);
        setView('employee-tickets');
    };

    // Fetch tickets filtered by employee
    const fetchEmployeeTickets = useCallback(
        async (params?: { page?: number; page_size?: number }) => {
            if (!selectedEmployee) {
                return { results: [], count: 0, next: null, previous: null, page: 1, page_size: 20, total_count: 0 };
            }
            return getManagerTeamTickets({ ...params, assigned_to: selectedEmployee.id });
        },
        [selectedEmployee]
    );

    if (isLoading) {
        return <div className="flex justify-center p-12"><LoadingSpinner message="Loading team data..." /></div>;
    }

    if (error) {
        return <ErrorMessage error={error} title="Failed to load team data" onRetry={loadData} />;
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 dark:text-white">Team Management</h1>
                    <p className="text-surface-500 mt-1">
                        Team statistics, performance metrics, and ticket management
                    </p>
                </div>
            </header>

            {/* Tab Navigation */}
            <div className="bg-surface-100 dark:bg-surface-800 p-1 rounded-xl inline-flex">
                <TabButton active={view === 'overview'} onClick={() => setView('overview')}>
                    <BarChart3 className="w-4 h-4" />
                    Overview
                </TabButton>
                <TabButton active={view === 'team'} onClick={() => setView('team')}>
                    <Users className="w-4 h-4" />
                    Team Members
                </TabButton>
                {selectedEmployee && (
                    <TabButton active={view === 'employee-tickets'} onClick={() => setView('employee-tickets')}>
                        <Ticket className="w-4 h-4" />
                        {selectedEmployee.name}'s Tickets
                    </TabButton>
                )}
            </div>

            {/* Overview View - Stats & Charts */}
            {view === 'overview' && analytics && (
                <div className="space-y-6">
                    {/* Stats Cards */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard
                            icon={Ticket}
                            label="Total Tickets"
                            value={analytics.team_total_tickets}
                            color="blue"
                        />
                        <StatCard
                            icon={Clock}
                            label="Open Tickets"
                            value={analytics.team_open}
                            color="amber"
                        />
                        <StatCard
                            icon={CheckCircle}
                            label="Closed Tickets"
                            value={analytics.team_closed}
                            color="green"
                        />
                        <StatCard
                            icon={Users}
                            label="Team Size"
                            value={teamMembers.length}
                            color="purple"
                        />
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Status Breakdown */}
                        <div className="card p-6">
                            <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                                <BarChart3 className="w-5 h-5 text-surface-400" />
                                Status Breakdown
                            </h3>
                            {statusChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <PieChart>
                                        <Pie
                                            data={statusChartData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={2}
                                            dataKey="value"
                                            label={({ name, percent }) => percent !== undefined ? `${name} (${(percent * 100).toFixed(0)}%)` : name}
                                        >
                                            {statusChartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || '#6b7280'} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[250px] flex items-center justify-center text-surface-400">
                                    No data available
                                </div>
                            )}
                        </div>

                        {/* Priority Distribution */}
                        <div className="card p-6">
                            <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-surface-400" />
                                Priority Distribution
                            </h3>
                            {priorityChartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={priorityChartData} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" />
                                        <XAxis type="number" stroke="#888" />
                                        <YAxis type="category" dataKey="name" width={80} stroke="#888" />
                                        <Tooltip />
                                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                            {priorityChartData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={PRIORITY_COLORS[entry.key] || '#6b7280'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[250px] flex items-center justify-center text-surface-400">
                                    No data available
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Trend Chart */}
                    {trendData.length > 0 && (
                        <div className="card p-6">
                            <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                                <TrendingUp className="w-5 h-5 text-surface-400" />
                                Ticket Volume Trend (Last 30 Days)
                            </h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={trendData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.2)" />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#888"
                                        tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                                    />
                                    <YAxis stroke="#888" />
                                    <Tooltip
                                        labelFormatter={(label) => new Date(label).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="count"
                                        stroke="#ef4444"
                                        strokeWidth={2}
                                        dot={{ fill: '#ef4444', strokeWidth: 2 }}
                                        activeDot={{ r: 6, fill: '#ef4444' }}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* Employee Performance Table */}
                    <div className="card p-6">
                        <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                            <Users className="w-5 h-5 text-surface-400" />
                            Employee Performance
                        </h3>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-surface-200 dark:border-surface-700">
                                        <th className="text-left py-3 px-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Employee</th>
                                        <th className="text-center py-3 px-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Total</th>
                                        <th className="text-center py-3 px-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Open</th>
                                        <th className="text-center py-3 px-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Closed</th>
                                        <th className="text-center py-3 px-4 text-xs font-semibold uppercase tracking-wider text-surface-500">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-surface-100 dark:divide-surface-800">
                                    {analytics.per_employee_stats.map((emp) => (
                                        <tr key={emp.employee_id} className="hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors">
                                            <td className="py-3 px-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-sm font-bold text-primary-600 dark:text-primary-400">
                                                        {emp.employee_name.charAt(0)}
                                                    </div>
                                                    <div>
                                                        <div className="font-medium text-surface-900 dark:text-white">{emp.employee_name}</div>
                                                        <div className="text-xs text-surface-500">{emp.employee_email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <span className="font-semibold text-surface-900 dark:text-white">{emp.total}</span>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
                                                    {emp.open}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                                                    {emp.closed}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <button
                                                    onClick={() => handleViewEmployeeTickets({ id: emp.employee_id, name: emp.employee_name })}
                                                    className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 font-medium"
                                                >
                                                    View Tickets
                                                    <ChevronRight className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Aging Tickets Alert */}
                    {analytics.aging_tickets.length > 0 && (
                        <div className="card p-6 border-l-4 border-l-amber-500">
                            <h3 className="text-lg font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-amber-500" />
                                Aging Tickets ({analytics.aging_tickets.length})
                            </h3>
                            <div className="space-y-2">
                                {analytics.aging_tickets.slice(0, 5).map((ticket) => (
                                    <div
                                        key={ticket.id}
                                        className="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800/50 rounded-lg"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <span className="text-xs font-mono text-surface-500 mr-2">#{ticket.ticket_number}</span>
                                            <span className="text-sm text-surface-900 dark:text-white truncate">{ticket.title}</span>
                                        </div>
                                        <div className="flex items-center gap-4 text-xs text-surface-500">
                                            <span>{ticket.assigned_to_name}</span>
                                            <span className="text-amber-600 dark:text-amber-400 font-medium">{ticket.age_days} days old</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Team Members View */}
            {view === 'team' && (
                <section className="space-y-4">
                    {teamMembers.length === 0 ? (
                        <div className="text-center py-12 text-surface-500 bg-surface-50 dark:bg-surface-800/50 rounded-2xl border border-surface-200 dark:border-surface-700">
                            <Users size={48} className="mx-auto mb-4 opacity-50" />
                            <p>No team members found.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {teamMembers.map((member) => {
                                const stats = analytics?.per_employee_stats.find(e => e.employee_id === member.id);
                                return (
                                    <div key={member.id} className="glass-panel p-5 rounded-xl hover-lift">
                                        <div className="flex items-start gap-4">
                                            <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-lg font-bold text-primary-600 dark:text-primary-400">
                                                {member.name.charAt(0)}
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-semibold text-surface-900 dark:text-white truncate">
                                                    {member.name}
                                                </h3>
                                                <div className="flex items-center gap-2 mt-1 text-xs text-surface-500">
                                                    <Mail size={14} />
                                                    <span className="truncate">{member.email}</span>
                                                </div>
                                            </div>
                                        </div>
                                        {stats && (
                                            <div className="mt-4 pt-4 border-t border-surface-200 dark:border-surface-700 grid grid-cols-3 gap-2 text-center">
                                                <div>
                                                    <div className="text-lg font-bold text-surface-900 dark:text-white">{stats.total}</div>
                                                    <div className="text-xs text-surface-500">Total</div>
                                                </div>
                                                <div>
                                                    <div className="text-lg font-bold text-amber-600 dark:text-amber-400">{stats.open}</div>
                                                    <div className="text-xs text-surface-500">Open</div>
                                                </div>
                                                <div>
                                                    <div className="text-lg font-bold text-green-600 dark:text-green-400">{stats.closed}</div>
                                                    <div className="text-xs text-surface-500">Closed</div>
                                                </div>
                                            </div>
                                        )}
                                        <button
                                            onClick={() => handleViewEmployeeTickets({ id: member.id, name: member.name })}
                                            className="mt-4 w-full btn btn-secondary text-sm"
                                        >
                                            View Tickets
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </section>
            )}

            {/* Employee Tickets View */}
            {view === 'employee-tickets' && selectedEmployee && (
                <section>
                    <div className="mb-4 flex items-center gap-2">
                        <button
                            onClick={() => setView('overview')}
                            className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400"
                        >
                            ← Back to Overview
                        </button>
                    </div>
                    <TicketList
                        title={`${selectedEmployee.name}'s Tickets`}
                        fetchTickets={fetchEmployeeTickets}
                        emptyMessage="No tickets found"
                        emptyDescription={`${selectedEmployee.name} doesn't have any tickets assigned.`}
                    />
                </section>
            )}
        </div>
    );
}

// Tab Button Component
function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
    return (
        <button
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${active
                ? 'bg-white dark:bg-surface-700 text-primary-600 dark:text-primary-400 shadow-sm'
                : 'text-surface-600 dark:text-surface-400 hover:text-surface-900 dark:hover:text-surface-200'
                }`}
            onClick={onClick}
        >
            {children}
        </button>
    );
}

// Stat Card Component
function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
    const colorClasses: Record<string, string> = {
        blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
        amber: 'bg-amber-500/10 text-amber-600 dark:text-amber-400',
        green: 'bg-green-500/10 text-green-600 dark:text-green-400',
        purple: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
        red: 'bg-red-500/10 text-red-600 dark:text-red-400',
    };

    return (
        <div className="card p-5">
            <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${colorClasses[color]}`}>
                    <Icon className="w-5 h-5" />
                </div>
                <div>
                    <div className="text-2xl font-bold text-surface-900 dark:text-white">{value}</div>
                    <div className="text-xs text-surface-500">{label}</div>
                </div>
            </div>
        </div>
    );
}
