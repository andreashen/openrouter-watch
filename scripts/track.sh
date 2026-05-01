#!/bin/bash
set -e
set -x
python scripts/fetch.py
python scripts/normalize.py
python scripts/derive.py