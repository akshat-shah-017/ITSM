// Pages - Login
// Premium enterprise login page with global network visualization - Light Mode

import { useState } from 'react';
import { useAuth } from '../auth';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import Logo from '../assets/logo.svg';

export function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard', { replace: true });
        } catch (err) {
            console.error('Login failed:', err);
            setError('Invalid credentials. Please check your email and password.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex bg-white relative overflow-hidden">

            {/* Left Side - Login Form */}
            <div className="w-full lg:w-[45%] xl:w-[40%] flex flex-col justify-center p-8 lg:p-16 relative z-10 bg-white">

                <div className="relative z-10 w-full max-w-md mx-auto">

                    {/* Logo */}
                    <div className="mb-12">
                        <img src={Logo} alt="Blackbox" className="w-44 h-auto" />
                    </div>

                    {/* Welcome Text */}
                    <div className="mb-10">
                        <h1 className="text-4xl font-bold text-surface-900 mb-3">
                            Sign In
                        </h1>
                        <p className="text-surface-500 text-lg">
                            Access your IT service management portal
                        </p>
                    </div>

                    {/* Login Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">

                        {/* Error Alert */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3 text-red-600 text-sm animate-fade-in">
                                <AlertCircle size={20} className="shrink-0 mt-0.5" />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Email Field */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-surface-700">
                                Email Address
                            </label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400 group-focus-within:text-primary-500 transition-colors" size={20} />
                                <input
                                    type="email"
                                    required
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full h-14 pl-12 pr-4 bg-surface-50 border border-surface-200 rounded-xl text-surface-900 placeholder-surface-400 
                                               focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500
                                               transition-all duration-200"
                                    placeholder="name@company.com"
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-surface-700">
                                Password
                            </label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-surface-400 group-focus-within:text-primary-500 transition-colors" size={20} />
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full h-14 pl-12 pr-4 bg-surface-50 border border-surface-200 rounded-xl text-surface-900 placeholder-surface-400 
                                               focus:outline-none focus:ring-2 focus:ring-primary-500/30 focus:border-primary-500
                                               transition-all duration-200"
                                    placeholder="Enter your password"
                                />
                            </div>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full h-14 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 
                                       text-white font-semibold rounded-xl shadow-lg shadow-primary-500/25
                                       transition-all duration-300 ease-out
                                       disabled:opacity-60 disabled:cursor-not-allowed
                                       group relative overflow-hidden"
                        >
                            <span className="relative z-10 flex items-center justify-center gap-2">
                                {isLoading ? (
                                    <>
                                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Signing in...
                                    </>
                                ) : (
                                    <>
                                        Sign In
                                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </span>

                            {/* Shine effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent 
                                            translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                        </button>
                    </form>

                    {/* Footer */}
                    <div className="mt-16 pt-8 border-t border-surface-200">
                        <p className="text-surface-400 text-xs text-center">
                            © {new Date().getFullYear()} Blackbox Technologies Private Limited
                        </p>
                    </div>
                </div>
            </div>

            {/* Right Side - Hero Visual */}
            <div className="hidden lg:flex lg:w-[55%] xl:w-[60%] relative items-center justify-center overflow-hidden">

                {/* Dynamic Background - Light theme with blue tones */}
                <div className="absolute inset-0">
                    {/* Gradient background */}
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-cyan-50 to-indigo-100" />

                    {/* Subtle grid */}
                    <div className="absolute inset-0 opacity-30"
                        style={{
                            backgroundImage: `
                                 linear-gradient(rgba(0,100,180,0.08) 1px, transparent 1px),
                                 linear-gradient(90deg, rgba(0,100,180,0.08) 1px, transparent 1px)
                             `,
                            backgroundSize: '50px 50px',
                        }}
                    />
                </div>

                {/* Globe Visualization */}
                <div className="relative z-10 w-full h-full flex items-center justify-center">

                    {/* Outer glow rings */}
                    <div className="absolute w-[550px] h-[550px] rounded-full border-2 border-cyan-300/40 animate-pulse" />
                    <div className="absolute w-[480px] h-[480px] rounded-full border border-cyan-400/20" />

                    {/* Globe container */}
                    <div className="relative w-[400px] h-[400px]">

                        {/* Globe glow */}
                        <div className="absolute inset-[-40px] bg-gradient-to-b from-cyan-400/20 via-blue-400/15 to-transparent rounded-full blur-[60px]" />

                        {/* Globe sphere */}
                        <div className="absolute inset-0 rounded-full bg-gradient-to-b from-cyan-200/60 via-blue-300/50 to-blue-500/40 
                                        shadow-[inset_0_0_80px_rgba(0,150,220,0.3),_0_0_60px_rgba(0,180,255,0.2)]
                                        border border-cyan-300/50">

                            {/* Latitude lines */}
                            <div className="absolute inset-4 rounded-full border border-cyan-400/30" />
                            <div className="absolute inset-14 rounded-full border border-cyan-500/25" />
                            <div className="absolute inset-24 rounded-full border border-cyan-400/20" />

                            {/* Network nodes */}
                            <div className="absolute top-[20%] left-[30%] w-3 h-3 bg-cyan-500 rounded-full animate-pulse shadow-[0_0_15px_rgba(0,180,220,0.7)]" />
                            <div className="absolute top-[35%] left-[60%] w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(0,100,255,0.6)]" style={{ animationDelay: '0.5s' }} />
                            <div className="absolute top-[50%] left-[25%] w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(0,200,255,0.5)]" style={{ animationDelay: '1s' }} />
                            <div className="absolute top-[65%] left-[55%] w-2.5 h-2.5 bg-blue-400 rounded-full animate-pulse shadow-[0_0_12px_rgba(0,150,255,0.5)]" style={{ animationDelay: '1.5s' }} />
                            <div className="absolute top-[40%] left-[42%] w-3.5 h-3.5 bg-orange-500 rounded-full animate-pulse shadow-[0_0_18px_rgba(255,150,0,0.7)]" style={{ animationDelay: '0.3s' }} />
                            <div className="absolute top-[55%] left-[68%] w-2 h-2 bg-orange-400 rounded-full animate-pulse shadow-[0_0_10px_rgba(255,150,0,0.5)]" style={{ animationDelay: '0.8s' }} />
                            <div className="absolute top-[28%] left-[48%] w-2 h-2 bg-indigo-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(100,100,255,0.6)]" style={{ animationDelay: '0.2s' }} />
                            <div className="absolute top-[72%] left-[35%] w-2 h-2 bg-cyan-300 rounded-full animate-pulse shadow-[0_0_10px_rgba(0,200,255,0.6)]" style={{ animationDelay: '1.2s' }} />
                        </div>

                        {/* Red diamond logo overlay */}
                        <div className="absolute -right-12 top-1/2 -translate-y-1/2">
                            <div className="relative">
                                {/* Outer diamond */}
                                <div className="w-28 h-28 border-4 border-primary-500 rotate-45 transform 
                                                shadow-[0_0_30px_rgba(200,30,30,0.3)]" />
                                {/* Inner diamond */}
                                <div className="absolute inset-2.5 border-4 border-primary-400 rotate-0" />
                            </div>
                        </div>
                    </div>

                    {/* Decorative connection lines */}
                    <svg className="absolute inset-0 w-full h-full opacity-40" viewBox="0 0 800 800" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M200 300 Q 400 200 500 400" stroke="url(#gradientLight1)" strokeWidth="2" />
                        <path d="M300 500 Q 450 350 600 450" stroke="url(#gradientLight1)" strokeWidth="1.5" />
                        <path d="M350 250 Q 500 400 550 300" stroke="url(#gradientLight1)" strokeWidth="1.5" />
                        <defs>
                            <linearGradient id="gradientLight1" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0" />
                                <stop offset="50%" stopColor="#06b6d4" stopOpacity="0.8" />
                                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                            </linearGradient>
                        </defs>
                    </svg>
                </div>

                {/* Tagline overlay */}
                <div className="absolute bottom-16 left-16 right-16 z-20">
                    <h2 className="text-4xl xl:text-5xl font-bold text-surface-800 leading-tight mb-4">
                        Connecting
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-600 to-blue-600"> Global </span>
                        IT Operations
                    </h2>
                    <p className="text-surface-500 text-lg max-w-md">
                        Enterprise-grade service management trusted by organizations across 40+ countries
                    </p>
                </div>
            </div>
        </div>
    );
}
