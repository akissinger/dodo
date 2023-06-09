#     Dodo - A graphical, hackable email client based on notmuch
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Dodo
#
# Dodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dodo. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from typing import Optional

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from . import keymap
from . import util
from . import settings

class HelpWindow(QWidget):
    """A window showing all keybindings"""

    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.help_text = QTextBrowser()
        self.layout().addWidget(self.help_text)
        self.resize(400, 800)
        self.setWindowTitle('Dodo - Help')

        maps = [
            ("Global", keymap.global_keymap),
            ("Search view", keymap.search_keymap),
            ("Tag view", keymap.tag_keymap),
            ("Thread view", keymap.thread_keymap),
            ("Compose view", keymap.compose_keymap),
            ("Command bar", keymap.command_bar_keymap),
        ]

        s = ''

        for name, mp in maps:
            s += f'<h2>{name} key bindings</h2>\n'
            s += f'<table style="font-family: {settings.search_font}; font-size: {settings.search_font_size}pt">\n'
            for key,val in mp.items():
                if isinstance(val, tuple): desc = val[0]
                else: desc = '(no description)'
                s += f'<tr><td width="100" style="color: {settings.theme["fg_bright"]}">{util.simple_escape(key)}</td>\n'
                s += f'<td style="color: {settings.theme["fg"]}">{desc}</td></tr>\n'
            s += '</table><br />'

        s += '<br /><br />'

        self.help_text.setHtml(s)

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Handle key press

        If <escape> is pressed, exit, otherwise pass the keypress on."""

        if e.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)
