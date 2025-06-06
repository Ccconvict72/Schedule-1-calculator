"""
views/product_pricing.py

Dialog for managing per-product price settings.
Now reads/writes each product’s “last‐used” options into settings_manager["product_pricing"].
"""

import os
from typing import Dict, Any
import logging

# PyQt6 imports
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QGroupBox,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QScrollArea,
    QButtonGroup
)
from PyQt6.QtGui import QPixmap, QFont, QIcon, QFontDatabase
from PyQt6.QtCore import Qt

# Models and helpers
from models.pricing import update_product_prices
from models.loader import load_products, save_products
from models.product import Product
from helpers.background_utils import set_background
from helpers.font_utils import load_custom_font
from helpers.logger import log_info, log_debug

logger = logging.getLogger(__name__)


class ProductPricePage(QDialog):
    """
    ProductPricePage allows the user to configure pricing options for each product.
    Now, each tab reads/writes its own choices into settings_manager["product_pricing"].
    """

    def __init__(self, products: Dict[str, Product], settings_manager):
        """
        Initialize ProductPricePage.

        Args:
            products: Dictionary of Product objects loaded from models.loader.
            settings_manager: SettingsManager instance (including "product_pricing" dict).
        """
        super().__init__()

        self.products = products
        self.settings_manager = settings_manager

        # Apply user’s background & font settings
        self._apply_theme()
        self.custom_font = self._load_font_from_settings()
        self.font_color = self.settings_manager.get("font_color") or "#FF0000"

        self.setWindowTitle("Product Price Page")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        log_debug("ProductPricePage: Building tabs for products", tag="ProductPricePage")
        self._build_tabs()

        close_btn = QPushButton("Close")
        close_btn.setFont(self.custom_font)
        close_btn.setStyleSheet(f"color: {self.font_color};")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        log_info("ProductPricePage initialized", tag="ProductPricePage")

    def _apply_theme(self):
        """
        Apply background image from settings_manager, if it exists.
        """
        bg = self.settings_manager.get("background")
        if bg and os.path.exists(bg):
            set_background(self, bg)
            log_debug(f"ProductPricePage: Applied background '{bg}'", tag="ProductPricePage")

    def _load_font_from_settings(self) -> QFont:
        """
        Load the font specified by settings_manager["font"], fallback to Arial.
        """
        font_name = self.settings_manager.get("font")
        if font_name:
            family = load_custom_font(font_name)
            log_debug(f"ProductPricePage: Loaded custom font '{family}'", tag="ProductPricePage")
        else:
            family = "Arial"
            log_debug("ProductPricePage: No custom font in settings; using Arial", tag="ProductPricePage")
        return QFont(family, 12)

    def _build_tabs(self):
        """
        Create one tab per product. Each tab’s controls are initialized from
        settings_manager["product_pricing"]. When “Calculate” or “Reset” is clicked,
        we update settings_manager["product_pricing"][product_name] accordingly.
        """
        # Fetch the saved “product_pricing” dict from settings_manager
        saved_pricing: Dict[str, Any] = self.settings_manager.get("product_pricing") or {}

        ordered_keys = sorted(self.products.keys(), key=lambda k: self.products[k].Order)
        self.tab_controls = {}

        for key in ordered_keys:
            product = self.products[key]
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(8, 8, 8, 8)

            # Header (icon + name)
            self._add_header(tab_layout, product)

            # Scrollable area for controls
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(8, 8, 8, 8)
            scroll.setWidget(content)
            tab_layout.addWidget(scroll)

            controls = {}

            # Retrieve this product’s previously saved pricing choices, if any
            prev_choices = saved_pricing.get(product.Name, {})

            if product.Name != "Meth":
                # Growth Container radio buttons
                controls.update(self._add_group(
                    content_layout,
                    "Growth Container",
                    [
                        ("Grow Tent", "grow_tent_icon.webp"),
                        ("Cheap Plastic Pot", "cheap_plastic_pot_icon.webp"),
                        ("Moisture-Preserving Pot", "moisture_preserving_pot_icon.webp"),
                        ("Air Pot", "air_pot_icon.webp")
                    ],
                    "container_buttons",
                    prev_checked=prev_choices.get("container")
                ))
                # Soil radio buttons
                controls.update(self._add_group(
                    content_layout,
                    "Soil",
                    [
                        ("Soil", "soil_icon.webp"),
                        ("Long-Life Soil", "LongLifeSoil_Icon.webp"),
                        ("Extra Long-Life Soil", "ExtraLongLifeSoil_Stored_Icon.webp")
                    ],
                    "soil_buttons",
                    prev_checked=prev_choices.get("soil")
                ))
                # Crop Enhancers checkboxes
                controls.update(self._add_checkboxes(
                    content_layout,
                    "Crop Enhancers",
                    [
                        ("Fertilizer", "fertilizer_icon.webp"),
                        ("PGR", "pgr_icon.webp"),
                        ("Speed Grow", "SpeedGrow_Icon.webp")
                    ],
                    "enhancer_checkboxes",
                    prev_checked_list=prev_choices.get("enhancers", [])
                ))
            else:
                # Pseudo Quality radio buttons for “Meth”
                controls.update(self._add_group(
                    content_layout,
                    "Pseudo Quality",
                    [
                        ("Poor", "pseudo_icon.webp"),
                        ("Standard", "pseudo_icon.webp"),
                        ("Premium", "pseudo_icon.webp")
                    ],
                    "pseudo_buttons",
                    prev_checked=prev_choices.get("quality")
                ))

            # “Disable product prices” checkbox (persisted per settings_manager)
            disable_cb = QCheckBox("Disable product prices")
            disable_cb.setFont(self.custom_font)
            disable_cb.setStyleSheet(f"color: {self.font_color};")

            # Initialize from settings_manager (global flag is still used)
            saved_disable = self.settings_manager.get("product_pricing_disabled")
            disable_cb.setChecked(bool(saved_disable))
            disable_cb.toggled.connect(self._on_disable_pricing_toggled)
            tab_layout.addWidget(disable_cb)
            controls["disable_prices_checkbox"] = disable_cb

            # Calculate & Reset buttons
            btn_hbox = QHBoxLayout()
            calc_btn = QPushButton("Calculate")
            reset_btn = QPushButton("Reset")
            for btn in (calc_btn, reset_btn):
                btn.setFont(self.custom_font)
                btn.setStyleSheet(f"color: {self.font_color};")
            btn_hbox.addWidget(calc_btn)
            btn_hbox.addWidget(reset_btn)
            tab_layout.addLayout(btn_hbox)

            # Connect actions—pass along the controls + any previously saved choices
            calc_btn.clicked.connect(lambda _, p=product.Name, c=controls: self._on_calculate(p, c))
            reset_btn.clicked.connect(lambda _, p=product.Name, c=controls: self._on_reset(p, c))
            controls["calculate_btn"] = calc_btn
            controls["reset_btn"] = reset_btn

            # Add this tab
            self.tab_widget.addTab(tab, product.Name)
            self.tab_widget.setTabToolTip(self.tab_widget.indexOf(tab), product.Name)
            self.tab_controls[product.Name] = controls

            log_debug(f"ProductPricePage: Tab created for '{product.Name}' with prev_choices={prev_choices}", tag="ProductPricePage")

    def _add_header(self, layout, product: Product):
        """
        Add a header that shows the product icon (if exists) and product name.
        """
        hbox = QHBoxLayout()
        icon = QLabel()
        icon_path = os.path.join("assets", "icons", f"{product.Name.replace(' ', '_')}_Icon.webp")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            icon.setPixmap(pix)
        name = QLabel(product.Name)
        name.setFont(self.custom_font)
        name.setStyleSheet(f"color: {self.font_color};")
        hbox.addWidget(icon)
        hbox.addWidget(name)
        hbox.addStretch()
        layout.addLayout(hbox)

    def _add_group(
        self,
        layout,
        title: str,
        items: list[tuple[str, str]],
        key: str,
        prev_checked: str | None = None
    ) -> dict[str, QButtonGroup]:
        """
        Add a QGroupBox with mutually exclusive QRadioButtons.
        - If prev_checked is provided, that radio button will be setChecked(True).

        Returns:
            { key: QButtonGroup }
        """
        group = QGroupBox(title)
        group.setFont(self.custom_font)
        group.setStyleSheet(
            f"QGroupBox {{ background-color: rgba(50, 50, 50, 153); color: {self.font_color}; border-radius: 4px; }}"
        )
        vbox = QVBoxLayout(group)
        buttons = QButtonGroup(group)

        for idx, (name, icon_file) in enumerate(items):
            btn = QRadioButton(name)
            btn.setFont(self.custom_font)
            btn.setStyleSheet(f"color: {self.font_color};")
            icon_fp = os.path.join("assets", "icons", icon_file)
            if os.path.exists(icon_fp):
                pix = QPixmap(icon_fp).scaled(
                    24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                btn.setIcon(QIcon(pix))
            buttons.addButton(btn, id=idx)
            vbox.addWidget(btn)
            # If this was previously selected, check it now
            if prev_checked and name == prev_checked:
                btn.setChecked(True)

        layout.addWidget(group)
        return {key: buttons}

    def _add_checkboxes(
        self,
        layout,
        title: str,
        items: list[tuple[str, str]],
        key: str,
        prev_checked_list: list[str] | None = None
    ) -> dict[str, list[QCheckBox]]:
        """
        Add a QGroupBox containing multiple QCheckBoxes (for “Enhancers”).
        - If prev_checked_list is provided, any checkbox whose text appears in that list is setChecked(True).

        Returns:
            { key: [QCheckBox, ...] }
        """
        group = QGroupBox(title)
        group.setFont(self.custom_font)
        group.setStyleSheet(
            f"QGroupBox {{ background-color: rgba(50, 50, 50, 153); color: {self.font_color}; border-radius: 4px; }}"
        )
        vbox = QVBoxLayout(group)
        checkboxes: list[QCheckBox] = []

        for name, icon_file in items:
            cb = QCheckBox(name)
            cb.setFont(self.custom_font)
            cb.setStyleSheet(f"color: {self.font_color};")
            icon_fp = os.path.join("assets", "icons", icon_file)
            if os.path.exists(icon_fp):
                pix = QPixmap(icon_fp).scaled(
                    24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                cb.setIcon(QIcon(pix))
            if prev_checked_list and name in prev_checked_list:
                cb.setChecked(True)
            checkboxes.append(cb)
            vbox.addWidget(cb)

        layout.addWidget(group)
        return {key: checkboxes}

    def _on_disable_pricing_toggled(self, checked: bool):
        """
        Whenever “Disable product prices” is toggled in any tab, immediately persist that.
        (Other code paths may still rely on this global flag.)
        """
        self.settings_manager.set("product_pricing_disabled", checked)
        log_info(f"ProductPricePage: product_pricing_disabled = {checked}", tag="ProductPricePage")

    def _on_calculate(self, product_name: str, ctrls: Dict[str, Any]):
        """
        Handle the “Calculate” click for a given product:
        1) Read the chosen container/soil/enhancers/quality.
        2) Call update_product_prices(...) to recalc and save the new Product dictionary.
        3) Save back into `settings_manager.settings["product_pricing"][product_name]`:
            {
              "container": str,
              "soil": str,
              "enhancers": [...],
              "quality": str (if Meth),
            }
        4) Persist products to disk via save_products(...).
        """
        disable = ctrls["disable_prices_checkbox"].isChecked()
        self.settings_manager.set("product_pricing_disabled", disable)

        # Build a dict of “this product’s choices” so we can store in SettingsManager
        choice_record: dict[str, Any] = {}

        if product_name == "Meth":
            quality = self._get_checked_text(ctrls.get("pseudo_buttons")) or "Premium"
            choice_record["quality"] = quality

            updated = update_product_prices(
                self.products,
                "Grow Tent",  # This is a default placeholder, not relevant for Meth
                "Soil",
                [],
                quality,
                disable
            )
        else:
            container = self._get_checked_text(ctrls.get("container_buttons")) or "Grow Tent"
            soil = self._get_checked_text(ctrls.get("soil_buttons")) or "Extra Long-Life Soil"
            enhancers = [
                cb.text()
                for cb in ctrls.get("enhancer_checkboxes", [])
                if cb.isChecked()
            ] or ["Fertilizer", "Speed Grow"]

            choice_record["container"] = container
            choice_record["soil"] = soil
            choice_record["enhancers"] = enhancers

            updated = update_product_prices(
                self.products,
                container,
                soil,
                enhancers,
                "Premium",
                disable
            )

        # Update the in-memory products map and write to disk
        self.products = updated
        save_products(self.products)

        # Now store this product’s last-used choices under settings_manager["product_pricing"]
        all_pricing = self.settings_manager.get("product_pricing") or {}
        all_pricing[product_name] = choice_record
        self.settings_manager.set("product_pricing", all_pricing)

        self._info_dialog("Saved", f"Price for '{product_name}' recalculated and saved.")
        log_info(f"ProductPricePage: Saved pricing choices for '{product_name}': {choice_record}", tag="ProductPricePage")

    def _on_reset(self, product_name: str, ctrls: Dict[str, Any]):
        """
        Handle the “Reset” click for a given product:
        1) Restore worst-case defaults (and uncheck “disable pricing”).
        2) Call update_product_prices(...) with those defaults.
        3) Persist the default choice_record to settings_manager["product_pricing"].
        """
        # Uncheck global disable flag
        self.settings_manager.set("product_pricing_disabled", False)
        ctrls["disable_prices_checkbox"].setChecked(False)

        default_record: dict[str, Any] = {}

        if product_name == "Meth":
            # Default “Premium” quality
            for btn in ctrls.get("pseudo_buttons").buttons():
                btn.setAutoExclusive(False)
                btn.setChecked(btn.text() == "Premium")
                btn.setAutoExclusive(True)
            default_record["quality"] = "Premium"

            updated = update_product_prices(
                self.products,
                "Grow Tent",
                "Soil",
                [],
                "Premium",
                False
            )
        else:
            # Default container → “Grow Tent”
            for btn in ctrls.get("container_buttons").buttons():
                btn.setAutoExclusive(False)
                btn.setChecked(btn.text() == "Grow Tent")
                btn.setAutoExclusive(True)
            default_record["container"] = "Grow Tent"

            # Default soil → “Extra Long-Life Soil”
            for btn in ctrls.get("soil_buttons").buttons():
                btn.setAutoExclusive(False)
                btn.setChecked(btn.text() == "Extra Long-Life Soil")
                btn.setAutoExclusive(True)
            default_record["soil"] = "Extra Long-Life Soil"

            # Default enhancers → “Fertilizer” and “Speed Grow”
            for cb in ctrls.get("enhancer_checkboxes", []):
                cb.setChecked(cb.text() in ("Fertilizer", "Speed Grow"))
            default_record["enhancers"] = ["Fertilizer", "Speed Grow"]

            updated = update_product_prices(
                self.products,
                "Grow Tent",
                "Extra Long-Life Soil",
                ["Fertilizer", "Speed Grow"],
                "Premium",
                False
            )

        # Persist the updated products map
        self.products = updated
        save_products(self.products)

        # Save default_record into settings_manager["product_pricing"]
        all_pricing = self.settings_manager.get("product_pricing") or {}
        all_pricing[product_name] = default_record
        self.settings_manager.set("product_pricing", all_pricing)

        self._info_dialog("Reset", f"'{product_name}' price reset to worst-case.")
        log_info(f"ProductPricePage: Reset pricing choices for '{product_name}' to {default_record}", tag="ProductPricePage")

    def _get_checked_text(self, group: QButtonGroup) -> str | None:
        """
        Return the text of the checked radio button in `group`, or None if none.
        """
        if group:
            btn = group.checkedButton()
            return btn.text() if btn else None
        return None

    def _info_dialog(self, title: str, message: str):
        """
        Display a modal info dialog with a given title and message.
        """
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        lbl = QLabel(message, dlg)
        lbl.setFont(self.custom_font)
        lbl.setStyleSheet(f"color: {self.font_color};")
        layout = QVBoxLayout(dlg)
        layout.addWidget(lbl)
        ok = QPushButton("OK", dlg)
        ok.setFont(self.custom_font)
        ok.setStyleSheet(f"color: {self.font_color};")
        ok.clicked.connect(dlg.accept)
        layout.addWidget(ok, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()
