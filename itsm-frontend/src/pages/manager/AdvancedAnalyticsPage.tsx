// Pages - Manager Advanced Analytics
// Detailed ticket analytics with date range and org breakdown

import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { getDetailedAnalytics, getManagerAnalytics } from '../../api/analytics';
import type { DetailedAnalytics, ManagerAnalytics } from '../../api/analytics';
import { LoadingSpinner, ErrorMessage } from '../../components/common';
import {
    BarChart3,
    Building2,
    Landmark,
    Calendar,
    TrendingUp,
    Clock,
    CheckCircle,
    AlertCircle,
    Users,
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
    Legend,
} from 'recharts';

// Color palettes
const STATUS_COLORS: Record<string, string> = {
    'New': '#3b82f6',
    'Assigned': '#8b5cf6',
    'In Progress': '#f59e0b',
    'Waiting': '#6b7280',
    'On Hold': '#ef4444',
    'Closed': '#22c55e'
};

const PRIORITY_COLORS: Record<string, string> = {
    'P1': '#ef4444',
    'P2': '#f97316',
    'P3': '#eab308',
    'P4': '#22c55e'
};

const CHART_COLORS = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16'];

// Date presets
const DATE_PRESETS = [
    {
        label: 'This Month', getValue: () => {
            const now = new Date();
            return { start: new Date(now.getFullYear(), now.getMonth(), 1), end: now };
        }
    },
    {
        label: 'Last Month', getValue: () => {
            const now = new Date();
            return { start: new Date(now.getFullYear(), now.getMonth() - 1, 1), end: new Date(now.getFullYear(), now.getMonth(), 0) };
        }
    },
    {
        label: 'Last 90 Days', getValue: () => {
            const now = new Date();
            return { start: new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000), end: now };
        }
    },
];

function formatDate(date: Date): string {
    return date.toISOString().split('T')[0];
}

