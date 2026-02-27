import os
import sqlite3
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

DB_NAME = "users.db"
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


def init_db(db_path: Path) -> None:
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


def normalise_username(raw: str) -> str:
    u = raw.strip()
    if not u:
        return ""

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    u = "".join(ch for ch in u if ch in allowed)

    return u[:24]


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)

        if u.path == "/user":
            qs = parse_qs(u.query)
            username = normalise_username((qs.get("username") or [""])[0])

            conn = sqlite3.connect(self.server.db_path)
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
            conn = sqlite3.connect(self.server.db_path)
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
        
            # Open DB connection the same way you already do elsewhere
            conn = sqlite3.connect(self.server.db_path)
            cur = conn.cursor()
        
            try:
                if cmd == "set_balance":
                    username = normalise_username(str(data.get("username", "")))
                    amount = int(data.get("amount", 0))
        
                    cur.execute("UPDATE users SET balance = ? WHERE username = ?", (amount, username))
                    conn.commit()
        
                    if cur.rowcount == 0:
                        self.send_response(404)
                        payload = {"ok": False, "error": "user not found"}
                    else:
                        self.send_response(200)
                        payload = {"ok": True, "cmd": cmd, "username": username, "balance": amount}
        
                elif cmd == "adjust_balance":
                    username = normalise_username(str(data.get("username", "")))
                    delta = int(data.get("delta", 0))
        
                    cur.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (delta, username))
                    conn.commit()
        
                    if cur.rowcount == 0:
                        self.send_response(404)
                        payload = {"ok": False, "error": "user not found"}
                    else:
                        # fetch new balance to return it
                        cur.execute("SELECT balance FROM users WHERE username = ?", (username,))
                        new_balance = cur.fetchone()[0]
                        self.send_response(200)
                        payload = {"ok": True, "cmd": cmd, "username": username, "balance": new_balance}
        
                elif cmd == "inc_time":
                    step = int(data.get("step", 1))
                    if step < 1:
                        step = 1
                    TIME += step
        
                    self.send_response(200)
                    payload = {"ok": True, "cmd": cmd, "time": TIME}
        
                else:
                    self.send_response(400)
                    payload = {"ok": False, "error": "unknown cmd"}
        
            finally:
                conn.close()
        
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
                conn = sqlite3.connect(self.server.db_path)
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

        conn = sqlite3.connect(self.server.db_path)
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

        if path in ("/user", "/users"):
            return

        super().log_message(format, *args)


def format_time(t: int) -> str:
    return f"Y{t//4 + 1}Q{t%4 + 1}"


def main() -> None:
    host = "0.0.0.0"
    port = 8888
    
    projroot = Path(__file__).resolve().parent
    webroot = projroot / "webapp"
    if not webroot.is_dir():
        raise SystemExit(f"webapp directory not found: {webroot}")

    db_path = projroot / DB_NAME
    init_db(db_path)

    os.chdir(webroot)

    server = ThreadingHTTPServer((host, port), Handler)
    server.db_path = str(db_path)

    print(f"Serving {webroot} on http://{host}:{port}")
    print(f"DB at {db_path}")
    server.serve_forever()


if __name__ == "__main__":
    main()
