#!/usr/bin/env bash

#rm -rf ./.git
#rm ./gitignore
find . -type f -name '*.pyc' -exec rm {} +
find . -type d -name '__pycache__' -exec rm -rf {} +