import React, { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Download, Filter, RefreshCw } from 'lucide-react';
import axios from 'axios';
import DateRangeModal from '../components/DateRangeModal';

const Attendance = () => {
    const [records, setRecords] = useState([]);
    const [dateFilter, setDateFilter] = useState('today'); // today, month, yesterday, last_7_days, last_30_days, this_month, last_month, custom
    const [statusFilter, setStatusFilter] = useState('All'); // All, Present, Late, Absent
    const [loading, setLoading] = useState(false);
    const [showDateModal, setShowDateModal] = useState(false);
    const [customDateRange, setCustomDateRange] = useState({ startDate: '', endDate: '' });
    const [filterLabel, setFilterLabel] = useState('Today');

    useEffect(() => {
        fetchAttendance();
    }, [dateFilter, statusFilter, customDateRange]);

    const fetchAttendance = async () => {
        setLoading(true);
        try {
            const params = {
                filter: dateFilter,
                status: statusFilter
            };

            // Add custom date range if applicable
            if (dateFilter === 'custom' && customDateRange.startDate && customDateRange.endDate) {
                params.start_date = customDateRange.startDate;
                params.end_date = customDateRange.endDate;
            }

            const res = await axios.get('http://localhost:5001/api/attendance/daily', { params });
            setRecords(res.data);
        } catch (err) {
            console.error("Error fetching attendance:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDateRangeApply = ({ startDate, endDate }) => {
        setCustomDateRange({ startDate, endDate });
        setDateFilter('custom');
        setFilterLabel(`${startDate} to ${endDate}`);
    };

    const handleQuickFilter = (filter, label) => {
        setDateFilter(filter);
        setFilterLabel(label);
        setCustomDateRange({ startDate: '', endDate: '' });
    };

    const exportCSV = () => {
        // Simple CSV export
        const headers = ['Date', 'Employee', 'Entry Time', 'Work Time', 'Break Time', 'Status'];
        const rows = records.map(r => [
            r.date,
            r.name,
            r.first_in || '-',
            r.work_hours || '0h 0m',
            r.break_hours || '0h 0m',
            r.status
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attendance_${dateFilter}_${statusFilter}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Attendance Reports</h1>
                    <p className="text-gray-400">View and export attendance records.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchAttendance}
                        className="bg-dark-card border border-dark-border hover:bg-white/5 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw size={18} /> Refresh
                    </button>
                    <button
                        onClick={exportCSV}
                        className="bg-neon-blue/10 text-neon-blue border border-neon-blue/50 hover:bg-neon-blue hover:text-black px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                    >
                        <Download size={18} /> Export CSV
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="glass-panel p-4 flex gap-4 items-center flex-wrap">
                <Filter size={18} className="text-neon-blue" />
                <div className="flex gap-4 flex-1 flex-wrap">
                    {/* Date Filter Button */}
                    <div className="flex items-center gap-2">
                        <label className="text-gray-400 text-sm">Date:</label>
                        <button
                            onClick={() => setShowDateModal(true)}
                            className="bg-dark-card border border-dark-border text-white px-4 py-2 rounded-lg hover:border-neon-blue focus:outline-none focus:border-neon-blue transition-colors flex items-center gap-2"
                        >
                            <CalendarIcon size={16} />
                            <span>{filterLabel}</span>
                        </button>
                    </div>

                    {/* Quick Filters */}
                    <div className="flex gap-2">
                        <button
                            onClick={() => handleQuickFilter('today', 'Today')}
                            className={`px-3 py-2 rounded-lg text-sm transition-colors ${dateFilter === 'today'
                                    ? 'bg-neon-blue text-black font-medium'
                                    : 'bg-dark-card border border-dark-border text-gray-300 hover:border-neon-blue/50'
                                }`}
                        >
                            Today
                        </button>
                        <button
                            onClick={() => handleQuickFilter('this_month', 'This Month')}
                            className={`px-3 py-2 rounded-lg text-sm transition-colors ${dateFilter === 'this_month'
                                    ? 'bg-neon-blue text-black font-medium'
                                    : 'bg-dark-card border border-dark-border text-gray-300 hover:border-neon-blue/50'
                                }`}
                        >
                            This Month
                        </button>
                    </div>

                    {/* Status Filter */}
                    <div className="flex items-center gap-2">
                        <label className="text-gray-400 text-sm">Status:</label>
                        <select
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            className="bg-dark-card border border-dark-border text-white px-3 py-2 rounded-lg focus:outline-none focus:border-neon-blue transition-colors"
                        >
                            <option value="All">All</option>
                            <option value="Present">Present</option>
                            <option value="Late">Late</option>
                            <option value="Absent">Absent</option>
                        </select>
                    </div>
                </div>
                <div className="text-sm text-gray-400">
                    {records.length} record{records.length !== 1 ? 's' : ''}
                </div>
            </div>

            {/* Date Range Modal */}
            <DateRangeModal
                isOpen={showDateModal}
                onClose={() => setShowDateModal(false)}
                onApply={handleDateRangeApply}
            />

            {/* Content */}
            <div className="glass-panel overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center text-gray-400">Loading...</div>
                ) : (
                    <table className="w-full text-left">
                        <thead className="bg-white/5 text-gray-400 text-sm uppercase tracking-wider">
                            <tr>
                                <th className="p-4">Date</th>
                                <th className="p-4">Employee</th>
                                <th className="p-4">Entry Time</th>
                                <th className="p-4">Work Time</th>
                                <th className="p-4">Break Time</th>
                                <th className="p-4">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-dark-border text-gray-300">
                            {records.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="p-8 text-center text-gray-500">
                                        No attendance records found for the selected filters.
                                    </td>
                                </tr>
                            ) : (
                                records.map((r, i) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="p-4 text-gray-400">{r.date}</td>
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs font-bold text-white overflow-hidden">
                                                    {r.image_path ? (
                                                        <img src={`http://localhost:5001/images/${r.image_path.split('/').pop()}`} alt={r.name} className="w-full h-full object-cover" />
                                                    ) : (
                                                        r.name.substring(0, 2).toUpperCase()
                                                    )}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">{r.name}</div>
                                                    <div className="text-xs text-gray-500">{r.department}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4 text-neon-blue font-mono">{r.first_in || '-'}</td>
                                        <td className="p-4 text-gray-300 font-mono">{r.work_hours || '0h 0m'}</td>
                                        <td className="p-4 text-gray-400 font-mono">{r.break_hours || '0h 0m'}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${r.status === 'Present' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                                r.status === 'Late' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                                    'bg-red-500/10 text-red-400 border-red-500/20'
                                                }`}>
                                                {r.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default Attendance;
