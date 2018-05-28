#!/usr/bin/env bash
if [[ "$1" == "varbyte" ]]; then
  python index_simple.py "${@:2}"
else
  python index_simple.py "${@:2}"
fi