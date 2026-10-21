#!/usr/bin/env bash
# Keep a Render free instance warm while judging runs (Nov 9-20).
# Free instances spin down after ~15 idle minutes; this pings /health every 10.
#
#   nohup scripts/render_keepalive.sh https://YOUR-APP.onrender.com \
#     >> /tmp/opencode/render_keepalive.log 2>&1 &
#
# Note: this runs on this machine. If the machine reboots, restart it. A
# GitHub Actions schedule (cron: '*/10 * * * *') is the reboot-proof variant.
set -u
URL="${1:?usage: render_keepalive.sh https://your-app.onrender.com [logfile]}"
LOG="${2:-/tmp/opencode/render_keepalive.log}"
case "$URL" in
  http*) ;;
  *) echo "URL must start with http(s)://" >&2; exit 2 ;;
esac

while true; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$URL/health" || echo 000)
  printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$code" "$URL/health" >>"$LOG"
  sleep 600
done
