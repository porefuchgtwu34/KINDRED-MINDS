document.addEventListener('DOMContentLoaded', function () {
  // Unread badge polling
  const badge = document.getElementById('unread-badge');
  if (badge) {
    function pollUnread() {
      fetch('/api/unread-count')
        .then((r) => r.json())
        .then((data) => {
          if (data.unread > 0) {
            badge.textContent = data.unread;
            badge.style.display = 'inline-block';
          } else {
            badge.style.display = 'none';
          }
        })
        .catch(() => {});
    }
    pollUnread();
    setInterval(pollUnread, 15000);
  }

  // Chat polling + send
  const chatForm = document.getElementById('chat-form');
  const chatBox = document.getElementById('chat-messages');
  const chatInput = document.getElementById('chat-input');
  if (chatForm && chatBox && chatInput) {
    const username = chatForm.dataset.username;
    let since = chatBox.dataset.last || new Date().toISOString();

    function appendMessage(msg) {
      const div = document.createElement('div');
      div.className = 'msg' + (msg.sender_name === chatForm.dataset.me ? ' me' : '');
      div.innerHTML =
        '<span class="sender">' +
        msg.sender_name +
        '</span><span class="body">' +
        msg.content +
        '</span><span class="time">' +
        (msg.created_at || '').slice(11, 16) +
        '</span>';
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
      if (msg.created_at) since = msg.created_at;
    }

    function poll() {
      fetch('/api/messages/' + encodeURIComponent(username) + '/poll?since=' + encodeURIComponent(since))
        .then((r) => r.json())
        .then((rows) => {
          if (Array.isArray(rows)) rows.forEach(appendMessage);
        })
        .catch(() => {});
    }
    setInterval(poll, 3000);

    chatForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const content = chatInput.value.trim();
      if (!content) return;
      fetch('/api/messages/' + encodeURIComponent(username) + '/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: content }),
      })
        .then((r) => r.json())
        .then((msg) => {
          if (msg.content) {
            appendMessage(msg);
            chatInput.value = '';
          }
        })
        .catch(() => {});
    });
  }
});
