#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/linear_growth_demo.py" "$@"
SH
chmod +x "/Volumes/T9/Cursor Active/Aug8-papers/audit/scripts/run_growth.sh"
echo ok
