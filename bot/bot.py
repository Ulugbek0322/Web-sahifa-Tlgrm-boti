# -*- coding: utf-8 -*-
"""
Deutsch Mentor — ustozning Telegram boti.

Ikki iş bajaradi:
  1. Saytdagi "Arizani yuboriş" tugmasi bosilganda arizani ustozning Telegramiga yuboradi
     (HTTP manzil: POST /api/ariza).
  2. Botga yozgan odamlarga javob beradi va ularning xabarlarini ustozga yetkazadi.

Faqat Python'ning özi kerak (3.9 yoki yangi), qöşimça kutubxona örnatiş şart emas.
Sozlamalar: config.json. Işga tuşiriş: start.bat (Windows) yoki `python bot.py`.
"""
import html
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
STATE_PATH = os.path.join(HERE, "state.json")

# ---------------------------------------------------------------- sozlamalar
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


CONFIG = load_json(CONFIG_PATH, {})
TOKEN = (CONFIG.get("bot_token") or "").strip()
TEACHER = (CONFIG.get("teacher_username") or "").lstrip("@").strip().lower()
TEACHER_NAME = CONFIG.get("teacher_name") or "Ustoz"
PORT = int(CONFIG.get("port") or 8080)
ALLOWED_ORIGINS = CONFIG.get("allowed_origins") or ["*"]

if not TOKEN or "BU_YERGA" in TOKEN:
    print("XATO: config.json faylida bot_token yozilmagan.")
    print("@BotFather'dan olingan tokenni config.json içidagi \"bot_token\" qatoriga qöying.")
    input("Çiqiş uçun Enter bosing...")
    sys.exit(1)

API = "https://api.telegram.org/bot" + TOKEN + "/"
state_lock = threading.Lock()
STATE = load_json(STATE_PATH, {})


