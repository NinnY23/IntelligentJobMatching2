import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchConversations, fetchThread, sendMessage, markThreadRead } from '../api';
import './Messages.css';

export default function Messages({ user }) {
  const [conversations, setConversations] = useState([]);
  const [activePartnerId, setActivePartnerId] = useState(null);
  const [thread, setThread] = useState([]);
  const [messageText, setMessageText] = useState('');
  const [attachment, setAttachment] = useState(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef(null);
  const pollRef = useRef(null);
  const lastTimestampRef = useRef(null);

  const [searchParams] = useSearchParams();

  useEffect(() => {
    loadConversations();
    const partnerId = searchParams.get('partner');
    if (partnerId) {
      setActivePartnerId(Number(partnerId));
    }
  }, [searchParams]);

  useEffect(() => {
    if (activePartnerId) {
      loadThread(activePartnerId);
      markThreadRead(activePartnerId);
      startPolling(activePartnerId);
    }
    return () => clearInterval(pollRef.current);
  }, [activePartnerId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread]);

  async function loadConversations() {
    try {
      const convos = await fetchConversations();
      setConversations(convos);
    } catch (e) {
      setError('Failed to load conversations.');
    }
  }

  async function loadThread(partnerId) {
    const msgs = await fetchThread(partnerId);
    setThread(msgs);
    if (msgs.length > 0) {
      lastTimestampRef.current = msgs[msgs.length - 1].created_at;
    }
  }

  function startPolling(partnerId) {
    clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      const newMsgs = await fetchThread(partnerId, lastTimestampRef.current);
      if (newMsgs.length > 0) {
        setThread(prev => [...prev, ...newMsgs]);
        lastTimestampRef.current = newMsgs[newMsgs.length - 1].created_at;
        loadConversations();
      }
    }, 5000);
  }

  async function handleSend(e) {
    e.preventDefault();
    if (!messageText.trim() && !attachment) return;
    setSending(true);
    const result = await sendMessage(activePartnerId, messageText, attachment);
    if (result.ok) {
      setMessageText('');
      setAttachment(null);
      await loadThread(activePartnerId);
      loadConversations();
    } else {
      setError(result.data.message || 'Failed to send message.');
    }
    setSending(false);
  }

  function isImage(mimeType) {
    return mimeType && mimeType.startsWith('image/');
  }

  function attachUrl(path) {
    const token = localStorage.getItem('token');
    return `/api/uploads/${path}${token ? `?token=${token}` : ''}`;
  }

  return (
    <div className={`messages-page${activePartnerId ? ' has-active' : ''}`}>
      <div className="conversations-panel">
        <div className="conversations-header"><h3>Messages</h3></div>
        {conversations.length === 0 && (
          <div className="empty-state-sm">No conversations yet.</div>
        )}
        {conversations.map(c => (
          <div
            key={c.partner_id}
            className={`conversation-item ${activePartnerId === c.partner_id ? 'active' : ''}`}
            onClick={() => setActivePartnerId(c.partner_id)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && setActivePartnerId(c.partner_id)}
            aria-label={`Conversation with ${c.partner_name}`}
          >
            <div className="convo-avatar">
              {c.partner_name.slice(0, 2).toUpperCase()}
            </div>
            <div className="convo-info">
              <div className="convo-name">
                {c.partner_name}
                {c.unread_count > 0 && <span className="unread-badge">{c.unread_count}</span>}
              </div>
              <div className="convo-preview">{c.last_message}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="thread-panel">
        {!activePartnerId ? (
          <div className="thread-empty">Select a conversation to start messaging.</div>
        ) : (
          <>
            <div className="thread-header">
              <button
                className="thread-back-btn"
                onClick={() => setActivePartnerId(null)}
                aria-label="Back to conversations"
              >
                <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <div className="thread-header-avatar">
                {(conversations.find(c => c.partner_id === activePartnerId)?.partner_name || '??').slice(0, 2).toUpperCase()}
              </div>
              <span className="thread-header-name">
                {conversations.find(c => c.partner_id === activePartnerId)?.partner_name || 'Unknown'}
              </span>
            </div>
            <div className="thread-messages">
              {thread.map(msg => {
                const isMine = msg.sender_id === user.id;
                return (
                  <div key={msg.id} className={`message-bubble ${isMine ? 'mine' : 'theirs'}`}>
                    {msg.body && <p>{msg.body}</p>}
                    {msg.attachment_path && isImage(msg.attachment_type) && (
                      <a href={attachUrl(msg.attachment_path)} target="_blank" rel="noreferrer" className="msg-image-link">
                        <img
                          src={attachUrl(msg.attachment_path)}
                          alt={msg.attachment_name}
                          className="msg-image"
                        />
                      </a>
                    )}
                    {msg.attachment_path && !isImage(msg.attachment_type) && (
                      <a
                        href={attachUrl(msg.attachment_path)}
                        target="_blank"
                        rel="noreferrer"
                        className="msg-file-link"
                      >
                        <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                        </svg>
                        {msg.attachment_name}
                      </a>
                    )}
                    <span className="msg-time">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      {isMine && msg.read && <span className="msg-read-tick" aria-label="Read"> ✓</span>}
                    </span>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {error && <div className="error-banner">{error}</div>}

            <form className="message-input-bar" onSubmit={handleSend}>
              {attachment && (
                <div className="attachment-preview">
                  <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  {attachment.name}
                  <button type="button" onClick={() => setAttachment(null)} aria-label="Remove attachment">
                    <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              )}
              <input
                type="text"
                placeholder="Type a message..."
                aria-label="Message"
                value={messageText}
                onChange={e => setMessageText(e.target.value)}
              />
              <label className="attach-btn" title="Attach file">
                <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
                <input
                  type="file"
                  aria-label="Attach file"
                  accept="image/*,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setAttachment(e.target.files[0] || null)}
                />
              </label>
              <button
                type="submit"
                className="btn-primary send-btn"
                disabled={sending || (!messageText.trim() && !attachment)}
              >
                {sending ? 'Sending' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
