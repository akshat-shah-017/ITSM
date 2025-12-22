// Pages - Employee My Performance
// Employee self-view of their own performance metrics

import { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { getMyDetailedAnalytics } from '../../api/analytics';
import type { EmployeeDetailedAnalytics } from '../../api/analytics';
import { LoadingSpinner, ErrorMessage } from '../../components/common';
import {
    TrendingUp,
    Calendar,
    Clock,
    CheckCircle,
    AlertCircle,
    BarChart3,
    Target,
} from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';

// Status colors
const STATUS_COLORS: Record<string, string> = {
    'New': '#3b82f6',
    'Assigned': '#8b5cf6',
    'In Progress': '#f59e0b',
    'Waiting': '#6b7280',
    'On Hold': '#ef4444',
    'Closed': '#22c55e'
};

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

export function MyPerformancePage() {
    const [analytics, setAnalytics] = useState<EmployeeDetailedAnalytics | null>(null);
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
            const data = await getMyDetailedAnalytics(startDate, endDate);
            setAnalytics(data);
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

    const weeklyData = analytics?.by_week || [];

    // Calculate resolution rate
    const resolutionRate = analytics && analytics.summary.total > 0
        ? Math.round((analytics.summary.closed / analytics.summary.total) * 100)
        : 0;

    if (error) {
        return <ErrorMessage error={error} onRetry={loadData} />;
    }

    return (
        <div className="space-y-4">
            {/* Compact Header + Date Filter */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-6 h-6 text-primary-500" />
                    <h1 className="text-xl font-bold text-surface-900 dark:text-white">My Performance</h1>
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
                    <div className="grid grid-cols-5 gap-3">
                        <KPICard icon={BarChart3} label="Total" value={analytics.summary.total} color="blue" />
                        <KPICard icon={AlertCircle} label="Open" value={analytics.summary.open} color="amber" />
                        <KPICard icon={CheckCircle} label="Closed" value={analytics.summary.closed} color="green" />
                        <KPICard icon={Clock} label="Avg Res." value={analytics.summary.avg_resolution_hours ? `${analytics.summary.avg_resolution_hours.toFixed(1)}h` : 'N/A'} color="purple" />
                        <KPICard icon={Target} label="Rate" value={`${resolutionRate}%`} color="green" />
                    </div>

                    {/* Charts Row */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {/* Status Breakdown */}
                        <ChartCard title="Status Breakdown">
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2}>
                                        {statusData.map((entry, i) => <Cell key={i} fill={STATUS_COLORS[entry.name] || '#6b7280'} />)}
                                    </Pie>
                                    <Tooltip />
                                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </ChartCard>

                        {/* Weekly Performance */}
                        <ChartCard title="Weekly Performance">
                            <ResponsiveContainer width="100%" height={200}>
                                <BarChart data={weeklyData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                                    <XAxis dataKey="week_start" tick={{ fontSize: 10 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip labelFormatter={(v) => `Week of ${new Date(v).toLocaleDateString()}`} />
                                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                                    <Bar dataKey="assigned" name="Assigned" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="resolved" name="Resolved" fill="#22c55e" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </ChartCard>
                    </div>

                    {/* Category Breakdown */}
                    {analytics.by_category.length > 0 && (
                        <ChartCard title="Tickets by Category">
                            <ResponsiveContainer width="100%" height={180}>
                                <BarChart data={analytics.by_category.slice(0, 6)} layout="vertical">
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
function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="card p-4">
            <h3 className="text-sm font-semibold text-surface-900 dark:text-white mb-3">{title}</h3>
            {children}
        </div>
    );
}
