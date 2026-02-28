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
        conn.commit()
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
        conn.commit()
    finally:
        conn.close()


def init_stocks_db(db_path: Path) -> None:
    """Snapshot table: current price state used by frontend."""
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
        conn.commit()
    finally:
        conn.close()


def init_stock_prices_db(db_path: Path) -> None:
    """History table: append-only (symbol,time)->price."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_prices (
                symbol TEXT NOT NULL,
                time INTEGER NOT NULL,
                price REAL NOT NULL,
                PRIMARY KEY (symbol, time),
                FOREIGN KEY (symbol) REFERENCES stocks(symbol)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_stocks_if_empty(db_path: Path) -> None:
    stocks_seed = [
        ("AAPL", "Apple Inc.", "Tech", 184.22),
        ("MSFT", "Microsoft", "Tech", 412.10),
        ("NVDA", "NVIDIA", "Tech", 795.50),
        ("GOOGL", "Alphabet", "Tech", 141.32),

        ("JPM", "JPMorgan Chase", "Finance", 166.18),
        ("V", "Visa", "Finance", 273.60),
        ("GS", "Goldman Sachs", "Finance", 381.12),

        ("XOM", "ExxonMobil", "Energy/Materials", 104.70),
        ("BHP", "BHP Group", "Energy/Materials", 58.40),
        ("RIO", "Rio Tinto", "Energy/Materials", 71.25),

        ("BA", "Boeing", "Industrials", 192.44),
        ("CAT", "Caterpillar", "Industrials", 308.55),
        ("TSLA", "Tesla", "Industrials", 188.90),

        ("WMT", "Walmart", "Consumer", 168.12),
        ("MCD", "McDonald's", "Consumer", 292.05),

        ("GME", "GameStop", "Meme", 17.80),
    ]

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        count = cur.execute("SELECT COUNT(*) FROM stocks").fetchone()[0]
        if count > 0:
            return
        for sym, name, industry, price in stocks_seed:
            cur.execute(
                "INSERT INTO stocks(symbol, name, industry, price, prev_price) VALUES(?,?,?,?,?)",
                (sym, name, industry, float(price), float(price)),
            )
        conn.commit()
    finally:
        conn.close()


def ensure_history_at_time(db_path: Path, time_value: int) -> None:
    """Make sure every stock has a history row at time_value."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        rows = cur.execute("SELECT symbol, price FROM stocks").fetchall()
        for sym, price in rows:
            cur.execute(
                "INSERT OR IGNORE INTO stock_prices(symbol, time, price) VALUES(?,?,?)",
                (sym, int(time_value), float(price)),
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
    return [random.choice(events_bank) for _ in range(k)]



def tick_stock_market(users_db_path: str, news_items: list[dict], time_value: int) -> None:
    """Advance all stock prices by one tick and append history.

    News effects schema (v1):
      Each generated news item may contain:
        effects: {
          "stocks": [
            {
              "symbol": "NVDA",
              "ret_mu": -0.002,          # additive drift to return this tick (eg -0.2%)
              "ret_sigma_mult": 1.2,     # multiplies the base return draw's volatility
              "shock": -0.01             # additive one-off shock return (eg -1%)
            }
          ]
        }

    Any missing keys are treated as neutral. If "stocks" is absent, the item has no stock effects.
    """
    # Collect per-symbol effects (we apply them in aggregate below).
    effects_by_symbol: dict[str, list[dict]] = {}
    for item in (news_items or []):
        effects = item.get("effects") or {}
        stock_effects = effects.get("stocks") or []
        if isinstance(stock_effects, list):
            for eff in stock_effects:
                sym = str(eff.get("symbol", "")).strip().upper()
                if not sym:
                    continue
                effects_by_symbol.setdefault(sym, []).append(eff)

    conn = sqlite3.connect(users_db_path)
    try:
        cur = conn.cursor()
        rows = cur.execute("SELECT symbol, price FROM stocks").fetchall()

        for sym, old_price in rows:
            price = float(old_price)

            # Base move: small random return with mild tails.
            base_ret = random.gauss(0.0, 0.015)

            # Apply all effects targeting this symbol.
            mu_add = 0.0
            shock_add = 0.0
            sigma_mult = 1.0

            for eff in effects_by_symbol.get(sym, []):
                try:
                    mu_add += float(eff.get("ret_mu", 0.0) or 0.0)
                except Exception:
                    pass
                try:
                    shock_add += float(eff.get("shock", 0.0) or 0.0)
                except Exception:
                    pass
                try:
                    sigma_mult *= float(eff.get("ret_sigma_mult", 1.0) or 1.0)
                except Exception:
                    pass

            ret = base_ret * sigma_mult + mu_add + shock_add

            # Safety clamp (prevents single-tick nukes while still allowing drama).
            if ret > 0.25:
                ret = 0.25
            elif ret < -0.25:
                ret = -0.25

            new_price = max(0.01, price * (1.0 + ret))

            cur.execute(
                "UPDATE stocks SET prev_price = ?, price = ? WHERE symbol = ?",
                (price, new_price, sym),
            )
            cur.execute(
                "INSERT OR REPLACE INTO stock_prices(symbol, time, price) VALUES(?,?,?)",
                (sym, int(time_value), float(new_price)),
            )

        conn.commit()
    finally:
        conn.close()


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)

        if u.path == "/user":
            qs = parse_qs(u.query)
            username = normalise_username((qs.get("username") or [""])[0])

            conn = sqlite3.connect(self.server.users_db_path)
            try:
                row = conn.execute(
                    "SELECT balance FROM users WHERE username = ?",
                    (username,),
                ).fetchone()
            finally:
                conn.close()

            if not row:
                self.send_response(404)
                payload = {"ok": False, "error": "user not found"}
            else:
                self.send_response(200)
                payload = {
                    "ok": True,
                    "username": username,
                    "balance": row[0],
                    "time": TIME,
                    "time_string": format_time(TIME),
                }

            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if u.path == "/users":
            conn = sqlite3.connect(self.server.users_db_path)
            try:
                rows = conn.execute("SELECT username, balance FROM users ORDER BY username").fetchall()
            finally:
                conn.close()

            self.send_response(200)
            payload = {"ok": True, "users": [{"username": r[0], "balance": r[1]} for r in rows]}
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if u.path == "/news":
            qs = parse_qs(u.query)
            try:
                time_value = int((qs.get("time") or [str(TIME)])[0])
            except Exception:
                time_value = TIME

            conn = sqlite3.connect(self.server.news_db_path)
            try:
                rows = conn.execute(
                    "SELECT time, headline, body, effects_json FROM news WHERE time = ? ORDER BY id",
                    (time_value,),
                ).fetchall()
            finally:
                conn.close()

            items = []
            for t, headline, body, effects_json in rows:
                try:
                    effects = json.loads(effects_json) if effects_json else {}
                except Exception:
                    effects = {}
                items.append({
                    "time": t,
                    "time_string": format_time(t),
                    "headline": headline,
                    "body": body,
                    "effects": effects,
                })

            self.send_response(200)
            payload = {"ok": True, "time": time_value, "time_string": format_time(time_value), "items": items}
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
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
            for sym, name, industry, price, prev in rows:
                stocks.append({
                    "symbol": sym,
                    "name": name,
                    "industry": industry,
                    "price": float(price),
                    "prev_price": float(prev),
                })

            self.send_response(200)
            payload = {"ok": True, "time": TIME, "time_string": format_time(TIME), "stocks": stocks}
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if u.path == "/stock":
            qs = parse_qs(u.query)
            symbol = (qs.get("symbol") or [""])[0].strip().upper()

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
                payload = {"ok": False, "error": "stock not found"}
            else:
                sym, name, industry, price, prev = row
                payload = {
                    "ok": True,
                    "time": TIME,
                    "time_string": format_time(TIME),
                    "stock": {
                        "symbol": sym,
                        "name": name,
                        "industry": industry,
                        "price": float(price),
                        "prev_price": float(prev),
                    },
                }
                self.send_response(200)

            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        if u.path == "/stock_history":
            qs = parse_qs(u.query)
            symbol = (qs.get("symbol") or [""])[0].strip().upper()
            try:
                limit = int((qs.get("limit") or ["120"])[0])
            except Exception:
                limit = 120
            limit = max(1, min(limit, 2000))

            conn = sqlite3.connect(self.server.users_db_path)
            try:
                rows = conn.execute(
                    "SELECT time, price FROM stock_prices WHERE symbol = ? ORDER BY time DESC LIMIT ?",
                    (symbol, limit),
                ).fetchall()
            finally:
                conn.close()

            # reverse to ascending time for plotting
            series = []
            for t, price in reversed(rows):
                series.append({"time": int(t), "time_string": format_time(int(t)), "price": float(price)})

            self.send_response(200)
            payload = {"ok": True, "symbol": symbol, "time": TIME, "time_string": format_time(TIME), "series": series}
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        global TIME

        u = urlparse(self.path)

        if u.path == "/admin":
            if not is_localhost(self):
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "forbidden"}).encode("utf-8"))
                return

            data = read_json_body(self)
            cmd = (data.get("cmd") or "").strip()

            users_conn = sqlite3.connect(self.server.users_db_path)
            try:
                users_cur = users_conn.cursor()

                if cmd == "set_balance":
                    username = normalise_username(str(data.get("username", "")))
                    try:
                        balance = int(data.get("balance", 0))
                    except Exception:
                        balance = 0

                    users_cur.execute("UPDATE users SET balance = ? WHERE username = ?", (balance, username))
                    users_conn.commit()

                    self.send_response(200)
                    payload = {"ok": True, "cmd": cmd, "username": username, "balance": balance}

                elif cmd == "adjust_balance":
                    username = normalise_username(str(data.get("username", "")))
                    try:
                        delta = int(data.get("delta", 0))
                    except Exception:
                        delta = 0

                    row = users_cur.execute("SELECT balance FROM users WHERE username = ?", (username,)).fetchone()
                    if not row:
                        self.send_response(404)
                        payload = {"ok": False, "error": "user not found"}
                    else:
                        new_balance = int(row[0]) + int(delta)
                        users_cur.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
                        users_conn.commit()

                        self.send_response(200)
                        payload = {"ok": True, "cmd": cmd, "username": username, "balance": new_balance}

                elif cmd == "inc_time":
                    step = int(data.get("step", 1))
                    if step < 1:
                        step = 1

                    for _ in range(step):
                        TIME += 1
                        new_items = generate_news_for_turn(self.server.news_events_bank)
                        insert_news_items(self.server.news_db_path, TIME, new_items)

                        # tie market tick to the same endpoint, with access to this turn's news
                        tick_stock_market(self.server.users_db_path, new_items, TIME)

                    self.send_response(200)
                    payload = {"ok": True, "cmd": cmd, "time": TIME, "time_string": format_time(TIME)}

                else:
                    self.send_response(400)
                    payload = {"ok": False, "error": "unknown cmd"}

            finally:
                users_conn.close()

            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        # login form at /
        if u.path == "/login":
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
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        try:
            path = self.path.split("?", 1)[0]
        except Exception:
            path = self.path

        if path in ("/user", "/users", "/news", "/stocks", "/stock", "/stock_history"):
            return

        super().log_message(format, *args)


def main() -> None:
    global TIME

    host = "0.0.0.0"
    port = 8888

    projroot = Path(__file__).resolve().parent
    webroot = projroot / "webapp"
    if not webroot.is_dir():
        raise SystemExit(f"webapp directory not found: {webroot}")

    users_db_path = projroot / DB_NAME
    news_db_path = projroot / NEWS_DB_NAME

    init_users_db(users_db_path)
    init_news_db(news_db_path)

    # stocks + history live in users.db
    init_stocks_db(users_db_path)
    init_stock_prices_db(users_db_path)
    seed_stocks_if_empty(users_db_path)

    # ensure time-0 history exists
    ensure_history_at_time(users_db_path, TIME)

    events_bank = load_news_events(projroot)
    ensure_initial_news(str(news_db_path), events_bank)

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
