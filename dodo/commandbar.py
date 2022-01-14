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
from typing import Dict, List, Tuple
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent

from . import app
from . import util
from . import keymap
from . import search
from . import thread

class CommandBar(QLineEdit):
    """A command bar that appears on the bottom of the screen when searching
    or tagging."""

    def __init__(self, a: app.Dodo, label: QLabel, parent: QWidget):
        super().__init__(parent)
        self.app = a
        self.label = label
        self.mode = ''
        self.history: Dict[str, Tuple[int, List[str]]] = { 'search': (0, []), 'tag': (0, []) }

    def open(self, mode: str) -> None:
        """Open the command bar and give it focus

        This method sets the `command_area` QWidget (which contains the command bar and
        its label) to be visible, and sets the `command_label` to be equal to `mode`.

        :param mode: a string used to set both the label next to the command bar and to dictate
                     its behaviour. Recognized values are "search" and "tag"."""

        self.mode = mode
        self.label.setText(mode)
        self.parent().setVisible(True)
        self.setFocus()

    def close_bar(self) -> None:
        """Clear the command and close

        Call this method by itself to cancel the command and close the bar. Note we use
        `close_bar` to avoid a name clash with QWidget.close."""

        if self.mode in self.history:
            _, h = self.history[self.mode]
            self.history[self.mode] = (len(h), h)

        self.setText('')
        self.parent().setVisible(False)
        w = self.app.tabs.currentWidget()
        if w: w.setFocus()

    def accept(self) -> None:
        """Apply the command typed into the command bar and close

        After the command has been applied, this method saves the command to the command
        history associated with the current mode, then calls :func:`close_bar` to clear
        the command and close the command bar."""

        if self.mode == 'search':
            self.app.search(self.text())
        elif self.mode == 'tag':
            w = self.app.tabs.currentWidget()
            if w:
                if isinstance(w, search.SearchPanel): w.tag_thread(self.text())
                elif isinstance(w, thread.ThreadPanel): w.tag_message(self.text())
                w.refresh()

        if self.mode in self.history:
            pos, h = self.history[self.mode]
            h.append(self.text())
            self.history[self.mode] = (pos + 1, h)

        self.close_bar()

    def history_previous(self) -> None:
        """Cycle to the previous command in the command history

        Note a separate history is kept for each mode."""

        if self.mode in self.history:
            pos, h = self.history[self.mode]
            if len(h) != 0:
                pos = max(pos - 1, 0)
                self.history[self.mode] = (pos, h)
                self.setText(h[pos])

    def history_next(self) -> None:
        """Cycle to the next command in the command history

        Note a separate history is kept for each mode."""

        if self.mode in self.history:
            pos, h = self.history[self.mode]
            if len(h) != 0:
                pos = min(pos + 1, len(h) - 1)
                self.history[self.mode] = (pos, h)
                self.setText(h[pos])


    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Process keyboard input while the command bar is in focus

        Translate the key event into a string with :func:`~dodo.util.key_string`
        and check if it is in :func:`~dodo.keymap.command_bar_keymap`. If it is,
        fire the associated function. Otherwise, pass the event on to the text
        box.
        
        Note: Key chords are NOT supported in the command bar.
        """
        k = util.key_string(e)
        if k in keymap.command_bar_keymap:
            keymap.command_bar_keymap[k][1](self)
        else:
            super().keyPressEvent(e)
