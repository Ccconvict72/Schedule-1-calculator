"""
views/settings_page.py

Defines SettingsPage, a QDialog for configuring application-wide settings:
1) Background image selection (predefined thumbnails or imported file).
2) Font family selection and live preview.
3) Font color picker.
4) Maximum effects spinner with “–” and “+” controls.
5) Disable rank filtering toggle.
6) Access to ProductPricePage for per-product pricing.
7) Restore defaults and Save/Cancel actions.

Emits `settingsSaved` signal with a dictionary of chosen settings when the user clicks “Save.”
"""

import os
import logging

# PyQt6 imports
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QComboBox,
    QSpinBox,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QWidget,
    QFileDialog,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QFrame
)
from PyQt6.QtGui import QFont, QPixmap, QFontDatabase, QColor
from PyQt6.QtCore import Qt, pyqtSignal

# Helpers and models
from helpers.background_utils import set_background
from helpers.settings_manager import DEFAULT_SETTINGS
from helpers.logger import log_info, log_debug
from views.product_pricing import ProductPricePage
from models.loader import load_products

logger = logging.getLogger(__name__)


class SettingsPage(QDialog):
    """
    SettingsPage is a modal dialog that allows the user to configure:
    - Background image (select from thumbnails or import custom).
    - Font family and live font preview.
    - Font color via QColorDialog.
    - Maximum number of allowed effects.
    - Toggle to disable rank filtering.
    - Access to per-product pricing settings via ProductPricePage.
    - Restore defaults, Save, and Reset & Close functionality.

    Emits:
        settingsSaved(dict): Dictionary containing new settings on Save.
    """

    settingsSaved = pyqtSignal(dict)

    def __init__(
        self,
        parent=None,
        settings_manager=None,
        max_effects=20,
        current_background=None,
        initial_settings=None
    ):
        """
        Initialize the SettingsPage.

        Args:
            parent: Parent widget (MainWindow).
            settings_manager: Instance of SettingsManager for persisting settings.
            max_effects (int): Upper bound for the “Maximum effects” spinbox.
            current_background (str, optional): Path to currently applied background.
            initial_settings (dict, optional): Initial values to pre-populate controls.
        """
        super().__init__(parent)
        self.setWindowTitle("Settings")

        # Managers and parameters
        self.settings_manager = settings_manager
        self.max_effects = max_effects
        self.current_background = current_background
        self.initial_settings = initial_settings or {}
        self.setMinimumSize(800, 600)

        # Load custom font (berenika.ttf) if available; fallback to None
        self.custom_font_family = self._load_custom_font()
        log_debug(f"SettingsPage: custom_font_family = {self.custom_font_family}", tag="SettingsPage")

        # Build the UI on a translucent backdrop
        self._initUI()

        # Ensure default background is part of the selection list
        default_bg = DEFAULT_SETTINGS["background"]
        if default_bg not in self.background_paths:
            self.background_paths.insert(0, default_bg)

        # Preselect controls based on initial_settings or defaults
        self._apply_initial_settings()

        # Immediately apply chosen background to this dialog
        bg_to_apply = self.initial_settings.get("background", default_bg)
        if bg_to_apply and os.path.exists(bg_to_apply):
            set_background(self, bg_to_apply)
            log_debug(f"SettingsPage: Applied initial background '{bg_to_apply}'", tag="SettingsPage")

        log_info("SettingsPage initialized", tag="SettingsPage")

    def _load_custom_font(self) -> str | None:
        """
        Load 'berenika.ttf' from assets/fonts/, returning the family name if successful.

        Returns:
            str | None: Font family name, or None on failure.
        """
        font_path = os.path.join("assets", "fonts", "berenika.ttf")
        if not os.path.exists(font_path):
            log_debug("SettingsPage: berenika.ttf not found; skipping custom font load", tag="SettingsPage")
            return None

        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            log_debug("SettingsPage: Failed to load berenika.ttf", tag="SettingsPage")
            return None

        families = QFontDatabase.applicationFontFamilies(font_id)
        family = families[0] if families else None
        log_debug(f"SettingsPage: Loaded custom font family '{family}'", tag="SettingsPage")
        return family

    def _initUI(self):
        """
        Build all UI components on a translucent backdrop (rgba(50,50,50,153)).
        """
        # Outer layout for the dialog
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Backdrop frame (semi-transparent dark)
        backdrop = QFrame()
        backdrop.setFrameShape(QFrame.Shape.NoFrame)
        backdrop.setStyleSheet(
            "background-color: rgba(50, 50, 50, 153); border-radius: 8px;"
        )
        outer_layout.addWidget(backdrop)

        # Layout inside the backdrop
        main_layout = QVBoxLayout(backdrop)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ────────────────────────────────────────────────────────────────────
        # 1) Background Selection (Thumbnails)
        # ────────────────────────────────────────────────────────────────────
        bg_label = QLabel("Select Background:")
        bg_label.setFont(self._themed_font(14))
        main_layout.addWidget(bg_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # Predefined background image paths
        self.background_paths = [
            "assets/images/background1.png",
            "assets/images/background2.png",
            "assets/images/background3.png",
            "assets/images/background4.png"
        ]
        self.background_radio_buttons: list[QRadioButton] = []
        self.bg_button_group = QButtonGroup(self)
        self.bg_button_group.setExclusive(True)

        for idx, bg_path in enumerate(self.background_paths):
            wrapper = QWidget()
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(4, 4, 4, 4)
            wrapper.setStyleSheet(
                "background-color: rgba(50, 50, 50, 153); border-radius: 4px;"
            )

            thumb = QLabel()
            if os.path.exists(bg_path):
                thumb_pix = QPixmap(bg_path).scaled(
                    150, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                thumb.setPixmap(thumb_pix)
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wrapper_layout.addWidget(thumb)

            bg_radio = QRadioButton()
            bg_radio.setFont(self._themed_font(10))
            wrapper_layout.addWidget(bg_radio, alignment=Qt.AlignmentFlag.AlignCenter)

            self.bg_button_group.addButton(bg_radio, idx)
            self.background_radio_buttons.append(bg_radio)
            scroll_layout.addWidget(wrapper)

            # Update dialog background immediately on toggle
            bg_radio.toggled.connect(self._on_background_radio_toggled)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # “Import Custom Background…” button
        self.import_button = QPushButton("Import Custom Background…")
        self.import_button.setFont(self._themed_font(11))
        self.import_button.clicked.connect(self.importBackground)
        main_layout.addWidget(self.import_button)

        # ────────────────────────────────────────────────────────────────────
        # 2) Font Selection + Color Picker
        # ────────────────────────────────────────────────────────────────────
        font_layout = QHBoxLayout()
        font_label = QLabel("Choose Font:")
        font_label.setFont(self._themed_font(12))
        font_layout.addWidget(font_label)

        self.font_combo = QComboBox()
        self.font_combo.setFont(self._themed_font(11))

        # Add custom font first (if loaded)
        if self.custom_font_family:
            self.font_combo.addItem(self.custom_font_family)

        # Add all system font families
        families = QFontDatabase.families()
        self.font_combo.addItems(families)
        self.font_combo.currentIndexChanged.connect(self._update_font_preview)
        font_layout.addWidget(self.font_combo, stretch=1)
        main_layout.addLayout(font_layout)

        # Live font preview label
        self.font_preview = QLabel("This is how text will appear")
        self.font_preview.setFont(self._themed_font(12))
        main_layout.addWidget(self.font_preview)

        # ────────────────────────────────────────────────────────────────────
        # 2b) Font Color Picker
        # ────────────────────────────────────────────────────────────────────
        color_layout = QHBoxLayout()
        color_label = QLabel("Choose Font Color:")
        color_label.setFont(self._themed_font(12))
        color_layout.addWidget(color_label)

        self.color_button = QPushButton()
        self.color_button.setFixedSize(24, 24)
        self.color_button.clicked.connect(self._choose_font_color)
        color_layout.addWidget(self.color_button)

        self.color_code_label = QLabel()
        self.color_code_label.setFont(self._themed_font(11))
        color_layout.addWidget(self.color_code_label)

        color_layout.addStretch()
        main_layout.addLayout(color_layout)

        # ────────────────────────────────────────────────────────────────────
        # 3) Maximum effects Spinner (with “–” / “+” buttons)
        # ────────────────────────────────────────────────────────────────────
        eff_layout = QHBoxLayout()
        eff_label = QLabel("Maximum effects:")
        eff_label.setFont(self._themed_font(12))
        eff_layout.addWidget(eff_label)

        # “Minus” button
        self.eff_minus_btn = QPushButton("–")
        self.eff_minus_btn.setFont(self._themed_font(12))
        self.eff_minus_btn.setFixedSize(30, 30)
        self.eff_minus_btn.clicked.connect(self._decrease_effects)
        eff_layout.addWidget(self.eff_minus_btn)

        # SpinBox for max effects
        self.effects_spin = QSpinBox()
        self.effects_spin.setFont(self._themed_font(11))
        self.effects_spin.setRange(1, self.max_effects)
        self.effects_spin.setFixedWidth(60)
        eff_layout.addWidget(self.effects_spin)

        # “Plus” button
        self.eff_plus_btn = QPushButton("+")
        self.eff_plus_btn.setFont(self._themed_font(12))
        self.eff_plus_btn.setFixedSize(30, 30)
        self.eff_plus_btn.clicked.connect(self._increase_effects)
        eff_layout.addWidget(self.eff_plus_btn)

        eff_layout.addStretch()
        main_layout.addLayout(eff_layout)

        # ────────────────────────────────────────────────────────────────────
        # 4) Disable Rank Selection Toggle
        # ────────────────────────────────────────────────────────────────────
        self.rank_toggle = QCheckBox("Disable rank Selection")
        self.rank_toggle.setFont(self._themed_font(11))
        main_layout.addWidget(self.rank_toggle)

        # ────────────────────────────────────────────────────────────────────
        # 5) “Set Product Costs” Button
        # ────────────────────────────────────────────────────────────────────
        self.cost_button = QPushButton("Set Product Costs…")
        self.cost_button.setFont(self._themed_font(11))
        self.cost_button.clicked.connect(self.openCostSettings)
        main_layout.addWidget(self.cost_button)

        # ────────────────────────────────────────────────────────────────────
        # 6) Restore Defaults
        # ────────────────────────────────────────────────────────────────────
        self.restore_button = QPushButton("Restore Defaults")
        self.restore_button.setFont(self._themed_font(11))
        self.restore_button.clicked.connect(self.restoreDefaults)
        main_layout.addWidget(self.restore_button)

        # ────────────────────────────────────────────────────────────────────
        # 7) Save / Cancel Buttons
        # ────────────────────────────────────────────────────────────────────
        btn_hbox = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setFont(self._themed_font(11))
        self.save_button.clicked.connect(self.saveSettings)

        self.cancel_button = QPushButton("Reset & Close")
        self.cancel_button.setFont(self._themed_font(11))
        self.cancel_button.clicked.connect(self.resetAndClose)

        btn_hbox.addStretch()
        btn_hbox.addWidget(self.save_button)
        btn_hbox.addWidget(self.cancel_button)
        main_layout.addLayout(btn_hbox)

    def _themed_font(self, point_size: int) -> QFont:
        """
        Return a QFont using the chosen custom_font_family (or Arial if none).
        """
        family = self.custom_font_family or "Arial"
        return QFont(family, point_size)

    def _on_background_radio_toggled(self, checked: bool):
        """
        When a background thumbnail is selected, immediately apply that background.
        """
        if not checked:
            return
        idx = self.bg_button_group.checkedId()
        if 0 <= idx < len(self.background_paths):
            chosen_bg = self.background_paths[idx]
        else:
            chosen_bg = DEFAULT_SETTINGS["background"]

        if chosen_bg and os.path.exists(chosen_bg):
            set_background(self, chosen_bg)
            log_info(f"SettingsPage: Applied background '{chosen_bg}'", tag="SettingsPage")

    def importBackground(self):
        """
        Open a file dialog to import a custom background image.
        Adds it to the radio list, selects it, and applies it immediately.
        """
        dlg = QFileDialog(self)
        dlg.setNameFilter("Image files (*.png *.jpg *.jpeg *.bmp)")
        if dlg.exec():
            files = dlg.selectedFiles()
            if files:
                chosen = files[0]
                self.background_paths.append(chosen)

                # Create new thumbnail widget + radio button
                idx = len(self.background_paths) - 1
                wrapper = QWidget()
                wrapper_layout = QVBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(4, 4, 4, 4)
                wrapper.setStyleSheet(
                    "background-color: rgba(50, 50, 50, 153); border-radius: 4px;"
                )

                thumb = QLabel()
                pixmap = QPixmap(chosen)
                pixmap = pixmap.scaled(
                    150, 100,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                thumb.setPixmap(pixmap)
                thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                wrapper_layout.addWidget(thumb)

                bg_radio = QRadioButton()
                bg_radio.setFont(self._themed_font(10))
                wrapper_layout.addWidget(bg_radio, alignment=Qt.AlignmentFlag.AlignCenter)

                # Add to the scroll layout
                scroll_layout = self.findChild(QScrollArea).widget().layout()
                scroll_layout.addWidget(wrapper)

                self.bg_button_group.addButton(bg_radio, idx)
                self.background_radio_buttons.append(bg_radio)
                bg_radio.setChecked(True)

                # Immediately apply this new custom background
                set_background(self, chosen)
                log_info(f"SettingsPage: Imported and applied custom background '{chosen}'", tag="SettingsPage")

    def _choose_font_color(self):
        """
        Open QColorDialog to pick font color.
        Updates preview, button appearance, and saves into settings_manager immediately.
        """
        initial = QColor(self.settings_manager.get("font_color") or "#FFFFFF")
        color = QColorDialog.getColor(initial, parent=self)
        if color.isValid():
            hex_code = color.name()
            self.color_code_label.setText(hex_code)
            self.color_button.setStyleSheet(
                f"background-color: {hex_code}; border: 1px solid #000;"
            )
            # Persist to settings_manager so other dialogs pick it up
            self.settings_manager.set("font_color", hex_code)
            log_info(f"SettingsPage: font_color set to '{hex_code}'", tag="SettingsPage")

    def _update_font_preview(self):
        """
        Update the font preview label and apply the new font to the entire dialog.
        """
        font_name = self.font_combo.currentText()
        new_font = QFont(font_name, 12)
        self.font_preview.setFont(new_font)
        self._apply_global_font(new_font)
        log_debug(f"SettingsPage: Font preview updated to '{font_name}'", tag="SettingsPage")

    def _apply_global_font(self, font: QFont):
        """
        Recursively set the given QFont on this dialog so child widgets inherit it.
        """
        self.setFont(font)

    def _increase_effects(self):
        """Increase the maximum effects spinbox value by 1 (up to its maximum)."""
        current = self.effects_spin.value()
        if current < self.effects_spin.maximum():
            self.effects_spin.setValue(current + 1)
            log_debug(f"SettingsPage: Increased max_effects to {current + 1}", tag="SettingsPage")

    def _decrease_effects(self):
        """Decrease the maximum effects spinbox value by 1 (down to its minimum)."""
        current = self.effects_spin.value()
        if current > self.effects_spin.minimum():
            self.effects_spin.setValue(current - 1)
            log_debug(f"SettingsPage: Decreased max_effects to {current - 1}", tag="SettingsPage")

    def openCostSettings(self):
        """
        Open the ProductPricePage as a modal dialog, passing in the same settings_manager.
        """
        products = load_products()
        dialog = ProductPricePage(products, self.settings_manager)
        dialog.exec()
        log_info("SettingsPage: Opened ProductPricePage", tag="SettingsPage")

    def restoreDefaults(self):
        """
        Reset all controls to DEFAULT_SETTINGS and apply those defaults immediately.
        """
        # 1) Uncheck all background radios
        self.bg_button_group.setExclusive(False)
        for radio in self.background_radio_buttons:
            radio.setChecked(False)
        self.bg_button_group.setExclusive(True)

        # 2) Select default background and apply it
        default_bg = DEFAULT_SETTINGS["background"]
        if default_bg in self.background_paths:
            idx = self.background_paths.index(default_bg)
            self.bg_button_group.button(idx).setChecked(True)
        else:
            self.background_paths.insert(0, default_bg)
            idx = 0
            self.bg_button_group.button(idx).setChecked(True)

        if os.path.exists(default_bg):
            set_background(self, default_bg)
            log_info(f"SettingsPage: Restored default background '{default_bg}'", tag="SettingsPage")

        # 3) Reset font selection
        if self.custom_font_family:
            self.font_combo.setCurrentText(self.custom_font_family)
        else:
            self.font_combo.setCurrentIndex(0)
        self._update_font_preview()

        # 4) Reset font color
        default_color = DEFAULT_SETTINGS["font_color"]
        self.color_code_label.setText(default_color)
        self.color_button.setStyleSheet(
            f"background-color: {default_color}; border: 1px solid #000;"
        )
        self.settings_manager.set("font_color", default_color)
        log_info(f"SettingsPage: Restored default font_color '{default_color}'", tag="SettingsPage")

        # 5) Reset max effects
        self.effects_spin.setValue(DEFAULT_SETTINGS["max_effects"])
        log_info(f"SettingsPage: Restored default max_effects {DEFAULT_SETTINGS['max_effects']}", tag="SettingsPage")

        # 6) Reset rank toggle
        self.rank_toggle.setChecked(DEFAULT_SETTINGS["rank_filter_disabled"])
        log_info(f"SettingsPage: Restored default rank_filter_disabled {DEFAULT_SETTINGS['rank_filter_disabled']}", tag="SettingsPage")

        # 7) Reset settings_manager to defaults
        self.settings_manager.reset_to_defaults()

        QMessageBox.information(self, "Defaults Restored", "All settings have been reset to default.")
        log_info("SettingsPage: All settings reset to defaults", tag="SettingsPage")

    def getSettings(self) -> dict:
        """
        Gather current control values into a dictionary for saving.

        Returns:
            dict: {
                "background": str,
                "font": str,
                "font_color": str,
                "max_effects": int,
                "rank_filter_disabled": bool
            }
        """
        # Background
        bg_idx = self.bg_button_group.checkedId()
        if 0 <= bg_idx < len(self.background_paths):
            chosen_bg = self.background_paths[bg_idx]
        else:
            chosen_bg = DEFAULT_SETTINGS["background"]

        # Font
        chosen_font = self.font_combo.currentText()

        # Font color (already stored when changed)
        chosen_color = self.settings_manager.get("font_color")

        # Max effects
        chosen_max_eff = self.effects_spin.value()

        # Rank toggle
        chosen_rank_disabled = self.rank_toggle.isChecked()

        settings_dict = {
            "background": chosen_bg,
            "font": chosen_font,
            "font_color": chosen_color,
            "max_effects": chosen_max_eff,
            "rank_filter_disabled": chosen_rank_disabled,
        }
        log_debug(f"SettingsPage: Collected settings {settings_dict}", tag="SettingsPage")
        return settings_dict

    def _apply_initial_settings(self):
        """
        If initial_settings were provided by MainWindow, apply them to the controls.
        Otherwise, leave defaults.
        """
        if not self.initial_settings:
            return

        # 1) Background
        bg = self.initial_settings.get("background", DEFAULT_SETTINGS["background"])
        if bg in self.background_paths:
            idx = self.background_paths.index(bg)
            self.bg_button_group.button(idx).setChecked(True)
        else:
            idx = self.background_paths.index(DEFAULT_SETTINGS["background"])
            self.bg_button_group.button(idx).setChecked(True)

        # 2) Font
        font_name = self.initial_settings.get("font", self.custom_font_family or "Arial")
        self.font_combo.setCurrentText(font_name)
        self._update_font_preview()

        # 3) Font color
        font_color = self.initial_settings.get("font_color", DEFAULT_SETTINGS["font_color"])
        self.color_code_label.setText(font_color)
        self.color_button.setStyleSheet(
            f"background-color: {font_color}; border: 1px solid #000;"
        )
        # Apply font color to this dialog
        self.setStyleSheet(f"* {{ color: {font_color}; }}")

        # 4) Max effects
        self.effects_spin.setValue(self.initial_settings.get("max_effects", DEFAULT_SETTINGS["max_effects"]))

        # 5) Rank toggle
        self.rank_toggle.setChecked(self.initial_settings.get("rank_filter_disabled", False))

        log_info("SettingsPage: Applied initial settings to controls", tag="SettingsPage")

    def saveSettings(self):
        """
        Called when the user clicks “Save.” Writes each setting into settings_manager,
        emits `settingsSaved(new_settings)`, and closes the dialog.
        """
        new_settings = self.getSettings()
        for k, v in new_settings.items():
            self.settings_manager.set(k, v)
        log_info(f"SettingsPage: Saved settings {new_settings}", tag="SettingsPage")
        self.settingsSaved.emit(new_settings)
        self.accept()

    def resetAndClose(self):
        """
        Called when the user clicks “Reset & Close.” Reapplies initial_settings (or defaults)
        but does NOT persist changes. Closes the dialog with reject().
        """
        self._apply_initial_settings()
        log_info("SettingsPage: Reset controls and closed without saving", tag="SettingsPage")
        self.reject()
