// src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import JobMatch from './JobMatch';
import CreateJobPost from './CreateJobPost';
import Profile from './Profile';
import Login from './Login';
import SignUp from './SignUp';
import ForgotPassword from './ForgotPassword';
import './App.css';

function Header({ user, currentPage, onLogout, navigate }) {
  return (
    <header>
      <h1>Intelligent Job Matching</h1>
      <div className="nav-links">
        <button 
          className={`nav-link ${currentPage === 'jobs' ? 'active' : ''}`}
          onClick={() => navigate('/jobs')}
        >
          Browse Jobs
        </button>
        <button 
          className={`nav-link ${currentPage === 'create-job' ? 'active' : ''}`}
          onClick={() => navigate('/create-job')}
        >
          Post a Job
        </button>
        <button 
          className={`nav-link ${currentPage === 'profile' ? 'active' : ''}`}
          onClick={() => navigate('/profile')}
        >
          Profile
        </button>
      </div>
      <div className="user-info">
        <span>Welcome, {user.name || user.email}</span>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>
    </header>
  );
}

function AppContent() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
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

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    navigate('/jobs');
  };

  const handleSignUpSuccess = (userData) => {
    setUser(userData);
    navigate('/jobs');
  };

  const handleUpdateProfile = (updatedUser) => {
    setUser(updatedUser);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
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
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  // If logged in, show app routes
  return (
    <>
      <Routes>
        <Route path="/create-job" element={
          <>
            <Header user={user} currentPage="create-job" onLogout={handleLogout} navigate={navigate} />
            <CreateJobPost onPostCreated={() => navigate('/jobs')} onBack={() => navigate('/jobs')} />
          </>
        } />
        <Route path="/jobs" element={
          <>
            <Header user={user} currentPage="jobs" onLogout={handleLogout} navigate={navigate} />
            <JobMatch />
          </>
        } />
        <Route path="/profile" element={
          <>
            <Header user={user} currentPage="profile" onLogout={handleLogout} navigate={navigate} />
            <Profile user={user} onUpdateProfile={handleUpdateProfile} onBack={() => navigate('/jobs')} />
          </>
        } />
        <Route path="*" element={<Navigate to="/jobs" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}