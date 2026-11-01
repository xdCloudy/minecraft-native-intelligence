#!/usr/bin/env python3
"""Backward-compatible entry point for the canonical progress CLI."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tools/progress.py'), run_name='__main__')
