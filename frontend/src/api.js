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

export async function applyForJob(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/jobs/${jobId}/apply`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = new Error(res.status === 409 ? 'Already applied' : 'Failed to apply');
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function fetchMyApplications() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/applications', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error('Failed to fetch applications');
  }

  return res.json();
}

export async function withdrawApplication(appId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/applications/${appId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error('Failed to withdraw application');
  }
}

export async function updateJobPost(jobId, data) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return { ok: res.ok, data: await res.json() };
}

export async function deleteJobPost(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return { ok: res.ok, data: await res.json() };
}

export async function fetchJobApplicants(jobId) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/job-posts/${jobId}/applicants`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch applicants');
  return res.json();
}

export async function updateApplicationStatus(appId, status) {
  const token = localStorage.getItem('token');
  const res = await fetch(`/api/applications/${appId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ status }),
  });
  return { ok: res.ok, data: await res.json() };
}

export async function fetchEmployerDashboard() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/employer/dashboard', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
}

export async function fetchConversations() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/messages', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function fetchThread(userId, after = null) {
  const token = localStorage.getItem('token');
  const url = after
    ? `/api/messages/${userId}?after=${encodeURIComponent(after)}`
    : `/api/messages/${userId}`;
  const res = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function sendMessage(userId, body, attachmentFile = null) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  if (body) formData.append('body', body);
  if (attachmentFile) formData.append('attachment', attachmentFile);
  const res = await fetch(`/api/messages/${userId}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  return { ok: res.ok, status: res.status, data: await res.json() };
}

export async function markThreadRead(userId) {
  const token = localStorage.getItem('token');
  await fetch(`/api/messages/${userId}/read`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

export async function fetchUnreadCount() {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/messages', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) return 0;
  const convos = await res.json();
  return convos.reduce((sum, c) => sum + (c.unread_count || 0), 0);
}