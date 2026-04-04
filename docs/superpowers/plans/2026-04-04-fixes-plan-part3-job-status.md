# Part 3: Job Drafts & Archiving

[Back to plan index](2026-04-04-fixes-and-features-plan-index.md)

---

## Task 5: Add Job Status (Draft / Active / Archived)

**Files:**
- Modify: `models.py:68-134` (Job model)
- Modify: `app.py:488-543` (create_job_post), `app.py:545-554` (get_job_posts), `app.py:613-632` (update_job_post), `app.py:743-756` (get_employer_jobs)
- Modify: `frontend/src/CreateJobPost.jsx`
- Modify: `frontend/src/pages/MyJobs.jsx`
- Create: `tests/test_job_status.py`

### Step 1: Write failing tests for job status

- [ ] **Create tests/test_job_status.py**

```python
def test_create_job_defaults_to_active(client, employer_token):
    """New job without explicit status should be 'active'."""
    res = client.post('/api/job-posts', json={
        'position': 'Dev', 'company': 'Co', 'location': 'BKK',
        'description': 'Build stuff', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 201
    job = res.get_json()['job']
    assert job['status'] == 'active'


def test_create_draft_job(client, employer_token):
    """Job with status='draft' should be saved as draft."""
    res = client.post('/api/job-posts', json={
        'position': 'Draft Dev', 'company': 'Co', 'location': 'BKK',
        'description': 'WIP', 'required_skills': 'Python',
        'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 201
    job = res.get_json()['job']
    assert job['status'] == 'draft'


def test_draft_jobs_hidden_from_public_listing(client, employer_token, seeker_token):
    """GET /api/job-posts should only return active jobs."""
    # Create one active, one draft
    client.post('/api/job-posts', json={
        'position': 'Active Job', 'company': 'Co', 'location': 'BKK',
        'description': 'Active', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})

    client.post('/api/job-posts', json={
        'position': 'Draft Job', 'company': 'Co', 'location': 'BKK',
        'description': 'Draft', 'required_skills': 'Python',
        'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})

    # Public listing should only show active
    res = client.get('/api/job-posts')
    jobs = res.get_json()
    positions = [j['position'] for j in jobs]
    assert 'Active Job' in positions
    assert 'Draft Job' not in positions


def test_employer_sees_all_statuses(client, employer_token):
    """GET /api/employer/jobs should return all statuses."""
    client.post('/api/job-posts', json={
        'position': 'Active Emp', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})

    client.post('/api/job-posts', json={
        'position': 'Draft Emp', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python',
        'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})

    res = client.get('/api/employer/jobs',
                     headers={'Authorization': f'Bearer {employer_token}'})
    data = res.get_json()
    positions = [j['position'] for j in data['jobs']]
    assert 'Active Emp' in positions
    assert 'Draft Emp' in positions


def test_archive_job(client, employer_token):
    """PUT /api/job-posts/<id> with status='archived' should archive."""
    res = client.post('/api/job-posts', json={
        'position': 'To Archive', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    job_id = res.get_json()['job']['id']

    res = client.put(f'/api/job-posts/{job_id}', json={'status': 'archived'},
                     headers={'Authorization': f'Bearer {employer_token}'})
    assert res.status_code == 200
    assert res.get_json()['job']['status'] == 'archived'

    # Should not appear in public listing
    res = client.get('/api/job-posts')
    positions = [j['position'] for j in res.get_json()]
    assert 'To Archive' not in positions


def test_publish_draft(client, employer_token):
    """Change draft to active should make it appear in public listing."""
    res = client.post('/api/job-posts', json={
        'position': 'Was Draft', 'company': 'Co', 'location': 'BKK',
        'description': 'Desc', 'required_skills': 'Python',
        'status': 'draft'
    }, headers={'Authorization': f'Bearer {employer_token}'})
    job_id = res.get_json()['job']['id']

    # Publish
    client.put(f'/api/job-posts/{job_id}', json={'status': 'active'},
               headers={'Authorization': f'Bearer {employer_token}'})

    # Should now appear
    res = client.get('/api/job-posts')
    positions = [j['position'] for j in res.get_json()]
    assert 'Was Draft' in positions
```

- [ ] **Run tests to verify they fail**

```bash
pytest tests/test_job_status.py -v
```

Expected: FAIL — Job model has no `status` field.

### Step 2: Add status field to Job model

- [ ] **Modify models.py**

In `models.py`, add to the `Job` class after `applicants` (around line 85):

```python
    status = db.Column(db.String(20), default='active', nullable=False)  # 'draft', 'active', 'archived'
```

Update `to_dict()` to include status. Add `'status': self.status,` after the `'applicants'` line:

```python
    def to_dict(self):
        return {
            'id': self.id,
            'employer_id': self.employer_id,
            'position': self.position,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'job_type': self.job_type,
            'openings': self.openings,
            'deadline': self.deadline,
            'applicants': self.applicants,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
```

### Step 3: Update backend endpoints

- [ ] **Update create_job_post in app.py**

In the `create_job_post` function, after the line `applicants=0` in the Job constructor (around line 531), add:

```python
            status=data.get('status', 'active'),
```

Also add validation before the Job constructor — after the required fields validation block:

```python
        status = data.get('status', 'active')
        if status not in ('draft', 'active'):
            return jsonify({"message": "Status must be 'draft' or 'active'"}), 400
```

- [ ] **Update get_job_posts to filter active only**

In the `get_job_posts` function (around line 546-554), replace:

```python
        jobs = Job.query.all()
```

with:

```python
        jobs = Job.query.filter_by(status='active').all()
```

- [ ] **Update get_job_matches to filter active only**

In the `get_job_matches` function (around line 586), replace:

```python
    all_jobs = Job.query.all()
```

with:

