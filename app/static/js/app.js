/* ==========================================================================
   AIRSPACE — Frontend Controller & State Machine
   ========================================================================== */

const state = {
  currentUser: null,
  token: localStorage.getItem("airspace_token") || null,
  currentSession: null,
  preMood: null,
  postMood: null,
  activeView: "landing"
};

// API Client Helper
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
    throw new Error(errorMsg);
  }

  return data;
}

// Router & View Switcher
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

  // Lifecycle hooks per view
  if (viewName === "dashboard") loadDashboard();
  if (viewName === "history") loadHistory();
  if (viewName === "settings") loadSettings();
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

// Authentication Handlers
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
    logout();
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
    // Auto-login after registration
    await loginUser(email, password);
  } catch (err) {
    showNotice(err.message, "error", "register-alert");
  }
}

async function logout() {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch (e) {}
  state.token = null;
  state.currentUser = null;
  localStorage.removeItem("airspace_token");
  updateNav();
  showView("landing");
}

// Flow: Vent & Decompress Journey
function startNewSessionFlow() {
  state.currentSession = null;
  state.preMood = null;
  state.postMood = null;

  // Reset mood buttons
  document.querySelectorAll("#pre-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
  document.querySelectorAll("#post-mood-picker .mood-btn").forEach((b) => b.classList.remove("selected"));
  document.getElementById("vent-textarea").value = "";
  document.getElementById("vent-char-count").textContent = "0 characters";

  showView("pre-checkin");
}

async function submitPreCheckinAndContinue() {
  if (!state.preMood) {
    showNotice("Please select how you are feeling right now before continuing.", "error", "pre-checkin-alert");
    return;
  }
  showView("air-it-out");
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
    const session = await api("/sessions", {
      method: "POST",
      body: JSON.stringify({
        content: content,
        initial_mood: state.preMood,
      }),
    });
    state.currentSession = session;
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
      body: JSON.stringify({}),
    });
    state.currentSession.reflection = reflection;

    loadingBox.style.display = "none";
    resultBox.style.display = "block";
    aiOutputDisplay.textContent = reflection.content;
  } catch (err) {
    loadingBox.style.display = "none";
    resultBox.style.display = "block";
    aiOutputDisplay.textContent = `Note: The reflection assistant is taking a moment to recalibrate (${err.message}). Your session has been safely preserved! You can try reframing again or review it anytime in History.`;
  }
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
    showNotice("Your emotional reset is complete! Your session is safely stored in History.", "success", "dash-alert");
  } catch (err) {
    showNotice(err.message, "error", "post-checkin-alert");
  }
}

// Dashboard & History
async function loadDashboard() {
  try {
    const data = await api("/sessions");
    const countEl = document.getElementById("stat-total-sessions");
    const recentList = document.getElementById("dashboard-recent-list");

    if (countEl) countEl.textContent = data.total;

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

function renderSessionCard(session) {
  const dateStr = new Date(session.created_at).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const preCheckin = session.check_ins.find((c) => c.stage === "before");
  const postCheckin = session.check_ins.find((c) => c.stage === "after");

  return `
    <div class="session-card" onclick="viewSessionDetail(${session.id})">
      <div class="session-header">
        <span>🕒 ${dateStr}</span>
        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteSessionById(${session.id})">Delete</button>
      </div>
      <div class="session-preview">
        "${escapeHtml(session.content)}"
      </div>
      <div class="session-footer">
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
          ${preCheckin ? `<span class="mood-badge">Before: ${escapeHtml(preCheckin.value)}</span>` : ""}
          ${postCheckin ? `<span class="mood-badge" style="background: rgba(52, 211, 153, 0.15); color: #6ee7b7;">After: ${escapeHtml(postCheckin.value)}</span>` : ""}
        </div>
        ${session.reflection ? `<span class="mood-badge" style="background: rgba(56, 189, 248, 0.15); color: #7dd3fc;">✓ Reflected</span>` : ""}
      </div>
    </div>
  `;
}

async function viewSessionDetail(sessionId) {
  try {
    const session = await api(`/sessions/${sessionId}`);
    state.currentSession = session;

    document.getElementById("detail-timestamp").textContent = new Date(session.created_at).toLocaleString();
    document.getElementById("detail-content").textContent = session.content;

    const preCheckin = session.check_ins.find((c) => c.stage === "before");
    const postCheckin = session.check_ins.find((c) => c.stage === "after");
    document.getElementById("detail-pre-mood").textContent = preCheckin ? preCheckin.value : "None recorded";
    document.getElementById("detail-post-mood").textContent = postCheckin ? postCheckin.value : "None recorded";

    const refBox = document.getElementById("detail-reflection-box");
    const refText = document.getElementById("detail-reflection-content");
    const refBtn = document.getElementById("detail-request-reframing-btn");

    if (session.reflection) {
      refBox.style.display = "block";
      refText.textContent = session.reflection.content;
      refBtn.style.display = "none";
    } else {
      refBox.style.display = "none";
      refBtn.style.display = "inline-flex";
    }

    showView("session-detail");
  } catch (err) {
    showNotice(err.message, "error");
  }
}

async function triggerDetailReframing() {
  if (!state.currentSession) return;
  const btn = document.getElementById("detail-request-reframing-btn");
  btn.disabled = true;
  btn.textContent = "Generating Reflection...";

  try {
    const reflection = await api(`/sessions/${state.currentSession.id}/reflect`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.currentSession.reflection = reflection;
    document.getElementById("detail-reflection-box").style.display = "block";
    document.getElementById("detail-reflection-content").textContent = reflection.content;
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
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Global Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  // Navigation Buttons
  document.querySelectorAll("[data-nav]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const target = btn.dataset.nav;
      showView(target);
    });
  });

  // Mood Pickers (Pre & Post)
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

  // Vent Textarea character counting
  const ventTextarea = document.getElementById("vent-textarea");
  if (ventTextarea) {
    ventTextarea.addEventListener("input", () => {
      const len = ventTextarea.value.length;
      const words = ventTextarea.value.trim().split(/\s+/).filter(Boolean).length;
      document.getElementById("vent-char-count").textContent = `${words} words · ${len} characters`;
    });
  }

  // Initial Auth Check
  checkAuth();
});
