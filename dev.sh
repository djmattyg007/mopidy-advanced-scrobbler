#!/bin/bash

set -euo pipefail
set -x

cd "$(dirname -- "$0")"

pushd frontend
yarn run build
popd

rm -rf mopidy_advanced_scrobbler/static
cp -r frontend/dist mopidy_advanced_scrobbler/static

python setup.py install
