#!/usr/bin/env bash

set -e

eval "$(pyenv init -)"
pyenv deactivate
pyenv activate autoboto

pip install -r ./requirements.txt
pip list

pytest
flake8
isort

rm -rf ./autoboto.egg-info
rm -rf ./dist/*
rm -rf ./build/*

python -m autoboto.builder --yapf-style="" --services="*"

python setup.py sdist bdist_wheel

python -m autoboto.examples.try_cloudformation
python -m autoboto.examples.try_s3
