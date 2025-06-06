"""
Font utilities module.

Contains utilities for loading and managing custom application fonts in PyQt6 UI.
"""

import os
from PyQt6.QtGui import QFontDatabase
from helpers.logger import log_info, log_warning, log_error, log_debug, log_critical

def load_custom_font(font_name="berenika-Book"):
    """
    Load and register a custom font for the application.

    Attempts to load the given font (by name) from the assets/fonts directory.
    If loading fails, falls back to system font.

    Args:
        font_name (str): Name of the font (without extension).

    Returns:
        str: The name of the loaded font family, or the input font name as fallback.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "fonts"))

        extensions = [".ttf", ".otf"]
        for ext in extensions:
            font_file = font_name + ext
            font_path = os.path.join(fonts_dir, font_file)

            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    log_critical(f"Failed to load custom font '{font_file}' from '{font_path}'.", tag="FontUtils")
                    continue

                family = QFontDatabase.applicationFontFamilies(font_id)[0]
                log_info(f"Loaded custom font '{family}' from '{font_path}'.", tag="FontUtils")
                return family

        log_debug(f"No custom font file found for '{font_name}'. Assuming it's a system font.", tag="FontUtils")
        return font_name

    except Exception as e:
        log_error(f"Error loading font '{font_name}': {e}", tag="FontUtils")
        return font_name
