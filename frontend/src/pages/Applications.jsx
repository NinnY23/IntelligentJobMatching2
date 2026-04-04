// src/pages/Applications.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { fetchMyApplications, withdrawApplication } from '../api';
import './Applications.css';

const STATUS_TABS = ['All', 'Pending', 'Shortlisted', 'Withdrawn'];

const STATUS_MAP = {
  pending: { label: 'Pending', className: 'apps-chip apps-chip--pending' },
  shortlisted: { label: 'Shortlisted', className: 'apps-chip apps-chip--shortlisted' },
  withdrawn: { label: 'Withdrawn', className: 'apps-chip apps-chip--withdrawn' },
};

function formatDate(isoString) {
  if (!isoString) return '—';
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return isoString;
  }
}

function StatusChip({ status }) {
  const cfg = STATUS_MAP[status] || { label: status, className: 'apps-chip apps-chip--withdrawn' };
  return <span className={cfg.className}>{cfg.label}</span>;
}

function JobTypeChip({ type }) {
  if (!type) return null;
  const colorMap = {
    'Full-time': { bg: '#EEF2FF', color: '#4F46E5' },
    'Part-time': { bg: '#FFF7ED', color: '#C2410C' },
    'Contract': { bg: '#F0FDF4', color: '#15803D' },
    'Remote': { bg: '#F0F9FF', color: '#0369A1' },
  };
  const style = colorMap[type] || { bg: '#F3F4F6', color: '#374151' };
  return (
    <span className="apps-type-chip" style={{ background: style.bg, color: style.color }}>
      {type}
    </span>
  );
}

function ConfirmDialog({ message, onConfirm, onCancel, loading }) {
  return (
    <div className="apps-dialog-backdrop" role="dialog" aria-modal="true" aria-labelledby="apps-dialog-title">
      <div className="apps-dialog">
        <div className="apps-dialog-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h3 id="apps-dialog-title" className="apps-dialog-title">Withdraw Application?</h3>
        <p className="apps-dialog-message">{message}</p>
        <div className="apps-dialog-actions">
          <button className="apps-dialog-cancel" onClick={onCancel} disabled={loading}>
            Cancel
          </button>
          <button className="apps-dialog-confirm" onClick={onConfirm} disabled={loading}>
            {loading ? 'Withdrawing…' : 'Yes, Withdraw'}
          </button>
        </div>
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr className="apps-skel-row">
      <td><div className="apps-skel apps-skel-title" /></td>
      <td><div className="apps-skel apps-skel-sub" /></td>
      <td><div className="apps-skel apps-skel-sub" /></td>
      <td><div className="apps-skel apps-skel-chip-sm" /></td>
      <td><div className="apps-skel apps-skel-date" /></td>
      <td><div className="apps-skel apps-skel-btn" /></td>
    </tr>
  );
}

