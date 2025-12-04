import React, { useState } from 'react';
import { Calendar, X } from 'lucide-react';

const DateRangeModal = ({ isOpen, onClose, onApply }) => {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    if (!isOpen) return null;

    const handleQuickSelect = (type) => {
        const today = new Date();
        let start, end;

        switch (type) {
            case 'today':
                start = end = formatDate(today);
                break;
            case 'yesterday':
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                start = end = formatDate(yesterday);
                break;
            case 'last_7_days':
                const last7 = new Date(today);
                last7.setDate(last7.getDate() - 6);
                start = formatDate(last7);
                end = formatDate(today);
                break;
            case 'last_30_days':
                const last30 = new Date(today);
                last30.setDate(last30.getDate() - 29);
                start = formatDate(last30);
                end = formatDate(today);
                break;
            case 'this_month':
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                start = formatDate(firstDay);
                end = formatDate(today);
                break;
            case 'last_month':
                const lastMonthEnd = new Date(today.getFullYear(), today.getMonth(), 0);
                const lastMonthStart = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                start = formatDate(lastMonthStart);
                end = formatDate(lastMonthEnd);
                break;
            default:
                return;
        }

        setStartDate(start);
        setEndDate(end);
    };

    const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const handleApply = () => {
        if (startDate && endDate) {
            onApply({ startDate, endDate });
            onClose();
        } else {
            alert('Please select both start and end dates');
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="glass-panel w-full max-w-2xl mx-4 p-6 relative animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <Calendar className="text-neon-blue" size={24} />
                        <h2 className="text-2xl font-bold text-white">Select Date Range</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Subtitle */}
                <p className="text-gray-400 mb-6">Filter trips by date range (optional)</p>

                {/* Date Inputs */}
                <div className="space-y-4 mb-6">
                    {/* Start Date */}
                    <div className="bg-dark-card border border-dark-border rounded-lg p-4 flex items-center gap-3 hover:border-neon-blue/50 transition-colors">
                        <Calendar className="text-neon-blue" size={20} />
                        <div className="flex-1">
                            <label className="text-gray-400 text-sm block mb-1">Start Date</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="bg-transparent text-white text-lg w-full outline-none"
                                placeholder="Not selected"
                            />
                        </div>
                    </div>

                    {/* End Date */}
                    <div className="bg-dark-card border border-dark-border rounded-lg p-4 flex items-center gap-3 hover:border-neon-blue/50 transition-colors">
                        <Calendar className="text-neon-blue" size={20} />
                        <div className="flex-1">
                            <label className="text-gray-400 text-sm block mb-1">End Date</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                className="bg-transparent text-white text-lg w-full outline-none"
                                placeholder="Not selected"
                            />
                        </div>
                    </div>
                </div>

                {/* Quick Select */}
                <div className="mb-6">
                    <h3 className="text-gray-400 text-sm mb-3">Quick Select</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <button
                            onClick={() => handleQuickSelect('today')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            Today
                        </button>
                        <button
                            onClick={() => handleQuickSelect('yesterday')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            Yesterday
                        </button>
                        <button
                            onClick={() => handleQuickSelect('last_7_days')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            Last 7 Days
                        </button>
                        <button
                            onClick={() => handleQuickSelect('last_30_days')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            Last 30 Days
                        </button>
                        <button
                            onClick={() => handleQuickSelect('this_month')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            This Month
                        </button>
                        <button
                            onClick={() => handleQuickSelect('last_month')}
                            className="bg-dark-card border border-dark-border hover:border-neon-blue/50 hover:bg-neon-blue/10 text-white px-4 py-3 rounded-lg transition-all"
                        >
                            Last Month
                        </button>
                    </div>
                </div>

                {/* Apply Button */}
                <button
                    onClick={handleApply}
                    className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Apply Filter
                </button>
            </div>
        </div>
    );
};

export default DateRangeModal;
