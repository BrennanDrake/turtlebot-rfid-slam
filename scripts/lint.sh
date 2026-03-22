#!/usr/bin/env bash
# Fast checks that do not require sourcing ROS: syntax, XML, Ruff.
# Usage: ./scripts/lint.sh   (from repo root or any cwd)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT}/ros2_ws/src"
FAILED=0

echo "[lint] Python compileall -> ${SRC}"
if ! python3 -m compileall -q "${SRC}"; then
  FAILED=1
fi

if command -v xmllint >/dev/null 2>&1; then
  echo "[lint] xmllint package.xml files"
  while IFS= read -r -d '' f; do
    if ! xmllint --noout "$f"; then
      echo "  invalid XML: $f" >&2
      FAILED=1
    fi
  done < <(find "${SRC}" -name package.xml -print0 2>/dev/null)
else
  echo "[lint] xmllint not found; skipping XML validation (optional: apt install libxml2-utils)"
fi

RUFF=""
if [[ -x "${ROOT}/.venv/bin/ruff" ]]; then
  RUFF="${ROOT}/.venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  RUFF="ruff"
fi

if [[ -n "${RUFF}" ]]; then
  echo "[lint] ruff check (config: pyproject.toml)"
  if ! (cd "${ROOT}" && "${RUFF}" check "${SRC}"); then
    FAILED=1
  fi
else
  echo "[lint] ruff not installed; skip (install: python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt)"
fi

if [[ "${FAILED}" -ne 0 ]]; then
  echo "[lint] FAILED" >&2
  exit 1
fi
echo "[lint] OK"
