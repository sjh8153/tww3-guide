#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python build.py
python verify_site.py
