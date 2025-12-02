import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Employees from './pages/Employees';
import Attendance from './pages/Attendance';
import LiveFeed from './pages/LiveFeed';

const AppContent = () => {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <div className="flex h-screen bg-dark-bg text-white overflow-hidden">
      {!isLoginPage && <Sidebar />}
      <main className="flex-1 overflow-y-auto p-8 relative">
        {/* Background Glow Effects */}
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
          <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-neon-blue/5 rounded-full blur-[100px]" />
          <div className="absolute bottom-[-10%] left-[10%] w-[500px] h-[500px] bg-neon-purple/5 rounded-full blur-[100px]" />
        </div>

        <div className="relative z-10">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/live" element={<LiveFeed />} />
          </Routes>
        </div>
      </main>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
