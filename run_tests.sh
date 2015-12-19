#!/bin/bash

BASE_DIR=$(dirname $0)

with_rednose='--rednose --force-color'
with_coverage='--cover-html-dir=./htmlcov --with-coverage --cover-html --cover-package=dopy --cover-erase --cover-branches'

dotests=''
if [[ $1 != '' ]]; then
    dotests="--tests=$1"
fi

exec nosetests ${with_rednose} -s -v --with-doctest ${with_coverage} --where ${BASE_DIR}/tests ${dotests}
