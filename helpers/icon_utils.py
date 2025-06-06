"""
Icon utilities for UI components.

Provides functions to fetch, display, and build icon widgets using PyQt6.
Handles icon loading, scaling, and display in UI components.
"""

import os
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from helpers.logger import log_debug, log_warning, log_info

DEFAULT_ICON_SIZE = (16, 16)
ICON_SUFFIX = "_Icon.webp"
ICON_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons"))
DEFAULT_ICON_PATH = os.path.join(ICON_DIR, "default_icon.webp")

def get_icon_path(item_name: str) -> str:
    """
    Get the file path for an item's icon.

    Args:
        item_name (str): Name of the item.

    Returns:
        str: Path to icon image or default fallback path.
    """
    safe_name = item_name.strip().replace(" ", "_") + ICON_SUFFIX
    path = os.path.join(ICON_DIR, safe_name)

    if os.path.exists(path):
        log_debug(f"Resolved icon path for '{item_name}': {path}", tag="Icons")
        return path

    if not os.path.exists(DEFAULT_ICON_PATH):
        log_warning(f"Default icon missing at expected path: {DEFAULT_ICON_PATH}", tag="Icons")
        return ""

    log_warning(f"Missing icon for '{item_name}', using default.", tag="Icons")
    return DEFAULT_ICON_PATH

def create_icon_label(item_name: str, size: tuple[int, int] = DEFAULT_ICON_SIZE) -> QLabel:
    """
    Create a QLabel containing an icon and a tooltip.

    Args:
        item_name (str): Name of the item for the icon.
        size (tuple): Width and height in pixels.

    Returns:
        QLabel: Label with icon pixmap.
    """
    path = get_icon_path(item_name)
    label = QLabel()

    if path and os.path.exists(path):
        pixmap = QPixmap(path).scaled(size[0], size[1],
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)

    label.setToolTip(item_name)
    return label

def build_mixing_path_widget(path_items: list[str]) -> QWidget:
    """
    Create a scrollable icon sequence for a mixing path.

    Args:
        path_items (list[str]): Ordered list of items in the path.

    Returns:
        QWidget: Scrollable widget with icon sequence.
    """
    log_info(f"Building mixing path widget for: {path_items}", tag="UI")

    path_widget = QWidget()
    layout = QHBoxLayout()
    layout.setSpacing(5)
    layout.setContentsMargins(0, 0, 0, 0)

    for i, item_name in enumerate(path_items):
        icon = create_icon_label(item_name)

        name_label = QLabel(item_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 8pt;")

        item_widget = QWidget()
        item_layout = QVBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(2)
        item_layout.addWidget(icon)
        item_layout.addWidget(name_label)
        item_widget.setLayout(item_layout)

        layout.addWidget(item_widget)

        if i < len(path_items) - 1:
            arrow = QLabel("→")
            arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow.setStyleSheet("font-size: 10pt; font-weight: bold;")
            layout.addWidget(arrow)

    container = QWidget()
    container.setLayout(layout)

    scroll_area = QScrollArea()
    scroll_area.setWidget(container)
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setFixedHeight(70)

    return scroll_area
