// Local dev runs the frontend (5173) and backend (5174) as two separate static/Python
// servers, so it needs an absolute cross-origin URL. In production on Vercel, the frontend
// and the /api function deploy under the same origin, so a relative path is correct there.
const BACKEND_URL = location.port === "5173" ? "http://localhost:5174" : "";

const PLATFORMS = [
  {
    key: "google",
    name: "Google",
    url: "https://www.google.com/maps?cid=190491404382669009",
    instructions:
      "When you click Approve, we'll copy this text and open Google's page for The Liberty " +
      "Group of Nevada in a new tab. Once there, click \"Write a review,\" then paste " +
      "(Ctrl+V or Cmd+V) into the box that appears.",
  },
  {
    key: "facebook",
    name: "Facebook",
    url: "https://www.facebook.com/TheLibertyGroupofNV/reviews",
    instructions:
      "When you click Approve, we'll copy this text and open our Facebook Reviews tab in a " +
      "new tab. Once there, click to add a recommendation, then paste (Ctrl+V or Cmd+V) into " +
      "the box that appears. You'll need to be logged into Facebook.",
  },
  {
    key: "bbb",
    name: "BBB",
    url: "https://www.bbb.org/us/nv/reno/profile/business-brokers/the-liberty-group-of-nevada-llc-1166-90023748",
    instructions:
      "When you click Approve, we'll copy this text and open our BBB profile in a new tab. " +
      "Once there, look for \"Leave a Review\" (or similar), then paste (Ctrl+V or Cmd+V) into " +
      "the box that appears.",
  },
];

const QUESTIONS = [
  {
    id: "goal",
    text: "What did you come to The Liberty Group of Nevada for — buying a business, selling a business, a valuation, or something else?",
  },
  { id: "team", text: "Which team member(s) did you primarily work with?" },
  { id: "standout", text: "What stood out most about working with them or the process?" },
  {
    id: "surprise",
    text: "Was there anything that surprised you along the way — good or challenging?",
  },
  { id: "outcome", text: "How did things turn out, and how do you feel about it?" },
  {
    id: "recommend",
    text: "Would you recommend The Liberty Group of Nevada to someone else buying or selling a business? Why or why not?",
  },
  { id: "more", text: "Anything else you'd like to add?", optional: true },
];

const STORAGE_KEY = "lgnReviewSession";

function defaultChatState() {
  return {
    history: [],
    index: 0,
    answers: {},
    contactDone: false,
    contact: { name: "", email: "" },
  };
}

function loadState() {
  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (raw) {
    const parsed = JSON.parse(raw);
    if (!parsed.chat) parsed.chat = defaultChatState();
    if (!parsed.generatedDrafts) parsed.generatedDrafts = {};
    return parsed;
  }
  return {
    screen: "landing",
    usedPlatforms: [],
    activePlatform: null,
    generatedDrafts: {},
    chat: defaultChatState(),
  };
}

function saveState() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

let state = loadState();

function showScreen(name) {
  document.querySelectorAll(".screen").forEach((el) => {
    el.hidden = el.dataset.screen !== name;
  });
  state.screen = name;
  saveState();
}

function platformByKey(key) {
  return PLATFORMS.find((p) => p.key === key);
}

function currentQuestion() {
  return QUESTIONS[state.chat.index];
}

function renderChatLog() {
  const log = document.getElementById("chat-log");
  log.innerHTML = "";
  state.chat.history.forEach((entry) => {
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble " + entry.role;
    bubble.textContent = entry.text;
    log.appendChild(bubble);
  });
  log.scrollTop = log.scrollHeight;
}

function updateChatControls() {
  const inputRow = document.getElementById("chat-input-row");
  const contactRow = document.getElementById("contact-row");
  const continueBtn = document.getElementById("chat-continue-btn");
  const skipBtn = document.getElementById("skip-btn");
  const q = currentQuestion();

  if (q) {
    inputRow.hidden = false;
    contactRow.hidden = true;
    continueBtn.hidden = true;
    skipBtn.hidden = !q.optional;
    document.getElementById("chat-input").value = "";
  } else if (!state.chat.contactDone) {
    inputRow.hidden = true;
    contactRow.hidden = false;
    continueBtn.hidden = true;
    document.getElementById("contact-name").value = state.chat.contact.name;
    document.getElementById("contact-email").value = state.chat.contact.email;
  } else {
    inputRow.hidden = true;
    contactRow.hidden = true;
    continueBtn.hidden = false;
  }
}

function renderChatScreen() {
  if (state.chat.history.length === 0) {
    const q = currentQuestion();
    if (q) state.chat.history.push({ role: "bot", text: q.text });
    saveState();
  }
  renderChatLog();
  updateChatControls();
}

function submitAnswer(rawText) {
  const q = currentQuestion();
  if (!q) return;
  const text = rawText.trim();
  if (!text && !q.optional) return;

  state.chat.history.push({ role: "user", text: text || "(skipped)" });
  state.chat.answers[q.id] = text;
  state.chat.index += 1;

  const next = currentQuestion();
  if (next) {
    state.chat.history.push({ role: "bot", text: next.text });
  } else {
    state.chat.history.push({
      role: "bot",
      text: "Last thing — want to leave your name and email? Totally optional, just for our records.",
    });
  }

  saveState();
  renderChatLog();
  updateChatControls();
}

