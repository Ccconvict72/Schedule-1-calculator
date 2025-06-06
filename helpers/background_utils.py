"""
Background utilities for the Schedule 1 Calculator UI.

Provides helper functions to apply dynamic window backgrounds and reusable
style snippets for transparent UI elements in PyQt6.
"""

import logging
from pathlib import Path
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from PyQt6.QtCore import Qt

logger = logging.getLogger("Schedule1Calculator")

def set_background(widget, image_path: str | Path):
    """
    Set a scalable background image for a PyQt6 widget.

    Args:
        widget: The target PyQt6 widget or window.
        image_path (str | Path): Path to the background image.
    """
    image_path = Path(image_path)
    pixmap = QPixmap(str(image_path))

    if pixmap.isNull():
        logger.error(f"[Background] Failed to load background image: {image_path}")
        return

    def apply_scaled_background():
        scaled_pixmap = pixmap.scaled(
            widget.size(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        palette = widget.palette() or QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled_pixmap))
        widget.setAutoFillBackground(True)
        widget.setPalette(palette)

    apply_scaled_background()
    widget.update()

    # Preserve original resize handler if it exists
    original_resize = getattr(widget, "resizeEvent", None)

    def resize_event(event):
        apply_scaled_background()
        if original_resize:
            original_resize(event)
        else:
            event.accept()

    widget.resizeEvent = resize_event

def get_transparent_style() -> str:
    """
    Return CSS string for semi-transparent dark panels.

    Returns:
        str: A reusable PyQt6 stylesheet string.
    """
    return (
        "background-color: rgba(0, 0, 0, 0.6);"
        "border-radius: 8px;"
        "padding: 6px;"
    )
