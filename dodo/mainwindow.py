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
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QCloseEvent
import os

from . import app
from . import commandbar
from . import panel

class MainWindow(QMainWindow):
    def __init__(self, a: app.Dodo):
        super().__init__()
        conf = QSettings('dodo', 'dodo')
        self.app = a

        icon = os.path.dirname(__file__) + '/dodo.svg'
        if os.path.exists(icon):
            self.setWindowIcon(QIcon(icon))
        self.setWindowTitle("Dodo")

        w = QWidget(self)
        w.setLayout(QVBoxLayout())
        self.setCentralWidget(w)
        w.layout().setContentsMargins(0,0,0,0)
        w.layout().setSpacing(0)
        self.resize(1600, 800)
        
        geom = conf.value("main_window_geometry")
        if geom: self.restoreGeometry(geom)

        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.NoFocus)
        # self.tabs.resize(1600, 800)
        w.layout().addWidget(self.tabs)

        def panel_focused(i: int) -> None:
            w = self.tabs.widget(i)
            if w and isinstance(w, panel.Panel):
                w.setFocus()
                if w.dirty: w.refresh()

        self.tabs.currentChanged.connect(panel_focused)
        self.show()

        command_area = QWidget(self)
        command_label = QLabel("search", command_area)
        self.command_bar = commandbar.CommandBar(self.app, command_label, command_area)
        self.command_bar.setFocusPolicy(Qt.NoFocus)

        command_area.setLayout(QHBoxLayout())
        command_area.layout().addWidget(command_label)
        command_area.layout().addWidget(self.command_bar)

        w.layout().addWidget(command_area)
        command_area.setVisible(False)

    def closeEvent(self, e: QCloseEvent) -> None:
        conf = QSettings('dodo', 'dodo')
        conf.setValue("main_window_geometry", self.saveGeometry())
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)

            if isinstance(w, panel.Panel) and not w.before_close():
                e.ignore()
                return

        e.accept()
