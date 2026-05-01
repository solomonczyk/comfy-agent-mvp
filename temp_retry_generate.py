#!/usr/bin/env python3
import sys
import os

# Set sys.argv directly to bypass shell mangling
sys.argv = [
    'cli.py',
    'retry-generate-frames',
    '--project-root',
    r'F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01',
    '--execute',
    '--json'
]

# Import and run the CLI
from app.cli import main
main()
