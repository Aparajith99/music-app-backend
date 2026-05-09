/**
 * MusicCloud Frontend Application
 * Handles authentication, music queries, and subscription management.
 */

// ============ Configuration ============
// Backend options — update the URLs below with your actual deployment endpoints.
const BACKENDS = {
  EC2:    "http://54.88.173.155",
  ECS:   "http://music-app-alb-182039008.us-east-1.elb.amazonaws.com",
  Lambda: "https://imum9rqox0.execute-api.us-east-1.amazonaws.com/prod",
};

// Resolve API_BASE: saved choice → localStorage, fallback → first entry.
function getApiBase() {
  const saved = localStorage.getItem("backend");
  if (saved && BACKENDS[saved]) return BACKENDS[saved];
  return Object.values(BACKENDS)[0];
}

let API_BASE = getApiBase();

// ============ Session Management ============
const Session = {
  get() {
    return {
      email: sessionStorage.getItem("email"),
      userName: sessionStorage.getItem("userName"),
    };
  },
  set(email, userName) {
    sessionStorage.setItem("email", email);
    sessionStorage.setItem("userName", userName);
  },
  clear() {
    sessionStorage.removeItem("email");
    sessionStorage.removeItem("userName");
  },
  isLoggedIn() {
    return !!sessionStorage.getItem("email");
  },
};

// Track subscribed title_year keys for UI state
const subscribedKeys = new Set();

// ============ Initialisation ============
document.addEventListener("DOMContentLoaded", () => {
  initBackendSwitcher();           // mount dropdown on every page
  const page = document.body.dataset.page;
  if (page === "login") initLoginPage();
  else if (page === "register") initRegisterPage();
  else if (page === "main") initMainPage();
});

// ============ Backend Switcher ============
function initBackendSwitcher() {
  // Build the floating widget
  const wrapper = document.createElement("div");
  wrapper.id = "backend-switcher";
  wrapper.innerHTML = `
    <label for="backend-select">⚡ Backend</label>
    <select id="backend-select">
      ${Object.keys(BACKENDS)
        .map(
          (key) =>
            `<option value="${key}"${key === (localStorage.getItem("backend") || Object.keys(BACKENDS)[0]) ? " selected" : ""}>${key}</option>`
        )
        .join("")}
    </select>
    <span id="backend-indicator" class="indicator"></span>
  `;
  document.body.appendChild(wrapper);

  const select = document.getElementById("backend-select");
  const indicator = document.getElementById("backend-indicator");

  // Set initial indicator colour
  updateIndicator(indicator, select.value);

  select.addEventListener("change", () => {
    localStorage.setItem("backend", select.value);
    API_BASE = BACKENDS[select.value];
    updateIndicator(indicator, select.value);
    // Reload data on the main page so the new backend takes effect immediately
    if (document.body.dataset.page === "main" && Session.isLoggedIn()) {
      loadSubscriptions();
    }
  });
}

function updateIndicator(el, key) {
  const colours = { EC2: "#f59e0b", ECS: "#3b82f6", Lambda: "#10b981" };
  el.style.background = colours[key] || "#888";
  el.title = `Connected to ${key}`;
}

// ============ Login Page ============
function initLoginPage() {
  if (Session.isLoggedIn()) {
    window.location.href = "main.html";
    return;
  }
  document.getElementById("login-form").addEventListener("submit", handleLogin);
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  clearMessage("login-message");

  if (!email || !password) {
    showMessage("login-message", "Please fill in all fields.", "error");
    return;
  }

  setLoading("login-btn", true, "Logging in…");

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();

    if (data.success) {
      Session.set(data.email, data.user_name);
      window.location.href = "main.html";
    } else {
      showMessage("login-message", data.message, "error");
    }
  } catch (err) {
    showMessage("login-message", "Network error. Please try again.", "error");
  } finally {
    setLoading("login-btn", false, "Login");
  }
}

// ============ Register Page ============
function initRegisterPage() {
  if (Session.isLoggedIn()) {
    window.location.href = "main.html";
    return;
  }
  document
    .getElementById("register-form")
    .addEventListener("submit", handleRegister);
}

async function handleRegister(e) {
  e.preventDefault();
  const email = document.getElementById("register-email").value.trim();
  const username = document.getElementById("register-username").value.trim();
  const password = document.getElementById("register-password").value;

  clearMessage("register-message");

  if (!email || !username || !password) {
    showMessage("register-message", "Please fill in all fields.", "error");
    return;
  }

  setLoading("register-btn", true, "Registering…");

  try {
    const res = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, username, password }),
    });
    const data = await res.json();

    if (data.success) {
      showMessage(
        "register-message",
        "Registration successful! Redirecting to login…",
        "success"
      );
      setTimeout(() => (window.location.href = "index.html"), 1500);
    } else {
      showMessage("register-message", data.message, "error");
    }
  } catch (err) {
    showMessage(
      "register-message",
      "Network error. Please try again.",
      "error"
    );
  } finally {
    setLoading("register-btn", false, "Register");
  }
}

