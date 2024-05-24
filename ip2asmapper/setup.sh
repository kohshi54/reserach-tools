#!/bin/bash

VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
    echo "venv created"
else
    echo "using existing venv"
fi

#activate
source $VENV_DIR/bin/activate

pip install -r requirements.txt

exec "$SHELL"

