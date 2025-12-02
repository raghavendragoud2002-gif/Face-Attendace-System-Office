import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User } from 'lucide-react';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleLogin = (e) => {
        e.preventDefault();
        // TODO: Implement actual API login
        if (username === 'admin' && password === 'admin123') {
            navigate('/');
        } else {
            alert('Invalid credentials');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-dark-bg relative overflow-hidden">
            {/* Background Effects */}
            <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] bg-neon-blue/10 rounded-full blur-[120px]" />
            <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-neon-purple/10 rounded-full blur-[120px]" />

            <div className="glass-panel p-8 w-full max-w-md relative z-10 border-neon-blue/30 shadow-[0_0_30px_rgba(0,243,255,0.1)]">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold tracking-widest text-white mb-2">Cloud Harbor <span className="text-neon-blue">Technologies</span></h1>
                    <p className="text-gray-400 text-sm">SECURE ACCESS TERMINAL</p>
                </div>

                <form onSubmit={handleLogin} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Username</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 text-neon-blue" size={18} />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-dark-bg/50 border border-dark-border rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:border-neon-blue focus:shadow-[0_0_10px_rgba(0,243,255,0.2)] transition-all"
                                placeholder="Enter ID"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs uppercase tracking-wider text-gray-500 font-semibold">Password</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-neon-blue" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-dark-bg/50 border border-dark-border rounded-lg py-3 pl-10 pr-4 text-white focus:outline-none focus:border-neon-blue focus:shadow-[0_0_10px_rgba(0,243,255,0.2)] transition-all"
                                placeholder="Enter Password"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="w-full bg-neon-blue/10 text-neon-blue border border-neon-blue/50 py-3 rounded-lg font-semibold tracking-wide hover:bg-neon-blue hover:text-black transition-all duration-300 shadow-[0_0_15px_rgba(0,243,255,0.2)]"
                    >
                        AUTHENTICATE
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
