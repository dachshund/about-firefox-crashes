#!/bin/bash

virtualenv pyenv
source pyenv/bin/activate
pip install -U beautifulsoup4 requests
time ./analyse.py report.ids.1
