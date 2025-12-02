import React, { useState, useEffect } from 'react';
import { Users, UserCheck, Clock, AlertCircle } from 'lucide-react';
import axios from 'axios';

const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="glass-panel p-6 flex items-center gap-4 hover:bg-white/5 transition-colors group">
        <div className={`p-3 rounded-lg bg-${color}-500/10 text-${color}-400 group-hover:text-${color}-300 group-hover:shadow-[0_0_15px_rgba(var(--color-${color}),0.3)] transition-all`}>
            <Icon size={24} />
        </div>
        <div>
            <p className="text-gray-400 text-sm font-medium">{label}</p>
            <h3 className="text-2xl font-bold text-white">{value}</h3>
        </div>
    </div>
);

const Dashboard = () => {
    const [stats, setStats] = useState({
        total_employees: 0,
        present_today: 0,
        absent: 0,
        recent_activity: []
    });

    useEffect(() => {
        fetchStats();
        const interval = setInterval(fetchStats, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchStats = async () => {
        try {
            const res = await axios.get('http://localhost:5001/api/stats');
            setStats(res.data);
        } catch (err) {
            console.error("Error fetching stats:", err);
        }
    };

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">System Overview</h1>
                <p className="text-gray-400">Welcome back, Admin. Here's today's attendance summary.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard icon={Users} label="Total Employees" value={stats.total_employees} color="blue" />
                <StatCard icon={UserCheck} label="Present Today" value={stats.present_today} color="green" />
                <StatCard icon={Clock} label="Late Arrivals" value="0" color="yellow" />
                <StatCard icon={AlertCircle} label="Absent" value={stats.absent} color="red" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-panel p-6">
                    <h3 className="text-xl font-semibold mb-4">Recent Activity</h3>
                    <div className="space-y-4">
                        {stats.recent_activity.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No activity yet today.</p>
                        ) : (
                            stats.recent_activity.map((activity, i) => (
                                <div key={i} className="flex items-center justify-between py-3 border-b border-dark-border last:border-0">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-white">
                                            {activity.name.substring(0, 2).toUpperCase()}
                                        </div>
                                        <div>
                                            <p className="font-medium text-white">{activity.name}</p>
                                            <p className="text-xs text-gray-500">ID: {activity.employee_id}</p>
                                        </div>
                                    </div>
                                    <span className="text-sm text-neon-green">Checked In {activity.check_in_time}</span>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div className="glass-panel p-6">
                    <h3 className="text-xl font-semibold mb-4">System Status</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Camera Feed</span>
                            <span className="text-neon-green flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" /> Active</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Database Connection</span>
                            <span className="text-neon-green flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-neon-green" /> Connected</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400">Last Backup</span>
                            <span className="text-white">Today, 04:00 AM</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
