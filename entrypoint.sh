#!/bin/bash
set -e

cd "$GITHUB_WORKSPACE"
python -m src.grader "$@"
