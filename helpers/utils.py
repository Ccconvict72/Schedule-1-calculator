import sys
import os

# Utility function to get the absolute path to a resource.
def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for dev and for PyInstaller frozen app.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundles everything into a temp folder
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
