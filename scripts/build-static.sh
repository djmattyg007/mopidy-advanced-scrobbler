#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")/.."

pushd frontend
if [[ "${CI}" == "true" ]]; then
  yarn run build
else
  yarn run build --mode development
fi
popd

rm -rf mopidy_advanced_scrobbler/static
cp -r frontend/dist mopidy_advanced_scrobbler/static
