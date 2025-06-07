# main.py

"""
Entry point for the Schedule 1 Calculator application.
Sets up the main window, initializes data/models, and launches the PyQt6 GUI.
"""

import sys
import os
from typing import List

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QToolButton,
    QMessageBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize

# Application version
from version import __version__

# Helper functions and managers
from helpers.logger import log_info, log_debug, log_critical
from helpers.background_utils import set_background, get_transparent_style
from helpers.font_utils import load_custom_font
from helpers.ui_helpers import create_button
from helpers.settings_manager import SettingsManager
from helpers.rank import RankManager
from helpers.color_manager import ColorManager
from helpers.pricing_manager import PricingManager
from helpers.utils import resource_path


# Core application logic
from logic.mixer_logic import MixerLogic

# Data loaders
from models.loader import (
    load_products,
    load_additives,
    load_effects,
    load_transformations,
    load_ranks
)

# UI pages/windows
from views.settings_page import SettingsPage
from views.mixer import MixerWindow
from views.reverse import ReverseWindow
from views.product_pricing import ProductPricePage
from views.about_page import AboutDialog

class MainWindow(QMainWindow):
    """
    MainWindow is the primary QMainWindow for Schedule 1 Calculator.
    It handles:
      1) Loading initial data (products, additives, effects, transformations, ranks).
      2) Managing core managers (RankManager, PricingManager, ColorManager).
      3) Setting up application‐wide settings via SettingsManager.
      4) Building the main UI (rank dropdown, Mix/Unmix buttons, Settings & About buttons).
      5) Handling navigation to child windows (Mixer, Reverse, Product Pricing).
    """

    def __init__(self, ranks: List[str]):
        """
        Initialize MainWindow.

        Args:
            ranks (List[str]): List of rank names loaded from the data source.
        """
        super().__init__()

        # ——————————————————————————————
        # 1) Load data
        # ——————————————————————————————
        try:
            self.products = load_products()
            self.additives = load_additives()
            self.effects = load_effects()
            self.transformations = load_transformations()
            self.ranks = ranks
        except Exception as e:
            log_critical(f"Failed to load core data: {e}", tag="DataLoad")
            sys.exit(1)

        self.current_rank = None

        # ——————————————————————————————
        # 2) Core managers
        # ——————————————————————————————
        self.rank_manager = RankManager(self.ranks, self.products, self.additives)
        self.pricing_manager = PricingManager(
            products=self.products,
            additives=self.additives,
            effects=self.effects
        )
        self.color_manager = ColorManager(
            products=self.products,
            effects=self.effects
        )
        log_info("Core managers initialized", tag="Initialization")

        # ——————————————————————————————
        # 3) Settings Manager
        # ——————————————————————————————
        self.settings_manager = SettingsManager()
        log_info("SettingsManager initialized", tag="Initialization")

        # ——————————————————————————————
        # 4) UI Setup
        # ——————————————————————————————
        self.setWindowTitle(f"Schedule 1 Calculator – v{__version__}")
        self.setMinimumSize(500, 400)

        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 4a) Apply saved font & font color
        font_name = self.settings_manager.get("font")
        family = load_custom_font(font_name)
        app_font = QFont(family, 11)
        QApplication.instance().setFont(app_font)
        log_debug(f"Loaded custom font: {family}", tag="MainWindow")

        font_color = self.settings_manager.get("font_color") or "#FF0000"
        QApplication.instance().setStyleSheet(f"* {{ color: {font_color}; }}")

        # 4b) Rank dropdown
        self.rank_dropdown = QComboBox()
        self.rank_dropdown.setStyleSheet(get_transparent_style())
        self.rank_dropdown.addItem("Select rank to continue")
        self.rank_dropdown.addItems(self.ranks)
        self.rank_dropdown.currentIndexChanged.connect(self.rank_selected)
        layout.addWidget(self.rank_dropdown)

        # 4c) Mix / Unmix Buttons
        self.mix_button = create_button(
            "Mix (Effect Finder)",
            on_click=self.mix_clicked,
            style=get_transparent_style()
        )
        self.mix_button.setEnabled(False)
        layout.addWidget(self.mix_button)

        self.unmix_button = create_button(
            "Unmix (Ingredient Finder)",
            on_click=self.unmix_clicked,
            style=get_transparent_style()
        )
        self.unmix_button.setEnabled(False)
        layout.addWidget(self.unmix_button)

        # 4d) Apply saved background if valid
        background = self.settings_manager.get("background")
        if background and os.path.exists(background):
            set_background(self, background)
            log_info(f"Applied background: {background}", tag="MainWindow")

        # 4e) Settings Button (icon + label)
        self.settings_button = QToolButton(self)
        self.settings_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextUnderIcon
        )
        self.settings_button.setIcon(QIcon(resource_path("assets/icons/settings.webp")))
        self.settings_button.setText("Settings")
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setStyleSheet(
            f"""
            QToolButton {{
                padding: 10px;
                color: {font_color};
                background-color: rgba(50, 50, 50, 153);
                border: none;
            }}
            QToolButton:hover {{
                background-color: rgba(50, 50, 50, 180);
            }}
            """
        )
        self.settings_button.setMinimumSize(100, 70)
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setFont(app_font)

        # 4f) About Button (icon only)
        self.about_button = QToolButton(self)
        self.about_button.setIcon(QIcon(resource_path("assets/icons/About_Icon.webp")))
        about_icon = QIcon(resource_path("assets/icons/About_Icon.webp"))
        self.about_button.setIcon(about_icon)
        
        #Make the icon larger (e.g., 32x32)
        self.about_button.setIconSize(about_icon.actualSize(QSize(32, 32)))
        
        #Force the button's overall size to fit the icon snugly
        # (a few pixels of padding for a hover effect)
        self.about_button.setFixedSize(36, 36)
        
        self.about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.about_button.setStyleSheet(
            f"""
            QToolButton {{
                padding: 2px;  /*minimal padding */
                color: {font_color};
                background-color: rgba(50, 50, 50, 153);
                border: none;
            }}
            QToolButton:hover {{
                background-color: rgba(50, 50, 50, 180);
            }}
            """
        )
        self.about_button.setToolTip("About")
        self.about_button.setFont(app_font)
        self.about_button.clicked.connect(self._show_about)

        # Position settings and about buttons in top‐right corner
        self.settings_button.move(self.width() - 100, 10)
        self.about_button.move(
            self.width() - 100 - self.about_button.width() - 10,
            10
        )

        # 4g) Rank Filtering (hide/show logic based on saved setting)
        self.apply_rank_filter()

        # Track open child windows
        self.mixer_window = None
        self.reverse_window = None
        self.price_page = None

        log_info("MainWindow UI initialized", tag="MainWindow")

    def apply_rank_filter(self):
        """
        Show or hide the rank dropdown based on user preference.
        If rank filtering is disabled, automatically select the highest rank.
        """
        rank_filter_disabled = self.settings_manager.get("rank_filter_disabled")

        if rank_filter_disabled:
            self.rank_dropdown.setEnabled(False)
            self.rank_dropdown.hide()
            # Select highest rank by default
            self.current_rank = self.ranks[-1]
            self.rank_manager.set_current_rank(self.current_rank)
            self.mix_button.setEnabled(True)
            self.unmix_button.setEnabled(True)
            log_info(
                f"Rank filtering disabled. Using highest rank: {self.current_rank}",
                tag="RankFilter"
            )
        else:
            self.rank_dropdown.setEnabled(True)
            self.rank_dropdown.show()
            # Disable action buttons until rank is selected
            self.mix_button.setEnabled(False)
            self.unmix_button.setEnabled(False)
            self.rank_dropdown.setCurrentIndex(0)
            log_info("Rank filtering enabled. Awaiting rank selection.", tag="RankFilter")

    def rank_selected(self, idx: int):
        """
        Handler for rank dropdown changes.
        Enables/disables Mix/Unmix buttons and updates RankManager.
        """
        if idx == 0:
            # No rank selected
            self.current_rank = None
            self.mix_button.setEnabled(False)
            self.unmix_button.setEnabled(False)
            log_debug("Rank selection cleared", tag="RankSelection")
        else:
            self.current_rank = self.rank_dropdown.currentText()
            self.rank_manager.set_current_rank(self.current_rank)
            self.mix_button.setEnabled(True)
            self.unmix_button.setEnabled(True)
            accessible = self.rank_manager.get_accessible_product_names()
            log_debug(
                f"Accessible products for {self.current_rank}: {accessible}",
                tag="RankSelection"
            )
            log_info(f"Rank selected: {self.current_rank}", tag="MainWindow")

    def open_settings(self):
        """
        Open the settings dialog. On save, reapply settings to all windows.
        """
        settings_dialog = SettingsPage(
            parent=self,
            settings_manager=self.settings_manager,
            max_effects=len(self.effects),
            current_background=self.settings_manager.get("background"),
            initial_settings=self.settings_manager.settings.copy()
        )

        # When the user saves new settings, refresh child windows
        settings_dialog.settingsSaved.connect(lambda new: self._refresh_all_children())

        if settings_dialog.exec():
            new_settings = settings_dialog.getSettings()
            for key, value in new_settings.items():
                self.settings_manager.set(key, value)
            self.apply_settings()
            log_info("Settings updated via SettingsPage", tag="Settings")

    def apply_settings(self):
        """
        Reapply font, font color, settings & about button style, and background
        whenever settings are changed.
        """
        # 1) Update font family
        font_name = self.settings_manager.get("font")
        loaded_family = load_custom_font(font_name)
        new_font = QFont(loaded_family, 11)
        QApplication.instance().setFont(new_font)
        log_debug(f"Font changed to: {loaded_family}", tag="Settings")

        # 2) Update font color
        font_color = self.settings_manager.get("font_color") or "#FFFFFF"
        QApplication.instance().setStyleSheet(f"* {{ color: {font_color}; }}")

        # 3) Update Settings & About button styling
        style = (
            f"QToolButton {{ padding: 10px; color: {font_color}; "
            f"background-color: rgba(50, 50, 50, 153); border: none; }}\n"
            f"QToolButton:hover {{ background-color: rgba(50, 50, 50, 180); }}"
        )

        self.settings_button.setStyleSheet(style)
        self.settings_button.setFont(new_font)
        self.about_button.setStyleSheet(style)
        self.about_button.setFont(new_font)

        # 4) Background update (last)
        bg = self.settings_manager.get("background")
        if bg and os.path.exists(bg):
            set_background(self, bg)
            log_info(f"Background changed to: {bg}", tag="Settings")

        # Reapply rank filter in case that setting changed
        self.apply_rank_filter()

    def _refresh_all_children(self):
        """
        Called when SettingsPage.settingsSaved fires.
        Reapply settings on any open child windows (Mixer, Reverse, Pricing).
        """
        if self.mixer_window:
            self.mixer_window.apply_settings()
            log_debug("Reapplied settings to MixerWindow", tag="ChildRefresh")
        if self.reverse_window:
            self.reverse_window.apply_settings()
            log_debug("Reapplied settings to ReverseWindow", tag="ChildRefresh")
        if self.price_page:
            self.price_page.apply_settings()
            log_debug("Reapplied settings to ProductPricePage", tag="ChildRefresh")

    def resizeEvent(self, event):
        """
        Override resizeEvent to reposition the settings & about buttons in the top‐right corner.
        """
        super().resizeEvent(event)
        self.settings_button.move(
            self.width() - self.settings_button.width() - 10,
            10
        )
        self.about_button.move(
            self.width() - self.settings_button.width() - self.about_button.width() - 20,
            10
        )

    def _show_about(self):
        """
        Display the About dialog.
        """
        dlg = AboutDialog(self)
        dlg.exec()

    def _open_window(self, window_attr_name, window_cls, *args, **kwargs):
        """
        General helper to open a child window.
        If already open, bring it to front; otherwise create new and hide main window.

        Args:
            window_attr_name (str): Attribute name on self for the child window.
            window_cls (type): Class of the child window to instantiate.
            *args, **kwargs: Arguments to pass into the child window's constructor.
        """
        existing = getattr(self, window_attr_name, None)
        if existing is None:
            child = window_cls(
                *args,
                **kwargs,
                settings_manager=self.settings_manager
            )
            setattr(self, window_attr_name, child)
            child.show()
            self.hide()
            log_info(f"Opened window: {window_cls.__name__}", tag="WindowNavigation")
        else:
            existing.raise_()
            existing.activateWindow()
            log_debug(f"Activated existing window: {window_cls.__name__}", tag="WindowNavigation")

    def mix_clicked(self):
        """
        Handler for Mix button click.
        Opens MixerWindow with necessary data and callback.
        """
        log_info(f"Mix clicked with rank: {self.current_rank}", tag="MainWindow")
        self._open_window(
            "mixer_window",
            MixerWindow,
            products=self.products,
            additives=self.additives,
            effects=self.effects,
            transformations=self.transformations,
            rank_manager=self.rank_manager,
            return_callback=self.on_mixer_closed
        )

    def unmix_clicked(self):
        """
        Handler for Unmix button click.
        Opens ReverseWindow with necessary data and callback.
        """
        log_info(f"Unmix clicked with rank: {self.current_rank}", tag="MainWindow")
        self._open_window(
            "reverse_window",
            ReverseWindow,
            products=self.products,
            effects=self.effects,
            product_order=list(self.products.keys()),
            color_manager=self.color_manager,
            rank_manager=self.rank_manager,
            return_callback=self.on_reverse_closed
        )

    def on_mixer_closed(self):
        """
        Callback when MixerWindow is closed.
        Resets mixer_window reference and shows MainWindow again.
        """
        self.mixer_window = None
        self.show()
        log_debug("MixerWindow closed, main window shown", tag="WindowNavigation")

    def on_reverse_closed(self):
        """
        Callback when ReverseWindow is closed.
        Resets reverse_window reference and shows MainWindow again.
        """
        self.reverse_window = None
        self.show()
        log_debug("ReverseWindow closed, main window shown", tag="WindowNavigation")

    def open_price_page(self):
        """
        Example method to open the ProductPricePage if triggered by a menu/button.
        """
        self.price_page = ProductPricePage(
            self.products,
            self.settings_manager
        )
        self.price_page.show()
        self.hide()
        log_info("ProductPricePage opened", tag="WindowNavigation")

        # Any saved settings changes will be reapplied via _refresh_all_children
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Exit", "Are you sure you want to quit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """
    Application entry point.
    Initializes QApplication, loads ranks, and shows MainWindow.
    """
    app = QApplication(sys.argv)

    ranks = load_ranks()
    if not ranks:
        # If no ranks are loaded, log and exit
        log_critical("No rank data loaded. Exiting application.", tag="Startup")
        sys.exit(1)

    window = MainWindow(ranks)
    window.show()
    log_info("Application started", tag="Startup")

    sys.exit(app.exec())



if __name__ == "__main__":
    main()
