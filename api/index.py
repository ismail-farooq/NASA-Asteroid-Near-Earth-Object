import sys
import os

# Add App folder to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "App"))

from app import app

# Vercel expects variable named "app"