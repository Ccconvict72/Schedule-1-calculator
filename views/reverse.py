"""
views/reverse.py

Defines ReverseWindow, the main QMainWindow for “Unmix (Ingredient Finder)” mode.
Responsibilities:
1) Initialize ReverseLogic for computing additive sequences.
2) Instantiate UI (ReverseUI) for user to select product/effects and view results.
3) Handle passing SettingsManager to child UI for consistent theming.
"""

from typing import Callable, Dict, List, Optional
import os

# PyQt6 imports
from PyQt6.QtWidgets import QMainWindow

# Helper functions and managers
from helpers.logger import log_info, log_debug
from helpers.rank import RankManager
from helpers.color_manager import ColorManager
from helpers.pricing_manager import PricingManager

# Core application logic
from logic.reverse_logic import ReverseLogic

# UI widget for reverse functionality
from ui.reverse_ui import ReverseUI


class ReverseWindow(QMainWindow):
    """
    ReverseWindow is the QMainWindow for the “Unmixer” feature.
    Responsibilities:
    1) Load nested effect rules and additive data.
    2) Create PricingManager and ReverseLogic instances.
    3) Embed ReverseUI as the central widget for user interaction.
    """

    def __init__(
        self,
        products: Dict[str, object],
        effects: Dict[str, object],
        product_order: List[str],
        color_manager: ColorManager,
        rank_manager: RankManager,
        settings_manager=None,              # Optional SettingsManager for theming
        return_callback: Optional[Callable] = None,
    ):
        """
        Initialize ReverseWindow.

        Args:
            products (Dict[str, object]): All product data from models.loader.
            effects (Dict[str, object]): All effect data from models.loader.
            product_order (List[str]): Ordered list of product names for UI.
            color_manager (ColorManager): Manages color assignments.
            rank_manager (RankManager): Manages accessibility by rank.
            settings_manager: Optional SettingsManager for font, color, background.
            return_callback (Callable, optional): Function to call when window closes.
        """
        super().__init__()

        # Position window and set title
        self.move(600, 0)
        self.setWindowTitle("Schedule 1 Calculator – Unmixer")
        log_info("ReverseWindow initialized", tag="ReverseWindow")

        # Store managers and callback
        self.rank_manager = rank_manager
        self.color_manager = color_manager
        self.settings_manager = settings_manager
        self.return_callback = return_callback

        # ——————————————————————————————
        # 1) Load nested effect rules & additive data
        # ——————————————————————————————
        from models.loader import load_effect_rules_nested, load_additives
        nested_rules = load_effect_rules_nested()
        additives = load_additives()
        log_debug("Loaded nested effect rules and additives", tag="ReverseWindow")

        # ——————————————————————————————
        # 2) Create PricingManager
        # ——————————————————————————————
        self.pricing_manager = PricingManager(
            products=products,
            additives=additives,
            effects=effects
        )
        log_debug("PricingManager instantiated in ReverseWindow", tag="ReverseWindow")

        # ——————————————————————————————
        # 3) Create ReverseLogic
        # ——————————————————————————————
        self.reverse_logic = ReverseLogic(
            products=products,
            effect_rules=nested_rules,
            rank_manager=self.rank_manager,
            pricing_manager=self.pricing_manager
        )
        log_debug("ReverseLogic instantiated in ReverseWindow", tag="ReverseWindow")

        # ——————————————————————————————
        # 4) Build UI (pass settings_manager for theming)
        # ——————————————————————————————
        self.reverse_ui = ReverseUI(
            products=products,
            effect_colors=self.color_manager.effect_colors,
            product_order=product_order,
            color_manager=self.color_manager,
            reverse_logic=self.reverse_logic,
            rank_manager=self.rank_manager,
            settings_manager=self.settings_manager,
            return_callback=self.return_callback,
        )
        self.setCentralWidget(self.reverse_ui)
        log_info("ReverseUI set as central widget", tag="ReverseWindow")

    def closeEvent(self, event):
        """
        Override closeEvent to call return_callback (if provided) before closing.
        """
        if callable(self.return_callback):
            log_info("Calling return_callback before closing ReverseWindow", tag="ReverseWindow")
            self.return_callback()
        super().closeEvent(event)
        log_info("ReverseWindow closed", tag="ReverseWindow")
