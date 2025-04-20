#!/bin/bash

ENV="$1"
TARGET=~/bin/ipdet

if [ "$ENV" == "--help" ]
then
  echo "To use python from the path for the venv base:"
  echo "  $0"
  echo "To use another environment as the venv base:"
  echo "  $0 <environment>"
  exit -1
fi

SCRIPTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPTDIR"

if [ ! -e .venv/bin/python ]
then
  if [ "$ENV" == "" ]
  then
    python3 -m venv .venv
  else
    runvenv "$ENV" -m venv .venv
  fi
fi &&

.venv/bin/pip install maxminddb whoisit &&
if [ ! -e GeoLite2-City.mmdb ]
then
  ( wget https://git.io/GeoLite2-City.mmdb ||
    wget https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-City.mmdb
  )
fi &&
SUCCESS=yes ||
SUCCESS=no

if [ "$SUCCESS" == "yes" ]
then
  if [ ! -e "$TARGET" ]
  then
    mkdir ~/bin 2>/dev/null
    ln -s "$SCRIPTDIR"/ipdet.py "$TARGET"
  fi

  runvenv -w .venv ipdet.py >/dev/null ||
  ( echo "Could not find environment with runvenv.  Is it installed?";
    echo "https://github.com/rcolyer/runvenv"
  )
fi

