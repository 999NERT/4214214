import os
import sys
from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force reload of modules to avoid caching issues
if 'exporter' in sys.modules:
    del sys.modules['exporter']
if 'menu' in sys.modules:
    del sys.modules['menu']

from menu import install_menu, uninstall_menu


def install():
    install_menu()
    print("[exUE5] Menu installed successfully")


def uninstall():
    uninstall_menu()
    print("[exUE5] Menu removed successfully")


if __name__ == "__main__":
    install()
