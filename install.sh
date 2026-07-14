#!/usr/bin/env bash
# Install nature-academic-search for Codex, Claude Code, or both.
# Backward compatible usage: bash install.sh researcher@example.com
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT="both"
EMAIL="${PUBMED_EMAIL:-}"
DRY_RUN=0

usage() {
  echo "Usage: bash install.sh [PUBMED_EMAIL] [--client codex|claude|both] [--email EMAIL] [--dry-run]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --client)
      CLIENT="${2:?--client requires a value}"
      shift 2
      ;;
    --email)
      EMAIL="${2:?--email requires a value}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "${EMAIL}" ]]; then
        echo "Only one positional PUBMED_EMAIL is accepted" >&2
        exit 2
      fi
      EMAIL="$1"
      shift
      ;;
  esac
done

if [[ "${CLIENT}" != "codex" && "${CLIENT}" != "claude" && "${CLIENT}" != "both" ]]; then
  echo "--client must be codex, claude, or both" >&2
  exit 2
fi

if [[ -z "${EMAIL}" ]]; then
  echo "A PubMed contact email is required. Pass --email or set PUBMED_EMAIL." >&2
  exit 2
fi

if command -v uv >/dev/null 2>&1; then
  INSTALLER=(uv tool install --force "${SCRIPT_DIR}")
elif command -v pipx >/dev/null 2>&1; then
  INSTALLER=(pipx install --force "${SCRIPT_DIR}")
else
  echo "Install uv or pipx first; global pip installation is intentionally unsupported." >&2
  exit 1
fi

if [[ ${DRY_RUN} -eq 1 ]]; then
  printf 'dry-run:'
  printf ' %q' "${INSTALLER[@]}"
  printf '\n'
  PYTHONPATH="${SCRIPT_DIR}/src" python3 -m nature_academic_search install \
    --client "${CLIENT}" \
    --email "${EMAIL}" \
    --skill-source "${SCRIPT_DIR}" \
    --dry-run
  exit 0
fi

"${INSTALLER[@]}"
nature-academic-search install \
  --client "${CLIENT}" \
  --email "${EMAIL}" \
  --skill-source "${SCRIPT_DIR}"
