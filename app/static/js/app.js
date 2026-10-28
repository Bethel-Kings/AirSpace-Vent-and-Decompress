/* ==========================================================================
   AIRSPACE — Frontend Controller & State Machine
   ========================================================================== */

const FOLLOWUP_LABELS = {
  reset_3d: "3-day reset",
  reset_5d: "5-day reset",
  reset_7d: "7-day reset",
};

const FOLLOWUP_MOODS = [
  { value: "Still heavy (1/5)", emoji: "🌧️", label: "Still heavy" },
  { value: "Mixed (3/5)", emoji: "⛅", label: "Mixed" },
  { value: "Steadier (4/5)", emoji: "🌿", label: "Steadier" },
  { value: "Clearer (5/5)", emoji: "✨", label: "Clearer" },
];

const state = {
  currentUser: null,
  token: localStorage.getItem("airspace_token") || null,
  currentSession: null,
  preMood: null,
  postMood: null,
  activeView: "landing",
  pendingFollowupStage: null,
  autosaveTimer: null,
};

async function api(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }

  const response = await fetch(`/api/v1${endpoint}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const errorMsg = data.detail || (typeof data === "string" ? data : "An error occurred");
    throw new Error(typeof errorMsg === "string" ? errorMsg : JSON.stringify(errorMsg));
  }

  return data;
}

function showView(viewName) {
  state.activeView = viewName;
  document.querySelectorAll(".view-container").forEach((el) => {
    el.style.display = "none";
  });

  const target = document.getElementById(`view-${viewName}`);
  if (target) {
    target.style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  updateNav();

  if (viewName === "dashboard") loadDashboard();
  if (viewName === "history") loadHistory();
  if (viewName === "settings") loadSettings();
  if (viewName === "reset-tracking") loadResetTracking();
}

function updateNav() {
  const authNav = document.getElementById("auth-nav");
  const guestNav = document.getElementById("guest-nav");
  const userEmail = document.getElementById("nav-user-email");

  if (state.currentUser) {
    if (authNav) authNav.style.display = "flex";
    if (guestNav) guestNav.style.display = "none";
    if (userEmail) userEmail.textContent = state.currentUser.email;
  } else {
    if (authNav) authNav.style.display = "none";
    if (guestNav) guestNav.style.display = "flex";
  }

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === state.activeView);
  });
}

function showNotice(message, type = "error", containerId = null) {
  const alertBox = containerId ? document.getElementById(containerId) : document.getElementById("global-alert");
  if (!alertBox) return;
  alertBox.className = `alert alert-${type}`;
  alertBox.textContent = message;
  alertBox.style.display = "flex";
  setTimeout(() => {
    alertBox.style.display = "none";
  }, 5000);
}

function renderCrisisBanner(safety, containerId = "crisis-banner") {
  const box = document.getElementById(containerId);
  if (!box) return;
  if (!safety || !safety.is_crisis) {
    box.style.display = "none";
    box.innerHTML = "";
    return;
  }
  const lines = (safety.helplines || [])
    .map((h) => `<li><a href="${escapeHtml(h.url)}" target="_blank" rel="noopener">${escapeHtml(h.name)}</a> — ${escapeHtml(h.contact)}</li>`)
    .join("");
  box.innerHTML = `
    <strong>${escapeHtml(safety.title || "Support is available")}</strong>
    <p>${escapeHtml(safety.message || "")}</p>
    <ul>${lines}</ul>
  `;
  box.style.display = "block";
}

async function checkAuth() {
  if (!state.token) {
    updateNav();
    showView("landing");
    return;
  }
  try {
    const me = await api("/me");
    state.currentUser = me;
    updateNav();
    showView("dashboard");
  } catch (err) {
    logout(true);
  }
}

async function loginUser(email, password) {
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    state.token = data.access_token;
    localStorage.setItem("airspace_token", data.access_token);
    const me = await api("/me");
    state.currentUser = me;
    updateNav();
    showView("dashboard");
  } catch (err) {
    showNotice(err.message, "error", "login-alert");
  }
}

async function registerUser(email, password) {
  try {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    await loginUser(email, password);
  } catch (err) {
    showNotice(err.message, "error", "register-alert");
  }
}

async function logout(silent = false) {
  try {
    if (!silent) await api("/auth/logout", { method: "POST" });
  } catch (e) {}
  state.token = null;
  state.currentUser = null;
  localStorage.removeItem("airspace_token");
  updateNav();
  showView("landing");
}

function startNewSessionFlow() {
  state.currentSession = null;
  state.preMood = null;
  state.postMood = null;
  state.pendingFollowupStage = null;

  document.querySelectorAll("#pre-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
  document.querySelectorAll("#post-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
  document.getElementById("vent-textarea").value = "";
  document.getElementById("vent-char-count").textContent = "0 characters";
  document.getElementById("vent-autosave-status").textContent = "Drafts autosave privately";
  renderCrisisBanner(null);

  showView("pre-checkin");
}

async function submitPreCheckinAndContinue() {
  if (!state.preMood) {
    showNotice("Please select how you are feeling right now before continuing.", "error", "pre-checkin-alert");
    return;
  }
  showView("air-it-out");
}

async function autosaveDraft() {
  const content = document.getElementById("vent-textarea").value;
  const statusEl = document.getElementById("vent-autosave-status");
  if (!content.trim() || !state.preMood) return;

  try {
    if (!state.currentSession) {
      const session = await api("/sessions", {
        method: "POST",
        body: JSON.stringify({
          content,
          initial_mood: state.preMood,
          status: "draft",
        }),
      });
      state.currentSession = session;
      renderCrisisBanner(session.safety);
    } else {
      const session = await api(`/sessions/${state.currentSession.id}`, {
        method: "PATCH",
        body: JSON.stringify({ content, status: "draft" }),
      });
      state.currentSession = session;
      renderCrisisBanner(session.safety);
    }
    if (statusEl) statusEl.textContent = "Draft saved";
  } catch (err) {
    if (statusEl) statusEl.textContent = "Autosave paused";
  }
}

async function submitVentingEntry() {
  const content = document.getElementById("vent-textarea").value.trim();
  if (!content) {
    showNotice("Please write out your thoughts before submitting.", "error", "vent-alert");
    return;
  }

  const submitBtn = document.getElementById("submit-vent-btn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Saving Session...";

  try {
    if (state.currentSession) {
      state.currentSession = await api(`/sessions/${state.currentSession.id}`, {
        method: "PATCH",
        body: JSON.stringify({ content, status: "completed" }),
      });
    } else {
      state.currentSession = await api("/sessions", {
        method: "POST",
        body: JSON.stringify({
          content,
          initial_mood: state.preMood,
          status: "completed",
        }),
      });
    }
    renderCrisisBanner(state.currentSession.safety);
    submitBtn.disabled = false;
    submitBtn.textContent = "Release & Decompress";
    showDecompressView();
  } catch (err) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Release & Decompress";
    showNotice(err.message, "error", "vent-alert");
  }
}

async function showDecompressView() {
  showView("reframe");
  const loadingBox = document.getElementById("reframe-loading");
  const resultBox = document.getElementById("reframe-result");
  const userVentDisplay = document.getElementById("reframe-user-vent");
  const aiOutputDisplay = document.getElementById("reframe-ai-output");

  loadingBox.style.display = "flex";
  resultBox.style.display = "none";
  userVentDisplay.textContent = state.currentSession.content;

  try {
    const reflection = await api(`/sessions/${state.currentSession.id}/reflect`, {
      method: "POST",
      body: JSON.stringify({ save_immediately: false }),
    });
    state.currentSession.reflection = reflection;
    loadingBox.style.display = "none";
    resultBox.style.display = "block";
    aiOutputDisplay.textContent = reflection.content;
  } catch (err) {
    loadingBox.style.display = "none";
    resultBox.style.display = "block";
    aiOutputDisplay.textContent = `The reflection assistant is temporarily unavailable. Your original session is still saved. You can try reframing again from History.`;
  }
}

async function keepGeneratedReflection() {
  if (!state.currentSession) return;
  try {
    const reflection = await api(`/sessions/${state.currentSession.id}/reflection`, {
      method: "PATCH",
      body: JSON.stringify({ is_saved: true }),
    });
    state.currentSession.reflection = reflection;
    showNotice("Reflection saved with this session.", "success");
  } catch (err) {
    showNotice(err.message, "error");
  }
}

async function discardGeneratedReflection() {
  if (!state.currentSession) return;
  try {
    await api(`/sessions/${state.currentSession.id}/reflection`, { method: "DELETE" });
    state.currentSession.reflection = null;
    const output = document.getElementById("reframe-ai-output");
    if (output) output.textContent = "Reflection discarded. Your original writing is unchanged.";
    const detailBox = document.getElementById("detail-reflection-box");
    if (detailBox && state.activeView === "session-detail") detailBox.style.display = "none";
    showNotice("Reflection discarded. Your original session is intact.", "success");
  } catch (err) {
    showNotice(err.message, "error");
  }
}

async function keepAndContinue() {
  await keepGeneratedReflection();
  proceedToPostCheckin();
}

function proceedToPostCheckin() {
  showView("post-checkin");
}

async function submitPostCheckin() {
  if (!state.postMood) {
    showNotice("Please select your current emotional state to complete your reset.", "error", "post-checkin-alert");
    return;
  }

  try {
    await api(`/sessions/${state.currentSession.id}/check-ins`, {
      method: "POST",
      body: JSON.stringify({
        stage: "after",
        value: state.postMood,
      }),
    });
    showView("dashboard");
    showNotice("Reset saved. We'll invite a 3, 5, and 7 day follow-up when those days arrive.", "success", "dash-alert");
  } catch (err) {
    showNotice(err.message, "error", "post-checkin-alert");
  }
}

async function loadDashboard() {
  try {
    const data = await api("/sessions");
    const followups = await api("/reset-followups");
    const countEl = document.getElementById("stat-total-sessions");
    const pendingEl = document.getElementById("stat-pending-resets");
    const recentList = document.getElementById("dashboard-recent-list");

    if (countEl) countEl.textContent = data.total;
    if (pendingEl) pendingEl.textContent = followups.pending.length;

    if (recentList) {
      if (data.sessions.length === 0) {
        recentList.innerHTML = `<p style="color: var(--text-muted); text-align: center; padding: 2rem 0;">No venting sessions yet. When life gets heavy, air it out above.</p>`;
      } else {
        recentList.innerHTML = data.sessions.slice(0, 3).map(renderSessionCard).join("");
      }
    }
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

async function loadHistory() {
  const historyList = document.getElementById("history-sessions-list");
  if (!historyList) return;

  historyList.innerHTML = "<p style='color: var(--text-muted);'>Loading sessions...</p>";

  try {
    const data = await api("/sessions");
    if (data.sessions.length === 0) {
      historyList.innerHTML = "<p style='color: var(--text-muted); text-align: center; padding: 3rem 0;'>No sessions found. Start a new session whenever you are ready.</p>";
    } else {
      historyList.innerHTML = data.sessions.map(renderSessionCard).join("");
    }
  } catch (err) {
    historyList.innerHTML = `<p style="color: var(--accent-rose);">Failed to load history: ${err.message}</p>`;
  }
}

async function loadResetTracking() {
  const pendingList = document.getElementById("reset-pending-list");
  const historyList = document.getElementById("reset-history-list");
  try {
    const followups = await api("/reset-followups");
    const history = await api("/check-ins");

    if (!followups.pending.length) {
      pendingList.innerHTML = `<p style="color: var(--text-muted);">No follow-ups due yet. Come back 3, 5, or 7 days after a session.</p>`;
    } else {
      pendingList.innerHTML = followups.pending
        .map(
          (item) => `
        <div class="session-card" onclick="viewSessionDetail(${item.session_id})">
          <div class="session-header">
            <span>${FOLLOWUP_LABELS[item.stage] || item.stage} · due ${new Date(item.due_at).toLocaleDateString()}</span>
          </div>
          <div class="session-preview">"${escapeHtml(item.session_preview)}"</div>
        </div>`
        )
        .join("");
    }

    if (!history.check_ins.length) {
      historyList.innerHTML = `<p style="color: var(--text-muted);">No check-ins recorded yet.</p>`;
    } else {
      historyList.innerHTML = history.check_ins
        .map(
          (c) => `
        <div class="checkin-row">
          <span class="mood-badge">${escapeHtml(c.stage)}</span>
          <span>${escapeHtml(c.value)}</span>
          <span style="color: var(--text-muted); font-size: 0.85rem;">${new Date(c.created_at).toLocaleString()}</span>
        </div>`
        )
        .join("");
    }
  } catch (err) {
    pendingList.innerHTML = `<p style="color: var(--accent-rose);">${escapeHtml(err.message)}</p>`;
  }
}

function renderSessionCard(session) {
  const dateStr = new Date(session.created_at).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const preCheckin = (session.check_ins || []).find((c) => c.stage === "before");
  const postCheckin = (session.check_ins || []).find((c) => c.stage === "after");
  const followups = (session.check_ins || []).filter((c) => c.stage.startsWith("reset_"));
  const savedReflection = session.reflection && session.reflection.is_saved;

  return `
    <div class="session-card" onclick="viewSessionDetail(${session.id})">
      <div class="session-header">
        <span>🕒 ${dateStr}${session.status === "draft" ? " · Draft" : ""}</span>
        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteSessionById(${session.id})">Delete</button>
      </div>
      <div class="session-preview">
        "${escapeHtml(session.content)}"
      </div>
      <div class="session-footer">
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          ${preCheckin ? `<span class="mood-badge">Before: ${escapeHtml(preCheckin.value)}</span>` : ""}
          ${postCheckin ? `<span class="mood-badge" style="background: rgba(52, 211, 153, 0.15); color: #6ee7b7;">After: ${escapeHtml(postCheckin.value)}</span>` : ""}
          ${followups.map((f) => `<span class="mood-badge">${FOLLOWUP_LABELS[f.stage] || f.stage}</span>`).join("")}
        </div>
        ${savedReflection ? `<span class="mood-badge" style="background: rgba(56, 189, 248, 0.15); color: #7dd3fc;">✓ Reflected</span>` : ""}
      </div>
    </div>
  `;
}

function followupStageDue(session, stage, days) {
  const created = new Date(session.created_at).getTime();
  const due = created + days * 24 * 60 * 60 * 1000;
  const has = (session.check_ins || []).some((c) => c.stage === stage);
  return !has && Date.now() >= due;
}

async function viewSessionDetail(sessionId) {
  try {
    const session = await api(`/sessions/${sessionId}`);
    state.currentSession = session;

    document.getElementById("detail-timestamp").textContent = new Date(session.created_at).toLocaleString();
    document.getElementById("detail-content").textContent = session.content;

    const preCheckin = (session.check_ins || []).find((c) => c.stage === "before");
    const postCheckin = (session.check_ins || []).find((c) => c.stage === "after");
    document.getElementById("detail-pre-mood").textContent = preCheckin ? preCheckin.value : "None recorded";
    document.getElementById("detail-post-mood").textContent = postCheckin ? postCheckin.value : "None recorded";
    const followText = (session.check_ins || [])
      .filter((c) => c.stage.startsWith("reset_"))
      .map((c) => `${FOLLOWUP_LABELS[c.stage] || c.stage}: ${c.value}`)
      .join(" · ");
    document.getElementById("detail-followup-moods").textContent = followText || "";

    const refBox = document.getElementById("detail-reflection-box");
    const refText = document.getElementById("detail-reflection-content");
    const refBtn = document.getElementById("detail-request-reframing-btn");
    const refActions = document.getElementById("detail-reflection-actions");
    const refBadge = document.getElementById("detail-reflection-badge");

    if (session.reflection) {
      refBox.style.display = "block";
      refText.textContent = session.reflection.content;
      refBtn.style.display = session.reflection.is_saved ? "none" : "inline-flex";
      refActions.style.display = session.reflection.is_saved ? "none" : "flex";
      refBadge.textContent = session.reflection.is_saved ? "✓ Saved reflection" : "Draft reflection (not retained)";
    } else {
      refBox.style.display = "none";
      refBtn.style.display = "inline-flex";
      refActions.style.display = "none";
    }

    const dueStage =
      (followupStageDue(session, "reset_3d", 3) && "reset_3d") ||
      (followupStageDue(session, "reset_5d", 5) && "reset_5d") ||
      (followupStageDue(session, "reset_7d", 7) && "reset_7d") ||
      null;
    renderFollowupPicker(dueStage);

    showView("session-detail");
  } catch (err) {
    showNotice(err.message, "error");
  }
}

function renderFollowupPicker(stage) {
  const box = document.getElementById("detail-followup-box");
  const picker = document.getElementById("followup-mood-picker");
  const copy = document.getElementById("detail-followup-copy");
  state.pendingFollowupStage = stage;
  if (!stage) {
    box.style.display = "none";
    return;
  }
  box.style.display = "block";
  copy.textContent = `This ${FOLLOWUP_LABELS[stage]} check-in is due. How does this situation sit with you now?`;
  picker.innerHTML = FOLLOWUP_MOODS.map(
    (m) => `
    <div class="mood-btn" data-mood="${escapeHtml(m.value)}">
      <span class="emoji">${m.emoji}</span>
      <span class="label">${m.label}</span>
    </div>`
  ).join("");
  picker.querySelectorAll(".mood-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      picker.querySelectorAll(".mood-btn").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      try {
        await api(`/sessions/${state.currentSession.id}/check-ins`, {
          method: "POST",
          body: JSON.stringify({ stage, value: btn.dataset.mood }),
        });
        showNotice("Follow-up check-in saved.", "success");
        viewSessionDetail(state.currentSession.id);
      } catch (err) {
        showNotice(err.message, "error");
      }
    });
  });
}

async function triggerDetailReframing() {
  if (!state.currentSession) return;
  const btn = document.getElementById("detail-request-reframing-btn");
  btn.disabled = true;
  btn.textContent = "Generating Reflection...";

  try {
    const reflection = await api(`/sessions/${state.currentSession.id}/reflect`, {
      method: "POST",
      body: JSON.stringify({ save_immediately: false }),
    });
    state.currentSession.reflection = reflection;
    document.getElementById("detail-reflection-box").style.display = "block";
    document.getElementById("detail-reflection-content").textContent = reflection.content;
    document.getElementById("detail-reflection-actions").style.display = "flex";
    document.getElementById("detail-reflection-badge").textContent = "Draft reflection (not retained)";
    btn.style.display = "none";
  } catch (err) {
    showNotice(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Request Decompress & Reframe";
  }
}

async function deleteSessionById(sessionId) {
  if (!confirm("Are you sure you want to permanently delete this session? This action cannot be undone.")) {
    return;
  }
  try {
    await api(`/sessions/${sessionId}`, { method: "DELETE" });
    if (state.activeView === "session-detail") {
      showView("history");
    } else {
      loadHistory();
      loadDashboard();
    }
  } catch (err) {
    alert(`Could not delete session: ${err.message}`);
  }
}

function loadSettings() {
  if (state.currentUser) {
    document.getElementById("settings-user-email").textContent = state.currentUser.email;
    document.getElementById("settings-user-id").textContent = state.currentUser.id;
  }
}

async function confirmDeleteAccount() {
  const confirmed = confirm(
    "WARNING: Are you absolutely sure you want to delete your AirSpace account?\n\nThis will permanently erase all your venting sessions, reflections, and emotional tracking data. This action is irreversible."
  );
  if (!confirmed) return;

  try {
    await api("/account", { method: "DELETE" });
    state.token = null;
    state.currentUser = null;
    localStorage.removeItem("airspace_token");
    updateNav();
    showView("landing");
    alert("Your account and all associated data have been permanently deleted.");
  } catch (err) {
    alert(`Failed to delete account: ${err.message}`);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-nav]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      showView(btn.dataset.nav);
    });
  });

  document.querySelectorAll("#pre-mood-picker .mood-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#pre-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.preMood = btn.dataset.mood;
    });
  });

  document.querySelectorAll("#post-mood-picker .mood-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#post-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.postMood = btn.dataset.mood;
    });
  });

  const ventTextarea = document.getElementById("vent-textarea");
  if (ventTextarea) {
    ventTextarea.addEventListener("input", () => {
      const len = ventTextarea.value.length;
      const words = ventTextarea.value.trim().split(/\s+/).filter(Boolean).length;
      document.getElementById("vent-char-count").textContent = `${words} words · ${len} characters`;
      clearTimeout(state.autosaveTimer);
      state.autosaveTimer = setTimeout(autosaveDraft, 1500);
    });
  }

  checkAuth();
});
