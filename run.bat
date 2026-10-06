@echo off
py -m coverage run -m pytest tests/test_mbt.py
py -m coverage report -m