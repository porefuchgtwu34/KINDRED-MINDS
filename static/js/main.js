/* ==========================================================================
   Kindred Minds — front-end interactions
   Handles: near-real-time chat via polling, unread badge, small UX niceties.
   ========================================================================== */

(function () {
  "use strict";

  // ------------------------------------------------------------------
  // Unread messages badge in the sidebar (polls every 15s on every page)
  // ------------------------------------------------------------------
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

  // ------------------------------------------------------------------
  // Chat window: send + poll for new messages
  // ------------------------------------------------------------------
  const chatForm = document.getElementById("chat-form");
  const chatBox = document.getElementById("chat-messages");
  const chatInput = document.getElementById("chat-input");

  if (chatForm && chatBox && chatInput) {
    const username = chatForm.dataset.username;
    const me = chatForm.dataset.me;
    let since = chatBox.dataset.last || new Date(0).toISOString();

    function appendMessage(msg) {
      const div = document.createElement("div");
      const mine = msg.sender_name === me;
      div.className = "chat-bubble " + (mine ? "chat-bubble-mine" : "chat-bubble-theirs");
      const time = (msg.created_at || "").slice(11, 16);
      div.innerHTML =
        "<span>" +
        escapeHtml(msg.content) +
        "</span><time>" +
        time +
        "</time>";
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
      if (msg.created_at) since = msg.created_at;
    }

    function escapeHtml(s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function poll() {
      fetch(
        "/api/messages/" +
          encodeURIComponent(username) +
          "/poll?since=" +
          encodeURIComponent(since)
      )
        .then((r) => (r.ok ? r.json() : []))
        .then((rows) => {
          if (Array.isArray(rows)) rows.forEach(appendMessage);
        })
        .catch(() => {});
    }

    setInterval(poll, 3000);
    chatBox.scrollTop = chatBox.scrollHeight;

    chatForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const content = chatInput.value.trim();
      if (!content) return;
      chatInput.value = "";
      fetch("/api/messages/" + encodeURIComponent(username) + "/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: content }),
      })
        .then((r) => r.json())
        .then((msg) => {
          if (msg && msg.content) appendMessage(msg);
        })
        .catch(() => {});
    });
  }

  // ------------------------------------------------------------------
  // Flash message dismiss
  // ------------------------------------------------------------------
  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });
})();
