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
from typing import Optional, List, Set
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import *
import shutil
import logging

from . import app
from . import keymap
from . import util
from . import settings

logger = logging.getLogger(__name__)

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

    def __init__(self, a: app.Dodo, keep_open: bool=False, parent: Optional[QWidget]=None):
        """Initialise a panel"""

        super().__init__(parent)
        self.app = a
        self.keep_open = keep_open
        self.is_open = True

        self.keymap: Optional[dict] = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.dirty = True
        self.temp_dirs: List[str] = []

        # set up timer and prefix cache for handling keychords
        self._prefix = ""
        self._prefixes: Set[str] = set()
        self._prefix_timer = QTimer()
        self._prefix_timer.setSingleShot(True)
        self._prefix_timer.setInterval(500)

        def prefix_timeout() -> None:
            if self.keymap and self._prefix in self.keymap:
                self.keymap[self._prefix][1](self)
            elif self._prefix in keymap.global_keymap:
                keymap.global_keymap[self._prefix][1](self.app)
            self._prefix = ""

        self._prefix_timer.timeout.connect(prefix_timeout)

    def title(self) -> str:
        """The title shown on this panel's tab"""

        return 'view'

    def set_keymap(self, mp: dict) -> None:
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


    def refresh(self) -> None:
        self.dirty = False

    def before_close(self) -> bool:
        """Called before closing a panel

        Cleans up temp dirs and returns True. Overriding methods should call this method
        *after* checking they are ready to close.

        :returns: True if the panel is ready to close, or False to cancel
        """

        logger.info('before_close: starting')
        if settings.remove_temp_dirs == 'always':
            for d in self.temp_dirs: shutil.rmtree(d)
        elif settings.remove_temp_dirs == 'ask':
            if len(self.temp_dirs) != 0:
                q = "The following temp dirs were created:\n"
                for d in self.temp_dirs:
                    q += f'  - {d}\n'
                q += '\nClean them up now?'

                if QMessageBox.question(self, 'Remove temp dirs', q) == QMessageBox.StandardButton.Yes:
                    for d in self.temp_dirs: shutil.rmtree(d)

        self.is_open = False
        logger.info('before_close: end')
        return True

    def keyPressEvent(self, e: QKeyEvent) -> None:
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
        logger.info('keyPressEvent: %s', k)
        if not k: return None
        # print("key: " + util.key_string(e))
        cmd = self._prefix + " " + k if self._prefix != "" else k
        self._prefix_timer.stop()

        if cmd in self._prefixes:
            self._prefix = cmd
            self._prefix_timer.start()
        elif self.keymap and cmd in self.keymap:
            self._prefix = ""
            self.keymap[cmd][1](self)
        elif cmd in keymap.global_keymap:
            self._prefix = ""
            keymap.global_keymap[cmd][1](self.app)
        else:
            self._prefix = ""
