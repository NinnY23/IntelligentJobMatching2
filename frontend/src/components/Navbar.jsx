import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Navbar.css';

export default function Navbar({ user, onLogout, unreadMessages = 0 }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const isActive = (path) => location.pathname === path;

  const employeeLinks = [
    { path: '/jobs', label: 'Find Jobs' },
    { path: '/applications', label: 'My Applications' },
    { path: '/messages', label: 'Messages', badge: unreadMessages },
    { path: '/profile', label: 'Profile' },
  ];

  const employerLinks = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/my-jobs', label: 'My Jobs' },
    { path: '/create-job', label: 'Post a Job' },
    { path: '/messages', label: 'Messages', badge: unreadMessages },
    { path: '/profile', label: 'Profile' },
  ];

  const links = user?.role === 'employer' ? employerLinks : employeeLinks;
  const initials = user?.name
    ? user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  return (
    <nav className="navbar" aria-label="Main navigation">
      <div
        className="navbar-brand"
        onClick={() => navigate(user?.role === 'employer' ? '/dashboard' : '/jobs')}
        role="link"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && navigate(user?.role === 'employer' ? '/dashboard' : '/jobs')}
      >
        JobMatch<span>AI</span>
      </div>
      <button className="nav-hamburger" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
        {menuOpen ? '✕' : '☰'}
      </button>
      <div className={`navbar-links${menuOpen ? ' nav-links-open' : ''}`}>
        {links.map(link => (
          <button
            key={link.path}
            className={`nav-link${isActive(link.path) ? ' active' : ''}`}
            onClick={() => navigate(link.path)}
            aria-current={isActive(link.path) ? 'page' : undefined}
          >
            {link.label}
            {link.badge > 0 && (
              <span className="nav-badge" aria-label={`${link.badge} unread`}>
                {link.badge}
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="navbar-user">
        <div className="avatar" aria-hidden="true">{initials}</div>
        <span className="navbar-name">{user?.name}</span>
        <button className="btn-logout" onClick={onLogout} aria-label="Log out">
          Logout
        </button>
      </div>
    </nav>
  );
}
