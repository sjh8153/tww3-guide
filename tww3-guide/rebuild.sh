#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python build.py
echo "완료: docs/ 가 갱신되었습니다."
