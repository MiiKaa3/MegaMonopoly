from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

def main() -> None:
    host = "0.0.0.0"
    port = 8888

    webroot = Path(__file__).resolve().parent / "webapp"
    if not webroot.is_dir():
        raise SystemExit(f"webapp directory not found: {webroot}")
    os.chdir(webroot)

    server = ThreadingHTTPServer((host, port), SimpleHTTPRequestHandler)
    print(f"Serving {webroot} on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    main()
