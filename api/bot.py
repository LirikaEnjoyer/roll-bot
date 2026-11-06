import json
import os
import random
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get("BOT_TOKEN", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")

HELP = (
    "Использование:\n"
    "/roll — число от 1 до 100\n"
    "/roll 50 — число от 1 до 50\n"
    "/roll 10 20 — число от 10 до 20\n"
    "/roll пицца суши роллы — случайное слово из списка\n"
    "/roll идти в кино, сидеть дома — варианты через запятую\n"
    "/howgay — случайный процент"
)


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    urllib.request.urlopen(req, timeout=8)


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def build_reply(text):
    parts = text.split(maxsplit=1)
    if not parts:
        return None
    command = parts[0].split("@")[0].lower()
    if command == "/howgay":
        return f"🏳️‍🌈 I’m {random.randint(0, 100)}% gay"
    if command != "/roll":
        return None

    rest = parts[1].strip() if len(parts) > 1 else ""
    args = rest.split()

    # Режим чисел: пусто, одно или два целых числа без запятых
    if "," not in rest and len(args) <= 2 and all(is_int(a) for a in args):
        if len(args) == 0:
            low, high = 1, 100
        elif len(args) == 1:
            low, high = 1, int(args[0])
        else:
            low, high = int(args[0]), int(args[1])
        if low > high:
            low, high = high, low
        return f"🎲 {random.randint(low, high)} (от {low} до {high})"

    # Режим слов: через запятую или через пробел
    if "," in rest:
        options = [o.strip() for o in rest.split(",") if o.strip()]
    else:
        options = args

    if len(options) < 2:
        return HELP
    return f"🎯 {random.choice(options)}"


class handler(BaseHTTPRequestHandler):
    def _ok(self, body=b"ok"):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._ok(b"bot is alive")

    def do_POST(self):
        # Проверка секрета, чтобы никто посторонний не дёргал функцию
        if SECRET and self.headers.get("X-Telegram-Bot-Api-Secret-Token") != SECRET:
            self.send_response(403)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            update = json.loads(self.rfile.read(length) or b"{}")
            message = update.get("message") or {}
            text = message.get("text", "")
            chat_id = (message.get("chat") or {}).get("id")

            reply = build_reply(text) if chat_id else None
            if reply:
                send_message(chat_id, reply)
        except Exception as e:
            print("error:", e)

        # Всегда отвечаем 200, иначе Telegram будет слать сообщение повторно
        self._ok()

