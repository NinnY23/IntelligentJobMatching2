// src/api.js
export async function loginUser(email, password) {
  const res = await fetch('/api/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  if (!res.ok) {
    throw new Error('Login failed');
  }
  
  return res.json();
}

export async function fetchJobPosts() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/job-posts', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}

export async function fetchJobMatches() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/jobs/matches', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}

export async function logoutUser() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}

export async function getProfile() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/profile', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch profile');
  }
  
  return res.json();
}

export async function updateProfile(profileData) {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/profile', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(profileData),
  });
  
  if (!res.ok) {
    throw new Error('Failed to update profile');
  }
  
  return res.json();
}