function renderPickerScreen() {
  const list = document.getElementById("platform-list");
  const offerMore = document.getElementById("offer-more");
  const confirmation = document.getElementById("picker-confirmation");
  list.innerHTML = "";

  const hasPostedAny = state.usedPlatforms.length > 0;
  const allUsed = state.usedPlatforms.length === PLATFORMS.length;

  offerMore.hidden = !hasPostedAny || allUsed;
  confirmation.hidden = !hasPostedAny;

  if (allUsed) {
    const done = document.createElement("p");
    done.textContent = "You've shared this on every site — thank you!";
    list.appendChild(done);
    return;
  }

  PLATFORMS.forEach((platform) => {
    const posted = state.usedPlatforms.includes(platform.key);
    const row = document.createElement(posted ? "div" : "button");
    row.className = "platform-option" + (posted ? " posted" : "");

    const label = document.createElement("span");
    label.className = "platform-name";
    label.textContent = platform.name;
    row.appendChild(label);

    const status = document.createElement("span");
    status.className = "platform-status";
    status.textContent = posted ? "Posted ✓" : "";
    row.appendChild(status);

    if (!posted) {
      row.addEventListener("click", () => selectPlatform(platform.key));
    }

    list.appendChild(row);
  });
}

function selectPlatform(key) {
  state.activePlatform = key;
  saveState();
  showScreen("draft");
  renderDraftScreen();
}

async function renderDraftScreen() {
  const platform = platformByKey(state.activePlatform);
  document.getElementById("draft-heading-platform").textContent = platform.name;
  document.getElementById("draft-instructions").textContent = platform.instructions;

  const isRepeat = state.usedPlatforms.length > 0;
  const repeatNotice = document.getElementById("repeat-notice");
  repeatNotice.hidden = !isRepeat;
  repeatNotice.textContent = isRepeat
    ? `Since you're sharing this on another site, we've reworded it a bit so it's not identical to what you posted before.`
    : "";

  const textarea = document.getElementById("draft-text");
  const approveBtn = document.querySelector('[data-action="approve-draft"]');

  textarea.value = "Writing your review draft…";
  textarea.disabled = true;
  approveBtn.disabled = true;

  const priorDrafts = state.usedPlatforms
    .map((key) => state.generatedDrafts[key])
    .filter(Boolean);

  try {
    const response = await fetch(`${BACKEND_URL}/api/generate-review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        answers: state.chat.answers,
        platform: platform.key,
        priorDrafts,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Generation failed");
    textarea.value = data.review;
  } catch (err) {
    console.warn("Review generation failed", err);
    textarea.value = "";
    textarea.placeholder =
      "We couldn't generate a draft automatically — go ahead and write your review here in your own words.";
  } finally {
    textarea.disabled = false;
    approveBtn.disabled = false;
  }
}

async function approveDraft() {
  const platform = platformByKey(state.activePlatform);
  const text = document.getElementById("draft-text").value;

  try {
    await navigator.clipboard.writeText(text);
  } catch (err) {
    console.warn("Clipboard copy failed", err);
  }

  window.open(platform.url, "_blank");

  state.generatedDrafts[platform.key] = text;
  if (!state.usedPlatforms.includes(platform.key)) {
    state.usedPlatforms.push(platform.key);
  }
  state.activePlatform = null;
  saveState();

  renderPickerScreen();
  showScreen("picker");
}

document.querySelector('[data-action="start"]').addEventListener("click", () => {
  renderChatScreen();
  showScreen("chat");
});

document.getElementById("send-btn").addEventListener("click", () => {
  submitAnswer(document.getElementById("chat-input").value);
});

document.getElementById("chat-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitAnswer(document.getElementById("chat-input").value);
  }
});

document.getElementById("skip-btn").addEventListener("click", () => {
  submitAnswer("");
});

document.getElementById("contact-continue-btn").addEventListener("click", () => {
  state.chat.contact.name = document.getElementById("contact-name").value.trim();
  state.chat.contact.email = document.getElementById("contact-email").value.trim();
  state.chat.contactDone = true;

  const providedAny = state.chat.contact.name || state.chat.contact.email;
  state.chat.history.push({ role: "user", text: providedAny ? "Thanks, got it!" : "(skipped)" });

  saveState();
  renderChatLog();
  updateChatControls();
});

document.getElementById("chat-continue-btn").addEventListener("click", () => {
  renderPickerScreen();
  showScreen("picker");
});

const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById("mic-btn");
let recognizer = null;
let listening = false;

if (!SpeechRecognitionCtor) {
  micBtn.disabled = true;
  micBtn.title = "Voice input isn't supported in this browser — please type your answer.";
} else {
  recognizer = new SpeechRecognitionCtor();
  recognizer.continuous = false;
  recognizer.interimResults = false;
  recognizer.lang = "en-US";

  recognizer.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById("chat-input");
    input.value = (input.value ? input.value + " " : "") + transcript;
  });

  recognizer.addEventListener("end", () => {
    listening = false;
    micBtn.classList.remove("listening");
  });

  recognizer.addEventListener("error", () => {
    listening = false;
    micBtn.classList.remove("listening");
  });

  micBtn.addEventListener("click", () => {
    if (listening) {
      recognizer.stop();
      return;
    }
    listening = true;
    micBtn.classList.add("listening");
    recognizer.start();
  });
}

document.querySelector('[data-action="approve-draft"]').addEventListener("click", approveDraft);

if (state.screen === "draft" && state.activePlatform) {
  renderDraftScreen();
} else if (state.screen === "chat") {
  renderChatScreen();
} else {
  renderPickerScreen();
}
showScreen(state.screen);
