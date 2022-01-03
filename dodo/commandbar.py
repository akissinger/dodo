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

from PyQt5.QtWidgets import *

from . import util
from . import keymap
from . import search
from . import thread

class CommandBar(QLineEdit):
    """A command bar that appears on the bottom of the screen when searching
    or tagging."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mode = ''
        self.history = { 'search': [0, []], 'tag': [0, []] }

    def open(self, mode):
        """Open the command bar and give it focus

        This method sets the `command_area` QWidget (which contains the command bar and
        its label) to be visible, and sets the `command_label` to be equal to `mode`.

        :param mode: a string used to set both the label next to the command bar and to dictate
                     its behaviour. Recognized values are "search" and "tag"."""

        self.mode = mode
        self.app.command_label.setText(mode)
        self.app.command_area.setVisible(True)
        self.setFocus()

    def close(self):
        """Clear the command and close

        Call this method by itself to cancel the command."""

        if self.mode in self.history:
            h = self.history[self.mode]
            h[0] = len(h[1])

        self.setText('')
        self.app.command_area.setVisible(False)
        w = self.app.tabs.currentWidget()
        if w: w.setFocus()

    def accept(self):
        """Apply the command typed into the command bar and close

        After the command has been applied, this method saves the command to the command
        history associated with the current mode, then calls :func:`close` to clear
        the command and close the command bar."""

        if self.mode == 'search':
            self.app.search(self.text())
        elif self.mode == 'tag':
            w = self.app.tabs.currentWidget()
            if w:
                if isinstance(w, search.SearchView): w.tag_thread(self.text())
                elif isinstance(w, thread.ThreadView): w.tag_message(self.text())
                w.refresh()

        if self.mode in self.history:
            self.history[self.mode][1].append(self.text())

        self.close()

    def history_previous(self):
        """Cycle to the previous command in the command history

        Note a separate history is kept for each mode."""

        if self.mode in self.history:
            h = self.history[self.mode]
            if len(h[1]) != 0:
                i = max(h[0] - 1, 0)
                h[0] = i
                self.setText(h[1][i])

    def history_next(self):
        """Cycle to the next command in the command history

        Note a separate history is kept for each mode."""

        if self.mode in self.history:
            h = self.history[self.mode]
            if len(h[1]) != 0:
                i = min(h[0] + 1, len(h[1]) - 1)
                h[0] = i
                self.setText(h[1][i])


    def keyPressEvent(self, e):
        """Process keyboard input while the command bar is in focus

        Translate the key event into a string with :func:`~dodo.util.key_string`
        and check if it is in :func:`~dodo.keymap.command_bar_keymap`. If it is,
        fire the associated function. Otherwise, pass the event on to the text
        box.
        
        Note: Key chords are NOT supported in the command bar.
        """
        k = util.key_string(e)
        if k in keymap.command_bar_keymap:
            if isinstance(keymap.command_bar_keymap[cmd], tuple):
                keymap.command_bar_keymap[k][1](self)
            else:
                keymap.command_bar_keymap[k](self)
        else:
            super().keyPressEvent(e)
