#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

scripts/build-static.sh

python setup.py install
