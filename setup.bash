#!/usr/bin/env bash

THISPATH=$(dirname "$BASH_SOURCE")

THISPATH="$(cd "$THISPATH" && pwd)"

echo Creating virtual environment in: "$THISPATH"

# Install virtualenv, if it doesnt' exist.
python3 -m pip install virtualenv
# Install the virtual environment
python3 -m virtualenv "$THISPATH/venv"

# Activate our virtualenv, then install wxPython 4 and numpy.
source "$THISPATH/venv/bin/activate"
python3 -m pip install wxPython numpy pdfrw opencv-python serial
deactivate
