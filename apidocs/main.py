
import json

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, DictLoader, select_autoescape

BRAND = "XBOMER"
BASE_URL = "https://xbomer.uz/api/v1"

LANGUAGES = [
    ("curl", "cURL"),
    ("php", "PHP"),
    ("python", "Python"),
    ("cpp", "C++"),
    ("csharp", "C#"),
    ("java", "Java"),
]



def _curl_snippet(url: str, payload: dict) -> str:
    body = json.dumps(payload, indent=4, ensure_ascii=False)
    return (
        f'curl -X POST "{url}" \\\n'
        '  -H "Content-Type: application/json" \\\n'
        f"  -d '{body}'"
    )


def _php_snippet(url: str, payload: dict) -> str:
    lines = []
    for k, v in payload.items():
        val = f"'{v}'" if isinstance(v, str) else str(v)
        lines.append(f"    '{k}' => {val}")
    arr = ",\n".join(lines)
    return (
        "<?php\n"
        f"$ch = curl_init('{url}');\n"
        "curl_setopt($ch, CURLOPT_POST, true);\n"
        "curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);\n"
        "curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);\n"
        "curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([\n"
        f"{arr}\n"
        "]));\n"
        "$response = curl_exec($ch);\n"
        "echo $response;\n"
    )


def _python_snippet(url: str, payload: dict) -> str:
    lines = []
    for k, v in payload.items():
        val = f'"{v}"' if isinstance(v, str) else str(v)
        lines.append(f'    "{k}": {val}')
    body = ",\n".join(lines)
    return (
        "import requests\n\n"
        f'url = "{url}"\n'
        "payload = {\n"
        f"{body}\n"
        "}\n"
        "response = requests.post(url, json=payload)\n"
        "print(response.json())\n"
    )


def _cpp_snippet(url: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False)
    return (
        "#include <curl/curl.h>\n"
        "#include <iostream>\n"
        "#include <string>\n\n"
        "int main() {\n"
        "    CURL *curl = curl_easy_init();\n"
        "    if (curl) {\n"
        f'        std::string url = "{url}";\n'
        f'        std::string data = R"({body})";\n\n'
        "        struct curl_slist *headers = NULL;\n"
        '        headers = curl_slist_append(headers, "Content-Type: application/json");\n\n'
        "        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());\n"
        "        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);\n"
        "        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data.c_str());\n\n"
        "        CURLcode res = curl_easy_perform(curl);\n"
        "        curl_slist_free_all(headers);\n"
        "        curl_easy_cleanup(curl);\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
    )


def _csharp_snippet(url: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False).replace('"', '""')
    return (
        "using System;\n"
        "using System.Net.Http;\n"
        "using System.Text;\n"
        "using System.Threading.Tasks;\n\n"
        "class Program\n"
        "{\n"
        "    static async Task Main()\n"
        "    {\n"
        "        var client = new HttpClient();\n"
        f'        var url = "{url}";\n'
        f'        var json = @"{body}";\n'
        '        var content = new StringContent(json, Encoding.UTF8, "application/json");\n\n'
        "        var response = await client.PostAsync(url, content);\n"
        "        var result = await response.Content.ReadAsStringAsync();\n"
        "        Console.WriteLine(result);\n"
        "    }\n"
        "}\n"
    )


def _java_snippet(url: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False).replace('"', '\\"')
    return (
        "import java.net.URI;\n"
        "import java.net.http.HttpClient;\n"
        "import java.net.http.HttpRequest;\n"
        "import java.net.http.HttpResponse;\n\n"
        "public class Main {\n"
        "    public static void main(String[] args) throws Exception {\n"
        f'        String json = "{body}";\n\n'
        "        HttpClient client = HttpClient.newHttpClient();\n"
        "        HttpRequest request = HttpRequest.newBuilder()\n"
        f'            .uri(URI.create("{url}"))\n'
        '            .header("Content-Type", "application/json")\n'
        "            .POST(HttpRequest.BodyPublishers.ofString(json))\n"
        "            .build();\n\n"
        "        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());\n"
        "        System.out.println(response.body());\n"
        "    }\n"
        "}\n"
    )


def build_code_samples(url: str, payload: dict) -> dict:
    """Berilgan url + JSON payload asosida barcha tillardagi kod namunalarini qaytaradi."""
    return {
        "curl": _curl_snippet(url, payload),
        "php": _php_snippet(url, payload),
        "python": _python_snippet(url, payload),
        "cpp": _cpp_snippet(url, payload),
        "csharp": _csharp_snippet(url, payload),
        "java": _java_snippet(url, payload),
    }