export function AdvancedAnalyticsPage() {
    const [analytics, setAnalytics] = useState<DetailedAnalytics | null>(null);
    const [managerData, setManagerData] = useState<ManagerAnalytics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const [startDate, setStartDate] = useState(() => {
        const now = new Date();
        return formatDate(new Date(now.getFullYear(), now.getMonth(), 1));
    });
    const [endDate, setEndDate] = useState(() => formatDate(new Date()));

    const location = useLocation();

    const loadData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const [detailed, manager] = await Promise.all([
                getDetailedAnalytics(startDate, endDate),
                getManagerAnalytics()
            ]);
            setAnalytics(detailed);
            setManagerData(manager);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to load analytics'));
        } finally {
            setIsLoading(false);
        }
    }, [startDate, endDate]);

    // Refetch on navigation or date change
    useEffect(() => {
        loadData();
    }, [loadData, location.pathname]);

    const applyPreset = (preset: typeof DATE_PRESETS[0]) => {
        const { start, end } = preset.getValue();
        setStartDate(formatDate(start));
        setEndDate(formatDate(end));
    };

    // Prepare chart data
    const statusData = analytics?.by_status
        ? Object.entries(analytics.by_status).map(([name, value]) => ({ name, value }))
        : [];

    const priorityData = analytics?.by_priority
        ? Object.entries(analytics.by_priority).map(([name, value]) => ({ name, value }))
        : [];

    // Company breakdown for pie chart
    const companyPieData = analytics?.by_company
        ?.filter(c => c.total > 0)
        .map(c => ({ name: c.name, value: c.total })) || [];

    // Business group breakdown
    const bgPieData = analytics?.by_business_group
        ?.filter(bg => bg.total > 0)
        .map(bg => ({ name: bg.name, value: bg.total })) || [];

    // Employee closed tickets for ring chart
    const employeeClosedData = managerData?.per_employee_stats
        ?.filter(e => e.closed > 0)
        .map(e => ({ name: e.employee_name.split(' ')[0], value: e.closed, fullName: e.employee_name })) || [];

    if (error) {
        return <ErrorMessage error={error} onRetry={loadData} />;
    }

    return (
        <div className="space-y-4">
            {/* Compact Header + Date Filter */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-primary-500" />
                    <h1 className="text-xl font-bold text-surface-900 dark:text-white">Analytics</h1>
                </div>

                {/* Compact Date Range */}
                <div className="flex items-center gap-2 flex-wrap">
                    <Calendar className="w-4 h-4 text-surface-400" />
                    <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="input py-1 px-2 text-xs w-32"
                    />
                    <span className="text-surface-400 text-xs">to</span>
                    <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="input py-1 px-2 text-xs w-32"
                    />
                    {DATE_PRESETS.map((preset) => (
                        <button
                            key={preset.label}
                            onClick={() => applyPreset(preset)}
                            className="px-2 py-1 text-xs font-medium rounded-md bg-surface-100 dark:bg-surface-800 hover:bg-surface-200 dark:hover:bg-surface-700 text-surface-500 transition-colors"
                        >
                            {preset.label}
                        </button>
                    ))}
                </div>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-12"><LoadingSpinner /></div>
            ) : analytics ? (
                <>
                    {/* KPI Summary Row */}
                    <div className="grid grid-cols-4 gap-3">
                        <KPICard icon={BarChart3} label="Total" value={analytics.summary.total} color="blue" />
                        <KPICard icon={AlertCircle} label="Open" value={analytics.summary.open} color="amber" />
                        <KPICard icon={CheckCircle} label="Closed" value={analytics.summary.closed} color="green" />
                        <KPICard icon={Clock} label="Avg Res." value={analytics.summary.avg_resolution_hours ? `${analytics.summary.avg_resolution_hours.toFixed(1)}h` : 'N/A'} color="purple" />
                    </div>

                    {/* Row 1: Status + Priority + Employee Closed */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        {/* Status Breakdown */}
                        <ChartCard title="Status Breakdown">
                            <ResponsiveContainer width="100%" height={180}>
                                <PieChart>
                                    <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2}>
                                        {statusData.map((entry, i) => <Cell key={i} fill={STATUS_COLORS[entry.name] || '#6b7280'} />)}
                                    </Pie>
                                    <Tooltip />
                                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Priority Distribution */}
                        <ChartCard title="Priority Distribution">
                            <ResponsiveContainer width="100%" height={180}>
                                <BarChart data={priorityData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                                    <XAxis type="number" tick={{ fontSize: 10 }} />
                                    <YAxis dataKey="name" type="category" width={35} tick={{ fontSize: 10 }} />
                                    <Tooltip />
                                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                        {priorityData.map((entry, i) => <Cell key={i} fill={PRIORITY_COLORS[entry.name] || '#6b7280'} />)}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Employee Closed Ring Chart */}
                        <ChartCard title="Closed by Employee" icon={Users}>
                            {employeeClosedData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={180}>
                                    <PieChart>
                                        <Pie data={employeeClosedData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={2}>
                                            {employeeClosedData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                                        </Pie>
                                        <Tooltip formatter={(value, _, props) => [`${value} tickets`, props.payload.fullName]} />
                                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[180px] flex items-center justify-center text-surface-500 text-sm">No data</div>
                            )}
                        </ChartCard>
                    </div>

                    {/* Row 2: Company + Business Group Pie Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Company Breakdown Pie */}
                        <ChartCard title="Tickets by Company" icon={Building2}>
                            {companyPieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={200}>
                                    <PieChart>
                                        <Pie data={companyPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
                                            {companyPieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[200px] flex items-center justify-center text-surface-500 text-sm">No company data</div>
                            )}
                        </ChartCard>

                        {/* Business Group Breakdown Pie */}
                        <ChartCard title="Tickets by Business Group" icon={Landmark}>
                            {bgPieData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={200}>
                                    <PieChart>
                                        <Pie data={bgPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`} labelLine={false}>
                                            {bgPieData.map((_, i) => <Cell key={i} fill={CHART_COLORS[(i + 3) % CHART_COLORS.length]} />)}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-[200px] flex items-center justify-center text-surface-500 text-sm">No business group data</div>
                            )}
                        </ChartCard>
                    </div>

                    {/* Volume Trend */}
                    {analytics.volume_trend.length > 0 && (
                        <ChartCard title="Volume Trend" icon={TrendingUp}>
                            <ResponsiveContainer width="100%" height={220}>
                                <LineChart data={analytics.volume_trend}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                                    <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} />
                                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                                    <Line type="monotone" dataKey="created" name="Created" stroke="#3b82f6" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="closed" name="Closed" stroke="#22c55e" strokeWidth={2} dot={false} />
                                </LineChart>
                            </ResponsiveContainer>
                        </ChartCard>
                    )}

                    {/* Top Categories */}
                    {analytics.by_category.length > 0 && (
                        <ChartCard title="Top Categories">
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={analytics.by_category.slice(0, 8)} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                                    <XAxis type="number" tick={{ fontSize: 10 }} />
                                    <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 10 }} />
                                    <Tooltip />
                                    <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>
                    )}
                </>
            ) : null}
        </div>
    );
}

// Compact KPI Card
function KPICard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number | string; color: 'blue' | 'green' | 'amber' | 'purple' }) {
    const colors = {
        blue: 'text-blue-500 bg-blue-500/10',
        green: 'text-green-500 bg-green-500/10',
        amber: 'text-amber-500 bg-amber-500/10',
        purple: 'text-purple-500 bg-purple-500/10',
    };
    return (
        <div className="card p-3">
            <div className="flex items-center gap-2">
                <div className={`p-1.5 rounded-lg ${colors[color]}`}><Icon className="w-4 h-4" /></div>
                <div>
                    <p className="text-xs text-surface-500">{label}</p>
                    <p className="text-lg font-bold text-surface-900 dark:text-white">{value}</p>
                </div>
            </div>
        </div>
    );
}

// Chart Card Wrapper
function ChartCard({ title, icon: Icon, children }: { title: string; icon?: any; children: React.ReactNode }) {
    return (
        <div className="card p-4">
            <h3 className="text-sm font-semibold text-surface-900 dark:text-white mb-3 flex items-center gap-2">
                {Icon && <Icon className="w-4 h-4 text-primary-500" />}
                {title}
            </h3>
            {children}
        </div>
    );
}
