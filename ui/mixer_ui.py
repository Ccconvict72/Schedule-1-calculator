"""
views/mixer_ui.py

Defines MixerUI, the QWidget that provides the “Mix (Effect Finder)” interface.
Responsibilities:
1) Apply user-selected theme (font, font color, background).
2) Allow the user to select a base product and additives.
3) Trigger mix logic and display results (effects, pricing, mixing path).
4) Provide controls to add/remove/reorder additives and reset/return.
"""

import os
from typing import Callable, Dict, Any, List

# PyQt6 imports
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QScrollArea,
    QFrame,
    QPushButton,
    QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Helpers
from helpers.logger import log_info, log_debug, log_error
from helpers.font_utils import load_custom_font
from helpers.ui_helpers import create_button
from helpers.background_utils import get_transparent_style, set_background
from helpers.icon_utils import build_mixing_path_widget
from helpers.rank import RankManager

# Core logic
from logic.mixer_logic import MixerLogic

# Data loader
from models.loader import load_products


class MixerUI(QWidget):
    """
    MixerUI is the central widget for the “Effect Finder” mode.
    It provides:
    - Dropdown to select base product (filtered by rank).
    - Dynamic list of additive dropdowns (add/remove/reorder).
    - “Mix Now” button that computes effects, pricing, and displays results.
    - Mixing path bar showing the sequence of ingredients.
    - Reset and “Return to Start” buttons.
    """

    def __init__(
        self,
        rank_manager: RankManager,
        mixer_logic: MixerLogic,
        settings_manager=None,       # Optional SettingsManager for theme
        return_callback: Callable = None,
    ):
        """
        Initialize MixerUI.

        Args:
            rank_manager (RankManager): Manages which products/additives are accessible.
            mixer_logic (MixerLogic): Core mixing logic to compute effects and pricing.
            settings_manager: Optional SettingsManager to apply themes.
            return_callback (Callable): Function to call when returning to main window.
        """
        super().__init__()
        self.settings_manager = settings_manager
        self.return_callback = return_callback
        self.rank_manager = rank_manager
        self.mixer_logic = mixer_logic

        # Determine font family (matches ReverseUI approach)
        chosen_font = None
        if self.settings_manager:
            font_name = self.settings_manager.get("font")
            chosen_font = load_custom_font(font_name)
        self.font_family = chosen_font or "Arial"

        # Load all products once (full data)
        self.products = load_products()

        # Track additive dropdown widgets: list of (container_frame, dropdown_widget, up_btn, down_btn, remove_btn)
        self.additive_dropdowns: List[Any] = []

        # Apply theme (font, color, background)
        self.apply_settings()

        # If no valid background in settings, use default image
        bg = self.settings_manager.get("background") if self.settings_manager else None
        if not (bg and os.path.exists(bg)):
            set_background(self, resource_path("assets/images/background1.png"))

        # Build UI components
        self.init_ui()

    def apply_settings(self):
        """
        Apply theme settings from settings_manager (if provided):
          • Set global QApplication font.
          • Set this widget’s font so children inherit it.
          • Set a global stylesheet to enforce font color.
          • Apply background image to this widget.
        """
        if not self.settings_manager:
            log_debug("MixerUI: No settings_manager provided; skipping theming", tag="MixerUI")
            return

        # Font family and size
        app_font = QFont(self.font_family, 11)
        QApplication.instance().setFont(app_font)
        self.setFont(app_font)
        log_debug(f"MixerUI: Applied font '{self.font_family}'", tag="MixerUI")

        # Font color
        font_color = self.settings_manager.get("font_color") or "#FFFFFF"
        self.setStyleSheet(f"* {{ color: {font_color}; }}")
        log_debug(f"MixerUI: Applied font color '{font_color}'", tag="MixerUI")

        # Background image
        bg = self.settings_manager.get("background")
        if bg and os.path.exists(bg):
            set_background(self, bg)
            log_info(f"MixerUI: Applied background '{bg}'", tag="MixerUI")

    def init_ui(self):
        """
        Construct and arrange all UI elements for mixing:
        - Left panel: base product dropdown, additive dropdowns, and control buttons.
        - Right panel: result label (effects & pricing).
        - Bottom: mixing path bar (displays sequence of ingredients as icons).
        """
        self.setWindowTitle("Schedule 1 Calculator – Mix Mode")
        self.setMinimumSize(1200, 900)

        main_layout = QVBoxLayout(self)

        # Top portion: left side (controls) and right side (results)
        top_layout = QHBoxLayout()

        # ─── LEFT PANEL ─────────────────────────────────────────────────
        left_panel = QVBoxLayout()

        # 1) Base product label and dropdown
        lbl_base = QLabel("Select Base Product:")
        lbl_base.setFont(QFont(self.font_family, 11))
        left_panel.addWidget(lbl_base)

        self.base_dropdown = QComboBox()
        self.base_dropdown.addItem("Select Product")
        # Filter products by accessible names and sort by order attribute
        allowed_products = self.rank_manager.get_accessible_product_names()
        filtered_products = sorted(
            (p for p in self.products.values() if p.Name in allowed_products),
            key=lambda p: p.Order
        )
        for product in filtered_products:
            self.base_dropdown.addItem(product.Name)
        self.base_dropdown.setStyleSheet(get_transparent_style())
        self.base_dropdown.setFont(QFont(self.font_family, 11))
        self.base_dropdown.currentTextChanged.connect(self.check_mix_button_state)
        left_panel.addWidget(self.base_dropdown)

        # 2) Additives section label and scroll area
        lbl_add = QLabel("Items Added:")
        lbl_add.setFont(QFont(self.font_family, 11))
        left_panel.addWidget(lbl_add)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.additives_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        # Transparent styling for scroll area and its content
        self.scroll_area.setStyleSheet(get_transparent_style())
        self.scroll_content.setStyleSheet(get_transparent_style())
        left_panel.addWidget(self.scroll_area)

        # Start with one additive dropdown
        self.filtered_data = self.mixer_logic.get_filtered_data()
        self.additive_order = list(self.filtered_data["additives"].keys())
        self.add_additive_dropdown()

        # 3) Control buttons under additives
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        add_btn = create_button("Add Item", self.add_additive_dropdown)
        add_btn.setFont(QFont(self.font_family, 11))

        self.mix_button = create_button("Mix Now", self.mix_now)
        self.mix_button.setFont(QFont(self.font_family, 11))
        self.mix_button.setEnabled(False)  # Initially disabled until base selected

        reset_btn = create_button("Reset", self.reset)
        reset_btn.setFont(QFont(self.font_family, 11))

        return_btn = create_button("Return to Start", self.return_to_start)
        return_btn.setFont(QFont(self.font_family, 11))

        for btn in (add_btn, self.mix_button, reset_btn, return_btn):
            btn.setStyleSheet(get_transparent_style())
            btn.setFixedWidth(200)
            btn_layout.addWidget(btn)

        left_panel.addLayout(btn_layout)
        top_layout.addLayout(left_panel, 2)  # Left panel takes 2/3 of width

        # ─── RIGHT PANEL ────────────────────────────────────────────────
        right_panel = QVBoxLayout()
        self.result_label = QLabel("Results will appear here")
        self.result_label.setWordWrap(True)
        font_family_css = f"font-family: '{self.font_family}';"
        self.result_label.setStyleSheet(
            get_transparent_style() + font_family_css + " font-size:16px; color:white;"
        )
        self.result_label.setFont(QFont(self.font_family, 11))
        right_panel.addWidget(self.result_label)
        top_layout.addLayout(right_panel, 1)  # Right panel takes 1/3 of width

        main_layout.addLayout(top_layout)

        # ─── MIXING PATH BAR (BOTTOM) ────────────────────────────────────
        self.path_frame = QFrame()
        self.path_frame.setStyleSheet(get_transparent_style())
        self.path_frame.setFixedHeight(80)
        self.path_layout = QHBoxLayout(self.path_frame)
        self.path_layout.setContentsMargins(5, 5, 5, 5)
        self.path_layout.setSpacing(10)
        main_layout.addWidget(self.path_frame)

        self.mixing_path_widget = None

    def add_additive_dropdown(self):
        """
        Add a new dropdown row for selecting an additive, along with up/down/remove buttons.
        """
        container_layout = QHBoxLayout()
        dropdown = QComboBox()
        dropdown.addItem(" ")
        allowed_additives = self.rank_manager.get_accessible_additive_names()
        dropdown.addItems(sorted([a for a in self.additive_order if a in allowed_additives]))
        dropdown.setStyleSheet(get_transparent_style())
        dropdown.setFont(QFont(self.font_family, 11))
        dropdown.setFixedWidth(200)
        dropdown.currentTextChanged.connect(self.check_mix_button_state)

        up_btn = create_button("↑")
        down_btn = create_button("↓")
        rm_btn = create_button("✕")
        for btn in (up_btn, down_btn, rm_btn):
            btn.setFixedWidth(30)
            btn.setStyleSheet(get_transparent_style())
            btn.setFont(QFont(self.font_family, 11))

        container_layout.addWidget(dropdown)
        container_layout.addWidget(up_btn)
        container_layout.addWidget(down_btn)
        container_layout.addWidget(rm_btn)

        row_frame = QFrame()
        row_frame.setLayout(container_layout)
        self.additives_layout.addWidget(row_frame)
        self.additive_dropdowns.append((row_frame, dropdown, up_btn, down_btn, rm_btn))

        # Connect button signals for reordering/removal
        up_btn.clicked.connect(lambda _, f=row_frame: self.move_additive(-1, f))
        down_btn.clicked.connect(lambda _, f=row_frame: self.move_additive(1, f))
        rm_btn.clicked.connect(lambda _, f=row_frame: self.remove_additive_dropdown(f))

        self.update_reorder_buttons()
        log_debug("MixerUI: Added new additive dropdown", tag="MixerUI")

    def move_additive(self, direction: int, frame: QFrame):
        """
        Move an additive dropdown up or down in the list.
        
        Args:
            direction (int): -1 to move up, +1 to move down.
            frame (QFrame): The container frame of the dropdown to move.
        """
        idx = next((i for i, (f, *_ ) in enumerate(self.additive_dropdowns) if f == frame), None)
        if idx is None:
            return
        new_idx = idx + direction
        if 0 <= new_idx < len(self.additive_dropdowns):
            # Swap the positions in the internal list
            self.additive_dropdowns[idx], self.additive_dropdowns[new_idx] = (
                self.additive_dropdowns[new_idx], self.additive_dropdowns[idx]
            )
            # Rearrange the widgets in the layout
            widget = self.additives_layout.takeAt(idx).widget()
            if widget:
                self.additives_layout.insertWidget(new_idx, widget)
            self.update_reorder_buttons()
            log_debug(f"MixerUI: Moved additive from index {idx} to {new_idx}", tag="MixerUI")

    def remove_additive_dropdown(self, frame: QFrame):
        """
        Remove an additive dropdown row from the UI.
        
        Args:
            frame (QFrame): The container frame of the dropdown to remove.
        """
        for i, (f, *_ ) in enumerate(self.additive_dropdowns):
            if f == frame:
                self.additive_dropdowns.pop(i)
                f.setParent(None)
                f.deleteLater()
                log_debug(f"MixerUI: Removed additive dropdown at index {i}", tag="MixerUI")
                break
        self.update_reorder_buttons()

    def update_reorder_buttons(self):
        """
        Enable/disable the up/down buttons on each additive row
        based on its position in the list.
        """
        count = len(self.additive_dropdowns)
        for i, (_, _, up_btn, down_btn, _) in enumerate(self.additive_dropdowns):
            up_btn.setEnabled(i != 0)
            down_btn.setEnabled(i != count - 1)

    def mix_now(self):
        """
        Trigger mixing logic when “Mix Now” is clicked:
        - Gather selected base product and additives.
        - Call MixerLogic.calculate_mix to compute:
            • effects (list of effect names)
            • effect_colors (mapping effect→color)
            • base_color (color string for base product)
            • base_cost, additive_cost, total_cost, final_price (floats)
        - Build HTML string to display results (product, costs, effects).
        - Update mixing path bar with icons for each ingredient.
        """
        base_product = self.base_dropdown.currentText()
        additives = [
            d.currentText().strip()
            for _, d, *_ in self.additive_dropdowns
            if d.currentText().strip()
        ]

        disable_pricing = self.settings_manager.get("product_pricing_disabled") if self.settings_manager else False

        try:
            (effects, effect_colors,
             base_color, base_cost,
             additive_cost, total_cost,
             final_price) = self.mixer_logic.calculate_mix(base_product, additives)
        except Exception as e:
            log_error(f"MixerUI: Error during mixing: {e}", tag="MixerUI")
            self.result_label.setText("<b>An error occurred during mixing.</b>")
            return

        # Build HTML-enhanced result display
        html = f"""
        <div style='font-family:\"{self.font_family}\";'>
          <span style='font-size:18px; color:#a01302;'><b>Selected Product:</b></span><br>
          <span style='font-size:32px; color:{base_color};'><b>{base_product}</b></span><br><br>
        """
        if not disable_pricing:
            html += f"""
            <span style='font-size:18px; color:#a01302;'><b>Product Cost:</b></span> ${base_cost:.2f}<br>
            <span style='font-size:18px; color:#a01302;'><b>Additives Cost:</b></span> ${additive_cost:.2f}<br>
            <span style='font-size:18px; color:#a01302;'><b>Total Estimated Cost:</b></span> ${total_cost:.2f}<br>
            <span style='font-size:18px; color:#a01302;'><b>Sell Price:</b></span> ${final_price:.2f}<br><br>
            """
        else:
            html += f"""
            <span style='font-size:18px; color:#a01302;'><b>Additives Cost:</b></span> ${additive_cost:.2f}<br>
            <span style='font-size:18px; color:#a01302;'><b>Sell Price:</b></span> ${final_price:.2f}<br><br>
            """
        html += """
          <span style='font-size:18px; color:#a01302;'><b>Selected Effects:</b></span><br>
        """
        if effects:
            html += "<ul style='font-size:24px;'>"
            for name in effects:
                color = effect_colors.get(name, "#FFFFFF")
                html += f"<li style='color:{color};'>{name}</li>"
            html += "</ul>"
        else:
            html += "<span style='font-size:18px;'>None</span>"
        html += "</div>"

        self.result_label.setText(html)
        log_info(f"MixerUI: Displayed mix results for base '{base_product}'", tag="MixerUI")

        # Update mixing path bar
        if self.mixing_path_widget:
            self.path_layout.removeWidget(self.mixing_path_widget)
            self.mixing_path_widget.deleteLater()

        path = [base_product] + additives
        self.mixing_path_widget = build_mixing_path_widget(path)
        self.path_layout.addWidget(self.mixing_path_widget)

    def check_mix_button_state(self):
        """
        Enable “Mix Now” button only if a valid base product is selected.
        """
        base_selected = self.base_dropdown.currentText() != "Select Product"
        self.mix_button.setEnabled(base_selected)

    def reset(self):
        """
        Reset the UI to its initial state:
        - Clear all existing additive dropdowns.
        - Re-add a single additive dropdown.
        - Reset base dropdown to default.
        - Clear result label and mixing path.
        """
        for frame, *_ in self.additive_dropdowns:
            frame.setParent(None)
            frame.deleteLater()
        self.additive_dropdowns.clear()

        self.base_dropdown.setCurrentIndex(0)
        self.add_additive_dropdown()
        self.result_label.setText("Results will appear here")

        if self.mixing_path_widget:
            self.path_layout.removeWidget(self.mixing_path_widget)
            self.mixing_path_widget.deleteLater()
            self.mixing_path_widget = None

        log_info("MixerUI: Reset UI to initial state", tag="MixerUI")

    def return_to_start(self):
        """
        Handle “Return to Start” button:
        - Close this MixerUI’s parent window (MixerWindow).
        - Invoke the return_callback to let MainWindow re-show itself.
        """
        log_info("MixerUI: Returning to main window", tag="MixerUI")
        if callable(self.return_callback):
            self.window().close()
            self.return_callback()