# ============================================================================
# 3) ENDPOINTLAR RO'YXATI
# ============================================================================

def _ep(id_, group, title, method, path, description, params, payload, response):
    url = f"{BASE_URL.rsplit('/api/v1', 1)[0]}{path}" if path.startswith("/api") else BASE_URL
    return {
        "id": id_,
        "group": group,
        "type": "endpoint",
        "title": title,
        "method": method,
        "path": path,
        "description": description,
        "params": params,
        "response": response,
        "code": build_code_samples(url, payload),
    }


ENDPOINTS = [
    _ep(
        "test", "Endpointlar", "Test uchun", "POST", "/api/v1",
        "API kalitingiz to'g'ri ishlayotganini tekshirish uchun oddiy so'rov. "
        "Faqat `key` parametrini yuborish kifoya — muvaffaqiyatli bo'lsa server "
        "tasdiqlovchi xabar bilan javob qaytaradi.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
        ],
        {"key": "YOUR_API_KEY"},
        {"status": True, "message": "✅ API ishlamoqda"},
    ),
    _ep(
        "balance", "Endpointlar", "Balans", "POST", "/api/v1/balance",
        "Hisobingizdagi joriy balansni so'rash. `action` parametrini doim "
        "`\"balance\"` qiymati bilan yuboring.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'balance' qiymatini yuboring"},
        ],
        {"key": "YOUR_API_KEY", "action": "balance"},
        {"balance": 10000, "currency": "UZS"},
    ),
    _ep(
        "nomer-olish", "Raqamlar", "Nomer olish", "POST", "/api/v1/accounts_get",
        "Tanlangan davlat uchun SMS qabul qilishga tayyor yangi vaqtinchalik raqam "
        "sotib oladi. Qaytgan `id` qiymatini keyinchalik kodni olish uchun ishlating.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'accounts_get' qiymatini yuboring"},
            {"name": "country", "type": "string", "required": True, "desc": "Davlat kodi, masalan 'US'"},
        ],
        {"key": "YOUR_API_KEY", "action": "accounts_get", "country": "US"},
        {"id": 7890, "number": "12025550123", "country": "US"},
    ),
    _ep(
        "kod-olish", "Raqamlar", "Kod olish", "POST", "/api/v1/accounts_code",
        "Sotib olingan raqamga kelgan SMS-kodni qaytaradi. `order_id` sifatida "
        "\"Nomer olish\" so'rovidan qaytgan `id` qiymatini yuboring.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'accounts_code' qiymatini yuboring"},
            {"name": "order_id", "type": "integer", "required": True, "desc": "Nomer olishda qaytgan buyurtma ID raqami"},
        ],
        {"key": "YOUR_API_KEY", "action": "accounts_code", "order_id": 1231},
        {"id": 7890, "status": "OK", "code": "33450", "password": "h1i4b92"},
    ),
]

# ---------------------------------------------------------------------------
# "Xato kodlari" — bu oddiy endpoint emas, shuning uchun alohida "errors" turi
# bilan qo'shiladi (kod tab/tablari emas, xatolar jadvali ko'rsatiladi).
# ---------------------------------------------------------------------------
ERROR_CODES = [
    ("MISSING_API_KEY", 401, "API kaliti ('key') yuborilmadi"),
    ("INVALID_API_KEY", 401, "API kalit noto'g'ri yoki bloklangan"),
    ("MISSING_ACTION", 400, "'action' parametri topilmadi"),
    ("INVALID_ACTION", 400, "Noma'lum 'action' qiymati yuborildi"),
    ("INSUFFICIENT_BALANCE", 402, "Balansda mablag' yetarli emas"),
    ("COUNTRY_NOT_SUPPORTED", 400, "Ko'rsatilgan 'country' uchun raqam mavjud emas"),
    ("NUMBER_NOT_AVAILABLE", 404, "Hozircha bo'sh raqam yo'q"),
    ("ORDER_NOT_FOUND", 404, "'order_id' bo'yicha buyurtma topilmadi"),
    ("CODE_NOT_RECEIVED", 408, "SMS-kod hali kelmadi, birozdan keyin qayta urinib ko'ring"),
    ("RATE_LIMIT_EXCEEDED", 429, "So'rovlar soni limitdan oshdi (60/daqiqa)"),
]

