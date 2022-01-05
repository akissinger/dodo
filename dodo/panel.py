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

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import *
import shutil

from . import keymap
from . import util
from . import settings

class Panel(QWidget):
    """A container widget that can handle key events and be shown on a tab

    This is the base class for :class:`~dodo.search.SearchPanel`,
    :class:`~dodo.thread.ThreadPanel`, and
    :class:`~dodo.compose.ComposePanel`, which are the main top-level
    containers used by Dodo.


    :param keep_open: If this is True, keep the panel open even when instructed to close.
                      This is used to make sure the "Inbox" :class:`~dodo.search.SearchPanel`
                      always stays open.
    """

    def __init__(self, app, keep_open=False, parent=None):
        """Initialise a panel"""

        super().__init__(parent)
        self.app = app
        self.keep_open = keep_open

        self.keymap = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.dirty = True
        self.temp_dirs = []

        # set up timer and prefix cache for handling keychords
        self._prefix = ""
        self._prefixes = set()
        self._prefix_timer = QTimer()
        self._prefix_timer.setSingleShot(True)
        self._prefix_timer.setInterval(500)

        def prefix_timeout():
            if self.keymap and self._prefix in self.keymap:
                self.keymap[self._prefix](self)
            elif self._prefix in keymap.global_keymap:
                keymap.global_keymap[self._prefix](self.app)
            self._prefix = ""

        self._prefix_timer.timeout.connect(prefix_timeout)

    def title(self):
        """The title shown on this panel's tab"""

        return 'view'

    def set_keymap(self, mp):
        """Set the local keymap to be the given dictionary.

        This needs to be called in the :func:`__init__` method of each child class
        to ensure it handles keychords correctly."""

        self.keymap = mp

        # update prefix cache for current keymap
        self._prefixes = set()
        for m in [keymap.global_keymap, self.keymap]:
            for k in m:
                for i in range(1,len(k)):
                    self._prefixes.add(k[0:-i])


    def refresh(self):
        self.dirty = False

    def before_close(self):
        """Called before closing a panel

        Cleans up temp dirs and returns True. Overriding methods should call this method
        *after* checking they are ready to close.

        :returns: True if the panel is ready to close, or False to cancel
        """

        if settings.remove_temp_dirs == 'always':
            for d in self.temp_dirs: shutil.rmtree(d)
        elif settings.remove_temp_dirs == 'ask':
            if len(self.temp_dirs) != 0:
                q = "The following temp dirs were created:\n"
                for d in self.temp_dirs:
                    q += f'  - {d}\n'
                q += '\nClean them up now?'

                if QMessageBox.question(self, 'Remove temp dirs', q) == QMessageBox.Yes:
                    for d in self.temp_dirs: shutil.rmtree(d)

        return True

    def keyPressEvent(self, e):
        """Passes key events to the appropriate keymap

        First a key press (possibly with modifiers) is translated into a string
        representation using :func:`~dodo.util.key_string`. Then, if that string
        is part of a keychord, start a timer to try to gather more input.

        Once we have the full keychord (or a timeout has occurred), check if the
        string of the keychord is in the keymap set via :func:`set_keymap`. If so,
        fire the associated function. Otherwise, check :func:`~dodo.keymap.global_keymap`
        and fire the associated function. If it is not in either, swallow the input and
        do nothing.
        """

        k = util.key_string(e)
        if not k: return None
        # print("key: " + util.key_string(e))
        cmd = self._prefix + " " + k if self._prefix != "" else k
        self._prefix_timer.stop()

        if cmd in self._prefixes:
            self._prefix = cmd
            self._prefix_timer.start()
        elif self.keymap and cmd in self.keymap:
            self._prefix = ""
            if isinstance(self.keymap[cmd], tuple):
                self.keymap[cmd][1](self)
            else: 
                self.keymap[cmd](self)
        elif cmd in keymap.global_keymap:
            self._prefix = ""
            if isinstance(keymap.global_keymap[cmd], tuple):
                keymap.global_keymap[cmd][1](self.app)
            else:
                keymap.global_keymap[cmd](self.app)
