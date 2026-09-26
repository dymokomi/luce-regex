#!/bin/sh
set -eu
cd "$(dirname "$0")"
# Every fragment is laid out as the pinned compiler's formatter lays it out.
echo "== luce-base fmt --check"
for file in $(git ls-files '*.lucb'); do
    luce-base fmt "$file" --check > /dev/null || { echo "$file is not formatted (luce-base fmt $file --write)"; exit 1; }
done
exec python3 tests/run.py "$@"
