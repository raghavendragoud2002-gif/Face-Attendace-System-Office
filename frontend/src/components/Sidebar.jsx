import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Calendar, Video, LogOut } from 'lucide-react';
import logo from '../assets/logo.png';

const Sidebar = () => {
    const navItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        { icon: Users, label: 'Employees', path: '/employees' },
        { icon: Calendar, label: 'Attendance', path: '/attendance' },
        { icon: Video, label: 'Live Feed', path: '/live' },
    ];

    return (
        <div className="h-screen w-64 bg-dark-card border-r border-dark-border flex flex-col p-4">
            <div className="mb-8 flex items-center gap-3 px-2">
                <img src={logo} alt="Logo" className="w-8 h-8 rounded-full shadow-[0_0_15px_#00f3ff]" />
                <h1 className="text-xl font-bold tracking-wider text-white">Cloud Harbor <span className="text-neon-blue">Technologies</span></h1>
            </div>

            <nav className="flex-1 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-300 ${isActive
                                ? 'bg-neon-blue/10 text-neon-blue border border-neon-blue/30 shadow-[0_0_10px_rgba(0,243,255,0.1)]'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                            }`
                        }
                    >
                        <item.icon size={20} />
                        <span className="font-medium">{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="mt-auto pt-4 border-t border-dark-border">
                <div className="flex items-center gap-3 px-4 py-3 mb-4 bg-dark-bg rounded-lg border border-dark-border">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500" />
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">Admin User</p>
                        <p className="text-xs text-gray-500 truncate">System Admin</p>
                    </div>
                </div>
                <button
                    onClick={() => window.location.href = '/login'}
                    className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-lg transition-colors"
                >
                    <LogOut size={20} />
                    <span className="font-medium">Logout</span>
                </button>

            </div>
        </div>
    );
};

export default Sidebar;
