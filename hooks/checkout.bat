@echo off

python -m pip install -r "%~dp0../python/requirements.txt"
python "%~dp0../python/checkout.py"
