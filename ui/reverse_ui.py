"""
views/reverse_ui.py

Defines ReverseUI, the QWidget for the “Unmix (Ingredient Finder)” interface.
Responsibilities:
1) Apply user-selected theme (font, font color, background).
2) Allow user to select a base product (or pick best) and choose desired effects.
3) Launch background threads for unmix or pick-best-product logic.
4) Display resulting additive sequence, mixing path, and pricing summary.
"""

import os
from typing import Callable, Dict, Any, List, Union
from traceback import format_exc

# PyQt6 imports
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QTextEdit,
    QCheckBox,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QDialog,
    QApplication
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QObject  # Added QObject
from PyQt6.QtGui import QFont

# Helpers
from helpers.logger import log_info, log_debug, log_error
from helpers.font_utils import load_custom_font
from helpers.background_utils import set_background, get_transparent_style
from helpers.icon_utils import build_mixing_path_widget
from helpers.settings_manager import DEFAULT_SETTINGS
from helpers.rank import RankManager

# Core logic
from logic.reverse_logic import ReverseLogic

# UI components
from ui.loading_dialog import LoadingDialog  # Fixed path to the loading dialog


class UnmixWorker(QObject):
    """
    Worker that runs ReverseLogic.unmix in a separate thread.
    Emits 'finished' signal with the result dict once done.
    """
    finished = pyqtSignal(object)

    def __init__(self, reverse_logic: ReverseLogic, product: str, effects: List[str]):
        super().__init__()
        self.logic = reverse_logic
        self.product = product
        self.effects = effects

    def run(self):
        log_debug(f"[UnmixWorker] Starting unmix for product={self.product}, effects={self.effects}", tag="UnmixWorker")
        result = self.logic.unmix(self.product, self.effects)
        log_debug("[UnmixWorker] Finished unmix, emitting result", tag="UnmixWorker")
        self.finished.emit(result)


class PickBestProductWorker(QObject):
    """
    Worker that runs ReverseLogic.pick_best_product in a separate thread.
    Emits 'finished' signal with the result dict once done.
    """
    finished = pyqtSignal(object)

    def __init__(self, reverse_logic: ReverseLogic, effects: List[str]):
        super().__init__()
        self.logic = reverse_logic
        self.effects = effects

    def run(self):
        log_debug(f"[PickBestProductWorker] Starting pick_best_product for effects={self.effects}", tag="PickBestProductWorker")
        result = self.logic.pick_best_product(self.effects)
        log_debug("[PickBestProductWorker] Finished pick_best_product, emitting result", tag="PickBestProductWorker")
        self.finished.emit(result)


