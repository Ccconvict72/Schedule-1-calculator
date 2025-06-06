"""
views/mixer.py

Defines MixerWindow, the QMainWindow responsible for the “Mix (Effect Finder)” functionality.
Handles:
1) Applying user-selected theme (font, font color, background).
2) Initializing core managers (PricingManager, ColorManager).
3) Instantiating MixerLogic to compute effects from selected ingredients.
4) Embedding the MixerUI widget for user interaction.
"""

import os
from typing import Callable, Dict, Any

# PyQt6 imports
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QFont

# Helper functions and managers
from helpers.logger import log_info, log_debug
from helpers.background_utils import set_background
from helpers.font_utils import load_custom_font
from helpers.pricing_manager import PricingManager
from helpers.color_manager import ColorManager

# Core application logic
from logic.mixer_logic import MixerLogic

# UI widget for mixer
from ui.mixer_ui import MixerUI


class MixerWindow(QMainWindow):
    """
    MixerWindow is the main window for the “Effect Finder” part of the application.
    It is responsible for:
    1) Applying theme settings (font, font color, background).
    2) Creating PricingManager and ColorManager instances.
    3) Instantiating MixerLogic to handle mixing logic.
    4) Embedding MixerUI as the central widget for user interaction.
    """

    def __init__(
        self,
        products: Dict[str, Any],
        additives: Dict[str, Any],
        effects: Dict[str, Any],
        transformations: Dict[str, Any],
        rank_manager,
        base_prices: Dict[str, float] = None,
        return_callback: Callable = None,
        settings_manager=None,
    ):
        """
        Initialize MixerWindow.

        Args:
            products (Dict[str, Any]): Dictionary of product data loaded from models.
            additives (Dict[str, Any]): Dictionary of additive data loaded from models.
            effects (Dict[str, Any]): Dictionary of effect data loaded from models.
            transformations (Dict[str, Any]): Dictionary of transformation data loaded from models.
            rank_manager: Instance of RankManager to filter available products/additives.
            base_prices (Dict[str, float], optional): Existing price mapping if passed. Defaults to None.
            return_callback (Callable, optional): Function to call when this window closes. Defaults to None.
            settings_manager: Instance of SettingsManager for theme and persistent settings.
        """
        super().__init__()

        # Store the settings_manager and callback for later use
        self.settings_manager = settings_manager
        self.return_callback = return_callback

        # Position window and set title
        self.move(600, 0)
        self.setWindowTitle("Schedule 1 Calculator – Mixer")

        # Apply theme before building UI
        self.apply_settings()
        log_info("MixerWindow initialized", tag="MixerWindow")

        # ——————————————————————————————
        # ① Core Managers
        # ——————————————————————————————
        # PricingManager calculates and retrieves prices for products/additives
        self.pricing_manager = PricingManager(
            products=products,
            additives=additives,
            effects=effects
        )
        log_debug("PricingManager instantiated", tag="MixerWindow")

        # ColorManager manages color assignments for products/effects
        self.color_manager = ColorManager(
            products=products,
            effects=effects
        )
        log_debug("ColorManager instantiated", tag="MixerWindow")

        # ——————————————————————————————
        # ② Mixer Logic
        # ——————————————————————————————
        # MixerLogic handles the core mixing algorithm (finding effects given ingredients)
        self.mixer_logic = MixerLogic(
            products=products,
            additives=additives,
            effects=effects,
            transformations=transformations,
            rank_manager=rank_manager,
            pricing_manager=self.pricing_manager,
            color_manager=self.color_manager
        )
        log_debug("MixerLogic initialized", tag="MixerWindow")

        # ——————————————————————————————
        # ③ UI Setup
        # ——————————————————————————————
        # Initialize MixerUI, passing in the logic, rank_manager, and settings
        self.mixer_ui = MixerUI(
            rank_manager=rank_manager,
            mixer_logic=self.mixer_logic,
            settings_manager=self.settings_manager,
            return_callback=return_callback
        )
        self.setCentralWidget(self.mixer_ui)
        log_info("MixerUI set as central widget", tag="MixerWindow")

    def apply_settings(self):
        """
        Apply stored theme settings from settings_manager (if available):
          • Font family and size → load_custom_font + QApplication.setFont
          • Font color → self.setStyleSheet to apply text color to all widgets
          • Background image → set_background on this window
        """
        if not self.settings_manager:
            # No settings manager provided; skip theming
            log_debug("No SettingsManager provided; skipping theme application", tag="MixerWindow")
            return

        # — Font family —
        font_name = self.settings_manager.get("font")
        family = load_custom_font(font_name)
        app_font = QFont(family, 11)
        QApplication.instance().setFont(app_font)
        self.setFont(app_font)
        log_debug(f"Applied font: {family}", tag="MixerWindow")

        # — Font color —
        font_color = self.settings_manager.get("font_color") or "#FFFFFF"
        # This stylesheet applies text color to all child widgets in this window
        self.setStyleSheet(f"* {{ color: {font_color}; }}")
        log_debug(f"Applied font color: {font_color}", tag="MixerWindow")

        # — Background image —
        bg = self.settings_manager.get("background")
        if bg and os.path.exists(bg):
            set_background(self, bg)
            log_info(f"Applied background: {bg}", tag="MixerWindow")

    def closeEvent(self, event):
        """
        Override closeEvent to call the return_callback (if provided)
        before actually closing the window.
        """
        if callable(self.return_callback):
            log_info("Calling return_callback before closing MixerWindow", tag="MixerWindow")
            self.return_callback()
        super().closeEvent(event)
        log_info("MixerWindow closed", tag="MixerWindow")
