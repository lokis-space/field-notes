#!/bin/sh
# Rebuild everything: icons, each guide, then the home page.
set -e
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
$PY src/make_icons.py
$PY src/kcd1/build.py kcd1
$PY src/build_hub.py