// ============ Main Page ============
function initMainPage() {
  if (!Session.isLoggedIn()) {
    window.location.href = "index.html";
    return;
  }

  const { userName } = Session.get();
  document.getElementById("user-name-display").textContent = userName;

  loadSubscriptions();

  document.getElementById("query-form").addEventListener("submit", handleQuery);
  document.getElementById("logout-btn").addEventListener("click", handleLogout);
}

// ---------- Subscriptions ----------
async function loadSubscriptions() {
  const { email } = Session.get();
  const container = document.getElementById("subscriptions-container");
  container.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch(
      `${API_BASE}/subscriptions/${encodeURIComponent(email)}`
    );
    const data = await res.json();

    if (data.success && data.items && data.items.length > 0) {
      container.innerHTML = "";
      subscribedKeys.clear();
      data.items.forEach((item) => {
        const key = item.title_year || `${item.title}#${item.year}`;
        subscribedKeys.add(key);
        container.appendChild(createSongCard(item, "remove"));
      });
    } else {
      container.innerHTML =
        '<div class="empty-state"><div class="icon">🎧</div><p>No subscriptions yet. Discover music below!</p></div>';
    }
  } catch (err) {
    container.innerHTML =
      '<div class="empty-state"><p>Failed to load subscriptions.</p></div>';
  }
}

async function removeSubscription(titleYear, cardElement) {
  const { email } = Session.get();

  try {
    const res = await fetch(
      `${API_BASE}/subscriptions/${encodeURIComponent(email)}/${encodeURIComponent(titleYear)}`,
      { method: "DELETE" }
    );
    const data = await res.json();

    if (data.success) {
      subscribedKeys.delete(titleYear);

      // Animate out and remove just this card
      if (cardElement) {
        cardElement.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        cardElement.style.opacity = "0";
        cardElement.style.transform = "scale(0.9)";
        cardElement.addEventListener("transitionend", () => {
          cardElement.remove();
          // Show empty state if no cards left
          const container = document.getElementById("subscriptions-container");
          if (!container.querySelector(".song-card")) {
            container.innerHTML =
              '<div class="empty-state"><div class="icon">🎧</div><p>No subscriptions yet. Discover music below!</p></div>';
          }
        }, { once: true });
      }
      return true;
    }
  } catch (err) {
    alert("Failed to remove subscription. Please try again.");
  }
  return false;
}

// ---------- Query ----------
async function handleQuery(e) {
  e.preventDefault();

  const title = document.getElementById("query-title").value.trim();
  const artist = document.getElementById("query-artist").value.trim();
  const year = document.getElementById("query-year").value.trim();
  const album = document.getElementById("query-album").value.trim();

  clearMessage("query-message");

  if (!title && !artist && !year && !album) {
    showMessage(
      "query-message",
      "Please fill in at least one search field.",
      "error"
    );
    return;
  }

  const params = new URLSearchParams();
  if (title) params.append("title", title);
  if (artist) params.append("artist", artist);
  if (year) params.append("year", year);
  if (album) params.append("album", album);

  const container = document.getElementById("query-results");
  container.innerHTML = '<div class="loading-spinner"></div>';

  try {
    const res = await fetch(`${API_BASE}/query?${params.toString()}`);
    const data = await res.json();

    if (data.success && data.items && data.items.length > 0) {
      container.innerHTML = "";
      data.items.forEach((item) => {
        const titleYear = item.title_year || `${item.title}#${item.year}`;
        const actionType = subscribedKeys.has(titleYear) ? "remove" : "subscribe";
        container.appendChild(createSongCard(item, actionType));
      });
    } else {
      container.innerHTML = "";
      showMessage(
        "query-message",
        data.message || "No result is retrieved. Please query again",
        "error"
      );
    }
  } catch (err) {
    container.innerHTML = "";
    showMessage("query-message", "Network error. Please try again.", "error");
  }
}

// ---------- Subscribe ----------
async function subscribe(songData) {
  const { email } = Session.get();

  // Extract the clean filename from a presigned URL so the backend
  // can later regenerate a fresh presigned URL from it.
  const imageFilename = extractImageFilename(songData.image_url);

  try {
    const res = await fetch(`${API_BASE}/subscriptions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: email,
        artist: songData.artist,
        title: songData.title,
        year: songData.year,
        album: songData.album,
        image_url: imageFilename,
      }),
    });
    const data = await res.json();

    if (data.success) {
      const titleYear = songData.title_year || `${songData.title}#${songData.year}`;
      subscribedKeys.add(titleYear);

      // Append the new card directly instead of re-rendering everything
      const container = document.getElementById("subscriptions-container");
      // Clear the empty-state placeholder if present
      const emptyState = container.querySelector(".empty-state");
      if (emptyState) emptyState.remove();

      const newCard = createSongCard(songData, "remove");
      container.appendChild(newCard);
      return true;
    }
  } catch (err) {
    alert("Failed to subscribe. Please try again.");
  }
  return false;
}

