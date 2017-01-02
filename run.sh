#!/bin/bash

cd "$(dirname $(realpath $0))"


cp game/script.rpym game/script.rpy
../run.sh . director --compile
