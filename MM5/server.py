import os
import sqlite3
import json
import random
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

DB_NAME = "users.db"
NEWS_DB_NAME = "news.db"
NEWS_EVENTS_FILE = "news_events.json"

TIME = 0


def is_localhost(handler) -> bool:
    ip = handler.client_address[0]
    return ip == "127.0.0.1" or ip == "::1"


def read_json_body(handler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def init_users_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                balance INTEGER NOT NULL DEFAULT 0
            )
            """
        )
    finally:
        conn.close()


def init_news_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER NOT NULL,
                headline TEXT NOT NULL,
                body TEXT NOT NULL,
                effects_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
    finally:
        conn.close()


def init_stocks_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT NOT NULL,
                price REAL NOT NULL,
                prev_price REAL NOT NULL
            )
            """
        )
    finally:
        conn.close()


DEFAULT_STOCKS = [
    ("AAPL", "Apple Inc.", "Tech", 184.22),
    ("MSFT", "Microsoft Corporation", "Tech", 412.10),
    ("NVDA", "NVIDIA Corporation", "Tech", 885.40),
    ("GOOGL", "Alphabet Inc.", "Tech", 151.77),

    ("JPM", "JPMorgan Chase & Co.", "Finance", 172.33),
    ("V", "Visa Inc.", "Finance", 273.90),
    ("GS", "Goldman Sachs Group, Inc.", "Finance", 388.55),

    ("XOM", "Exxon Mobil Corporation", "Energy / Materials", 113.08),
    ("BHP", "BHP Group Limited", "Energy / Materials", 59.42),
    ("RIO", "Rio Tinto Group", "Energy / Materials", 67.18),

    ("BA", "The Boeing Company", "Industrials", 190.14),
    ("CAT", "Caterpillar Inc.", "Industrials", 327.66),
    ("TSLA", "Tesla, Inc.", "Industrials", 212.73),

    ("WMT", "Walmart Inc.", "Consumer", 167.21),
    ("MCD", "McDonald's Corporation", "Consumer", 289.95),

    ("GME", "GameStop Corp.", "Meme", 18.42),
]


