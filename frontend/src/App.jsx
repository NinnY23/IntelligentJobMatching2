// src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import CreateJobPost from './CreateJobPost';
import Profile from './Profile';
import Login from './Login';
import SignUp from './SignUp';
import ForgotPassword from './ForgotPassword';
import Jobs from './pages/Jobs';
import Applications from './pages/Applications';
import MyJobs from './pages/MyJobs';
import Applicants from './pages/Applicants';
import Dashboard from './pages/Dashboard';

function Header({ user, currentPage, onLogout, navigate }) {
  return (
    <header>
      <h1>Intelligent Job Matching</h1>
      <div className="nav-links">
        {/* Employee navigation */}
        {user && user.role === 'employee' && (
          <>
            <button
              className={`nav-link ${currentPage === 'jobs' ? 'active' : ''}`}
              onClick={() => navigate('/jobs')}
            >
              Find Jobs
            </button>
            <button
              className={`nav-link ${currentPage === 'applications' ? 'active' : ''}`}
              onClick={() => navigate('/applications')}
            >
              My Applications
            </button>
            <button
              className={`nav-link ${currentPage === 'profile' ? 'active' : ''}`}
              onClick={() => navigate('/profile')}
            >
              Profile
            </button>
          </>
        )}

        {/* Employer navigation */}
        {user && user.role === 'employer' && (
          <>
            <button
              className={`nav-link ${currentPage === 'dashboard' ? 'active' : ''}`}
              onClick={() => navigate('/dashboard')}
            >
              Dashboard
            </button>
            <button
              className={`nav-link ${currentPage === 'my-jobs' ? 'active' : ''}`}
              onClick={() => navigate('/my-jobs')}
            >
              My Jobs
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
          </>
        )}
      </div>
      <div className="user-info">
        <span>Welcome, {user.name || user.email}</span>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>
    </header>
  );
}

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
            <Jobs user={user} />
          </>
        } />
        <Route path="/applications" element={
          <>
            <Header user={user} currentPage="applications" onLogout={handleLogout} navigate={navigate} />
            <Applications user={user} />
          </>
        } />
        <Route path="/profile" element={
          <>
            <Header user={user} currentPage="profile" onLogout={handleLogout} navigate={navigate} />
            <Profile user={user} onUpdateProfile={handleUpdateProfile} onBack={() => navigate('/jobs')} />
          </>
        } />
        <Route path="/dashboard" element={
          <>
            <Header user={user} currentPage="dashboard" onLogout={handleLogout} navigate={navigate} />
            <DashboardWrapper user={user} />
          </>
        } />
        <Route path="/my-jobs" element={
          <>
            <Header user={user} currentPage="my-jobs" onLogout={handleLogout} navigate={navigate} />
            <MyJobsWrapper user={user} />
          </>
        } />
        <Route path="/jobs/:jobId/applicants" element={
          <>
            <Header user={user} currentPage="applicants" onLogout={handleLogout} navigate={navigate} />
            <ApplicantsWrapper />
          </>
        } />
        <Route path="*" element={<Navigate to={user.role === 'employer' ? '/dashboard' : '/jobs'} replace />} />
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