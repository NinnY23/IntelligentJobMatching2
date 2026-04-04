import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';

// Mock fetch
global.fetch = jest.fn();

beforeEach(() => {
  fetch.mockClear();
  Storage.prototype.setItem = jest.fn();
});

describe('Login', () => {
  const mockLoginSuccess = jest.fn();
  const mockSwitchToSignUp = jest.fn();
  const mockSwitchToForgotPassword = jest.fn();

  function renderLogin() {
    return render(
      <Login
        onLoginSuccess={mockLoginSuccess}
        onSwitchToSignUp={mockSwitchToSignUp}
        onSwitchToForgotPassword={mockSwitchToForgotPassword}
      />
    );
  }

  beforeEach(() => {
    mockLoginSuccess.mockClear();
  });

  test('renders login form with email and password fields', () => {
    renderLogin();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  test('calls onLoginSuccess with user data on successful login', async () => {
    const mockUser = { id: 1, name: 'Test', email: 'test@test.com', role: 'employee' };
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: 'jwt.token.here', user: mockUser }),
    });

    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pass123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockLoginSuccess).toHaveBeenCalledWith(mockUser);
    });

    expect(localStorage.setItem).toHaveBeenCalledWith('token', 'jwt.token.here');
    expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
  });

  test('displays error message on failed login', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ message: 'Invalid email or password' }),
    });

    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bad@test.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  test('displays network error on fetch failure', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    renderLogin();
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@test.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'pass' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});
