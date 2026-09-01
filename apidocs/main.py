"""
XBOMER API — Custom Documentation Site (SINGLE FILE)
-----------------------------------------------------
Bitta faylda to'liq ishlaydigan FastAPI ilova: HTML, CSS va JS shu faylning
o'zida (Jinja2 DictLoader orqali) saqlanadi — alohida templates/ yoki static/
papka kerak emas.

Routing:
    "/"      -> Landing (xush kelibsiz) sahifa
    "/docs"  -> Custom API hujjatlar sahifasi (shuningdek "/api" ham ishlaydi).
                Bu BITTA uzluksiz sahifa: barcha bo'limlar (Test uchun, Balans,
                Nomer olish, Kod olish, Xato kodlari) ketma-ket joylashgan va
                sidebar'dagi havolalar shu bo'limlarga scroll qiladi (anchor).

Ishga tushirish:
    pip install fastapi uvicorn jinja2
    uvicorn main:app --reload

Keyin http://127.0.0.1:8000/ ni oching.
"""

import json
from api.v1 import router as v1_router

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, DictLoader, select_autoescape

# ============================================================================
# 1) SOZLAMALAR
# ============================================================================

BRAND = "XBOMER"
BASE_URL = "https://xbomer.uz/api/v1/"

LANGUAGES = [
    ("curl", "cURL"),
    ("php", "PHP"),
    ("python", "Python"),
    ("cpp", "C++"),
    ("csharp", "C#"),
    ("java", "Java"),
]


# ============================================================================
# 2) HAR BIR TIL UCHUN KOD NAMUNASINI AVTOMATIK YASOVCHI FUNKSIYALAR
# ============================================================================

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
#    Har bir endpoint uchun ikkita namuna javob saqlanadi:
#    - response        -> muvaffaqiyatli (200 OK) javob
#    - error_example   -> xato holatidagi javob (status matni + JSON tanasi)
# ============================================================================

def _ep(id_, group, title, method, path, description, params, payload, response, error_status, error_body):
    url = f"{BASE_URL.rsplit('/api/v1/', 1)[0]}{path}" if path.startswith("/api") else BASE_URL
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
        "error_status": error_status,
        "error_body": error_body,
        "code": build_code_samples(url, payload),
    }


ENDPOINTS = [
    _ep(
        "test", "Endpointlar", "Test uchun", "POST", "/api/v1/",
        "API kalitingiz to'g'ri ishlayotganini tekshirish uchun oddiy so'rov. "
        "Faqat `key` parametrini yuborish kifoya — muvaffaqiyatli bo'lsa server "
        "tasdiqlovchi xabar bilan javob qaytaradi.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
        ],
        {"key": "YOUR_API_KEY"},
        {"status": True, "message": "✅ API ishlamoqda"},
        "401 Unauthorized",
        {"status": False, "message": "API kalit noto'g'ri yoki bloklangan", "error_code": "INVALID_API_KEY"},
    ),
    _ep(
        "balance", "Endpointlar", "Balans", "POST", "/api/v1/balance/",
        "Hisobingizdagi joriy balansni so'rash. `action` parametrini doim "
        "`\"balance\"` qiymati bilan yuboring.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'balance' qiymatini yuboring"},
        ],
        {"key": "YOUR_API_KEY", "action": "balance"},
        {"balance": 10000, "currency": "UZS"},
        "401 Unauthorized",
        {"status": False, "message": "API kalit noto'g'ri yoki bloklangan", "error_code": "INVALID_API_KEY"},
    ),
    _ep(
        "nomer-olish", "Raqamlar", "Nomer olish", "POST", "/api/v1/accounts_get/",
        "Tanlangan davlat uchun SMS qabul qilishga tayyor yangi vaqtinchalik raqam "
        "sotib oladi. Qaytgan `id` qiymatini keyinchalik kodni olish uchun ishlating.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'accounts_get' qiymatini yuboring"},
            {"name": "country", "type": "string", "required": True, "desc": "Davlat kodi, masalan 'US'"},
        ],
        {"key": "YOUR_API_KEY", "action": "accounts_get", "country": "US"},
        {"id": 7890, "number": "12025550123", "country": "US"},
        "404 Not Found",
        {"status": False, "message": "Hozircha bo'sh raqam yo'q", "error_code": "NUMBER_NOT_AVAILABLE"},
    ),
    _ep(
        "kod-olish", "Raqamlar", "Kod olish", "POST", "/api/v1/accounts_code/",
        "Sotib olingan raqamga kelgan SMS-kodni qaytaradi. `order_id` sifatida "
        "\"Nomer olish\" so'rovidan qaytgan `id` qiymatini yuboring.",
        [
            {"name": "key", "type": "string", "required": True, "desc": "Sizning API kalitingiz"},
            {"name": "action", "type": "string", "required": True, "desc": "Har doim 'accounts_code' qiymatini yuboring"},
            {"name": "order_id", "type": "integer", "required": True, "desc": "Nomer olishda qaytgan buyurtma ID raqami"},
        ],
        {"key": "YOUR_API_KEY", "action": "accounts_code", "order_id": 1231},
        {"id": 7890, "status": "OK", "code": "33450", "password": "h1i4b92"},
        "404 Not Found",
        {"status": False, "message": "'order_id' bo'yicha buyurtma topilmadi", "error_code": "ORDER_NOT_FOUND"},
    ),
]

