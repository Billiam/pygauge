#!/usr/bin/env bash
set -e

cd `dirname $0`

rm gauge.zip 2> /dev/null || true
rm -r dist/* 2> /dev/null || true
pyinstaller --onefile gauge.py
cp config.yml dist
cp LICENSE.md dist/LICENSE.txt
7z a -tzip dist/gauge.zip ./dist/* -mx0