def ensure_initial_stocks(users_db_path: str) -> None:
    conn = sqlite3.connect(users_db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
        if count > 0:
            return

        conn.executemany(
            "INSERT INTO stocks (symbol, name, industry, price, prev_price) VALUES (?, ?, ?, ?, ?)",
            [(sym, name, ind, price, price) for (sym, name, ind, price) in DEFAULT_STOCKS],
        )
        conn.commit()
    finally:
        conn.close()


def normalise_username(raw: str) -> str:
    u = raw.strip()
    if not u:
        return ""

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    u = "".join(ch for ch in u if ch in allowed)

    return u[:24]


def normalise_symbol(raw: str) -> str:
    s = raw.strip().upper()
    if not s:
        return ""
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    s = "".join(ch for ch in s if ch in allowed)
    return s[:10]


def format_time(t: int) -> str:
    return f"Y{t//4 + 1}Q{t%4 + 1}"


def load_news_events(projroot: Path) -> list[dict]:
    p = projroot / NEWS_EVENTS_FILE
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def insert_news_items(news_db_path: str, time_value: int, items: list[dict]) -> None:
    if not items:
        return
    conn = sqlite3.connect(news_db_path)
    try:
        cur = conn.cursor()
        for ev in items:
            headline = str(ev.get("headline", "")).strip() or "Untitled"
            body = str(ev.get("body", "")).strip() or ""
            effects = ev.get("effects") or {}
            cur.execute(
                "INSERT INTO news (time, headline, body, effects_json) VALUES (?, ?, ?, ?)",
                (time_value, headline, body, json.dumps(effects)),
            )
        conn.commit()
    finally:
        conn.close()


def ensure_initial_news(news_db_path: str, events_bank: list[dict]) -> None:
    conn = sqlite3.connect(news_db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM news").fetchone()[0]
    finally:
        conn.close()

    if count > 0:
        return

    # Populate turn 0 with up to 3 events (as requested)
    if not events_bank:
        insert_news_items(news_db_path, 0, [{
            "headline": "No news bank found",
            "body": "news_events.json is missing or invalid.",
            "effects": {}
        }])
        return

    seed_items = events_bank[:3]
    insert_news_items(news_db_path, 0, seed_items)


def generate_news_for_turn(events_bank: list[dict], k_min: int = 1, k_max: int = 3) -> list[dict]:
    if not events_bank:
        return []
    k = random.randint(k_min, k_max)
    # Repeatable events are allowed, so we can sample with replacement
    return [random.choice(events_bank) for _ in range(k)]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)

        if u.path == "/user":
            qs = parse_qs(u.query)
            username = normalise_username((qs.get("username") or [""])[0])

            conn = sqlite3.connect(self.server.users_db_path)
            try:
                row = conn.execute(
                    "SELECT username, balance FROM users WHERE username = ?",
                    (username,),
                ).fetchone()
            finally:
                conn.close()

            if not row:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "unknown user"}).encode())
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "username": row[0],
                "balance": row[1],
                "time": TIME,
                "time_string": format_time(TIME),
            }).encode())
            return

        if u.path == "/users":
            conn = sqlite3.connect(self.server.users_db_path)
            try:
                rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
            finally:
                conn.close()

            users = [r[0] for r in rows]

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "users": users}).encode())
            return

        if u.path == "/news":
            qs = parse_qs(u.query)
            try:
                limit = int((qs.get("limit") or ["50"])[0])
            except Exception:
                limit = 50
            try:
                offset = int((qs.get("offset") or ["0"])[0])
            except Exception:
                offset = 0

            limit = max(1, min(limit, 500))
            offset = max(0, offset)

            conn = sqlite3.connect(self.server.news_db_path)
            try:
                rows = conn.execute(
                    "SELECT id, time, headline, body, effects_json FROM news ORDER BY time DESC, id DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            finally:
                conn.close()

            items = []
            for r in rows:
                items.append({
                    "id": r[0],
                    "time": r[1],
                    "time_string": format_time(r[1]),
                    "headline": r[2],
                    "body": r[3],
                    "effects_json": r[4],
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "items": items}).encode())
            return

        if u.path == "/stocks":
            conn = sqlite3.connect(self.server.users_db_path)
            try:
                rows = conn.execute(
                    "SELECT symbol, name, industry, price, prev_price FROM stocks ORDER BY industry, symbol"
                ).fetchall()
            finally:
                conn.close()

            stocks = []
            for r in rows:
                stocks.append({
                    "symbol": r[0],
                    "name": r[1],
                    "industry": r[2],
                    "price": r[3],
                    "prev_price": r[4],
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "time": TIME, "time_string": format_time(TIME), "stocks": stocks}).encode())
            return

        if u.path == "/stock":
            qs = parse_qs(u.query)
            symbol = normalise_symbol((qs.get("symbol") or [""])[0])
            if not symbol:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "missing symbol"}).encode())
                return

            conn = sqlite3.connect(self.server.users_db_path)
            try:
                row = conn.execute(
                    "SELECT symbol, name, industry, price, prev_price FROM stocks WHERE symbol = ?",
                    (symbol,),
                ).fetchone()
            finally:
                conn.close()

            if not row:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "unknown symbol"}).encode())
                return

            stock = {
                "symbol": row[0],
                "name": row[1],
                "industry": row[2],
                "price": row[3],
                "prev_price": row[4],
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "time": TIME, "time_string": format_time(TIME), "stock": stock}).encode())
            return


        return super().do_GET()

    def do_POST(self):
        global TIME

        if self.path == "/admin":
            if not is_localhost(self):
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "forbidden"}).encode("utf-8"))
                return

            data = read_json_body(self)
            cmd = data.get("cmd", "")

            users_conn = sqlite3.connect(self.server.users_db_path)
            users_cur = users_conn.cursor()

            try:
                if cmd == "set_balance":
                    username = normalise_username(str(data.get("username", "")))
                    amount = int(data.get("amount", 0))

                    users_cur.execute("UPDATE users SET balance = ? WHERE username = ?", (amount, username))
                    users_conn.commit()

                    if users_cur.rowcount == 0:
                        self.send_response(404)
                        payload = {"ok": False, "error": "user not found"}
                    else:
                        self.send_response(200)
                        payload = {"ok": True, "cmd": cmd, "username": username, "balance": amount}

                elif cmd == "adjust_balance":
                    username = normalise_username(str(data.get("username", "")))
                    delta = int(data.get("delta", 0))

                    users_cur.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (delta, username))
                    users_conn.commit()

                    if users_cur.rowcount == 0:
                        self.send_response(404)
                        payload = {"ok": False, "error": "user not found"}
                    else:
                        users_cur.execute("SELECT balance FROM users WHERE username = ?", (username,))
                        new_balance = users_cur.fetchone()[0]
                        self.send_response(200)
                        payload = {"ok": True, "cmd": cmd, "username": username, "balance": new_balance}

                elif cmd == "inc_time":
                    step = int(data.get("step", 1))
                    if step < 1:
                        step = 1

                    # Advance one turn at a time so we can generate news per turn
                    for _ in range(step):
                        TIME += 1
                        new_items = generate_news_for_turn(self.server.news_events_bank)
                        insert_news_items(self.server.news_db_path, TIME, new_items)

                    self.send_response(200)
                    payload = {"ok": True, "cmd": cmd, "time": TIME}

                else:
                    self.send_response(400)
                    payload = {"ok": False, "error": "unknown cmd"}

            finally:
                users_conn.close()

            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if self.path == "/transfer":
            data = read_json_body(self)

            from_user = normalise_username(str(data.get("from", "")))
            to_user = normalise_username(str(data.get("to", "")))
            try:
                amount = int(data.get("amount", 0))
            except Exception:
                amount = 0

            if not from_user or not to_user:
                self.send_response(400)
                payload = {"ok": False, "error": "missing user"}
            elif from_user == to_user:
                self.send_response(400)
                payload = {"ok": False, "error": "cannot send to yourself"}
            elif amount <= 0:
                self.send_response(400)
                payload = {"ok": False, "error": "amount must be positive"}
            else:
                conn = sqlite3.connect(self.server.users_db_path)
                try:
                    cur = conn.cursor()
                    cur.execute("BEGIN IMMEDIATE")

                    row_from = cur.execute(
                        "SELECT balance FROM users WHERE username = ?",
                        (from_user,),
                    ).fetchone()
                    row_to = cur.execute(
                        "SELECT balance FROM users WHERE username = ?",
                        (to_user,),
                    ).fetchone()

                    if not row_from or not row_to:
                        conn.rollback()
                        self.send_response(404)
                        payload = {"ok": False, "error": "unknown user"}
                    elif row_from[0] < amount:
                        conn.rollback()
                        self.send_response(400)
                        payload = {"ok": False, "error": "insufficient funds"}
                    else:
                        cur.execute(
                            "UPDATE users SET balance = balance - ? WHERE username = ?",
                            (amount, from_user),
                        )
                        cur.execute(
                            "UPDATE users SET balance = balance + ? WHERE username = ?",
                            (amount, to_user),
                        )

                        new_from = cur.execute(
                            "SELECT balance FROM users WHERE username = ?",
                            (from_user,),
                        ).fetchone()[0]

                        new_to = cur.execute(
                            "SELECT balance FROM users WHERE username = ?",
                            (to_user,),
                        ).fetchone()[0]

                        conn.commit()
                        self.send_response(200)
                        payload = {
                            "ok": True,
                            "from": from_user,
                            "to": to_user,
                            "amount": amount,
                            "from_balance": new_from,
                            "to_balance": new_to,
                        }
                finally:
                    conn.close()

            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if self.path != "/register":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        form = parse_qs(body)

        raw_username = (form.get("username") or [""])[0]
        username = normalise_username(raw_username)

        if not username:
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()
            return

        conn = sqlite3.connect(self.server.users_db_path)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (username, balance) VALUES (?, ?)",
                (username, 0)
            )
            conn.commit()
        finally:
            conn.close()

        self.send_response(303)
        self.send_header("Location", f"/dashboard.html?username={quote(username)}")
        self.end_headers()

    def log_message(self, format, *args):
        try:
            path = self.path.split("?", 1)[0]
        except Exception:
            path = self.path

        if path in ("/user", "/users", "/news", "/stocks", "/stock"):
            return

        super().log_message(format, *args)


def main() -> None:
    host = "0.0.0.0"
    port = 8888

    projroot = Path(__file__).resolve().parent
    webroot = projroot / "webapp"
    if not webroot.is_dir():
        raise SystemExit(f"webapp directory not found: {webroot}")

    users_db_path = projroot / DB_NAME
    news_db_path = projroot / NEWS_DB_NAME

    init_users_db(users_db_path)
    init_stocks_db(users_db_path)
    init_news_db(news_db_path)

    events_bank = load_news_events(projroot)

    # Turn 0 population (as requested)
    ensure_initial_news(str(news_db_path), events_bank)

    ensure_initial_stocks(str(users_db_path))

    os.chdir(webroot)

    server = ThreadingHTTPServer((host, port), Handler)
    server.users_db_path = str(users_db_path)
    server.news_db_path = str(news_db_path)
    server.news_events_bank = events_bank

    print(f"Serving {webroot} on http://{host}:{port}")
    print(f"Users DB at {users_db_path}")
    print(f"News DB at {news_db_path}")
    server.serve_forever()


if __name__ == "__main__":
    main()