// ---------- Logout ----------
function handleLogout() {
  Session.clear();
  window.location.href = "index.html";
}

// ============ UI Helpers ============

/**
 * Creates a song card DOM element.
 * @param {Object} song - Song data with title, artist, year, album, image_url, title_year
 * @param {"subscribe"|"remove"} actionType - Which button to show initially
 */
function createSongCard(song, actionType) {
  const card = document.createElement("div");
  card.className = "song-card";

  const img = document.createElement("img");
  img.className = "song-card-image";
  img.src = song.image_url;
  img.alt = `${song.artist} – ${song.title}`;
  img.loading = "lazy";
  // Fallback for broken images
  img.onerror = function () {
    this.src =
      "data:image/svg+xml," +
      encodeURIComponent(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" fill="%23333"><rect width="200" height="200"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="40" fill="%23666">🎵</text></svg>'
      );
  };

  const body = document.createElement("div");
  body.className = "song-card-body";
  body.innerHTML = `
    <div class="song-card-title">${escapeHtml(song.title)}</div>
    <div class="song-card-meta">🎤 ${escapeHtml(song.artist)}</div>
    <div class="song-card-meta">💿 ${escapeHtml(song.album)}</div>
    <div class="song-card-meta">📅 ${escapeHtml(song.year)}</div>
  `;

  const actionDiv = document.createElement("div");
  actionDiv.className = "song-card-action";

  const titleYear = song.title_year || `${song.title}#${song.year}`;

  /**
   * Renders the action button for the card.
   * In the subscriptions container the "Remove" button removes the card from the DOM.
   * In query results the button swaps between Subscribe ↔ Remove in-place.
   */
  function renderActionButton(type) {
    actionDiv.innerHTML = "";
    const btn = document.createElement("button");

    if (type === "subscribe") {
      btn.className = "btn btn-success btn-sm";
      btn.textContent = "Subscribe";
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Subscribing…";
        const ok = await subscribe(song);
        if (ok) {
          renderActionButton("remove");
        } else {
          btn.disabled = false;
          btn.textContent = "Subscribe";
        }
      });
    } else {
      btn.className = "btn btn-danger btn-sm";
      btn.textContent = "Remove";
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        btn.textContent = "Removing…";
        // If card is inside the subscriptions container, animate it out
        if (card.closest("#subscriptions-container")) {
          await removeSubscription(titleYear, card);
        } else {
          // Query results card: just unsubscribe and swap button back
          const ok = await removeSubscription(titleYear, null);
          if (ok) {
            // Also remove the corresponding card from the subscriptions container
            const subsContainer = document.getElementById("subscriptions-container");
            const subsCards = subsContainer.querySelectorAll(".song-card");
            subsCards.forEach((sc) => {
              if (sc.dataset.titleYear === titleYear) {
                sc.style.transition = "opacity 0.3s ease, transform 0.3s ease";
                sc.style.opacity = "0";
                sc.style.transform = "scale(0.9)";
                sc.addEventListener("transitionend", () => {
                  sc.remove();
                  if (!subsContainer.querySelector(".song-card")) {
                    subsContainer.innerHTML =
                      '<div class="empty-state"><div class="icon">🎧</div><p>No subscriptions yet. Discover music below!</p></div>';
                  }
                }, { once: true });
              }
            });
            renderActionButton("subscribe");
          } else {
            btn.disabled = false;
            btn.textContent = "Remove";
          }
        }
      });
    }

    actionDiv.appendChild(btn);
  }

  renderActionButton(actionType);
  card.dataset.titleYear = titleYear;
  card.append(img, body, actionDiv);
  return card;
}

/**
 * Extracts the S3 object key (filename) from a presigned URL.
 * The backend uses filename.split("/")[-1] to regenerate presigned URLs,
 * so we need to store just the clean filename.
 */
function extractImageFilename(url) {
  try {
    const parsed = new URL(url);
    // pathname is like /filename.jpg — remove leading slash
    return decodeURIComponent(parsed.pathname.split("/").pop());
  } catch {
    // If it's already a plain filename, return as-is
    return url;
  }
}

function showMessage(elementId, text, type) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = text;
  el.className = `message visible ${type}`;
}

function clearMessage(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.textContent = "";
  el.className = "message";
}

function setLoading(buttonId, isLoading, label) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;
  btn.disabled = isLoading;
  if (label) btn.textContent = label;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}
