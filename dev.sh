#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

CI=false scripts/build-static.sh

python setup.py install
