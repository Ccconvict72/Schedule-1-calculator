# views/about_page.py

import json
import urllib.request
import urllib.error
import webbrowser

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

# Pull version from version.py (no circular import)
from version import __version__


class AboutDialog(QDialog):
    """
    “About” dialog for Schedule 1 Calculator.  Explains all core features,
    and lets the user open GitHub or check whether a newer version exists.
    """
    GITHUB_API_LATEST = (
        "https://api.github.com/repos/Ccconvict72/Schedule-1-calculator/releases/latest"
    )
    GITHUB_URL = "https://github.com/Ccconvict72/Schedule-1-calculator"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Schedule 1 Calculator")
        self.resize(600, 500)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # ——— Title & Version ———
        title = QLabel("Schedule 1 Calculator")
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version_label = QLabel(f"Version {__version__}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFont(QFont("Arial", 11))
        layout.addWidget(version_label)

        # ——— Spacer ———
        layout.addSpacing(10)

        # ——— Feature Description ———
        features = (
            "<p><b>Mixing Calculator</b> – Determine exactly which final effects "
            "will result when you mix any combination of available base products "
            "and additives. This helps you predict the end‐product’s behavior before actually "
            "mixing in‐game.</p>"

            "<p><b>Unmixing Calculator</b> – Given your desired set of effects, the "
            "Unmixer will search for the least‐cost “recipe” (sequence of additives) that "
            "produces all of those effects. If there’s no valid path, it notifies you immediately. "
            "You can also use the <b>“Pick the Best for Me”</b> option to automatically select the "
            "cheapest starting product (strain of weed) for your chosen effects.</p>"

            "<p>All <b>product pricing</b> is computed solely from your own operational setup—"
            "container, soil type, and chosen enhancers—and <i>does not</i> include labor or overhead. "
            "We assume you bag up each unit at the end. If you disable product pricing entirely, "
            "you’ll see cost → sale purely in terms of additive‐only costs.</p>"

            "<p><b>Settings Page</b> – Customize look & feel and toggle key behaviors: "
            "change font, font‐color, background—enable or disable “rank” filtering (treat "
            "you as the highest rank to unlock everything)—and disable product pricing altogether. "
            "When rank filtering is on, both calculators only show products/additives at or below your "
            "current in‐game rank, keeping everything aligned with your progression.</p>"

            "<p><b>Quick Tips</b>:<br>"
            "• Unmixing can be computationally intensive; you may cancel at any time.<br>"
            "• Rank filtering narrows down the available items so you don’t see high‐tier ingredients "
            "before you’ve unlocked them.<br>"
            "• Always set up your own container/soil/enhancer choices on the Pricing Page for "
            "accurate cost estimates.</p>"

            "<p>Source code, issue tracker, and updates live on GitHub—click “Open GitHub” below, "
            "or use “Check for Updates” to see if a newer release is available.</p>"
        )

        description = QLabel(features)
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 10))
        description.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(description, stretch=1)

        # ——— Buttons at Bottom ———
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        open_github = QPushButton("Open GitHub")
        open_github.clicked.connect(self._open_github)
        btn_row.addWidget(open_github)

        check_updates = QPushButton("Check for Updates")
        check_updates.clicked.connect(self._check_for_updates)
        btn_row.addWidget(check_updates)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _open_github(self):
        webbrowser.open(AboutDialog.GITHUB_URL)

    def _check_for_updates(self):
        """
        Fetch GitHub’s latest release via REST API and compare against local __version__.
        """
        try:
            req = urllib.request.Request(
                AboutDialog.GITHUB_API_LATEST,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.load(resp)
        except urllib.error.URLError as e:
            QMessageBox.warning(
                self,
                "Update Check Failed",
                f"Could not reach GitHub:\n{e.reason}"
            )
            return

        latest_tag = data.get("tag_name", "")
        if not latest_tag.startswith("v"):
            # GitHub tag might be “1.0.1” or “v1.0.1”
            latest_tag = "v" + latest_tag

        local_ver = __version__.lstrip("v")
        remote_ver = latest_tag.lstrip("v")

        def _version_tuple(v: str):
            return tuple(int(x) for x in v.split("."))

        try:
            if _version_tuple(remote_ver) > _version_tuple(local_ver):
                QMessageBox.information(
                    self,
                    "Update Available",
                    f"A newer version is available on GitHub:\n\n"
                    f"  • Local: {__version__}\n"
                    f"  • Latest: {latest_tag}\n\n"
                    "Please visit GitHub to download the update."
                )
            else:
                QMessageBox.information(
                    self,
                    "Up to Date",
                    f"You are running the latest version ({__version__})."
                )
        except Exception:
            # In case parsing fails, just show raw tags
            QMessageBox.information(
                self,
                "Version Info",
                f"Local version: {__version__}\n"
                f"Latest GitHub tag: {latest_tag}"
            )
