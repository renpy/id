#!/bin/bash

set -e

cd "$(dirname $0)"

D="/tmp/id-$1"

rm -Rf "$D"

mkdir -p "$D/game"
cp game/*.rpy "$D/game"
cp game/*.rpym "$D/game"
cp game/script.rpym "$D/game/script.rpy"
cp README.rst "$D"
cp -a game/images "$D/game"
cp -a game/gui "$D/game"
cp -a game/sound "$D/game"

../run.sh "$D" compile

pushd /tmp
zip -9r "id-$1.zip" "id-$1"
popd

cp "$D.zip" ~/ab/renpy/dl/id/