ENDPOINTS.append({
    "id": "xato-kodlari",
    "group": "Ma'lumot",
    "type": "errors",
    "title": "Xato kodlari",
    "method": None,
    "path": None,
    "description": "API javob xatolari va ularning ma'nosi.",
    "params": [],
    "error_codes": ERROR_CODES,
    "response": {
        "status": False,
        "message": "Balansda mablag' yetarli emas",
        "error_code": "INSUFFICIENT_BALANCE",
    },
})

DEFAULT_SECTION = ENDPOINTS[0]["id"]  # "test"


def get_endpoint(endpoint_id: str) -> dict:
    for ep in ENDPOINTS:
        if ep["id"] == endpoint_id:
            return ep
    return ENDPOINTS[0]


# ============================================================================
# 4) CSS — barcha uslublar shu yerda, shablonlarga <style> orqali quyiladi
# ============================================================================

STYLE_CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif; }
code, pre, .font-mono { font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, "Liberation Mono", monospace; }

/* ---------- Sidebar ---------- */
.nav-group-label:first-child { margin-top: 0; }
.nav-link-active { background: #f1f0ff; color: #4740b8; font-weight: 600; }
.nav-link.hidden-by-search { display: none !important; }

.method-tag {
  display: inline-flex; align-items: center; justify-content: center;
  width: 38px; height: 17px; border-radius: 4px; font-size: 10px; font-weight: 700;
  letter-spacing: 0.02em; font-family: ui-monospace, monospace;
}
.method-get  { background: #e6f4ea; color: #1e7d3c; }
.method-post { background: #e6edff; color: #2547d0; }
.method-put  { background: #fff4e0; color: #b5760a; }
.method-delete { background: #fde8e8; color: #c2280f; }

.method-badge {
  display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 6px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.03em; font-family: ui-monospace, monospace;
}
.method-badge-get  { background: #e6f4ea; color: #1e7d3c; }
.method-badge-post { background: #e6edff; color: #2547d0; }
.method-badge-put  { background: #fff4e0; color: #b5760a; }
.method-badge-delete { background: #fde8e8; color: #c2280f; }

/* ---------- Unified code card: tabs + kod bitta uzluksiz karta ichida ---------- */
.code-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  background: #ffffff;
  margin-bottom: 2rem;
}
.code-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 10px 0 10px;
  background: #ffffff;
  border-bottom: 1px solid #eef0f3;
  overflow-x: auto;
}
.code-tab {
  padding: 8px 14px;
  font-size: 12.5px;
  font-weight: 500;
  color: #94a3b8;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  white-space: nowrap;
  transition: all 0.15s ease;
}
.code-tab:hover { color: #475569; }
.code-tab.active { color: #0f172a; border-bottom-color: #5851e0; }

.code-body-wrap { background: #0d1017; }

.code-window-header {
  display: flex; align-items: center; gap: 7px; padding: 9px 12px;
  background: #12151d; border-bottom: 1px solid #1c212b;
}
.dot { width: 9px; height: 9px; border-radius: 50%; }
.dot-red { background: #ff5f57; }
.dot-yellow { background: #febc2e; }
.dot-green { background: #28c840; }
.code-window-title { margin-left: 6px; font-size: 11.5px; color: #6b7280; flex: 1; }

.response-status {
  font-size: 11px; font-weight: 700; color: #34d399; background: rgba(52, 211, 153, 0.12);
  padding: 2px 8px; border-radius: 4px; font-family: ui-monospace, monospace;
}

.copy-btn {
  display: flex; align-items: center; gap: 5px; font-size: 11.5px; color: #8b93a7;
  background: transparent; padding: 4px 8px; border-radius: 6px; transition: all 0.15s ease;
}
.copy-btn:hover { background: #1c212b; color: #e5e7eb; }
.copy-btn.copied { color: #34d399; }

.code-window-body {
  padding: 16px 18px; font-size: 12.5px; line-height: 1.7; overflow-x: auto;
  color: #d3d7de; white-space: pre;
}

/* Standalone dark card — faqat "Namuna javob" bloki uchun */
.code-window {
  border-radius: 10px; overflow: hidden; border: 1px solid #1c212b; background: #0d1017;
}

.copy-static-btn { transition: color 0.15s ease; }

/* ---------- Syntax-highlight token ranglari ---------- */
.tok-kw   { color: #ff7ab8; }
.tok-str  { color: #a6e22e; }
.tok-num  { color: #ae81ff; }
.tok-com  { color: #6b7280; font-style: italic; }
.tok-key  { color: #79c0ff; }
.tok-type { color: #66d9ef; }

aside::-webkit-scrollbar, .code-window-body::-webkit-scrollbar, .code-tabs::-webkit-scrollbar { width: 8px; height: 6px; }
aside::-webkit-scrollbar-thumb { background: #1e2430; border-radius: 8px; }
aside::-webkit-scrollbar-track { background: transparent; }

/* ---------- Xatolar jadvali ---------- */
.error-table th { font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: #94a3b8; }
.error-code { color: #dc2626; font-weight: 600; }
.error-http { color: #b5760a; }

/* ---------- Footer (sahifa pastidagi bo'lim) ---------- */
.footer-icon { color: #94a3b8; flex-shrink: 0; }
.footer-link:hover .footer-icon { color: #5851e0; }
"""


# ============================================================================
# 5) JS — tab almashtirish, syntax highlight, copy, qidiruv
# ============================================================================

SCRIPT_JS = """
document.addEventListener("DOMContentLoaded", () => {
  const langDataEl = document.getElementById("lang-data");
  const langData = langDataEl ? JSON.parse(langDataEl.textContent) : {};

  const tabs = document.querySelectorAll(".code-tab");
  const requestCodeEl = document.querySelector("#code-request code");
  const reqLabel = document.getElementById("req-lang-label");

  const labelMap = { curl: "cURL", php: "PHP", python: "Python", cpp: "C++", csharp: "C#", java: "Java" };

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function highlight(code, lang) {
    let html = escapeHtml(code);
    html = html.replace(/(^|\\n)(\\s*)(#(?!include).*)/g, '$1$2<span class="tok-com">$3</span>');
    html = html.replace(/(^|\\n)(\\s*)(\\/\\/.*)/g, '$1$2<span class="tok-com">$3</span>');
    html = html.replace(/"([^"\\\\]|\\\\.)*"/g, (m) => `<span class="tok-str">${m}</span>`);
    html = html.replace(/'([^'\\\\]|\\\\.)*'/g, (m) => `<span class="tok-str">${m}</span>`);
    html = html.replace(/(?<![\\w"])\\b\\d+(\\.\\d+)?\\b(?!\\w)/g, (m) => `<span class="tok-num">${m}</span>`);

    const keywordsByLang = {
      curl: ["curl", "-X", "-H", "-d"],
      php: ["<?php", "curl_init", "curl_setopt", "curl_exec", "curl_close", "echo", "json_decode", "json_encode", "true", "false"],
      python: ["import", "print", "requests", "get", "post"],
      cpp: ["#include", "int", "main", "return", "if", "struct", "NULL", "std", "curl_easy_init", "curl_easy_setopt",
            "curl_easy_perform", "curl_easy_cleanup", "curl_slist_append", "curl_slist_free_all", "string"],
      csharp: ["using", "class", "static", "async", "Task", "var", "new", "await", "Console", "WriteLine", "Main", "void", "HttpClient", "StringContent"],
      java: ["import", "public", "class", "static", "void", "String", "new", "throws", "Exception", "System", "out", "println",
             "HttpClient", "HttpRequest", "HttpResponse"],
    };

    (keywordsByLang[lang] || []).forEach((kw) => {
      const escaped = kw.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");
      const re = new RegExp(`(?<!tok-\\\\w{2}">[^<]*)\\\\b${escaped}\\\\b`, "g");
      html = html.replace(re, (m) => `<span class="tok-kw">${m}</span>`);
    });

    return html;
  }

  function renderRequestCode(lang) {
    const raw = langData[lang] || "";
    requestCodeEl.innerHTML = highlight(raw, lang);
    requestCodeEl.dataset.raw = raw;
    if (reqLabel) reqLabel.textContent = `${labelMap[lang]} \\u00b7 So'rov`;
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      renderRequestCode(tab.dataset.lang);
    });
  });

  if (requestCodeEl) renderRequestCode("curl");

  const jsonEl = document.getElementById("json-response");
  if (jsonEl) {
    let raw = jsonEl.textContent;
    try { raw = JSON.stringify(JSON.parse(raw), null, 2); } catch (e) {}
    let html = escapeHtml(raw);
    html = html.replace(/"([^"]+)":/g, '<span class="tok-key">"$1"</span>:');
    html = html.replace(/: "([^"]*)"/g, ': <span class="tok-str">"$1"</span>');
    html = html.replace(/: (\\d+(\\.\\d+)?)/g, ': <span class="tok-num">$1</span>');
    jsonEl.innerHTML = html;
  }

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
        setTimeout(() => { btn.classList.remove("copied"); label.textContent = original; }, 1500);
      } catch (err) { console.error("Nusxalashda xatolik:", err); }
    });
  });

  document.querySelectorAll(".copy-static-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(btn.dataset.copy);
        btn.classList.add("text-emerald-500");
        setTimeout(() => btn.classList.remove("text-emerald-500"), 1200);
      } catch (err) { console.error("Nusxalashda xatolik:", err); }
    });
  });

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
"""


# ============================================================================
# 6) HTML SHABLONLARI (Jinja2, DictLoader orqali xotiradan yuklanadi)
# ============================================================================

TEMPLATES = {

"index.html": """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ brand }} — Virtual raqamlar va SMS-kod API</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = { theme: { extend: { colors: { brand: {
    50: '#f1f0ff', 100: '#e4e1ff', 500: '#635bff', 600: '#5851e0', 700: '#4740b8'
  } } } } }
</script>
<style>{{ style|safe }}</style>
</head>
<body class="bg-white text-slate-900 antialiased">

  <header class="sticky top-0 z-30 border-b border-slate-100 bg-white/80 backdrop-blur">
    <div class="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
          <span class="text-white font-bold text-sm">X</span>
        </div>
        <span class="font-semibold text-lg tracking-tight">{{ brand }}</span>
      </div>
      <nav class="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
        <a href="#features" class="hover:text-slate-900">Imkoniyatlar</a>
        <a href="#" class="hover:text-slate-900">Narxlar</a>
        <a href="/docs" class="hover:text-slate-900">Hujjatlar</a>
      </nav>
      <a href="/docs" class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 text-white text-sm font-medium px-4 py-2 hover:bg-slate-700 transition">
        API hujjatlari
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      </a>
    </div>
  </header>

  <section class="relative overflow-hidden">
    <div class="absolute inset-0 -z-10 bg-gradient-to-b from-brand-50 via-white to-white"></div>
    <div class="max-w-6xl mx-auto px-6 pt-20 pb-24 grid lg:grid-cols-2 gap-16 items-center">
      <div>
        <span class="inline-block text-xs font-semibold tracking-wide uppercase text-brand-700 bg-brand-100 px-3 py-1 rounded-full mb-5">
          v1 API endi ochiq
        </span>
        <h1 class="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1] text-slate-900">
          Virtual raqamlarni bir nechta<br> API chaqiruvi bilan oling
        </h1>
        <p class="mt-6 text-lg text-slate-600 leading-relaxed max-w-lg">
          {{ brand }} — istalgan davlat uchun vaqtinchalik telefon raqamlarini sotib olish
          va ularga kelgan SMS-kodlarni oddiy REST API orqali olish imkonini beradi.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <a href="/docs" class="rounded-lg bg-brand-600 text-white font-medium px-5 py-3 text-sm hover:bg-brand-700 transition shadow-sm shadow-brand-600/20">
            Hujjatlarni ko'rish
          </a>
          <a href="/docs?section=test" class="rounded-lg border border-slate-200 text-slate-700 font-medium px-5 py-3 text-sm hover:bg-slate-50 transition">
            Tezkor boshlash
          </a>
        </div>
        <div class="mt-8 flex items-center gap-6 text-sm text-slate-500">
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> 99.98% uptime</div>
          <div class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-brand-500"></span> ~120ms javob vaqti</div>
        </div>
      </div>

      <div class="rounded-xl overflow-hidden shadow-2xl shadow-slate-900/10 border border-slate-800/10">
        <div class="bg-[#0e1116] px-4 py-3 flex items-center gap-1.5">
          <span class="w-3 h-3 rounded-full bg-[#ff5f57]"></span>
          <span class="w-3 h-3 rounded-full bg-[#febc2e]"></span>
          <span class="w-3 h-3 rounded-full bg-[#28c840]"></span>
          <span class="ml-3 text-xs text-slate-400 font-mono">accounts_get.py</span>
        </div>
        <pre class="bg-[#0e1116] text-[13px] leading-relaxed p-5 overflow-x-auto font-mono"><code><span class="tok-kw">import</span> requests

url = <span class="tok-str">"{{ base_url }}/accounts_get"</span>
payload = {
    <span class="tok-str">"key"</span>: <span class="tok-str">"YOUR_API_KEY"</span>,
    <span class="tok-str">"action"</span>: <span class="tok-str">"accounts_get"</span>,
    <span class="tok-str">"country"</span>: <span class="tok-str">"US"</span>
}

response = requests.post(url, json=payload)
<span class="tok-kw">print</span>(response.json())</code></pre>
      </div>
    </div>
  </section>

  <section id="features" class="max-w-6xl mx-auto px-6 py-20 border-t border-slate-100">
    <h2 class="text-2xl font-bold tracking-tight text-center">Nega {{ brand }} API?</h2>
    <div class="mt-12 grid sm:grid-cols-3 gap-8">
      <div class="rounded-xl border border-slate-100 p-6 hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center mb-4 text-brand-700">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z"/></svg>
        </div>
        <h3 class="font-semibold">Xavfsiz</h3>
        <p class="text-sm text-slate-500 mt-1.5 leading-relaxed">Barcha so'rovlar TLS orqali shifrlanadi va shaxsiy API kalitingiz orqali autentifikatsiya qilinadi.</p>
      </div>
      <div class="rounded-xl border border-slate-100 p-6 hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center mb-4 text-brand-700">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h7l-1 8 11-14h-8l1-6z"/></svg>
        </div>
        <h3 class="font-semibold">Tezkor</h3>
        <p class="text-sm text-slate-500 mt-1.5 leading-relaxed">Raqam sotib olish va SMS-kodni olish soniyalar ichida amalga oshadi.</p>
      </div>
      <div class="rounded-xl border border-slate-100 p-6 hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-brand-100 flex items-center justify-center mb-4 text-brand-700">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 17V7a2 2 0 012-2h8l6 6v6a2 2 0 01-2 2H6a2 2 0 01-2-2z"/><path d="M14 5v6h6"/></svg>
        </div>
        <h3 class="font-semibold">Aniq hujjatlar</h3>
        <p class="text-sm text-slate-500 mt-1.5 leading-relaxed">Har bir endpoint uchun 6 xil tilda (cURL, PHP, Python, C++, C#, Java) namunalar tayyor holda.</p>
      </div>
    </div>
  </section>

  <footer class="border-t border-slate-100 py-8">
    <div class="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-slate-400">
      <span>© 2026 {{ brand }}. Barcha huquqlar himoyalangan.</span>
      <a href="/docs" class="hover:text-slate-700">API hujjatlari →</a>
    </div>
  </footer>

</body>
</html>""",

"docs.html": """<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ active.title }} · {{ brand }} API hujjatlari</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = { theme: { extend: { colors: { brand: {
    50: '#f1f0ff', 100: '#e4e1ff', 500: '#635bff', 600: '#5851e0', 700: '#4740b8'
  } } } } }
</script>
<style>{{ style|safe }}</style>
</head>
<body class="bg-white text-slate-900 antialiased">

  <div class="flex items-start">

    <!-- ============ SIDEBAR (sticky, lekin faqat o'z balandligicha — footer to'g'ri joylashishi uchun) ============ -->
    <aside class="w-72 shrink-0 border-r border-slate-100 flex flex-col self-start sticky top-0 max-h-screen overflow-y-auto">
      <div class="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
        <a href="/" class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <span class="text-white font-bold text-xs">X</span>
          </div>
          <span class="font-semibold tracking-tight">{{ brand }} docs</span>
        </a>
      </div>

      <div class="px-4 pt-4">
        <div class="relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input id="sidebar-search" type="text" placeholder="Qidirish..."
            class="w-full text-sm bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400">
        </div>
      </div>

      <div class="mx-4 mt-4 rounded-lg bg-slate-50 border border-slate-200 p-3">
        <div class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold mb-1">Base URL</div>
        <div class="flex items-center justify-between gap-2">
          <code class="text-[12.5px] text-slate-700 font-mono truncate">{{ base_url }}</code>
          <button class="copy-static-btn shrink-0 text-slate-400 hover:text-brand-600" data-copy="{{ base_url }}" title="Nusxalash">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          </button>
        </div>
      </div>

      <nav id="sidebar-nav" class="flex-1 px-3 mt-5 pb-6">
        {% set ns = namespace(last_group="") %}
        {% for ep in endpoints %}
          {% if ep.group != ns.last_group %}
            <div class="px-2 mt-5 mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400 nav-group-label">{{ ep.group }}</div>
            {% set ns.last_group = ep.group %}
          {% endif %}
          <a href="/docs?section={{ ep.id }}"
             data-label="{{ ep.title|lower }}"
             class="nav-link group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm mb-0.5 {% if ep.id == active.id %}nav-link-active{% else %}text-slate-600 hover:bg-slate-50 hover:text-slate-900{% endif %}">
            {% if ep.method %}
              <span class="method-tag method-{{ ep.method|lower }}">{{ ep.method }}</span>
            {% else %}
              <span class="w-9 h-4 flex items-center justify-center text-amber-500 shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
              </span>
            {% endif %}
            <span class="truncate">{{ ep.title }}</span>
          </a>
        {% endfor %}
      </nav>
    </aside>

    <!-- ============ MAIN CONTENT — oddiy sahifa oqimi, mustaqil scroll YO'Q ============ -->
    <main class="flex-1 min-w-0">
      <div class="max-w-3xl mx-auto px-10 py-12">

        <div class="text-xs font-medium text-brand-600 uppercase tracking-wide mb-2">{{ active.group }}</div>

        {% if active.type == "errors" %}
        <!-- ============ XATO KODLARI SAHIFASI ============ -->
        <div class="flex items-center gap-3">
          <span class="w-9 h-9 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center shrink-0">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
          </span>
          <h1 class="text-3xl font-bold tracking-tight">{{ active.title }}</h1>
        </div>
        <p class="mt-4 text-slate-600 leading-relaxed">{{ active.description }}</p>

        <div class="rounded-xl border border-slate-100 overflow-hidden mt-8 error-table">
          <table class="w-full text-sm">
            <thead class="bg-slate-50">
              <tr>
                <th class="text-left px-4 py-3">Xato kodi</th>
                <th class="text-left px-4 py-3">HTTP</th>
                <th class="text-left px-4 py-3">Tavsif</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              {% for code, http, desc in active.error_codes %}
              <tr>
                <td class="px-4 py-3 font-mono text-[12.5px] error-code">{{ code }}</td>
                <td class="px-4 py-3 font-mono text-[12.5px] error-http">{{ http }}</td>
                <td class="px-4 py-3 text-slate-600">{{ desc }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>

        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mt-10 mb-4">Xato javobi namunasi</h2>
        <div class="code-window">
          <div class="code-window-header">
            <span class="response-status" style="color:#f87171;background:rgba(248,113,113,0.12);">ERROR</span>
            <span class="code-window-title">JSON</span>
            <button class="copy-btn" data-target="code-response">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <span>Copy</span>
            </button>
          </div>
          <pre class="code-window-body" id="code-response"><code id="json-response">{{ active.response | tojson(indent=2) }}</code></pre>
        </div>

        {% else %}
        <!-- ============ ODDIY ENDPOINT SAHIFASI ============ -->
        <div class="flex items-center gap-3 flex-wrap">
          <span class="method-badge method-badge-{{ active.method|lower }}">{{ active.method }}</span>
          <code class="text-[15px] font-mono text-slate-700">{{ active.path }}</code>
        </div>
        <h1 class="text-3xl font-bold tracking-tight mt-3">{{ active.title }}</h1>
        <p class="mt-4 text-slate-600 leading-relaxed">{{ active.description }}</p>

        {% if active.params %}
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mt-10 mb-4">Parametrlar</h2>
        <div class="rounded-xl border border-slate-100 divide-y divide-slate-100 overflow-hidden">
          {% for p in active.params %}
          <div class="p-4 flex flex-col sm:flex-row sm:items-start gap-1 sm:gap-6">
            <div class="w-40 shrink-0">
              <code class="text-[13px] font-mono font-semibold text-slate-800">{{ p.name }}</code>
              <div class="text-[11px] text-slate-400 mt-0.5">
                {{ p.type }}
                {% if p.required %}<span class="text-rose-500 font-medium">· majburiy</span>{% else %}<span>· ixtiyoriy</span>{% endif %}
              </div>
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">{{ p.desc }}</p>
          </div>
          {% endfor %}
        </div>
        {% endif %}

        <!-- ---------- Kod namunalari: tab + kod BITTA uzluksiz kartada ---------- -->
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mt-10 mb-4">So'rov namunasi</h2>

        <div class="code-card">
          <div class="code-tabs">
            {% for lang_id, lang_label in languages %}
              <button class="code-tab {% if loop.first %}active{% endif %}" data-lang="{{ lang_id }}">{{ lang_label }}</button>
            {% endfor %}
          </div>
          <div class="code-body-wrap">
            <div class="code-window-header">
              <span class="dot dot-red"></span><span class="dot dot-yellow"></span><span class="dot dot-green"></span>
              <span class="code-window-title" id="req-lang-label">cURL &middot; So'rov</span>
              <button class="copy-btn" data-target="code-request">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                <span>Copy</span>
              </button>
            </div>
            <pre class="code-window-body" id="code-request"><code>{{ active.code.curl }}</code></pre>
          </div>
        </div>

        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-4">Namuna javob</h2>
        <div class="code-window">
          <div class="code-window-header">
            <span class="response-status">200 OK</span>
            <span class="code-window-title">JSON</span>
            <button class="copy-btn" data-target="code-response">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <span>Copy</span>
            </button>
          </div>
          <pre class="code-window-body" id="code-response"><code id="json-response">{{ active.response | tojson(indent=2) }}</code></pre>
        </div>
        {% endif %}

      </div>

      <!-- ============ FOOTER (sahifa pastida, to'liq eni bo'yicha) ============ -->
      <footer class="border-t border-slate-100">
        <div class="max-w-4xl mx-auto px-10 py-12 grid sm:grid-cols-3 gap-10">
          <div>
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
                <span class="text-white font-bold text-xs">X</span>
              </div>
              <span class="font-bold text-lg">{{ brand }} API</span>
            </div>
            <p class="text-sm text-slate-500 mt-3 leading-relaxed">Virtual raqamlar va SMS-kod olish uchun ishonchli platforma</p>
            <div class="text-xs text-slate-400 mt-3 font-mono">v1.0 · Stable · REST · JSON</div>
          </div>

          <div>
            <h4 class="font-semibold text-sm text-slate-900 mb-4">Havolalar</h4>
            <ul class="space-y-3 text-sm text-slate-600">
              <li><a href="/docs?section=test" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h7l-1 8 11-14h-8l1-6z"/></svg>
                Test uchun</a></li>
              <li><a href="/docs?section=balance" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20"/><circle cx="17" cy="15" r="1"/></svg>
                Balans</a></li>
              <li><a href="/docs?section=nomer-olish" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.12.81.31 1.6.57 2.36a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.72-1.14a2 2 0 012.11-.45c.76.26 1.55.45 2.36.57A2 2 0 0122 16.92z"/></svg>
                Nomer olish</a></li>
              <li><a href="/docs?section=kod-olish" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                Kod olish</a></li>
              <li><a href="/docs?section=xato-kodlari" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                Xato kodlari</a></li>
            </ul>
          </div>

          <div>
            <h4 class="font-semibold text-sm text-slate-900 mb-4">Aloqa</h4>
            <ul class="space-y-3 text-sm text-slate-600">
              <li><a href="https://t.me/xbomerbot" target="_blank" rel="noopener" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>
                @xbomerbot</a></li>
              <li><a href="https://t.me/biloliddinabdujabborov" target="_blank" rel="noopener" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
                @biloliddinabdujabborov</a></li>
              <li><a href="https://xbomer.uz" target="_blank" rel="noopener" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 010 20 15.3 15.3 0 010-20z"/></svg>
                xbomer.uz</a></li>
            </ul>
          </div>
        </div>

        <div class="border-t border-slate-100">
          <div class="max-w-4xl mx-auto px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <span>© 2026 {{ brand }} · Barcha huquqlar himoyalangan</span>
            <span>REST API · JSON · API Key</span>
          </div>
        </div>
      </footer>
    </main>
  </div>

  {% if active.code %}
  <script id="lang-data" type="application/json">
    {
      "curl": {{ active.code.curl | tojson }},
      "php": {{ active.code.php | tojson }},
      "python": {{ active.code.python | tojson }},
      "cpp": {{ active.code.cpp | tojson }},
      "csharp": {{ active.code.csharp | tojson }},
      "java": {{ active.code.java | tojson }}
    }
  </script>
  {% endif %}

  <script>{{ script|safe }}</script>
</body>
</html>""",

}

env = Environment(loader=DictLoader(TEMPLATES), autoescape=select_autoescape(["html"]))


def render(template_name: str, **context) -> str:
    context.setdefault("style", STYLE_CSS)
    context.setdefault("script", SCRIPT_JS)
    context.setdefault("brand", BRAND)
    context.setdefault("base_url", BASE_URL)
    return env.get_template(template_name).render(**context)


# ============================================================================
# 7) FASTAPI ILOVASI VA ROUTE'LAR
# ============================================================================

app = FastAPI(
    title="XBOMER API",
    description="XBOMER — SMS-kod qabul qilish uchun virtual raqamlar sotib olish API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Asosiy sahifa — xush kelibsiz / landing page."""
    return HTMLResponse(render("index.html"))


@app.get("/docs", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request, section: str = DEFAULT_SECTION):
    active = get_endpoint(section)
    return HTMLResponse(render(
        "docs.html",
        endpoints=ENDPOINTS,
        active=active,
        languages=LANGUAGES,
    ))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)