export default function Applications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('All');
  const [confirmTarget, setConfirmTarget] = useState(null); // { id, position }
  const [withdrawing, setWithdrawing] = useState(false);
  const [withdrawError, setWithdrawError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyApplications();
      setApplications(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setError('Failed to load your applications. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filteredApplications = applications.filter((app) => {
    if (activeTab === 'All') return true;
    return app.status === activeTab.toLowerCase();
  });

  const handleWithdrawClick = (app) => {
    setWithdrawError(null);
    setConfirmTarget({ id: app.id, position: app.job?.position || 'this job' });
  };

  const handleConfirmWithdraw = async () => {
    if (!confirmTarget) return;
    setWithdrawing(true);
    setWithdrawError(null);
    try {
      await withdrawApplication(confirmTarget.id);
      // Update status in state without full reload
      setApplications((prev) =>
        prev.map((a) => (a.id === confirmTarget.id ? { ...a, status: 'withdrawn' } : a))
      );
      setConfirmTarget(null);
    } catch (err) {
      setWithdrawError(err.message || 'Failed to withdraw application. It may already be shortlisted.');
    } finally {
      setWithdrawing(false);
    }
  };

  const handleCancelWithdraw = () => {
    setConfirmTarget(null);
    setWithdrawError(null);
  };

  const tabCounts = STATUS_TABS.reduce((acc, tab) => {
    if (tab === 'All') {
      acc[tab] = applications.length;
    } else {
      acc[tab] = applications.filter((a) => a.status === tab.toLowerCase()).length;
    }
    return acc;
  }, {});

  return (
    <div className="apps-page">
      {/* Page Header */}
      <div className="apps-header">
        <div>
          <h1 className="apps-title">My Applications</h1>
          {!loading && (
            <p className="apps-subtitle">
              {applications.length} {applications.length === 1 ? 'application' : 'applications'}
            </p>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="apps-error" role="alert">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{error}</span>
          <button className="apps-error-retry" onClick={load}>Retry</button>
        </div>
      )}

      {/* Withdraw error (inline) */}
      {withdrawError && (
        <div className="apps-error apps-error--warn" role="alert">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          <span>{withdrawError}</span>
          <button className="apps-error-close" onClick={() => setWithdrawError(null)} aria-label="Dismiss">×</button>
        </div>
      )}

      {/* Status Filter Tabs */}
      <div className="apps-tabs" role="tablist" aria-label="Filter applications by status">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            className={`apps-tab${activeTab === tab ? ' apps-tab--active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
            {tabCounts[tab] > 0 && (
              <span className="apps-tab-count">{tabCounts[tab]}</span>
            )}
          </button>
        ))}
      </div>

      {/* Table / Content Area */}
      <div className="apps-table-wrap">
        {loading ? (
          <table className="apps-table">
            <thead>
              <tr>
                <th>Position</th>
                <th>Company</th>
                <th>Location</th>
                <th>Type</th>
                <th>Applied</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4].map((i) => <SkeletonRow key={i} />)}
            </tbody>
          </table>
        ) : filteredApplications.length === 0 ? (
          <div className="apps-empty">
            <div className="apps-empty-icon">
              <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#C7D2FE" strokeWidth="1.4">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
            </div>
            {activeTab !== 'All' ? (
              <>
                <h3 className="apps-empty-title">No {activeTab.toLowerCase()} applications</h3>
                <p className="apps-empty-sub">
                  Switch to "All" to see all your applications, or{' '}
                  <a href="/jobs" className="apps-empty-link">browse jobs</a> to apply.
                </p>
              </>
            ) : (
              <>
                <h3 className="apps-empty-title">No applications yet</h3>
                <p className="apps-empty-sub">
                  You haven't applied for any jobs yet.{' '}
                  <a href="/jobs" className="apps-empty-link">Browse open positions</a> to get started.
                </p>
              </>
            )}
          </div>
        ) : (
          <table className="apps-table">
            <thead>
              <tr>
                <th>Position</th>
                <th>Company</th>
                <th>Location</th>
                <th>Type</th>
                <th>Applied</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredApplications.map((app) => {
                const job = app.job || {};
                const canWithdraw = app.status !== 'shortlisted' && app.status !== 'withdrawn';
                return (
                  <tr key={app.id} className="apps-row">
                    <td className="apps-td-position">
                      <span className="apps-position-name">{job.position || '—'}</span>
                    </td>
                    <td className="apps-td-company">{job.company || '—'}</td>
                    <td className="apps-td-location">
                      {job.location ? (
                        <span className="apps-location">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                          </svg>
                          {job.location}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="apps-td-type">
                      <JobTypeChip type={job.job_type} />
                    </td>
                    <td className="apps-td-date">{formatDate(app.created_at)}</td>
                    <td className="apps-td-status">
                      <StatusChip status={app.status} />
                    </td>
                    <td className="apps-td-action">
                      <button
                        className={`apps-withdraw-btn${!canWithdraw ? ' apps-withdraw-btn--disabled' : ''}`}
                        onClick={() => canWithdraw && handleWithdrawClick(app)}
                        disabled={!canWithdraw}
                        aria-label={`Withdraw application for ${job.position || 'this job'}`}
                        title={
                          app.status === 'shortlisted'
                            ? 'Cannot withdraw a shortlisted application'
                            : app.status === 'withdrawn'
                            ? 'Already withdrawn'
                            : 'Withdraw this application'
                        }
                      >
                        Withdraw
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Confirm Dialog */}
      {confirmTarget && (
        <ConfirmDialog
          message={`Are you sure you want to withdraw your application for "${confirmTarget.position}"? This action cannot be undone.`}
          onConfirm={handleConfirmWithdraw}
          onCancel={handleCancelWithdraw}
          loading={withdrawing}
        />
      )}
    </div>
  );
}
