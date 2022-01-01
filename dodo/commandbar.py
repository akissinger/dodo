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
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mode = ''
        self.history = { 'search': [0, []], 'tag': [0, []] }

    def open(self, mode):
        self.mode = mode
        self.app.command_label.setText(mode)
        self.app.command_area.setVisible(True)
        self.setFocus()

    def close(self):
        if self.mode in self.history:
            h = self.history[self.mode]
            h[0] = len(h[1])

        self.setText('')
        self.app.command_area.setVisible(False)
        w = self.app.tabs.currentWidget()
        if w: w.setFocus()

    def accept(self):
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
        if self.mode in self.history:
            h = self.history[self.mode]
            if len(h[1]) != 0:
                i = max(h[0] - 1, 0)
                h[0] = i
                self.setText(h[1][i])

    def history_next(self):
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
            keymap.command_bar_keymap[k](self)
        else:
            super().keyPressEvent(e)