def save_state():
    with state_lock:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(STATE, f, ensure_ascii=False, indent=2)


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- Telegram API
def tg(method, payload=None, timeout=40):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(API + method, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        log("Telegram xatosi", method, e.code, body[:200])
        return {"ok": False, "error_code": e.code, "description": body}
    except Exception as e:  # tarmoq uzilişi va h.k.
        log("Tarmoq xatosi", method, e)
        return {"ok": False, "description": str(e)}


def send(chat_id, text):
    return tg("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                              "disable_web_page_preview": True})


def teacher_chat():
    return STATE.get("teacher_chat_id")


# ---------------------------------------------------------------- bot xabarlari
WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "Bu <b>Deutsch Mentor</b> boti. Nemis tili ustozi <b>{name}</b> bilan boğlaniş uçun "
    "şu yerga yozişingiz mumkin, xabaringiz ustozga yetkaziladi.\n\n"
    "Avval saytdagi bepul testni topşirib, darajangizni bilib oling."
)


def handle_update(upd):
    msg = upd.get("message") or upd.get("edited_message")
    if not msg or "chat" not in msg:
        return
    chat_id = msg["chat"]["id"]
    user = msg.get("from") or {}
    username = (user.get("username") or "").lower()
    text = (msg.get("text") or "").strip()

    # Ustozning öziga tegişli
    if TEACHER and username == TEACHER:
        if STATE.get("teacher_chat_id") != chat_id:
            STATE["teacher_chat_id"] = chat_id
            save_state()
            log("Ustoz röyxatdan ötdi, chat_id =", chat_id)
        if text.startswith("/start"):
            send(chat_id, "✅ Siz ustoz sifatida röyxatdan ötdingiz.\n"
                          "Saytdan kelgan arizalar va botga yozilgan xabarlar şu yerga keladi.")
        return

    # Boşqa foydalanuvçilar
    if text.startswith("/start"):
        send(chat_id, WELCOME.format(name=html.escape(TEACHER_NAME)))
        return

    t = teacher_chat()
    who = html.escape((user.get("first_name") or "") + " " + (user.get("last_name") or "")).strip()
    handle = "@" + html.escape(user.get("username")) if user.get("username") else "username yöq"
    if t:
        tg("forwardMessage", {"chat_id": t, "from_chat_id": chat_id, "message_id": msg["message_id"]})
        send(t, "✉️ Botga yangi xabar: <b>{}</b> ({})".format(who or "Nomsiz", handle))
        send(chat_id, "Rahmat! Xabaringiz ustozga yetkazildi, tez orada javob beradi.")
    else:
        send(chat_id, "Rahmat! Ustoz hozirça botga ulanmagan. Iltimos, Telegramda @{} ga yozing.".format(TEACHER))


def polling_loop():
    offset = STATE.get("offset", 0)
    log("Bot Telegram xabarlarini kutmoqda...")
    while True:
        res = tg("getUpdates", {"offset": offset, "timeout": 30, "allowed_updates": ["message", "edited_message"]})
        if not res.get("ok"):
            if res.get("error_code") == 401:
                log("Token notöğri. config.json'dagi bot_token'ni tekşiring.")
            elif res.get("error_code") == 409:
                log("Bu bot boşqa joyda ham işlab turibdi. Faqat bitta nusxasini qoldiring.")
            time.sleep(5)
            continue
        for upd in res.get("result", []):
            offset = upd["update_id"] + 1
            try:
                handle_update(upd)
            except Exception as e:
                log("Xabarni qayta işlaşda xato:", e)
        if res.get("result"):
            STATE["offset"] = offset
            save_state()


# ---------------------------------------------------------------- saytdan ariza
RATE = {}  # ip -> [vaqtlar]
RATE_LIMIT, RATE_WINDOW = 5, 600  # 10 daqiqada 5 tadan köp emas


def rate_ok(ip):
    now = time.time()
    hits = [t for t in RATE.get(ip, []) if now - t < RATE_WINDOW]
    if len(hits) >= RATE_LIMIT:
        RATE[ip] = hits
        return False
    hits.append(now)
    RATE[ip] = hits
    return True


def clean(v, n):
    return html.escape(str(v or "").strip()[:n])


def format_lead(d):
    lines = ["🆕 <b>Yangi ariza — Deutsch Mentor</b>", ""]
    lines.append("👤 Ism: <b>{}</b>".format(clean(d.get("name"), 80)))
    lines.append("📞 Telefon: {}".format(clean(d.get("phone"), 40)))
    if d.get("course"):
        lines.append("📚 Kurs: {}".format(clean(d.get("course"), 120)))
    if d.get("goal"):
        lines.append("🎯 Maqsad: {}".format(clean(d.get("goal"), 120)))
    if d.get("result"):
        lines.append("📝 Test natijasi: <b>{}</b>".format(clean(d.get("result"), 60)))
    if d.get("message"):
        lines.append("💬 Izoh: {}".format(clean(d.get("message"), 800)))
    lines.append("")
    lines.append("🕒 " + datetime.now().strftime("%d.%m.%Y %H:%M"))
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        origin = self.headers.get("Origin") or "*"
        allow = "*" if "*" in ALLOWED_ORIGINS else (origin if origin in ALLOWED_ORIGINS else "")
        if allow:
            self.send_header("Access-Control-Allow-Origin", allow)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/health"):
            return self._json(200, {"ok": True, "teacher_connected": bool(teacher_chat())})
        self._json(404, {"ok": False})

    def do_POST(self):
        if self.path.rstrip("/") != "/api/ariza":
            return self._json(404, {"ok": False, "error": "Topilmadi"})
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        if not rate_ok(ip):
            return self._json(429, {"ok": False, "error": "Juda köp ariza. Birozdan keyin urinib köring."})
        try:
            size = int(self.headers.get("Content-Length") or 0)
            if size > 10000:
                return self._json(413, {"ok": False, "error": "Ariza juda katta"})
            d = json.loads(self.rfile.read(size).decode("utf-8") or "{}")
        except Exception:
            return self._json(400, {"ok": False, "error": "Notöğri ma'lumot"})

        if d.get("website"):  # spam-botlar uçun yaşirin maydon
            return self._json(200, {"ok": True})
        name = str(d.get("name") or "").strip()
        phone_digits = "".join(c for c in str(d.get("phone") or "") if c.isdigit())
        if len(name) < 2 or len(phone_digits) < 9:
            return self._json(400, {"ok": False, "error": "Ism va telefon raqamini töliq kiriting"})

        t = teacher_chat()
        if not t:
            log("Ariza keldi, lekin ustoz hali botga /start yozmagan.")
            return self._json(503, {"ok": False, "error": "Ustoz hali botni ulamagan"})
        res = send(t, format_lead(d))
        if not res.get("ok"):
            return self._json(502, {"ok": False, "error": "Telegramga yuborib bölmadi"})
        log("Yangi ariza yuborildi:", name)
        return self._json(200, {"ok": True})

    def log_message(self, fmt, *args):  # standart loglarni öçiramiz
        pass


def main():
    me = tg("getMe")
    if not me.get("ok"):
        log("Botga ulanib bölmadi. Token va internetni tekşiring.")
    else:
        log("Bot: @" + me["result"]["username"])
    if not teacher_chat():
        log("DIQQAT: ustoz (@{}) botga /start yozişi kerak, şunda arizalar unga keladi.".format(TEACHER))
    threading.Thread(target=polling_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log("Ariza qabul qiliş manzili: http://localhost:{}/api/ariza".format(PORT))
    log("Töxtatiş uçun bu oynani yoping yoki Ctrl+C bosing.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
