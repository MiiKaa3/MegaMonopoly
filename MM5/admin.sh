#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8888}"
BASE_URL="http://${HOST}:${PORT}"

die() { echo "admin.sh: $*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage:
  ./admin.sh set <username> <amount>
  ./admin.sh add <username> <delta>
  ./admin.sh tick [step]
  ./admin.sh time
  ./admin.sh user <username>

Env overrides:
  HOST=127.0.0.1 PORT=8888 ./admin.sh ...

Examples:
  ./admin.sh set mikey 250
  ./admin.sh add mikey -50
  ./admin.sh tick
  ./admin.sh tick 4
  ./admin.sh time
  ./admin.sh user mikey
EOF
}

need() { command -v "$1" >/dev/null 2>&1 || die "missing dependency: $1"; }
need curl

# If jq is available, pretty print JSON, otherwise just raw.
pretty() {
  if command -v jq >/dev/null 2>&1; then jq; else cat; fi
}

post_admin() {
  local json="$1"
  curl -sS -X POST "${BASE_URL}/admin" \
    -H "Content-Type: application/json" \
    -d "${json}"
}

get_user() {
  local username="$1"
  curl -sS "${BASE_URL}/user?username=${username}"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  ""|-h|--help|help)
    usage
    exit 0
    ;;

  set)
    [[ $# -eq 2 ]] || die "set requires: <username> <amount>"
    user="$1"; amt="$2"
    post_admin "{\"cmd\":\"set_balance\",\"username\":\"${user}\",\"amount\":${amt}}" | pretty
    ;;

  add|adjust)
    [[ $# -eq 2 ]] || die "add requires: <username> <delta>"
    user="$1"; delta="$2"
    post_admin "{\"cmd\":\"adjust_balance\",\"username\":\"${user}\",\"delta\":${delta}}" | pretty
    ;;

  tick|time+|inc_time)
    step="${1:-1}"
    post_admin "{\"cmd\":\"inc_time\",\"step\":${step}}" | pretty
    ;;

  time)
    # show current TIME by querying any user? You already return time in /user.
    # We'll just ask for a known user if provided, otherwise error.
    die "time needs a username in this codebase (TIME is returned by /user). Use: ./admin.sh user <username> (shows time too)."
    ;;

  user)
    [[ $# -eq 1 ]] || die "user requires: <username>"
    get_user "$1" | pretty
    ;;

  *)
    die "unknown command: $cmd (run ./admin.sh --help)"
    ;;
esac

