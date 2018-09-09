#!/usr/bin/env bash

set -e

eval "$(pyenv init -)"
pyenv deactivate
pyenv activate autoboto

flake8
isort

rm -rf ./autoboto.egg-info
rm -rf ./dist/*

# Rely on yapf_style from envvar BOTOGEN_YAPF_STYLE
python -m botogen --services="*"

python setup.py sdist bdist_wheel

python -m autoboto.examples.try_cloudformation
python -m autoboto.examples.try_s3
