import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock the api module
jest.mock('../api', () => ({
  fetchJobMatches: jest.fn(),
  fetchJobPosts: jest.fn(),
  applyForJob: jest.fn(),
}));

import { fetchJobMatches, fetchJobPosts } from '../api';
import Jobs from '../pages/Jobs';

beforeEach(() => {
  fetchJobMatches.mockClear();
  fetchJobPosts.mockClear();
  Storage.prototype.getItem = jest.fn((key) => {
    if (key === 'token') return 'mock.jwt.token';
    if (key === 'user') return JSON.stringify({ id: 1, role: 'employee', skills: 'Python, React' });
    return null;
  });
});

function renderJobs(userOverride) {
  if (userOverride) {
    Storage.prototype.getItem = jest.fn((key) => {
      if (key === 'token') return 'mock.jwt.token';
      if (key === 'user') return JSON.stringify(userOverride);
      return null;
    });
  }
  return render(
    <BrowserRouter>
      <Jobs />
    </BrowserRouter>
  );
}

describe('Jobs', () => {
  test('renders loading skeleton initially', () => {
    fetchJobMatches.mockReturnValue(new Promise(() => {})); // Never resolves
    renderJobs();
    expect(document.querySelector('.jobs-skeleton-card')).toBeTruthy();
  });

  test('renders job cards with match scores for employees', async () => {
    const mockJobs = [
      {
        id: 1, position: 'Python Developer', company: 'TechCo',
        location: 'Bangkok', description: 'Build APIs',
        required_skills: 'Python, Flask', preferred_skills: 'Docker',
        match_score: 85, matched_skills: ['Python'], missing_skills: ['Flask'],
        salary_min: 50000, salary_max: 80000, job_type: 'Full-time',
        status: 'active',
      },
    ];

    fetchJobMatches.mockResolvedValueOnce(mockJobs);

    renderJobs();

    await waitFor(() => {
      expect(screen.getByText('Python Developer')).toBeInTheDocument();
    });

    expect(screen.getByText(/85% match/i)).toBeInTheDocument();
  });

  test('shows empty state when no jobs available', async () => {
    fetchJobMatches.mockResolvedValueOnce([]);

    renderJobs();

    await waitFor(() => {
      const emptyEl = screen.queryByText(/no.*job/i) || document.querySelector('.jobs-empty');
      expect(emptyEl).toBeTruthy();
    });
  });

  test('renders job cards for employers using fetchJobPosts', async () => {
    const mockJobs = [
      {
        id: 1, position: 'React Dev', company: 'StartupX',
        location: 'Remote', description: 'Frontend work',
        required_skills: 'React, JavaScript', preferred_skills: '',
        salary_min: 60000, salary_max: 100000, job_type: 'Full-time',
        status: 'active',
      },
    ];

    fetchJobPosts.mockResolvedValueOnce(mockJobs);

    renderJobs({ id: 2, role: 'employer' });

    await waitFor(() => {
      expect(screen.getByText('React Dev')).toBeInTheDocument();
    });
  });
});
