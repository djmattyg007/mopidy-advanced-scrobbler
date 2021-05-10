#!/bin/bash

set -euo pipefail
cd "$(dirname "$0")/.."

pushd frontend
yarn run build --mode development
popd

rm -rf mopidy_advanced_scrobbler/static
cp -r frontend/dist mopidy_advanced_scrobbler/static
