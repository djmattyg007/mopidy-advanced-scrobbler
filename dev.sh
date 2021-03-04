#!/bin/bash

set -euo pipefail
set -x

cd "$(dirname -- "$0")"

SKIP_FRONTEND="${SKIP_FRONTEND:-}"

if [[ -z "${SKIP_FRONTEND}" ]]; then
    pushd frontend
    yarn run build --mode development
    popd
fi

rm -rf mopidy_advanced_scrobbler/static
cp -r frontend/dist mopidy_advanced_scrobbler/static

python setup.py install
