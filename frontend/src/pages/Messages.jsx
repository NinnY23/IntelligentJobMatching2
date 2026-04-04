import React, { useState, useEffect, useRef } from 'react';
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

  useEffect(() => {
    loadConversations();
  }, []);

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

  return (
    <div className="messages-page">
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
            <div className="thread-messages">
              {thread.map(msg => {
                const isMine = msg.sender_id === user.id;
                return (
                  <div key={msg.id} className={`message-bubble ${isMine ? 'mine' : 'theirs'}`}>
                    {msg.body && <p>{msg.body}</p>}
                    {msg.attachment_path && isImage(msg.attachment_type) && (
                      <img
                        src={`/api/uploads/${msg.attachment_path}`}
                        alt={msg.attachment_name}
                        className="msg-image"
                        onClick={() => window.open(`/api/uploads/${msg.attachment_path}`)}
                      />
                    )}
                    {msg.attachment_path && !isImage(msg.attachment_type) && (
                      <a
                        href={`/api/uploads/${msg.attachment_path}`}
                        target="_blank"
                        rel="noreferrer"
                        className="msg-file-link"
                      >
                        📎 {msg.attachment_name}
                      </a>
                    )}
                    <span className="msg-time">
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                  📎 {attachment.name}
                  <button type="button" onClick={() => setAttachment(null)}>✕</button>
                </div>
              )}
              <input
                type="text"
                placeholder="Type a message..."
                value={messageText}
                onChange={e => setMessageText(e.target.value)}
              />
              <label className="attach-btn" title="Attach file">
                📎
                <input
                  type="file"
                  accept="image/*,.pdf,.doc,.docx"
                  style={{ display: 'none' }}
                  onChange={e => setAttachment(e.target.files[0] || null)}
                />
              </label>
              <button
                type="submit"
                className="btn-primary"
                disabled={sending || (!messageText.trim() && !attachment)}
              >
                {sending ? '...' : 'Send'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
