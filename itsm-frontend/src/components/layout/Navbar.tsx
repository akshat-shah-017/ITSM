// Components - Navbar with Glassmorphism Styling and User Info Dropdown
import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth';
import { ThemeToggle } from './ThemeToggle';
import { LogOut, User, Mail, Phone, Shield, Clock, ChevronDown, BadgeCheck, Building2, Landmark, Building, Users, Menu, X } from 'lucide-react';
import Logo from '../../assets/logo.svg';
import { createPortal } from 'react-dom';

export function Navbar() {
    const { user, isAuthenticated, logout } = useAuth();
    const [showUserCard, setShowUserCard] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const userButtonRef = useRef<HTMLButtonElement>(null);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target as Node) &&
                userButtonRef.current &&
                !userButtonRef.current.contains(event.target as Node)
            ) {
                setShowUserCard(false);
            }
        }

        if (showUserCard) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [showUserCard]);

    // Emit event when mobile menu toggles
    useEffect(() => {
        window.dispatchEvent(new CustomEvent('mobileSidebarToggle', { detail: mobileMenuOpen }));
    }, [mobileMenuOpen]);

    // Listen for sidebar close event (when user navigates via sidebar links)
    useEffect(() => {
        const handleSidebarClose = () => setMobileMenuOpen(false);
        window.addEventListener('mobileSidebarClose', handleSidebarClose);
        return () => window.removeEventListener('mobileSidebarClose', handleSidebarClose);
    }, []);

    // Format last login date
    const formatLastLogin = (dateString: string | null) => {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    // Get dropdown position
    const getDropdownPosition = () => {
        if (!userButtonRef.current) return { top: 0, right: 0 };
        const rect = userButtonRef.current.getBoundingClientRect();
        return {
            top: rect.bottom + 8,
            right: window.innerWidth - rect.right,
        };
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white/80 dark:bg-[#0a0a0a]/90 backdrop-blur-xl border-b border-surface-200/50 dark:border-[#262626]/50">
            <div className="h-full flex items-center justify-between px-4 md:px-6 max-w-[1920px] mx-auto">
                {/* Left Section: Hamburger + Logo */}
                <div className="flex items-center gap-3">
                    {/* Mobile Hamburger Menu */}
                    {isAuthenticated && (
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-lg text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                            aria-label="Toggle navigation menu"
                        >
                            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
                        </button>
                    )}

                    {/* Logo Section */}
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-3 group"
                    >
                        <div className="h-8 md:h-9 transition-transform duration-300 group-hover:scale-105">
                            <img
                                src={Logo}
                                alt="Blackbox ITSM"
                                className="h-full w-auto"
                            />
                        </div>
                    </Link>
                </div>

                {/* Right Section */}
                <div className="flex items-center gap-3">
                    <ThemeToggle />

                    {isAuthenticated && user && (
                        <>
                            {/* User Info Button - Clickable */}
                            <button
                                ref={userButtonRef}
                                onClick={() => setShowUserCard(!showUserCard)}
                                className={`hidden md:flex items-center gap-3 px-4 py-2 rounded-xl bg-surface-100/80 dark:bg-surface-800/50 backdrop-blur-sm border transition-all cursor-pointer hover:bg-surface-200/80 dark:hover:bg-surface-700/50 ${showUserCard
                                    ? 'border-primary-500/50 ring-2 ring-primary-500/20'
                                    : 'border-surface-200/50 dark:border-surface-700/50'
                                    }`}
                            >
                                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white text-sm font-bold shadow-glow-sm">
                                    {user.name?.charAt(0).toUpperCase() || <User size={14} />}
                                </div>
                                <div className="flex flex-col text-left">
                                    <span className="text-sm font-semibold text-surface-700 dark:text-surface-200 leading-tight">
                                        {user.name}
                                    </span>
                                    <span className="text-xs text-surface-500 dark:text-surface-400 leading-tight capitalize">
                                        {user.roles?.[0]?.replace(/_/g, ' ') || 'User'}
                                    </span>
                                </div>
                                <ChevronDown
                                    size={16}
                                    className={`text-surface-400 transition-transform ${showUserCard ? 'rotate-180' : ''}`}
                                />
                            </button>

                            {/* User Info Dropdown */}
                            {showUserCard && createPortal(
                                <div
                                    ref={dropdownRef}
                                    className="fixed z-[9999] animate-fade-in"
                                    style={{
                                        top: getDropdownPosition().top,
                                        right: getDropdownPosition().right,
                                    }}
                                >
                                    <div className="w-96 bg-white dark:bg-surface-900 rounded-2xl shadow-depth-3 border border-surface-200 dark:border-surface-700 overflow-hidden">
                                        {/* Header with avatar */}
                                        <div className="p-5 bg-gradient-to-br from-primary-500/10 to-primary-600/5 dark:from-primary-500/20 dark:to-primary-600/10 border-b border-surface-200 dark:border-surface-700">
                                            <div className="flex items-center gap-4">
                                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                                                    {user.name?.charAt(0).toUpperCase()}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <h3 className="text-lg font-bold text-surface-900 dark:text-white truncate">
                                                        {user.name}
                                                    </h3>
                                                    {user.alias && (
                                                        <p className="text-sm text-surface-500 truncate">@{user.alias}</p>
                                                    )}
                                                </div>
                                                {user.is_active && (
                                                    <div className="flex items-center gap-1 px-2 py-1 bg-green-500/10 text-green-600 dark:text-green-400 rounded-full text-xs font-medium">
                                                        <BadgeCheck size={12} />
                                                        Active
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* User Details */}
                                        <div className="p-4 space-y-3">
                                            {/* Email */}
                                            <div className="flex items-center gap-3 p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl">
                                                <div className="p-2 bg-blue-500/10 rounded-lg">
                                                    <Mail size={16} className="text-blue-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs text-surface-500 uppercase tracking-wide font-medium">Email</p>
                                                    <p className="text-sm text-surface-900 dark:text-white truncate">{user.email}</p>
                                                </div>
                                            </div>

                                            {/* Phone */}
                                            <div className="flex items-center gap-3 p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl">
                                                <div className="p-2 bg-green-500/10 rounded-lg">
                                                    <Phone size={16} className="text-green-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs text-surface-500 uppercase tracking-wide font-medium">Phone</p>
                                                    <p className="text-sm text-surface-900 dark:text-white">
                                                        {user.phone || <span className="text-surface-400 italic">Not provided</span>}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Roles */}
                                            <div className="flex items-center gap-3 p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl">
                                                <div className="p-2 bg-purple-500/10 rounded-lg">
                                                    <Shield size={16} className="text-purple-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs text-surface-500 uppercase tracking-wide font-medium">Roles</p>
                                                    <div className="flex flex-wrap gap-1 mt-1">
                                                        {user.roles?.map((role) => (
                                                            <span
                                                                key={role}
                                                                className="px-2 py-0.5 text-xs font-medium bg-primary-500/10 text-primary-600 dark:text-primary-400 rounded-full capitalize"
                                                            >
                                                                {role.replace(/_/g, ' ')}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Organization Hierarchy */}
                                            {(user.team || user.department || user.company || user.business_group) && (
                                                <div className="p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl space-y-2">
                                                    <p className="text-xs text-surface-500 uppercase tracking-wide font-medium mb-2">Organization</p>
                                                    <div className="space-y-1.5">
                                                        {user.business_group && (
                                                            <div className="flex items-center gap-2 text-sm">
                                                                <Building2 size={14} className="text-surface-400 shrink-0" />
                                                                <span className="text-surface-500 shrink-0">Business Group:</span>
                                                                <span className="text-surface-900 dark:text-white font-medium truncate">{user.business_group.name}</span>
                                                            </div>
                                                        )}
                                                        {user.company && (
                                                            <div className="flex items-center gap-2 text-sm">
                                                                <Landmark size={14} className="text-surface-400 shrink-0" />
                                                                <span className="text-surface-500 shrink-0">Company:</span>
                                                                <span className="text-surface-900 dark:text-white font-medium truncate">{user.company.name}</span>
                                                            </div>
                                                        )}
                                                        {user.department && (
                                                            <div className="flex items-center gap-2 text-sm">
                                                                <Building size={14} className="text-surface-400 shrink-0" />
                                                                <span className="text-surface-500 shrink-0">Department:</span>
                                                                <span className="text-surface-900 dark:text-white font-medium truncate">{user.department.name}</span>
                                                            </div>
                                                        )}
                                                        {user.team && (
                                                            <div className="flex items-center gap-2 text-sm">
                                                                <Users size={14} className="text-surface-400 shrink-0" />
                                                                <span className="text-surface-500 shrink-0">Team:</span>
                                                                <span className="text-surface-900 dark:text-white font-medium truncate">{user.team.name}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Last Login */}
                                            <div className="flex items-center gap-3 p-3 bg-surface-50 dark:bg-surface-800/50 rounded-xl">
                                                <div className="p-2 bg-amber-500/10 rounded-lg">
                                                    <Clock size={16} className="text-amber-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-xs text-surface-500 uppercase tracking-wide font-medium">Last Login</p>
                                                    <p className="text-sm text-surface-900 dark:text-white">
                                                        {formatLastLogin(user.last_login)}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Footer with Sign Out */}
                                        <div className="p-4 border-t border-surface-200 dark:border-surface-700">
                                            <button
                                                onClick={() => {
                                                    setShowUserCard(false);
                                                    logout();
                                                }}
                                                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-primary-600 dark:text-primary-400 hover:bg-primary-500/10 rounded-xl transition-colors"
                                            >
                                                <LogOut size={18} />
                                                Sign out
                                            </button>
                                        </div>
                                    </div>
                                </div>,
                                document.body
                            )}

                            {/* Logout Button - Mobile */}
                            <button
                                onClick={logout}
                                className="md:hidden flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-surface-500 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-surface-100 dark:hover:bg-surface-800 rounded-xl transition-colors"
                                title="Sign out"
                            >
                                <LogOut size={18} />
                            </button>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
