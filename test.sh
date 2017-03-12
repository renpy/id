#!/bin/bash

set -x

cd "$(dirname $(realpath $0))"

rm -Rf ~/.renpy/id-*
cp game/script.rpym game/script.rpy
../run.sh . test --compile

