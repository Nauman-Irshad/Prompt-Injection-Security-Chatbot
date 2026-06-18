#!/usr/bin/env python3
"""Launch the security chatbot server."""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
server = os.path.join(PROJECT_ROOT, "backend", "chat_server.py")
subprocess.run([sys.executable, server], cwd=PROJECT_ROOT)
