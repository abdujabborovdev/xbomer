// =============================================================
// PayFlow API Docs — front-end interactivity
// (Tab almashtirish, oddiy syntax highlight, Copy tugmasi, Qidiruv)
// =============================================================

document.addEventListener("DOMContentLoaded", () => {
  const langDataEl = document.getElementById("lang-data");
  const langData = langDataEl ? JSON.parse(langDataEl.textContent) : {};

  const tabs = document.querySelectorAll(".lang-tab");
  const requestCodeEl = document.querySelector("#code-request code");
  const reqLabel = document.getElementById("req-lang-label");

  const labelMap = { curl: "cURL", php: "PHP", python: "Python" };

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // Juda sodda, dependency'siz syntax highlighter.
  function highlight(code, lang) {
    let html = escapeHtml(code);

    // Qatorlardagi izohlarni ajratamiz (# yoki //)
    html = html.replace(/(^|\n)(\s*)(#.*)/g, '$1$2<span class="tok-com">$3</span>');
    html = html.replace(/(^|\n)(\s*)(\/\/.*)/g, '$1$2<span class="tok-com">$3</span>');

    // Qo'shtirnoq ichidagi satrlar
    html = html.replace(/"([^"\\]|\\.)*"/g, (m) => `<span class="tok-str">${m}</span>`);
    html = html.replace(/'([^'\\]|\\.)*'/g, (m) => `<span class="tok-str">${m}</span>`);

    // Raqamlar
    html = html.replace(/(?<![\w"])\b\d+(\.\d+)?\b(?!\w)/g, (m) => `<span class="tok-num">${m}</span>`);

    const keywordsByLang = {
      curl: ["curl", "-X", "-H", "-d"],
      php: ["<?php", "curl_init", "curl_setopt", "curl_exec", "curl_close", "echo", "json_decode", "json_encode", "file_get_contents", "print_r", "true", "false"],
      python: ["import", "print", "requests", "get", "post"],
    };

    (keywordsByLang[lang] || []).forEach((kw) => {
      const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const re = new RegExp(`(?<!tok-\\w{2}">[^<]*)\\b${escaped}\\b`, "g");
      html = html.replace(re, (m) => `<span class="tok-kw">${m}</span>`);
    });

    return html;
  }

  function renderRequestCode(lang) {
    const raw = langData[lang] || "";
    requestCodeEl.innerHTML = highlight(raw, lang);
    requestCodeEl.dataset.raw = raw;
    if (reqLabel) reqLabel.textContent = `${labelMap[lang]} · So'rov`;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      renderRequestCode(tab.dataset.lang);
    });
  });

  // Boshlang'ich holat: cURL
  if (requestCodeEl) {
    renderRequestCode("curl");
  }

  // JSON javobni ham chiroyli formatlab, key'larni bo'yaymiz
  const jsonEl = document.getElementById("json-response");
  if (jsonEl) {
    let raw = jsonEl.textContent;
    try {
      raw = JSON.stringify(JSON.parse(raw), null, 2);
    } catch (e) { /* allaqachon formatlangan bo'lishi mumkin */ }
    let html = escapeHtml(raw);
    html = html.replace(/"([^"]+)":/g, '<span class="tok-key">"$1"</span>:');
    html = html.replace(/: "([^"]*)"/g, ': <span class="tok-str">"$1"</span>');
    html = html.replace(/: (\d+(\.\d+)?)/g, ': <span class="tok-num">$1</span>');
    jsonEl.innerHTML = html;
  }

  // ---------------- Copy tugmalari ----------------
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetId = btn.dataset.target;
      const targetEl = document.querySelector(`#${targetId} code`);
      const text = targetEl.dataset.raw || targetEl.textContent;
      try {
        await navigator.clipboard.writeText(text);
        const label = btn.querySelector("span:last-child");
        const original = label.textContent;
        btn.classList.add("copied");
        label.textContent = "Copied!";
        setTimeout(() => {
          btn.classList.remove("copied");
          label.textContent = original;
        }, 1500);
      } catch (err) {
        console.error("Nusxalashda xatolik:", err);
      }
    });
  });

  document.querySelectorAll(".copy-static-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        btn.classList.add("text-emerald-500");
        setTimeout(() => btn.classList.remove("text-emerald-500"), 1200);
      } catch (err) {
        console.error("Nusxalashda xatolik:", err);
      }
    });
  });

  // ---------------- Sidebar qidiruv ----------------
  const searchInput = document.getElementById("sidebar-search");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const q = searchInput.value.trim().toLowerCase();
      document.querySelectorAll("#sidebar-nav .nav-link").forEach((link) => {
        const label = link.dataset.label || "";
        link.classList.toggle("hidden-by-search", q.length > 0 && !label.includes(q));
      });
    });
  }
});