# ---------------------------------------------------------------------------
# "Xato kodlari" — oddiy endpoint emas, alohida "errors" turi bilan qo'shiladi
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

# ---------------------------------------------------------------------------
# "Narxlar" — davlat kodlari va ularning narxlari (UZS). "accounts_get"
# so'rovidagi `country` parametri aynan shu ikki xonali kodlardan biri
# bo'lishi kerak — shuning uchun bu sahifada har bir kodning to'liq nomi,
# bayrog'i va narxi ko'rsatiladi.
# ---------------------------------------------------------------------------
COUNTRY_NAMES = {
    "CO": "Kolumbiya 🇨🇴", "US": "Amerika 🇺🇸", "IN": "Hindiston 🇮🇳", "BD": "Bangladesh 🇧🇩",
    "IR": "Eron 🇮🇷", "ID": "Indoneziya 🇮🇩", "PK": "Pokiston 🇵🇰", "CL": "Chili 🇨🇱",
    "KE": "Keniya 🇰🇪", "AO": "Angola 🇦🇴", "NP": "Nepal 🇳🇵", "AF": "Afg'oniston 🇦🇫",
    "ZW": "Zimbabve 🇿🇼", "MG": "Madagaskar 🇲🇬", "SD": "Sudan 🇸🇩", "TZ": "Tanzaniya 🇹🇿",
    "DZ": "Jazoir 🇩🇿", "JM": "Yamayka 🇯🇲", "LK": "Shri-Lanka 🇱🇰", "PL": "Polsha 🇵🇱",
    "SZ": "Esvatini 🇸🇿", "UG": "Uganda 🇺🇬", "BF": "Burkina-Faso 🇧🇫", "MR": "Mavritaniya 🇲🇷",
    "PR": "Puerto-Riko 🇵🇷", "AR": "Argentina 🇦🇷", "CU": "Kuba 🇨🇺", "MX": "Meksika 🇲🇽",
    "NI": "Nikaragua 🇳🇮", "JE": "Jersi 🇯🇪", "BW": "Botsvana 🇧🇼",
    "CG": "Kongo 🇨🇬", "MU": "Mavrikiy 🇲🇺", "GN": "Gvineya 🇬🇳", "MA": "Marokash 🇲🇦",
    "DO": "Dominikan Respublikasi 🇩🇴", "TJ": "Tojikiston 🇹🇯", "VN": "Vyetnam 🇻🇳", "MQ": "Martinika 🇲🇶",
    "BR": "Braziliya 🇧🇷", "HN": "Gonduras 🇭🇳", "SV": "Salvador 🇸🇻", "GB": "Buyuk Britaniya 🇬🇧",
    "GG": "Gernsi 🇬🇬", "NA": "Namibiya 🇳🇦", "SO": "Somali 🇸🇴", "GW": "Gvineya-Bisau 🇬🇼",
    "ML": "Mali 🇲🇱", "TM": "Turkmaniston 🇹🇲", "IL": "Isroil 🇮🇱",
    "SY": "Suriya 🇸🇾", "UY": "Urugvay 🇺🇾", "HT": "Gaiti 🇭🇹", "GT": "Gvatemala 🇬🇹",
    "CV": "Kabo-Verde 🇨🇻", "SN": "Senegal 🇸🇳", "GM": "Gambiya 🇬🇲", "VI": "Virgin orollari (AQSh) 🇻🇮",
    "VE": "Venesuela 🇻🇪", "EE": "Estoniya 🇪🇪", "DJ": "Jibuti 🇩🇯", "LR": "Liberiya 🇱🇷",
    "TN": "Tunis 🇹🇳", "KN": "Sent-Kits va Nevis 🇰🇳", "TT": "Trinidad va Tobago 🇹🇹", "GU": "Guam 🇬🇺",
    "GD": "Grenada 🇬🇩", "PF": "Fransuz Polineziyasi 🇵🇫", "TO": "Tonga 🇹🇴", "MY": "Malayziya 🇲🇾",
    "GY": "Gayana 🇬🇾", "KM": "Comoros 🇰🇲", "AG": "Antigua va Barbuda 🇦🇬", "BS": "Bagama orollari 🇧🇸",
    "SA": "Saudiya Arabistoni 🇸🇦", "LB": "Livan 🇱🇧", "CN": "Xitoy 🇨🇳", "KH": "Kambodja 🇰🇭",
    "SB": "Solomon orollari 🇸🇧", "PE": "Peru 🇵🇪", "TD": "Chad 🇹🇩", "PS": "Falastin 🇵🇸",
    "TR": "Turkiya 🇹🇷", "LA": "Laos 🇱🇦", "HK": "Gonkong 🇭🇰", "FM": "Mikroneziya 🇫🇲",
    "KI": "Kiribati 🇰🇮", "WS": "Samoa 🇼🇸", "FJ": "Fiji 🇫🇯", "VU": "Vanuatu 🇻🇺",
    "TL": "Sharqiy Timor 🇹🇱", "CW": "Kurasao 🇨🇼", "PY": "Paragvay 🇵🇾", "IT": "Italiya 🇮🇹",
    "MK": "Shimoliy Makedoniya 🇲🇰", "ME": "Chernogoriya 🇲🇪", "FI": "Finlandiya 🇫🇮", "GL": "Grenlandiya 🇬🇱",
    "ER": "Eritreya 🇪🇷", "MW": "Malavi 🇲🇼", "RE": "Reunion 🇷🇪", "YT": "Mayotta 🇾🇹",
    "SC": "Seyshel orollari 🇸🇨", "GA": "Gabon 🇬🇦", "GQ": "Ekvatorial Gvineya 🇬🇶", "ST": "San-Tome va Prinsipi 🇸🇹",
    "CI": "Kot-d'Ivuar 🇨🇮", "LY": "Liviya 🇱🇾", "VC": "Sent-Vinsent va Grenadin 🇻🇨", "DM": "Dominika 🇩🇲",
    "LC": "Sent-Lusiya 🇱🇨", "SX": "Sint-Marten 🇸🇽", "BM": "Bermuda orollari 🇧🇲", "IM": "Men oroli 🇮🇲",
    "TC": "Turks va Kaykos 🇹🇨", "KG": "Qirg'iziston 🇰🇬", "JO": "Iordaniya 🇯🇴", "KZ": "Qozog'iston 🇰🇿",
    "GP": "Gvadelupa 🇬🇵", "BZ": "Beliz 🇧🇿", "DE": "Germaniya 🇩🇪", "BA": "Bosniya va Gersegovina 🇧🇦",
    "AM": "Armaniston 🇦🇲", "FR": "Fransiya 🇫🇷", "MN": "Mongoliya 🇲🇳", "AL": "Albaniya 🇦🇱",
    "AW": "Aruba 🇦🇼", "SS": "Janubiy Sudan 🇸🇸", "BE": "Belgiya 🇧🇪", "AZ": "Ozarbayjon 🇦🇿",
    "MD": "Moldova 🇲🇩", "ES": "Ispaniya 🇪🇸", "BT": "Butan 🇧🇹", "MV": "Maldiv orollari 🇲🇻",
    "NC": "Yangi Kaledoniya 🇳🇨", "GF": "Gviana (Fransuz) 🇬🇫", "BO": "Boliviya 🇧🇴", "PM": "Sen-Pyer va Mikelon 🇵🇲",
    "CZ": "Chexiya 🇨🇿", "HR": "Xorvatiya 🇭🇷", "LU": "Lyuksemburg 🇱🇺", "GR": "Gretsiya 🇬🇷",
    "AS": "Amerika Samoasi 🇦🇸", "KY": "Kayman orollari 🇰🇾", "VG": "Britaniya Virgin orollari 🇻🇬", "OM": "Omon 🇴🇲",
    "KW": "Kuvayt 🇰🇼", "AU": "Avstraliya 🇦🇺", "LT": "Litva 🇱🇹", "NL": "Niderlandiya 🇳🇱",
    "MO": "Makao 🇲🇴", "JP": "Yaponiya 🇯🇵", "DK": "Daniya 🇩🇰", "NZ": "Yangi Zelandiya 🇳🇿",
    "WF": "Uollis va Futuna 🇼🇫", "NR": "Nauru 🇳🇷", "NO": "Norvegiya 🇳🇴", "UA": "Ukraina 🇺🇦",
    "MT": "Malta 🇲🇹", "AE": "Birlashgan A.A 🇦🇪", "QA": "Qatar 🇶🇦", "KR": "Janubiy Koreya 🇰🇷",
    "BH": "Bahrayn 🇧🇭", "NU": "Niue 🇳🇺", "BN": "Bruney 🇧🇳", "SG": "Singapur 🇸🇬",
    "GI": "Gibraltar 🇬🇮",
    # Narxlar ro'yxatida uchraydi, lekin yuqoridagi lug'atda yo'q edi — qo'shildi:
    "UZ": "O'zbekiston 🇺🇿", "CR": "Kosta-Rika 🇨🇷", "CD": "Kongo DR 🇨🇩",
    "CF": "Markaziy Afrika Respublikasi 🇨🇫", "RO": "Ruminiya 🇷🇴", "PT": "Portugaliya 🇵🇹",
    "TW": "Tayvan 🇹🇼",
    "GE": "Gruziya 🇬🇪",
}

