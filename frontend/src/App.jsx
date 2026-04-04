// src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import CreateJobPost from './CreateJobPost';
import Profile from './Profile';
import Login from './Login';
import SignUp from './SignUp';
import ForgotPassword from './ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Jobs from './pages/Jobs';
import Applications from './pages/Applications';
import MyJobs from './pages/MyJobs';
import Applicants from './pages/Applicants';
import Dashboard from './pages/Dashboard';
import Messages from './pages/Messages';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import { fetchUnreadCount, logoutUser } from './api';

function DashboardWrapper({ user }) {
  const navigate = useNavigate();
  return <Dashboard navigate={navigate} user={user} />;
}

function MyJobsWrapper({ user }) {
  const navigate = useNavigate();
  return <MyJobs user={user} navigate={navigate} />;
}

function ApplicantsWrapper() {
  const { jobId } = useParams();
  return <Applicants jobId={jobId} />;
}

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadMessages, setUnreadMessages] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (err) {
        console.error('Error parsing saved user:', err);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!user) return;
    async function checkUnread() {
      try {
        const count = await fetchUnreadCount();
        setUnreadMessages(count);
      } catch {}
    }
    checkUnread();
    const interval = setInterval(checkUnread, 30000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    if (userData.role === 'employer') {
      navigate('/dashboard');
    } else {
      navigate('/jobs');
    }
  };

  const handleSignUpSuccess = (userData) => {
    setUser(userData);
    if (userData.role === 'employer') {
      navigate('/dashboard');
    } else {
      navigate('/jobs');
    }
  };

  const handleUpdateProfile = (updatedUser) => {
    setUser(updatedUser);
  };

  const handleLogout = async () => {
    await logoutUser();
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  // If not logged in, show auth routes
  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} onSwitchToSignUp={() => navigate('/signup')} onSwitchToForgotPassword={() => navigate('/forgot-password')} />} />
        <Route path="/signup" element={<SignUp onSignUpSuccess={handleSignUpSuccess} onSwitchToLogin={() => navigate('/login')} />} />
        <Route path="/forgot-password" element={<ForgotPassword onSwitchToLogin={() => navigate('/login')} />} />
        <Route path="/reset-password" element={<ResetPassword onSwitchToLogin={() => navigate('/login')} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // If logged in, show app routes
  return (
    <>
      <Navbar user={user} onLogout={handleLogout} unreadMessages={unreadMessages} />
      <Routes>
        <Route path="/create-job" element={
          <CreateJobPost onPostCreated={() => navigate('/jobs')} onBack={() => navigate('/jobs')} />
        } />
        <Route path="/jobs" element={<Jobs user={user} />} />
        <Route path="/applications" element={<Applications user={user} />} />
        <Route path="/messages" element={<Messages user={user} />} />
        <Route path="/profile" element={
          <Profile user={user} onUpdateProfile={handleUpdateProfile} onBack={() => navigate('/jobs')} />
        } />
        <Route path="/dashboard" element={<DashboardWrapper user={user} />} />
        <Route path="/my-jobs" element={<MyJobsWrapper user={user} />} />
        <Route path="/jobs/:jobId/applicants" element={<ApplicantsWrapper />} />
        <Route path="*" element={<Navigate to={user.role === 'employer' ? '/dashboard' : '/jobs'} replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AppContent />
      </Router>
    </ErrorBoundary>
  );
}