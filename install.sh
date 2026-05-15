#!/usr/bin/env bash
set -euo pipefail

DEST="${HOME}/.claude/skills/tikz-figure-skill"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== tikz-figure-skill installer ==="
echo "Destination: ${DEST}"

mkdir -p "${DEST}/references" "${DEST}/scripts"

cp "${SCRIPT_DIR}/SKILL.md" "${DEST}/SKILL.md"
cp -r "${SCRIPT_DIR}/references/"* "${DEST}/references/"
cp -r "${SCRIPT_DIR}/scripts/"* "${DEST}/scripts/"

echo "Files installed: $(find "${DEST}" -type f | wc -l)"
echo ""

# Run env check if Python available
if command -v python3 &>/dev/null; then
    echo "=== Environment check ==="
    python3 "${DEST}/scripts/check-env.py" || true
elif command -v python &>/dev/null; then
    echo "=== Environment check ==="
    python "${DEST}/scripts/check-env.py" || true
else
    echo "Python not found — skipping environment check"
fi

echo ""
echo "Done. Restart Claude Code to use /tikz-figure-skill"
