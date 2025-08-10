#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/ilg_gates_check.py" "$@"
SH
chmod +x "/Volumes/T9/Cursor Active/Aug8-papers/audit/scripts/run_ilg.sh"

cat > "/Volumes/T9/Cursor Active/Aug8-papers/audit/scripts/run_growth.sh" <<\"SH\"
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/linear_growth_demo.py" "$@"
SH
chmod +x "/Volumes/T9/Cursor Active/Aug8-papers/audit/scripts/run_growth.sh"

echo "wrappers created"
