import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../auth';
import {
    LayoutDashboard,
    Ticket,
    Inbox,
    UserCheck,
    Users,
    Settings,
    ChevronLeft,
    ChevronRight,
    Mail,
    TrendingUp,
    BarChart3,
} from 'lucide-react';

export function Sidebar() {
    const { isAuthenticated, isEmployee, isManager, isAdmin } = useAuth();
    const [isCollapsed, setIsCollapsed] = useState(false);

    if (!isAuthenticated) return null;

    const toggleCollapsed = () => setIsCollapsed(!isCollapsed);

    // Glassmorphism Nav Link Component
    const NavItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => (
        <NavLink
            to={to}
            className={({ isActive }) => `
                flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 mb-1 group relative font-medium
                ${isActive
                    ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400 border border-primary-500/20'
                    : 'text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800/50'
                }
            `}
            title={isCollapsed ? label : ''}
        >
            <Icon size={20} strokeWidth={2} className="shrink-0 transition-colors" />
            {!isCollapsed && (
                <span className="truncate text-sm opacity-0 animate-fade-in fill-mode-forwards" style={{ animationDelay: '50ms' }}>
                    {label}
                </span>
            )}

            {/* Tooltip for collapsed state */}
            {isCollapsed && (
                <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-3 py-2 bg-surface-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity shadow-lg">
                    {label}
                </div>
            )}
        </NavLink>
    );

    const SectionLabel = ({ label }: { label: string }) => (
        !isCollapsed && (
            <div className="px-4 mt-6 mb-3 text-xs font-bold uppercase tracking-wider text-surface-400 dark:text-surface-500">
                {label}
            </div>
        )
    );

    return (
        <aside
            className={`
                sticky top-16 h-[calc(100vh-4rem)] z-40
                bg-white/80 dark:bg-[#0a0a0a]/90 
                backdrop-blur-xl
                border-r border-surface-200/50 dark:border-[#262626]/50
                transition-all duration-300 ease-in-out
                flex flex-col shrink-0
                ${isCollapsed ? 'w-20' : 'w-64'}
            `}
        >
            <div className="flex-1 overflow-y-auto py-6 px-3 custom-scrollbar">

                <SectionLabel label="Overview" />
                <NavItem to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
                <NavItem to="/tickets" icon={Ticket} label="My Tickets" />

                {isEmployee && (
                    <>
                        <SectionLabel label="Work Space" />
                        <NavItem to="/employee/queue" icon={Inbox} label="Department Queue" />
                        <NavItem to="/employee/tickets" icon={UserCheck} label="Assigned to Me" />
                        <NavItem to="/employee/emails" icon={Mail} label="Email Inbox" />
                        <NavItem to="/employee/performance" icon={TrendingUp} label="My Performance" />
                    </>
                )}

                {isManager && (
                    <>
                        <SectionLabel label="Management" />
                        <NavItem to="/manager/team" icon={Users} label="Team Overview" />
                        <NavItem to="/manager/analytics" icon={BarChart3} label="Analytics" />
                    </>
                )}

                {isAdmin && (
                    <>
                        <SectionLabel label="System" />
                        <NavItem to="/admin/settings" icon={Settings} label="Settings" />
                    </>
                )}
            </div>

            {/* Footer / Collapse Toggle */}
            <div className="p-4 border-t border-surface-200/50 dark:border-surface-800/50">
                <button
                    onClick={toggleCollapsed}
                    className="w-full flex items-center justify-center p-3 rounded-xl text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                >
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>
        </aside>
    );
}

