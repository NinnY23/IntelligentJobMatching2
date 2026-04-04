import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CreateJobPost from '../CreateJobPost';

global.fetch = jest.fn();

beforeEach(() => {
  fetch.mockClear();
  Storage.prototype.getItem = jest.fn((key) => {
    if (key === 'token') return 'mock.jwt.token';
    return null;
  });
});

describe('CreateJobPost', () => {
  const mockPostCreated = jest.fn();
  const mockBack = jest.fn();

  function renderForm() {
    return render(
      <CreateJobPost onPostCreated={mockPostCreated} onBack={mockBack} />
    );
  }

  test('renders form with required fields', () => {
    renderForm();
    expect(screen.getByLabelText(/job title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/company name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/location/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/job description/i)).toBeInTheDocument();
  });

  test('shows validation error when required fields are empty', async () => {
    renderForm();

    // Save as Draft bypasses HTML5 form validation but runs custom validation
    const draftBtn = screen.getByRole('button', { name: /save as draft/i });
    fireEvent.click(draftBtn);

    await waitFor(() => {
      expect(screen.getByText(/please fill in all required fields/i)).toBeInTheDocument();
    });
  });

  test('submits job with active status by default', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ message: 'Created', job: { id: 1, status: 'active' } }),
    });

    renderForm();

    fireEvent.change(screen.getByLabelText(/job title/i), { target: { value: 'Dev', name: 'position' } });
    fireEvent.change(screen.getByLabelText(/company name/i), { target: { value: 'Co', name: 'company' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'BKK', name: 'location' } });
    fireEvent.change(screen.getByLabelText(/job description/i), { target: { value: 'Build stuff', name: 'description' } });

    fireEvent.submit(screen.getByRole('button', { name: /post job/i }).closest('form'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    const call = fetch.mock.calls[0];
    const body = JSON.parse(call[1].body);
    expect(body.status).toBe('active');
  });

  test('save as draft button submits with draft status', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ message: 'Created', job: { id: 1, status: 'draft' } }),
    });

    renderForm();

    fireEvent.change(screen.getByLabelText(/job title/i), { target: { value: 'Dev', name: 'position' } });
    fireEvent.change(screen.getByLabelText(/company name/i), { target: { value: 'Co', name: 'company' } });
    fireEvent.change(screen.getByLabelText(/location/i), { target: { value: 'BKK', name: 'location' } });
    fireEvent.change(screen.getByLabelText(/job description/i), { target: { value: 'WIP', name: 'description' } });

    fireEvent.click(screen.getByRole('button', { name: /save as draft/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });

    const call = fetch.mock.calls[0];
    const body = JSON.parse(call[1].body);
    expect(body.status).toBe('draft');
  });
});
