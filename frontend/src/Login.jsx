import React, { useState } from 'react';
import './components/AuthCard.css';
import { loginUser } from './api';

export default function Login({ onLoginSuccess, onSwitchToSignUp, onSwitchToForgotPassword }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await loginUser(email, password);
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">JobMatch<span>AI</span></div>
        <h2 className="auth-title">Welcome back</h2>
        <p className="auth-subtitle">Sign in to your account</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button type="submit" className="btn-primary auth-submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
        <div className="auth-footer">
          <button onClick={onSwitchToForgotPassword}>Forgot password?</button>
          &nbsp;·&nbsp;
          <button onClick={onSwitchToSignUp}>Create account</button>
        </div>
      </div>
    </div>
  );
}
