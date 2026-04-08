#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="lmt_files_$(date +%Y%m%d_%H%M%S).tar.gz"

tar -czf "$OUT_FILE" \
  README.md \
  app.py \
  requirements.txt \
  static/style.css \
  templates/index.html \
  templates/admin.html

echo "$OUT_FILE"
