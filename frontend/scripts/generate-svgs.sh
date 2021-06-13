#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")/.."

mdi="node_modules/@mdi/svg/svg"

SVG_PATHS=(
  "${mdi}/auto-upload.svg"
  "${mdi}/refresh.svg"
)

mkdir -p src/svg
rm src/svg/*.svg

for svg in "${SVG_PATHS[@]}"; do
  yarn run ts-node --require esm scripts/generate-svg.ts "${svg}"
done
