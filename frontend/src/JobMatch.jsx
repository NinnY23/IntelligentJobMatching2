// src/JobMatch.jsx
import React, { useState } from 'react';
import './JobMatch.css';

export default function JobMatch() {
  const [jobs, setJobs] = useState([
    {
      id: 1,
      company: 'Google',
      logo: '📍',
      position: 'Senior Frontend Developer',
      location: 'Mountain View, CA',
      salary: '$150,000 - $200,000',
      description: 'We are looking for an experienced Frontend Developer to join our team. You will work on cutting-edge web applications used by millions.',
      skills: ['React', 'JavaScript', 'TypeScript', 'CSS'],
      type: 'Full-time',
      postedDays: 2,
      applicants: 245
    },
    {
      id: 2,
      company: 'Microsoft',
      logo: '🪟',
      position: 'Full Stack Developer',
      location: 'Seattle, WA',
      salary: '$140,000 - $190,000',
      description: 'Join our team to build scalable cloud solutions. Experience with Azure and modern web technologies required.',
      skills: ['React', 'Node.js', 'Azure', 'Python'],
      type: 'Full-time',
      postedDays: 5,
      applicants: 189
    },
    {
      id: 3,
      company: 'Amazon',
      logo: '📦',
      position: 'Backend Engineer',
      location: 'Seattle, WA',
      salary: '$130,000 - $180,000',
      description: 'Build distributed systems that power Amazon. Strong background in system design and databases required.',
      skills: ['Java', 'Python', 'AWS', 'SQL'],
      type: 'Full-time',
      postedDays: 1,
      applicants: 312
    },
    {
      id: 4,
      company: 'Meta',
      logo: '👤',
      position: 'React Native Developer',
      location: 'San Francisco, CA',
      salary: '$160,000 - $210,000',
      description: 'Help us build the next generation of mobile applications. Experience with React Native and mobile development required.',
      skills: ['React Native', 'JavaScript', 'iOS', 'Android'],
      type: 'Full-time',
      postedDays: 3,
      applicants: 156
    },
    {
      id: 5,
      company: 'Apple',
      logo: '🍎',
      position: 'iOS Developer',
      location: 'Cupertino, CA',
      salary: '$170,000 - $220,000',
      description: 'Create amazing experiences for billions of users. Swift and iOS development expertise required.',
      skills: ['Swift', 'iOS', 'Objective-C', 'UIKit'],
      type: 'Full-time',
      postedDays: 4,
      applicants: 287
    }
  ]);

  const handleApply = (jobId) => {
    alert(`Applied to job #${jobId}`);
  };

  const handleSave = (jobId) => {
    alert(`Saved job #${jobId}`);
  };

  return (
    <div className="jobs-container">
      <div className="jobs-header">
        <h2>Job Opportunities</h2>
        <p>Find your perfect match</p>
      </div>

      <div className="jobs-list">
        {jobs.map((job) => (
          <div key={job.id} className="job-post">
            <div className="job-header">
              <div className="company-info">
                <div className="company-logo">{job.logo}</div>
                <div className="company-details">
                  <h3>{job.position}</h3>
                  <p className="company-name">{job.company}</p>
                </div>
              </div>
              <button className="save-btn" onClick={() => handleSave(job.id)}>
                ♡
              </button>
            </div>

            <div className="job-meta">
              <span className="meta-item">📍 {job.location}</span>
              <span className="meta-item">💼 {job.type}</span>
              <span className="meta-item">⏱️ {job.postedDays} days ago</span>
            </div>

            <div className="job-body">
              <p>{job.description}</p>
            </div>

            <div className="job-skills">
              {job.skills.map((skill, index) => (
                <span key={index} className="skill-tag">{skill}</span>
              ))}
            </div>

            <div className="job-footer">
              <div className="job-salary">{job.salary}</div>
              <div className="job-stats">
                <span>{job.applicants} applied</span>
              </div>
            </div>

            <button 
              className="apply-btn"
              onClick={() => handleApply(job.id)}
            >
              Apply Now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}