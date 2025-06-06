"""
UI helper functions for the application.

This module provides reusable UI component creation functions to maintain
a consistent look and feel throughout the application.
"""

from PyQt6.QtWidgets import QPushButton, QSizePolicy
from helpers.logger import log_info

def create_button(text, on_click=None, width=None, height=None, style=None):
    """
    Create and configure a QPushButton widget for use in the UI.
    
    This function creates buttons with consistent styling and behavior
    across the application, simplifying UI development.
    
    Args:
        text (str): The visible label for the button.
        on_click (callable, optional): Function to be called on button click.
        width (int, optional): Fixed width in pixels.
        height (int, optional): Fixed height in pixels.
        style (str, optional): CSS style string for custom appearance.
    
    Returns:
        QPushButton: A button configured with the specified options.
    """
    btn = QPushButton(text)

    if width:
        btn.setFixedWidth(width)
    if height:
        btn.setFixedHeight(height)

    # By default, expand horizontally, but keep height fixed
    btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    if style:
        btn.setStyleSheet(style)

    if on_click:
        btn.clicked.connect(on_click)

    log_info(f"Created button: '{text}' with size ({width}x{height})", tag="UI")
    return btn
