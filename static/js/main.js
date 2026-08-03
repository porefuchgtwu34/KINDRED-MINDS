/* ==========================================================================
   Kindred Minds — front-end interactions
   Handles: near-real-time chat via polling, unread badge, small UX niceties.
   ========================================================================== */

(function () {
  "use strict";

  function refreshUnreadBadge() {
    fetch("/api/unread-count")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data) return;
        const dot = document.getElementById("unread-dot");
        if (!dot) return;
        dot.hidden = data.unread === 0;
      })
      .catch(() => {});
  }

  if (document.getElementById("unread-dot")) {
    refreshUnreadBadge();
    setInterval(refreshUnreadBadge, 15000);
  }

  const chatWindow = document.querySelector(".chat-window");
  if (chatWindow && window.KINDRED_CHAT) {
    const { username, myId } = window.KINDRED_CHAT;
    const messagesEl = document.getElementById("chat-messages");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const statusEl = document.getElementById("chat-status");

    function scrollToBottom() {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }
    scrollToBottom();

    function lastTimestamp() {
      const bubbles = messagesEl.querySelectorAll(".chat-bubble");
      if (bubbles.length === 0) return "1970-01-01T00:00:00";
      return bubbles[bubbles.length - 1].dataset.time;
    }

    function appendMessage(msg) {
      const bubble = document.createElement("div");
      const mine = msg.sender_id === myId;
      bubble.className = "chat-bubble " + (mine ? "chat-bubble-mine" : "chat-bubble-theirs");
      bubble.dataset.time = msg.created_at;

      const p = document.createElement("p");
      p.textContent = msg.content;
      const time = document.createElement("time");
      time.textContent = msg.created_at.slice(11, 16);

      bubble.appendChild(p);
      bubble.appendChild(time);
      messagesEl.appendChild(bubble);
      scrollToBottom();
    }

    function poll() {
      fetch(`/api/messages/${encodeURIComponent(username)}/poll?since=${encodeURIComponent(lastTimestamp())}`)
        .then((r) => (r.ok ? r.json() : []))
        .then((newMessages) => {
          if (Array.isArray(newMessages) && newMessages.length) {
            newMessages.forEach(appendMessage);
          }
          if (statusEl) statusEl.textContent = "messages update automatically";
        })
        .catch(() => {
          if (statusEl) statusEl.textContent = "reconnecting…";
        });
    }

    const pollInterval = setInterval(poll, 3000);
    window.addEventListener("beforeunload", () => clearInterval(pollInterval));

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const content = input.value.trim();
      if (!content) return;
      input.value = "";
      fetch(`/api/messages/${encodeURIComponent(username)}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      })
        .then((r) => r.json())
        .then((msg) => {
          if (msg.error) {
            alert(msg.error);
            return;
          }
          appendMessage(msg);
        })
        .catch(() => alert("Couldn't send your message. Please try again."));
    });
  }

  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });
})();
