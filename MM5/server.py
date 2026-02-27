import os
import sqlite3
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

DB_NAME = "users.db"
TIME = 0


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
            username = (qs.get("username") or [""])[0].strip()

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

        return super().do_GET()


    def do_POST(self):
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


def format_time(t: int) -> str:
    return f"Y{t//4 + 1}Q{t%4 + 1}"


def main() -> None:
    host = "0.0.0.0"
    port = 8888
    
    projroot = Path(__file__).resolve().parent
    webroot = projroot / "webapp"
    if not webroot.is_dir():
        raise SystemExit(f"webapp directory not found: {webroot}")
    os.chdir(webroot)

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