# Xom narxlar ro'yxati — "ID: 851| CO | 6825" formatida, foydalanuvchi bergan
# tartibda. ID'lar saqlash uchun emas — pastda 1 dan qayta raqamlanadi.
_RAW_PRICING = """
ID: 851| CO | 6825
ID: 852| US | 7508
ID: 853| IN | 7963
ID: 854| BD | 7963
ID: 855| ID | 9100
ID: 856| CL | 10238
ID: 857| AO | 10920
ID: 858| IR | 11375
ID: 859| AF | 11375
ID: 860| ZW | 11375
ID: 861| MG | 11375
ID: 862| SD | 11375
ID: 863| TZ | 12513
ID: 864| DZ | 12513
ID: 865| JM | 12513
ID: 866| LK | 13650
ID: 867| SZ | 13650
ID: 868| UG | 13650
ID: 869| BF | 13650
ID: 870| MR | 13650
ID: 871| PR | 13650
ID: 872| UZ | 14788
ID: 873| AR | 14788
ID: 874| CU | 14788
ID: 875| MX | 14788
ID: 876| CR | 14788
ID: 877| NI | 14788
ID: 878| JE | 14788
ID: 879| BW | 14788
ID: 880| CD | 14788
ID: 881| CG | 14788
ID: 882| MU | 14788
ID: 883| GN | 14788
ID: 884| MA | 14788
ID: 885| DO | 14788
ID: 886| TJ | 15925
ID: 887| IL | 15925
ID: 888| VN | 15925
ID: 889| MQ | 15925
ID: 890| BR | 15925
ID: 891| HN | 15925
ID: 892| SV | 15925
ID: 893| GB | 15925
ID: 894| GG | 15925
ID: 895| NA | 15925
ID: 896| SO | 15925
ID: 897| GW | 15925
ID: 898| CF | 15925
ID: 899| ML | 15925
ID: 900| TM | 17063
ID: 901| UY | 17063
ID: 902| HT | 17063
ID: 903| GT | 17063
ID: 904| SN | 17063
ID: 905| GM | 17063
ID: 906| VI | 17063
ID: 907| SY | 18200
ID: 908| EE | 18200
ID: 909| DJ | 18200
ID: 910| LR | 18200
ID: 911| TN | 18200
ID: 912| KN | 18200
ID: 913| TT | 18200
ID: 914| GU | 18200
ID: 915| GD | 18200
ID: 916| PF | 19338
ID: 917| TO | 19338
ID: 918| MY | 19338
ID: 919| GY | 19338
ID: 920| RO | 19338
ID: 921| KM | 19338
ID: 922| AG | 19338
ID: 923| BS | 19338
ID: 924| SA | 20475
ID: 925| LB | 20475
ID: 926| CN | 20475
ID: 927| KH | 20475
ID: 928| SB | 20475
ID: 929| PE | 20475
ID: 930| IT | 20475
ID: 931| TD | 20475
ID: 932| PS | 22750
ID: 933| TR | 22750
ID: 934| LA | 22750
ID: 935| HK | 22750
ID: 936| FM | 22750
ID: 937| KI | 22750
ID: 938| WS | 22750
ID: 939| FJ | 22750
ID: 940| VU | 22750
ID: 941| TL | 22750
ID: 942| CW | 22750
ID: 943| PY | 22750
ID: 944| MK | 22750
ID: 945| ME | 22750
ID: 946| FI | 22750
ID: 947| PT | 22750
ID: 948| GL | 22750
ID: 949| ER | 22750
ID: 950| MW | 22750
ID: 951| RE | 22750
ID: 952| YT | 22750
ID: 953| SC | 22750
ID: 954| GA | 22750
ID: 955| GQ | 22750
ID: 956| ST | 22750
ID: 957| CI | 22750
ID: 958| LY | 22750
ID: 959| VC | 22750
ID: 960| DM | 22750
ID: 961| LC | 22750
ID: 962| SX | 22750
ID: 963| BM | 22750
ID: 964| IM | 25025
ID: 965| TC | 25025
ID: 966| KG | 27300
ID: 967| JO | 27300
ID: 968| KZ | 27300
ID: 969| GP | 27300
ID: 970| BZ | 27300
ID: 971| DE | 27300
ID: 972| BA | 27300
ID: 973| AM | 27300
ID: 974| FR | 27300
ID: 975| MN | 29575
ID: 976| AL | 29575
ID: 977| AW | 29575
ID: 978| SS | 29575
ID: 979| BE | 30713
ID: 980| GE | 31850
ID: 981| AZ | 31850
ID: 982| MD | 31850
ID: 983| ES | 31850
ID: 984| BT | 34125
ID: 985| MV | 34125
ID: 986| NC | 34125
ID: 987| GF | 34125
ID: 988| BO | 34125
ID: 989| PM | 34125
ID: 990| CZ | 34125
ID: 991| LU | 34125
ID: 992| GR | 34125
ID: 993| AS | 34125
ID: 994| KY | 34125
ID: 995| VG | 34125
ID: 996| OM | 36400
ID: 997| KW | 37538
ID: 998| AU | 38675
ID: 999| LT | 38675
ID: 1000| NL | 38675
ID: 1001| MO | 39813
ID: 1002| JP | 39813
ID: 1003| DK | 39813
ID: 1004| NZ | 40950
ID: 1005| TW | 43225
ID: 1006| WF | 45500
ID: 1007| NR | 45500
ID: 1008| NO | 45500
ID: 1009| UA | 45500
ID: 1010| MT | 45500
ID: 1011| AE | 52325
ID: 1012| QA | 53463
ID: 1013| KR | 63700
ID: 1014| BH | 68250
ID: 1015| NU | 68250
ID: 1016| BN | 68250
ID: 1017| SG | 68250
ID: 1018| GI | 91000
"""


