import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '60vh', padding: '24px',
          textAlign: 'center',
        }}>
          <h2 style={{ fontSize: '24px', marginBottom: '12px', color: '#1f2937' }}>
            Something went wrong
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '24px', maxWidth: '400px' }}>
            An unexpected error occurred. Please try refreshing the page.
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: '10px 24px', borderRadius: '8px', border: 'none',
              background: '#4F46E5', color: 'white', cursor: 'pointer',
              fontSize: '14px', fontWeight: 600,
            }}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
