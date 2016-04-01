#!/bin/sh

cd "$(dirname ${BASH_SOURCE[0]})"
asv run -j -p -k 46d7445457c47b7b47b45061bb3081e25c76c94f..development
asv publish
asv preview
cd -
