#!/bin/bash

if [ "$CLEAR_DB" == "true" ]; then
    python base_deleting_script.py
fi

python main.py