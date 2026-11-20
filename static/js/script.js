(() => {
  "use strict";

  const form = document.getElementById("chat-form");
  const input = document.getElementById("question-input");
  const conversation = document.getElementById("conversation");
  const typing = document.getElementById("typing-indicator");
  const sendButton = document.getElementById("send-button");
  const clearButton = document.getElementById("clear-chat");
  const suggestionList = document.getElementById("suggestions");
  const welcomeMarkup = conversation.innerHTML;

  const timeNow = () => new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" }).format(new Date());
  document.querySelectorAll(".message-time").forEach((time) => { time.textContent = timeNow(); });

  function scrollToLatest() {
    conversation.scrollTop = conversation.scrollHeight;
  }

  function appendMessage({ text, from, category, confidence, suggestions, error }) {
    const row = document.createElement("article");
    row.className = `message-row ${from === "user" ? "user-row" : "bot-row"}${error ? " error-message" : ""}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    const icon = document.createElement("i");
    icon.className = from === "user" ? "fa-regular fa-user" : "fa-solid fa-sparkles";
    avatar.append(icon);

    const content = document.createElement("div");
    content.className = "message-content";
    const meta = document.createElement("div");
    meta.className = "message-meta";
    const name = document.createElement("span");
    name.textContent = from === "user" ? "You" : "FAQ Assistant";
    const time = document.createElement("time");
    time.className = "message-time";
    time.textContent = timeNow();
    meta.append(name, time);

    const bubble = document.createElement("div");
    bubble.className = `message-bubble ${from === "user" ? "user-bubble" : "bot-bubble"}`;
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    bubble.append(paragraph);
    content.append(meta, bubble);

    if (from === "bot" && category) {
      const details = document.createElement("div");
      details.className = "answer-details";
      const categoryTag = document.createElement("span");
      categoryTag.className = "category-tag";
      categoryTag.textContent = category;
      const score = document.createElement("span");
      score.className = "confidence";
      score.textContent = `Match confidence: ${Math.round(confidence * 100)}%`;
      details.append(categoryTag, score);
      content.append(details);
    }

    if (from === "bot" && suggestions && suggestions.length) {
      const list = document.createElement("div");
      list.className = "fallback-suggestions";
      const label = document.createElement("span");
      label.className = "suggestion-label";
      label.textContent = "YOU COULD ASK";
      list.append(label);
      suggestions.forEach((question) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = question;
        button.addEventListener("click", () => sendQuestion(question));
        list.append(button);
      });
      content.append(list);
    }

    if (from === "user") row.append(content, avatar);
    else row.append(avatar, content);
    conversation.append(row);
    scrollToLatest();
  }

  function showTyping(visible) {
    typing.classList.toggle("visible", visible);
    typing.setAttribute("aria-hidden", String(!visible));
    sendButton.disabled = visible;
    if (visible) scrollToLatest();
  }

  async function sendQuestion(rawQuestion) {
    const question = rawQuestion.trim();
    if (!question) {
      input.focus();
      return;
    }

    appendMessage({ text: question, from: "user" });
    input.value = "";
    input.style.height = "auto";
    showTyping(true);
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.error || `The server returned an error (${response.status}).`);
      }
      appendMessage({
        text: data.answer,
        from: "bot",
        category: data.category,
        confidence: data.confidence,
        suggestions: data.suggestions,
      });
    } catch (error) {
      appendMessage({
        text: error.message || "I couldn't reach the assistant. Please check your connection and try again.",
        from: "bot",
        error: true,
      });
    } finally {
      showTyping(false);
      input.focus();
    }
  }

  async function loadSuggestions() {
    try {
      const response = await fetch("/faqs");
      if (!response.ok) throw new Error("FAQ list could not be loaded.");
      const data = await response.json();
      const questions = data.faqs.slice(0, 3).map((faq) => faq.question);
      suggestionList.replaceChildren();
      questions.forEach((question) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "suggestion-chip";
        button.textContent = question;
        button.addEventListener("click", () => sendQuestion(question));
        suggestionList.append(button);
      });
    } catch {
      suggestionList.textContent = "Ask about Python, AI, databases, or more.";
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendQuestion(input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 100)}px`;
  });
  clearButton.addEventListener("click", () => {
    conversation.innerHTML = welcomeMarkup;
    conversation.querySelectorAll(".message-time").forEach((time) => { time.textContent = timeNow(); });
    const freshList = conversation.querySelector("#suggestions");
    if (freshList) {
      freshList.replaceChildren();
      loadSuggestionsInto(freshList);
    }
    input.value = "";
    scrollToLatest();
    input.focus();
  });

  async function loadSuggestionsInto(target) {
    try {
      const response = await fetch("/faqs");
      if (!response.ok) return;
      const data = await response.json();
      data.faqs.slice(0, 3).forEach((faq) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "suggestion-chip";
        button.textContent = faq.question;
        button.addEventListener("click", () => sendQuestion(faq.question));
        target.append(button);
      });
    } catch {
      target.textContent = "Ask about Python, AI, databases, or more.";
    }
  }

  loadSuggestions();
})();