class ReverseUI(QWidget):
    """
    ReverseUI is the central widget for the “Unmixer” mode.
    Provides:
    - Product selection (checkbox grid, plus “Pick the best one” option).
    - Effect selection (checkbox grid, limited by max_effects setting).
    - “Unmix” button to compute additive sequence in background.
    - Result panel (HTML summary of steps and pricing).
    - Mixing path bar showing sequence as icons.
    - “Reset” and “Return to Start” buttons.
    """

    def __init__(
        self,
        products: Dict[str, Any],
        effect_colors: Dict[str, str],
        product_order: List[str],
        color_manager,
        reverse_logic: ReverseLogic,
        rank_manager: RankManager,
        settings_manager=None,      # Optional SettingsManager for theming
        return_callback: Callable = None
    ):
        """
        Initialize ReverseUI.

        Args:
            products (Dict[str, Any]): All product data from models.loader.
            effect_colors (Dict[str, str]): Mapping of effect_name → color hex.
            product_order (List[str]): Ordered list of product names.
            color_manager: Provides color assignments for products/effects.
            reverse_logic (ReverseLogic): Core unmixing logic.
            rank_manager (RankManager): Manages accessibility by rank.
            settings_manager: Optional SettingsManager for font, color, background.
            return_callback (Callable, optional): Called when returning to main window.
        """
        super().__init__()
        log_debug("[ReverseUI] __init__ start", tag="ReverseUI")

        self.products = products
        self.effect_colors = effect_colors
        self.product_order = product_order
        self.color_manager = color_manager
        self.reverse_logic = reverse_logic
        self.rank_manager = rank_manager
        self.settings_manager = settings_manager
        self.return_callback = return_callback

        # Selected product and effect state
        self.selected_product = None
        self.product_checkboxes: Dict[str, QCheckBox] = {}
        self.effect_checkboxes: List[QCheckBox] = []
        self.effect_list: List[str] = list(self.effect_colors.keys())

        # Determine font family (fallback to Arial)
        chosen_font = None
        if self.settings_manager:
            font_name = self.settings_manager.get("font")
            chosen_font = load_custom_font(font_name)
        self.font_family = chosen_font or "Arial"

        # Apply theming immediately
        self.apply_settings()

        # Build the UI
        self._build_ui()

        # Loading label (hidden by default)
        self.loading_label = QLabel("Processing...")
        self.loading_label.setVisible(False)
        self.layout().addWidget(self.loading_label)

        self.loading_dialog = None
        log_debug("[ReverseUI] __init__ end", tag="ReverseUI")

    def apply_settings(self):
        """
        Apply theme settings from settings_manager (if provided):
          • Font family → set via QApplication.instance() and this widget’s setFont.
          • Font color → set QWidget stylesheet globally.
          • Background image → set_background on this widget.
        """
        if not self.settings_manager:
            log_debug("ReverseUI: No settings_manager provided; skipping theming", tag="ReverseUI")
            return

        # Font family
        from PyQt6.QtWidgets import QApplication as _QApp
        app_font = QFont(self.font_family, 11)
        _QApp.instance().setFont(app_font)
        self.setFont(app_font)
        log_debug(f"ReverseUI: Applied font '{self.font_family}'", tag="ReverseUI")

        # Font color
        font_color = self.settings_manager.get("font_color") or "#FFFFFF"
        self.setStyleSheet(f"* {{ color: {font_color}; }}")
        log_debug(f"ReverseUI: Applied font color '{font_color}'", tag="ReverseUI")

        # Background image
        bg = self.settings_manager.get("background")
        if bg and os.path.exists(bg):
            set_background(self, bg)
            log_info(f"ReverseUI: Applied background '{bg}'", tag="ReverseUI")

    def _build_ui(self):
        """
        Construct and arrange all UI elements:
        - Top section: product selection with checkboxes.
        - Middle: effects selection and results panel.
        - Bottom: mixing path bar.
        """

        self.setMinimumHeight(1000)
        
        # If no valid background, use default
        bg = self.settings_manager.get("background") if self.settings_manager else None
        if not (bg and os.path.exists(bg)):
            set_background(self, resource_path("assets/images/background1.png"))

        main_layout = QVBoxLayout(self)

        #
        # ── PRODUCTS ZONE ──
        #
        prod_outer = QFrame()
        prod_outer.setFrameShape(QFrame.Shape.StyledPanel)
        prod_outer.setStyleSheet(get_transparent_style())
        main_layout.addWidget(prod_outer)
        prod_outer_l = QVBoxLayout(prod_outer)

        prod_inner = QFrame()
        prod_inner.setFrameShape(QFrame.Shape.StyledPanel)
        prod_inner.setStyleSheet(get_transparent_style())
        prod_outer_l.addWidget(prod_inner)
        prod_inner_l = QVBoxLayout(prod_inner)

        # Label
        lbl = QLabel("Select Product:")
        lbl.setFont(QFont(self.font_family, 12, QFont.Weight.Bold))
        lbl.setStyleSheet("color: Orange;")
        prod_inner_l.addWidget(lbl)

        # Grid: each product checkbox + label
        product_layout = QGridLayout()
        cols = (len(self.product_order) + 1) // 2 + 1
        product_layout.setSpacing(15)

        allowed = self.rank_manager.get_accessible_product_names()
        special = "Pick the best one for me"
        all_products = [p for p in self.product_order if p in allowed] + [special]

        for idx, name in enumerate(all_products):
            r = idx // cols
            c = (idx % cols) * 2

            # Checkbox
            cb = QCheckBox()
            cb.setStyleSheet(get_transparent_style())
            cb.toggled.connect(self.enforce_single_product_selection)
            cb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            product_layout.addWidget(cb, r, c, alignment=Qt.AlignmentFlag.AlignCenter)
            self.product_checkboxes[name] = cb

            # Label next to checkbox
            label = QLabel(name)
            label.setFont(QFont(self.font_family, 12, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if name == special:
                # “Pick the best one for me” in rainbow colors
                label.setText(
                    '<span style="color:red">P</span><span style="color:orange">i</span>'
                    '<span style="color:yellow">c</span><span style="color:green">k</span> '
                    '<span style="color:blue">t</span><span style="color:violet">h</span>'
                    '<span style="color:pink">e</span> '
                    '<span style="color:red">b</span><span style="color:orange">e</span>'
                    '<span style="color:yellow">s</span><span style="color:green">t</span> '
                    '<span style="color:blue">o</span><span style="color:violet">n</span>'
                    '<span style="color:pink">e</span> '
                    '<span style="color:red">f</span><span style="color:orange">o</span>'
                    '<span style="color:yellow">r</span> '
                    '<span style="color:green">m</span><span style="color:blue">e</span>'
                )
            else:
                # Normal product name colored by product color
                prod_color = self.color_manager.product_colors.get(name, "#FFFFFF")
                label.setStyleSheet(f"color: {prod_color};")

            product_layout.addWidget(label, r, c + 1)

        prod_inner_l.addLayout(product_layout)

        #
        # ── MIDDLE: EFFECTS & RESULTS ──
        #
        middle = QHBoxLayout()
        main_layout.addLayout(middle, 1)

        # 1) EFFECTS SECTION
        eff_outer = QFrame()
        eff_outer.setFrameShape(QFrame.Shape.StyledPanel)
        eff_outer.setStyleSheet(get_transparent_style())
        middle.addWidget(eff_outer, 1)
        eff_outer_l = QVBoxLayout(eff_outer)

        eff_inner = QFrame()
        eff_inner.setFrameShape(QFrame.Shape.StyledPanel)
        eff_inner.setStyleSheet(get_transparent_style())
        eff_outer_l.addWidget(eff_inner)
        eff_inner_l = QVBoxLayout(eff_inner)

        effects_container = QWidget()
        self.icons_layout = QGridLayout(effects_container)
        self.create_effect_checkboxes()

        effects_container.setSizePolicy(QSizePolicy.Policy.Expanding,
                                        QSizePolicy.Policy.Preferred)
        eff_inner_l.addWidget(effects_container)


        # 2) RESULTS SECTION
        res_outer = QFrame()
        res_outer.setFrameShape(QFrame.Shape.StyledPanel)
        res_outer.setStyleSheet(get_transparent_style())
        middle.addWidget(res_outer, 1)
        res_outer_l = QVBoxLayout(res_outer)

        res_inner = QFrame()
        res_inner.setFrameShape(QFrame.Shape.StyledPanel)
        res_inner.setStyleSheet(get_transparent_style())
        res_outer_l.addWidget(res_inner)
        res_inner_l = QVBoxLayout(res_inner)

        # QTextEdit for displaying results
        self.result_panel = QTextEdit()
        self.result_panel.setReadOnly(True)
        font = QFont(self.font_family, 12)
        self.result_panel.setFont(font)
        # Ensure white text for readability
        self.result_panel.setStyleSheet(get_transparent_style() + " color: white; font-size: 12pt;")
        self.result_panel.setMinimumWidth(400)
        res_inner_l.addWidget(self.result_panel, 1)

        # Buttons row: Unmix, Reset, Return
        btn_row = QHBoxLayout()
        self.unmix_button = QPushButton("Unmix")
        self.unmix_button.setEnabled(False)
        self.unmix_button.setStyleSheet(get_transparent_style())
        self.unmix_button.clicked.connect(self.safe_handle_unmix)
        btn_row.addWidget(self.unmix_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(get_transparent_style())
        self.reset_button.clicked.connect(self.reset_selection)
        btn_row.addWidget(self.reset_button)

        self.return_button = QPushButton("Return to Start")
        self.return_button.setStyleSheet(get_transparent_style())
        self.return_button.clicked.connect(self.return_to_start)
        btn_row.addWidget(self.return_button)

        res_inner_l.addLayout(btn_row)

        #
        # ── MIXING PATH BAR ──
        #
        icon_outer = QFrame()
        icon_outer.setFrameShape(QFrame.Shape.StyledPanel)
        icon_outer.setStyleSheet(get_transparent_style())
        main_layout.addWidget(icon_outer)
        icon_outer_l = QVBoxLayout(icon_outer)

        icon_inner = QFrame()
        icon_inner.setFrameShape(QFrame.Shape.StyledPanel)
        icon_inner.setStyleSheet(get_transparent_style())
        icon_outer_l.addWidget(icon_inner)

        self.path_layout = QHBoxLayout(icon_inner)
        self.path_layout.setContentsMargins(5, 5, 5, 5)
        self.path_layout.setSpacing(10)
        self.mixing_path_widget = None

        log_debug("[ReverseUI] _build_ui end", tag="ReverseUI")

    def create_effect_checkboxes(self):
        """
        Create a QCheckBox for each effect, styled by effect_colors.
        Enforces maximum selection count (max_effects) from settings_manager.
        """
        max_eff = DEFAULT_SETTINGS["max_effects"]
        if self.settings_manager:
            max_eff = self.settings_manager.get("max_effects")

        for i, effect in enumerate(self.effect_list):
            color = self.color_manager.effect_colors.get(effect, "#FFFFFF")
            cb = QCheckBox(effect)
            cb.setFont(QFont(self.font_family, 10))
            cb.setStyleSheet(get_transparent_style() + f" font-weight: bold; color: {color};")
            cb.toggled.connect(self.limit_effect_selection)
            cb.stateChanged.connect(self.update_unmix_button_state)
            self.effect_checkboxes.append(cb)
            self.icons_layout.addWidget(cb, i // 4, i % 4)

        # Store max_effects for use in limit_effect_selection
        self._max_effects_allowed = max_eff
        log_debug(f"ReverseUI: Created {len(self.effect_list)} effect checkboxes (max {max_eff})", tag="ReverseUI")

    def enforce_single_product_selection(self):
        """
        Ensures that only one product checkbox can be checked at a time.
        Updates selected_product accordingly.
        """
        sender = self.sender()
        if sender.isChecked():
            for product, checkbox in self.product_checkboxes.items():
                if checkbox != sender:
                    checkbox.setChecked(False)
        self.update_selected_product()

    def update_selected_product(self):
        """
        Update self.selected_product based on which product checkbox is checked.
        Updates Unmix button state afterward.
        """
        checked = [p for p, cb in self.product_checkboxes.items() if cb.isChecked()]
        self.selected_product = checked[0] if len(checked) == 1 else None
        log_debug(f"ReverseUI: Selected product set to: {self.selected_product}", tag="ReverseUI")
        self.update_unmix_button_state()

    def limit_effect_selection(self):
        """
        Enforce maximum number of selected effects.
        If user selects beyond limit, uncheck the last toggled box and show warning.
        """
        selected = [cb for cb in self.effect_checkboxes if cb.isChecked()]
        if len(selected) > self._max_effects_allowed:
            sender = self.sender()
            sender.blockSignals(True)
            sender.setChecked(False)
            sender.blockSignals(False)

            warning_msg = f"You can select a maximum of {self._max_effects_allowed} effects."
            log_error(f"ReverseUI: Effect selection limit exceeded (max {self._max_effects_allowed})", tag="ReverseUI")
            QMessageBox.warning(self, "Too Many Effects", warning_msg)

    def update_unmix_button_state(self):
        """
        Enable “Unmix” only if at least one effect is selected AND one product is selected.
        """
        any_checked = any(cb.isChecked() for cb in self.effect_checkboxes)
        product_chosen = self.selected_product is not None
        self.unmix_button.setEnabled(any_checked and product_chosen)

    def safe_handle_unmix(self):
        """
        Wrap handle_unmix in try/except to catch user-facing errors and display them.
        """
        log_debug("[ReverseUI] safe_handle_unmix called", tag="ReverseUI")
        try:
            self.handle_unmix()
        except Exception as e:
            log_error(f"ReverseUI: safe_handle_unmix error: {e}\n{format_exc()}", tag="ReverseUI")
            QMessageBox.warning(self, "Error", str(e))

    def handle_unmix(self):
        """
        Launch the unmix operation in a background thread:
        1) Validate that a product is selected.
        2) If “Pick the best one for me”, call pick_best_product logic.
        3) Otherwise, start UnmixWorker in QThread.
        4) Display LoadingDialog during computation.
        """
        if not self.selected_product:
            raise ValueError("No product selected. Please select a product first.")

        product, effects = self.get_selected_data()

        if product == "Pick the best one for me":
            self._handle_pick_best_product(effects)
            return

        # Show loading dialog
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.cancel_requested.connect(self.cancel_search)
        self.loading_dialog.start()

        self.reverse_logic.reset_cancel_flag()

        self.unmix_thread = QThread()
        self.unmix_worker = UnmixWorker(self.reverse_logic, product, effects)
        self.unmix_worker.moveToThread(self.unmix_thread)
        self.unmix_thread.started.connect(self.unmix_worker.run)
        self.unmix_worker.finished.connect(self.unmix_thread.quit)
        self.unmix_worker.finished.connect(self.unmix_worker.deleteLater)
        self.unmix_thread.finished.connect(self.unmix_thread.deleteLater)
        self.unmix_worker.finished.connect(self.display_result)
        self.unmix_thread.start()

    def _handle_pick_best_product(self, effects: List[str]):
        """
        Launch pick-best-product operation in a background thread:
        Shows LoadingDialog and uses PickBestProductWorker.
        """
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.cancel_requested.connect(self.cancel_search)
        self.loading_dialog.start()

        self.reverse_logic.reset_cancel_flag()

        self.unmix_thread = QThread()
        self.unmix_worker = PickBestProductWorker(self.reverse_logic, effects)
        self.unmix_worker.moveToThread(self.unmix_thread)
        self.unmix_thread.started.connect(self.unmix_worker.run)
        self.unmix_worker.finished.connect(self.unmix_thread.quit)
        self.unmix_worker.finished.connect(self.unmix_worker.deleteLater)
        self.unmix_thread.finished.connect(self.unmix_thread.deleteLater)
        self.unmix_worker.finished.connect(self.display_result)
        self.unmix_thread.start()

    def display_result(self, result: Dict[str, Any]):
        """
        Callback invoked when a background worker finishes:
        1) Stop and close LoadingDialog.
        2) If 'error' in result, show error in result_panel.
        3) Otherwise, build mixing path and HTML summary of steps + pricing.
        """
        if self.loading_dialog:
            log_debug("[ReverseUI] Stopping loading dialog after result", tag="ReverseUI")
            self.loading_dialog.stop()
            self.loading_dialog = None

        if result.get("error"):
            self.result_panel.setPlainText(result["error"])
            return

        product = result["product"]
        steps = result["steps"]           # List of (additive_name, effects_set)
        final_fx = result["final_effects"]  # List[str]
        cost = result["cost"]
        sell = result["sell_value"]

        # Build path bar: [product → each additive]
        path_items = [product] + [s[0] for s in steps]
        if self.mixing_path_widget:
            self.path_layout.removeWidget(self.mixing_path_widget)
            self.mixing_path_widget.deleteLater()

        self.mixing_path_widget = build_mixing_path_widget(path_items)
        self.path_layout.addWidget(self.mixing_path_widget)

        # Build HTML summary
        html_parts: List[str] = []

        # a) Starting product
        html_parts.append(
            f"<p><b>Start:</b> "
            f"<span style='color:{self.color_manager.product_colors.get(product, '#FFFFFF')};'>{product}</span></p>"
        )

        # b) Each additive step
        for addy, effs in steps:
            eff_html = ", ".join(
                f"<span style='color:{self.color_manager.effect_colors.get(e, '#FFFFFF')};'>{e}</span>"
                for e in sorted(effs)
            )
            html_parts.append(
                f"<p>➕ Add <b>{addy}</b> → effects: {eff_html}</p>"
            )

        # c) Final effects
        final_html = ", ".join(
            f"<span style='color:{self.color_manager.effect_colors.get(e, '#FFFFFF')};'>{e}</span>"
            for e in sorted(final_fx)
        )
        html_parts.append(f"<p><b>Final effects:</b> {final_html}</p>")

        # d) Pricing block
        disable_pricing = False
        if self.settings_manager:
            disable_pricing = self.settings_manager.get("product_pricing_disabled")

        html_parts.append("<hr>")

        if not disable_pricing:
            html_parts.append(f"<p>📦 Base cost: ${cost['base_product']:.2f}</p>")
            html_parts.append(f"<p>➕ Additives cost: ${cost['additives']:.2f}</p>")
            html_parts.append(f"<p><b>Total cost:</b> ${cost['total']:.2f}</p>")
            html_parts.append(f"<p><b>Estimated sell price:</b> ${sell:.2f}</p>")
        else:
            html_parts.append(f"<p>➕ Additives cost: ${cost['additives']:.2f}</p>")
            html_parts.append(f"<p><b>Estimated sell price:</b> ${sell:.2f}</p>")

        self.result_panel.setHtml("".join(html_parts))
        log_info("ReverseUI: Displayed unmix results", tag="ReverseUI")

    def get_selected_data(self) -> (str, List[str]):
        """
        Retrieve the selected product name and list of selected effects.

        Returns:
            Tuple[str, List[str]]: (selected_product, selected_effects_list)
        """
        selected_effects = [cb.text() for cb in self.effect_checkboxes if cb.isChecked()]
        return self.selected_product, selected_effects

    def reset_selection(self):
        """
        Reset all selections and clear result panel and mixing path.
        """
        for cb in self.product_checkboxes.values():
            cb.setChecked(False)
        for cb in self.effect_checkboxes:
            cb.setChecked(False)
        self.result_panel.clear()
        if self.mixing_path_widget:
            self.path_layout.removeWidget(self.mixing_path_widget)
            self.mixing_path_widget.deleteLater()
            self.mixing_path_widget = None
        self.selected_product = None
        self.update_unmix_button_state()
        log_info("ReverseUI: Reset selections", tag="ReverseUI")

    def return_to_start(self):
        """
        Invoke return_callback to navigate back to the main window.
        """
        log_info("ReverseUI: Returning to main window", tag="ReverseUI")
        if callable(self.return_callback):
            self.return_callback()

    def cancel_search(self):
        """
        Cancel any ongoing unmix or pick-best-product search:
        - Set cancel flag in ReverseLogic.
        - Quit and wait for the thread if still running.
        - Stop and hide LoadingDialog.
        - Display “Operation cancelled” in result_panel.
        """
        log_debug("[ReverseUI] cancel_search invoked", tag="ReverseUI")
        self.reverse_logic.cancel()
        if hasattr(self, 'unmix_thread'):
            running = self.unmix_thread.isRunning()
            log_debug(f"[ReverseUI] cancel_search: unmix_thread running? {running}", tag="ReverseUI")
            if running:
                self.unmix_thread.quit()
                self.unmix_thread.wait()
                log_debug("[ReverseUI] cancel_search: thread stopped", tag="ReverseUI")
        if self.loading_dialog:
            self.loading_dialog.stop()
            self.loading_dialog = None
        self.result_panel.setPlainText("Operation cancelled.")
        log_info("ReverseUI: Operation cancelled by user", tag="ReverseUI")
