"""
helpers/settings_manager.py

Manages loading/saving user preferences (background, font, etc.) plus
per-product pricing configurations in a single JSON file.
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../data/settings.json')

DEFAULT_SETTINGS = {
    "background": "assets/images/background1.png",
    "font": "berenika-Book",
    "font_color": "#FF0000",
    "product_pricing_disabled": False,
    "max_effects": 8,
    "rank_filter_disabled": False,
    # Add this new key to hold per-product pricing choices:
    "product_pricing": {}
}


class SettingsManager:
    """
    SettingsManager loads and saves preferences (background, font, color, etc.)
    plus a “product_pricing” dict where each product’s last‐used choices are stored.
    """

    def __init__(self, config_path=SETTINGS_PATH):
        self.config_path = config_path
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        """
        Load settings from JSON. If missing, create file with DEFAULT_SETTINGS.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
                    logger.debug(f"SettingsManager: Loaded settings from {self.config_path}", tag="SettingsManager")
            except Exception as e:
                logger.error(f"SettingsManager: Error loading settings ({e}); using defaults", tag="SettingsManager")
        else:
            self.save_settings()
            logger.debug(f"SettingsManager: Created new settings file at {self.config_path}", tag="SettingsManager")

    def save_settings(self):
        """
        Persist the entire settings dict (including per-product pricing) to JSON.
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(self.settings, f, indent=4)
            logger.debug(f"SettingsManager: Saved settings to {self.config_path}", tag="SettingsManager")
        except Exception as e:
            logger.error(f"SettingsManager: Error saving settings ({e})", tag="SettingsManager")

    def get(self, key):
        """
        Return settings[key], or fall back to DEFAULT_SETTINGS[key].
        """
        value = self.settings.get(key)
        if value is None:
            value = DEFAULT_SETTINGS.get(key)
        logger.debug(f"SettingsManager: Retrieved '{key}' = {value}", tag="SettingsManager")
        return value

    def set(self, key, value):
        """
        Update settings[key] = value and immediately save to disk.
        """
        self.settings[key] = value
        self.save_settings()
        logger.debug(f"SettingsManager: Set '{key}' = {value}", tag="SettingsManager")

    def reset_to_defaults(self):
        """
        Restore all keys to DEFAULT_SETTINGS (including wiping out any product_pricing).
        """
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()
        logger.info("SettingsManager: Reset all settings to defaults", tag="SettingsManager")