def _parse_pricing(raw: str) -> list:
    rows = []
    seq = 1
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # "ID: 851| CO | 6825" -> "|" bo'yicha bo'lamiz, ID ustunini tashlab yuboramiz
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            continue
        code = parts[1].upper()
        try:
            price = int(parts[2])
        except ValueError:
            continue
        rows.append({
            "no": seq,                       # 1 dan qayta raqamlangan tartib raqami
            "code": code,
            "name": COUNTRY_NAMES.get(code, code),
            "price": price,
        })
        seq += 1
    return rows


PRICING = _parse_pricing(_RAW_PRICING)

ENDPOINTS.append({
    "id": "narxlar",
    "group": "Ma'lumot",
    "type": "pricing",
    "title": "Narxlar",
    "method": None,
    "path": None,
    "description": (
        "\"Nomer olish\" so'rovidagi `country` parametri quyidagi ikki xonali "
        "davlat kodlaridan biri bo'lishi shart. Har bir davlat uchun narx "
        "so'mda (UZS) ko'rsatilgan — bu bitta SMS-qabul qiluvchi raqamning narxi."
    ),
    "pricing": PRICING,
})


# ============================================================================
# 4) CSS
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

/* ---------- Unified code card: tabs + kod bitta uzluksiz karta ---------- */
.code-card {
  border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; background: #ffffff; margin-bottom: 2rem;
}
.code-tabs {
  display: flex; gap: 4px; padding: 8px 10px 0 10px; background: #ffffff;
  border-bottom: 1px solid #eef0f3; overflow-x: auto;
}
.code-tab, .resp-tab {
  padding: 8px 14px; font-size: 12.5px; font-weight: 500; color: #94a3b8;
  border-bottom: 2px solid transparent; margin-bottom: -1px; white-space: nowrap; transition: all 0.15s ease;
}
.code-tab:hover, .resp-tab:hover { color: #475569; }
.code-tab.active, .resp-tab.active { color: #0f172a; border-bottom-color: #5851e0; }

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
.response-status.is-error { color: #f87171; background: rgba(248, 113, 113, 0.12); }

.copy-btn {
  display: flex; align-items: center; gap: 5px; font-size: 11.5px; color: #8b93a7;
  background: transparent; padding: 4px 8px; border-radius: 6px; transition: all 0.15s ease;
}
.copy-btn:hover { background: #1c212b; color: #e5e7eb; }
.copy-btn.copied { color: #34d399; }

.code-window-body {
  padding: 16px 18px; font-size: 12.5px; line-height: 1.7; overflow-x: auto; color: #d3d7de; white-space: pre;
}

.code-window { border-radius: 10px; overflow: hidden; border: 1px solid #1c212b; background: #0d1017; }

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

/* ---------- Footer ---------- */
.footer-icon { color: #94a3b8; flex-shrink: 0; }
.footer-link:hover .footer-icon { color: #5851e0; }

/* Section anchor'lar sticky header ostida kesilib qolmasin */
main section[id] { scroll-margin-top: 24px; }

/* ---------- Mobil sidebar (drawer) ---------- */
#sidebar.sidebar-open { transform: translateX(0); }
@media (min-width: 768px) {
  #sidebar { transform: none !important; }
}
"""


# ============================================================================
# 5) JS
# ============================================================================

SCRIPT_JS = """
document.addEventListener("DOMContentLoaded", () => {
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

  document.querySelectorAll(".code-card").forEach((card) => {
    const langDataEl = card.querySelector(".lang-data-el");
    const langData = langDataEl ? JSON.parse(langDataEl.textContent) : {};
    const tabs = card.querySelectorAll(".code-tab");
    const codeEl = card.querySelector(".code-request-el");
    const labelEl = card.querySelector(".req-lang-label");

    function render(lang) {
      const raw = langData[lang] || "";
      if (!codeEl) return;
      codeEl.innerHTML = highlight(raw, lang);
      codeEl.dataset.raw = raw;
      if (labelEl) labelEl.textContent = `${labelMap[lang]} \\u00b7 So'rov`;
    }

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        render(tab.dataset.lang);
      });
    });

    render("curl");
  });

  function highlightJson(raw) {
    let pretty = raw;
    try { pretty = JSON.stringify(JSON.parse(raw), null, 2); } catch (e) {}
    let html = escapeHtml(pretty);
    html = html.replace(/"([^"]+)":/g, '<span class="tok-key">"$1"</span>:');
    html = html.replace(/: "([^"]*)"/g, ': <span class="tok-str">"$1"</span>');
    html = html.replace(/: (\\d+(\\.\\d+)?)/g, ': <span class="tok-num">$1</span>');
    html = html.replace(/: (true|false)/g, ': <span class="tok-kw">$1</span>');
    return { html, pretty };
  }

  // Statik (bitta) JSON javoblar — masalan "Xato kodlari" sahifasidagi namuna
  document.querySelectorAll(".json-response-el").forEach((el) => {
    const { html, pretty } = highlightJson(el.textContent);
    el.innerHTML = html;
    el.dataset.raw = pretty;
  });

  // ---------------- Har bir endpointdagi javob-karta: 200 OK / Xato tab almashtirish ----------------
  document.querySelectorAll(".code-card").forEach((card) => {
    const dataEl = card.querySelector(".resp-data-el");
    if (!dataEl) return;
    const data = JSON.parse(dataEl.textContent);
    const tabs = card.querySelectorAll(".resp-tab");
    const codeEl = card.querySelector(".json-response-el");
    const statusEl = card.querySelector(".resp-status-el");

    function renderResp(kind) {
      const entry = data[kind];
      if (!entry || !codeEl) return;
      const { html, pretty } = highlightJson(JSON.stringify(entry.body));
      codeEl.innerHTML = html;
      codeEl.dataset.raw = pretty;
      if (statusEl) {
        statusEl.textContent = entry.label;
        statusEl.classList.toggle("is-error", kind === "error");
      }
    }

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        renderResp(tab.dataset.resp);
      });
    });

    renderResp("success");
  });

  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const container = btn.closest(".code-body-wrap, .code-window");
      const codeEl = container ? container.querySelector("code") : null;
      if (!codeEl) return;
      const text = codeEl.dataset.raw || codeEl.textContent;
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

  // ---------------- Narxlar jadvalida qidiruv ----------------
  const pricingSearch = document.getElementById("pricing-search");
  if (pricingSearch) {
    const rows = document.querySelectorAll(".pricing-row");
    const emptyMsg = document.getElementById("pricing-empty");
    pricingSearch.addEventListener("input", () => {
      const q = pricingSearch.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const match = q.length === 0 || (row.dataset.label || "").includes(q);
        row.classList.toggle("hidden", !match);
        if (match) visible++;
      });
      if (emptyMsg) emptyMsg.classList.toggle("hidden", visible !== 0);
    });
  }

  const params = new URLSearchParams(location.search);
  const legacySection = params.get("section");
  if (legacySection) {
    const target = document.getElementById(legacySection);
    if (target) setTimeout(() => target.scrollIntoView(), 0);
  }

  const sections = document.querySelectorAll("main section[id]");
  const navLinks = document.querySelectorAll("#sidebar-nav .nav-link");

  function setActiveLink(id) {
    navLinks.forEach((link) => {
      const isActive = link.getAttribute("href") === "#" + id;
      link.classList.toggle("nav-link-active", isActive);
      link.classList.toggle("text-slate-600", !isActive);
    });
  }

  if ("IntersectionObserver" in window && sections.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveLink(entry.target.id);
        });
      },
      { rootMargin: "-15% 0px -70% 0px", threshold: 0 }
    );
    sections.forEach((s) => observer.observe(s));
    setActiveLink(sections[0].id);
  }

  // ---------------- Mobil sidebar (drawer) ----------------
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const menuBtn = document.getElementById("mobile-menu-btn");
  const closeBtn = document.getElementById("sidebar-close-btn");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("sidebar-open");
    if (backdrop) backdrop.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("sidebar-open");
    if (backdrop) backdrop.classList.add("hidden");
    document.body.style.overflow = "";
  }

  if (menuBtn) menuBtn.addEventListener("click", openSidebar);
  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  // Mobilda bo'lim havolasini bosganda drawer avtomatik yopiladi
  document.querySelectorAll("#sidebar-nav .nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth < 768) closeSidebar();
    });
  });

  // Ekran kengaytirilsa (md va undan katta), drawer holatini tozalab qo'yamiz
  window.addEventListener("resize", () => {
    if (window.innerWidth >= 768) closeSidebar();
  });
});
"""


# ============================================================================
# 6) HTML SHABLONLARI
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
        <a href="/docs#narxlar" class="hover:text-slate-900">Narxlar</a>
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
          <a href="/docs#narxlar" class="rounded-lg border border-slate-200 text-slate-700 font-medium px-5 py-3 text-sm hover:bg-slate-50 transition">
            Narxlarni korish
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
        <pre class="bg-[#0e1116] text-[13px] leading-relaxed p-5 overflow-x-auto font-mono text-slate-300"><code><span class="tok-kw">import</span> requests

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
        <p class="text-sm text-slate-500 mt-1.5 leading-relaxed">Har bir endpoint uchun 6 xil tilda (cURL, PHP, Python, C++, C#, Java) namunalar, muvaffaqiyatli va xato javoblari bilan.</p>
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
<title>{{ brand }} API hujjatlari</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = { theme: { extend: { colors: { brand: {
    50: '#f1f0ff', 100: '#e4e1ff', 500: '#635bff', 600: '#5851e0', 700: '#4740b8'
  } } } } }
</script>
<style>{{ style|safe }}</style>
</head>
<body class="bg-white text-slate-900 antialiased">

  <!-- ============ MOBIL TEPA PANEL (faqat kichik ekranlarda ko'rinadi) ============ -->
  <div class="md:hidden sticky top-0 z-40 bg-white/90 backdrop-blur border-b border-slate-100 flex items-center gap-3 px-4 py-3">
    <button id="mobile-menu-btn" class="p-1.5 -ml-1 text-slate-600" aria-label="Menyu">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </button>
    <div class="w-6 h-6 rounded-md bg-brand-600 flex items-center justify-center">
      <span class="text-white font-bold text-[11px]">X</span>
    </div>
    <span class="font-semibold text-sm tracking-tight">{{ brand }} docs</span>
  </div>

  <!-- Mobilda sidebar ochilganda orqa fonni qorong'ilashtiruvchi qatlam -->
  <div id="sidebar-backdrop" class="hidden md:hidden fixed inset-0 bg-black/30 z-40"></div>

  <div class="md:flex md:items-start">

    <!-- ============ SIDEBAR ============ -->
    <aside id="sidebar"
      class="fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] bg-white border-r border-slate-100 flex flex-col overflow-y-auto -translate-x-full transition-transform duration-200 ease-out
             md:translate-x-0 md:static md:z-auto md:max-w-none md:self-start md:sticky md:top-0 md:max-h-screen">
      <div class="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-2">
        <a href="/" class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <span class="text-white font-bold text-xs">X</span>
          </div>
          <span class="font-semibold tracking-tight">{{ brand }} docs</span>
        </a>
        <button id="sidebar-close-btn" class="md:hidden p-1 text-slate-400" aria-label="Yopish">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
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
          <a href="#{{ ep.id }}"
             data-label="{{ ep.title|lower }}"
             class="nav-link group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm mb-0.5 text-slate-600 hover:bg-slate-50 hover:text-slate-900">
            {% if ep.method %}
              <span class="method-tag method-{{ ep.method|lower }}">{{ ep.method }}</span>
            {% elif ep.type == "pricing" %}
              <span class="w-9 h-4 flex items-center justify-center text-brand-500 shrink-0">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41L11 3.83V3H10.17L1 12.17V13l9.59 9.59a2 2 0 002.82 0l7.18-7.18a2 2 0 000-2.82z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>
              </span>
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

    <!-- ============ MAIN CONTENT ============ -->
    <main class="flex-1 min-w-0">

      {% for ep in endpoints %}
      <section id="{{ ep.id }}" class="max-w-4xl mx-auto px-5 sm:px-10 py-10 sm:py-12 {% if not loop.first %}border-t border-slate-100{% endif %}">

        <div class="text-xs font-medium text-brand-600 uppercase tracking-wide mb-2">{{ ep.group }}</div>

        {% if ep.type == "errors" %}
        <div class="flex items-center gap-3">
          <span class="w-9 h-9 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center shrink-0">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
          </span>
          <h1 class="text-3xl font-bold tracking-tight">{{ ep.title }}</h1>
        </div>
        <p class="mt-4 text-slate-600 leading-relaxed">{{ ep.description }}</p>

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
              {% for code, http, desc in ep.error_codes %}
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
            <span class="response-status is-error">ERROR</span>
            <span class="code-window-title">JSON</span>
            <button class="copy-btn">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              <span>Copy</span>
            </button>
          </div>
          <pre class="code-window-body"><code class="json-response-el">{{ ep.response | tojson(indent=2) }}</code></pre>
        </div>

        {% elif ep.type == "pricing" %}
        <div class="flex items-center gap-3">
          <span class="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41L11 3.83V3H10.17L1 12.17V13l9.59 9.59a2 2 0 002.82 0l7.18-7.18a2 2 0 000-2.82z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>
          </span>
          <h1 class="text-3xl font-bold tracking-tight">{{ ep.title }}</h1>
        </div>
        <p class="mt-4 text-slate-600 leading-relaxed">{{ ep.description }}</p>

        <div class="relative mt-6 max-w-sm">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input id="pricing-search" type="text" placeholder="Davlat nomi yoki kodi bo'yicha qidirish..."
            class="w-full text-sm bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400">
        </div>

        <div class="rounded-xl border border-slate-100 overflow-hidden mt-6">
          <table class="w-full text-sm">
            <thead class="bg-slate-50">
              <tr>
                <th class="text-left px-4 py-3 w-14">#</th>
                <th class="text-left px-4 py-3">Davlat</th>
                <th class="text-left px-4 py-3 w-24">Kod</th>
                <th class="text-right px-4 py-3 w-36">Narxi (UZS)</th>
              </tr>
            </thead>
            <tbody id="pricing-tbody" class="divide-y divide-slate-100">
              {% for row in ep.pricing %}
              <tr class="pricing-row" data-label="{{ row.name|lower }} {{ row.code|lower }}">
                <td class="px-4 py-3 text-slate-400 font-mono text-[12.5px]">{{ row.no }}</td>
                <td class="px-4 py-3 text-slate-700">{{ row.name }}</td>
                <td class="px-4 py-3"><code class="text-[12.5px] font-mono font-semibold text-slate-800">{{ row.code }}</code></td>
                <td class="px-4 py-3 text-right font-mono text-[13px] font-semibold text-slate-900">{{ "{:,}".format(row.price).replace(",", " ") }}</td>
              </tr>
              {% endfor %}
            </tbody>
          </table>
          <p id="pricing-empty" class="hidden text-center text-sm text-slate-400 py-8">Hech narsa topilmadi</p>
        </div>

        {% else %}
        <div class="flex items-center gap-3 flex-wrap">
          <span class="method-badge method-badge-{{ ep.method|lower }}">{{ ep.method }}</span>
          <code class="text-[15px] font-mono text-slate-700">{{ ep.path }}</code>
        </div>
        <h1 class="text-3xl font-bold tracking-tight mt-3">{{ ep.title }}</h1>
        <p class="mt-4 text-slate-600 leading-relaxed">{{ ep.description }}</p>

        {% if ep.params %}
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mt-10 mb-4">Parametrlar</h2>
        <div class="rounded-xl border border-slate-100 divide-y divide-slate-100 overflow-hidden">
          {% for p in ep.params %}
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
              <span class="code-window-title req-lang-label">cURL &middot; So'rov</span>
              <button class="copy-btn">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                <span>Copy</span>
              </button>
            </div>
            <pre class="code-window-body"><code class="code-request-el">{{ ep.code.curl }}</code></pre>
          </div>
          <script type="application/json" class="lang-data-el">
            {
              "curl": {{ ep.code.curl | tojson }},
              "php": {{ ep.code.php | tojson }},
              "python": {{ ep.code.python | tojson }},
              "cpp": {{ ep.code.cpp | tojson }},
              "csharp": {{ ep.code.csharp | tojson }},
              "java": {{ ep.code.java | tojson }}
            }
          </script>
        </div>

        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mt-10 mb-4">Namuna javob</h2>

        <div class="code-card">
          <div class="code-tabs">
            <button class="resp-tab active" data-resp="success">200 OK</button>
            <button class="resp-tab" data-resp="error">{{ ep.error_status }}</button>
          </div>
          <div class="code-body-wrap">
            <div class="code-window-header">
              <span class="response-status resp-status-el">200 OK</span>
              <span class="code-window-title">JSON</span>
              <button class="copy-btn">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
                <span>Copy</span>
              </button>
            </div>
            <pre class="code-window-body"><code class="json-response-el"></code></pre>
          </div>
          <script type="application/json" class="resp-data-el">
            {
              "success": {"label": "200 OK", "body": {{ ep.response | tojson }} },
              "error": {"label": {{ ep.error_status | tojson }}, "body": {{ ep.error_body | tojson }} }
            }
          </script>
        </div>
        {% endif %}

      </section>
      {% endfor %}

      <footer class="border-t border-slate-100">
        <div class="px-10 py-12 grid sm:grid-cols-3 gap-10">
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
              <li><a href="#test" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h7l-1 8 11-14h-8l1-6z"/></svg>
                Test uchun</a></li>
              <li><a href="#balance" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20"/><circle cx="17" cy="15" r="1"/></svg>
                Balans</a></li>
              <li><a href="#nomer-olish" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.12.81.31 1.6.57 2.36a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.72-1.14a2 2 0 012.11-.45c.76.26 1.55.45 2.36.57A2 2 0 0122 16.92z"/></svg>
                Nomer olish</a></li>
              <li><a href="#kod-olish" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                Kod olish</a></li>
              <li><a href="#xato-kodlari" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                Xato kodlari</a></li>
              <li><a href="#narxlar" class="footer-link flex items-center gap-2 hover:text-brand-600 transition">
                <svg class="footer-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41L11 3.83V3H10.17L1 12.17V13l9.59 9.59a2 2 0 002.82 0l7.18-7.18a2 2 0 000-2.82z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>
                Narxlar</a></li>
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
          <div class="px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
            <span>© 2026 {{ brand }} · Barcha huquqlar himoyalangan</span>
            <span>REST API · JSON · API Key</span>
          </div>
        </div>
      </footer>
    </main>
  </div>

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

app.include_router(v1_router)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Asosiy sahifa — xush kelibsiz / landing page."""
    return HTMLResponse(render("index.html"))


@app.get("/docs", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    """
    Custom API hujjatlar sahifasi — BITTA uzluksiz sahifa.
    Barcha bo'limlar ketma-ket joylashgan; sidebar havolalari va eski
    ?section=xxx havolalari sahifa ichidagi tegishli bo'limga scroll qiladi.
    """
    return HTMLResponse(render(
        "docs.html",
        endpoints=ENDPOINTS,
        languages=LANGUAGES,
    ))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