```python
    all_jobs = Job.query.filter_by(status='active').all()
```

- [ ] **Update update_job_post to allow status changes**

In the `update_job_post` function (around line 622-626), add `'status'` to the updatable_fields list:

```python
    updatable_fields = [
        'position', 'company', 'location', 'description',
        'required_skills', 'preferred_skills',
        'salary_min', 'salary_max', 'job_type', 'openings', 'deadline',
        'status'
    ]
```

Add validation after the field update loop:

```python
    if 'status' in data and data['status'] not in ('draft', 'active', 'archived'):
        return jsonify({"message": "Invalid status"}), 400
```

### Step 4: Run tests

- [ ] **Run all tests**

```bash
pytest tests/test_job_status.py -v
pytest tests/ -v
```

Expected: All tests PASS.

### Step 5: Update CreateJobPost.jsx — Save as Draft button

- [ ] **Modify CreateJobPost.jsx**

In `frontend/src/CreateJobPost.jsx`, find the `handleSubmit` function. Currently it sends the form data to the API. Refactor it to accept a status parameter:

Find the existing `handleSubmit` and rename it to a helper, then create two handlers:

After the existing `setLoading(true);` and before the try block, find where it builds the request body. Wrap the submission logic into a function that accepts status:

```javascript
  const submitJob = async (status) => {
    setError('');
    setSuccess('');

    if (!formData.position || !formData.company || !formData.location || !formData.description) {
      setError('Please fill in all required fields');
      return;
    }

    if (formData.salaryMin && formData.salaryMax && parseInt(formData.salaryMin) > parseInt(formData.salaryMax)) {
      setError('Minimum salary cannot be greater than maximum salary');
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/job-posts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...formData,
          required_skills: formData.skills,
          status: status,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.message || 'Failed to create job post');
      }

      setSuccess(status === 'draft' ? 'Job saved as draft!' : 'Job posted successfully!');
      if (status === 'active' && onPostCreated) {
        setTimeout(() => onPostCreated(), 1500);
      }
    } catch (err) {
      setError(err.message || 'Failed to create job post');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    submitJob('active');
  };

  const handleSaveDraft = () => {
    submitJob('draft');
  };
```

In the JSX, find the submit button and add a "Save as Draft" button next to it:

```jsx
          <div style={{ display: 'flex', gap: '12px' }}>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Posting...' : 'Post Job'}
            </button>
            <button type="button" onClick={handleSaveDraft} disabled={loading}
              className="btn-secondary"
              style={{ background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' }}>
              {loading ? 'Saving...' : 'Save as Draft'}
            </button>
          </div>
```

### Step 6: Update MyJobs.jsx — Status badges, archive, filter tabs

- [ ] **Modify MyJobs.jsx**

In `frontend/src/pages/MyJobs.jsx`, add a filter state and update the UI:

Add state for filter after existing state declarations (around line 10):
```javascript
  const [filter, setFilter] = useState('all');
```

Update `loadMyJobs` to use the employer endpoint instead of filtering client-side. Replace the existing `loadMyJobs` function:

```javascript
  async function loadMyJobs() {
    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/employer/jobs', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      setJobs(data.jobs || []);
    } catch {
      setMessage('Failed to load jobs.');
    }
    setLoading(false);
  }
```

Add archive handler after `handleDelete`:
```javascript
  async function handleArchive(jobId) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ status: 'archived' }),
      });
      if (res.ok) {
        setMessage('Job archived.');
        loadMyJobs();
      }
    } catch {
      setMessage('Failed to archive job.');
    }
  }

  async function handlePublish(jobId) {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`/api/job-posts/${jobId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ status: 'active' }),
      });
      if (res.ok) {
        setMessage('Job published!');
        loadMyJobs();
      }
    } catch {
      setMessage('Failed to publish job.');
    }
  }

  const filteredJobs = filter === 'all' ? jobs : jobs.filter(j => j.status === filter);
```

In the JSX, add filter tabs before the job list:
```jsx
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {['all', 'active', 'draft', 'archived'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            style={{
              padding: '6px 16px', borderRadius: '20px', border: 'none', cursor: 'pointer',
              background: filter === f ? '#4F46E5' : '#f3f4f6',
              color: filter === f ? 'white' : '#374151',
              fontWeight: filter === f ? 600 : 400,
            }}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>
```

For each job card, add a status badge and action buttons:
```jsx
      {/* Status badge — add near the job title */}
      <span style={{
        padding: '2px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
        background: job.status === 'active' ? '#DCFCE7' : job.status === 'draft' ? '#FEF3C7' : '#F3F4F6',
        color: job.status === 'active' ? '#166534' : job.status === 'draft' ? '#92400E' : '#6B7280',
      }}>
        {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
      </span>

      {/* Action buttons — add alongside existing edit/delete */}
      {job.status === 'draft' && (
        <button onClick={() => handlePublish(job.id)} style={{ color: '#16a34a' }}>Publish</button>
      )}
      {job.status === 'active' && (
        <button onClick={() => handleArchive(job.id)} style={{ color: '#f59e0b' }}>Archive</button>
      )}
      {job.status === 'archived' && (
        <button onClick={() => handlePublish(job.id)} style={{ color: '#4F46E5' }}>Reactivate</button>
      )}
```

Use `filteredJobs` instead of `jobs` when mapping over job cards.

### Step 7: Commit

- [ ] **Commit job status feature**

```bash
cd "E:/Projects/Intelligent job matching website"
git add models.py app.py tests/test_job_status.py frontend/src/CreateJobPost.jsx frontend/src/pages/MyJobs.jsx
git commit -m "feat: add job draft/active/archived status

Employers can save as draft, publish, archive, and reactivate jobs.
Public listings filter to active only. Implements PDF UC4-A2, UC5-A2."
```
