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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import subprocess

from . import search
from . import thread
from . import compose
from . import settings
from . import themes
from . import util
from . import keymap
from . import commandbar
from . import help

class SyncMailThread(QThread):
    done = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            subprocess.run(settings.sync_mail_command, stdout=subprocess.PIPE)
            subprocess.run(['notmuch', 'new'], stdout=subprocess.PIPE)
        finally:
            self.done.emit()

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        conf = QSettings('dodo', 'dodo')
        self.setApplicationName('Dodo')

        # find a load config.py
        self.config_file = QStandardPaths.locate(QStandardPaths.ConfigLocation, 'dodo/config.py')
        if self.config_file:
            exec(open(self.config_file).read())
        else:
            config_locs = QStandardPaths.standardLocations(QStandardPaths.ConfigLocation)
            print('No config.py found in:\n' + '\n'.join([f'  {d}/dodo' for d in config_locs]))
            sys.exit(1)

        # construct help window
        self.help_window = help.HelpWindow()

        # apply theme
        themes.apply_theme(self, settings.theme)

        # set up GUI
        self.main_window = QWidget()
        self.main_window.setWindowIcon(QIcon('icons/dodo.svg'))
        self.main_window.setWindowTitle("Dodo")
        self.main_window.setLayout(QVBoxLayout())
        self.main_window.layout().setContentsMargins(0,0,0,0)
        self.main_window.resize(1600, 800)
        
        geom = conf.value("main_window_geometry")
        if geom: self.main_window.restoreGeometry(geom)
        self.aboutToQuit.connect(lambda:
                conf.setValue("main_window_geometry", self.main_window.saveGeometry()))

        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.NoFocus)
        # self.tabs.resize(1600, 800)
        self.main_window.layout().addWidget(self.tabs)

        def panel_focused(i):
            w = self.tabs.widget(i)
            if w:
                w.setFocus()
                if w.dirty: w.refresh()

        self.tabs.currentChanged.connect(panel_focused)
        self.main_window.show()

        self.command_label = QLabel("search")
        self.command_bar = commandbar.CommandBar(self)
        self.command_bar.setFocusPolicy(Qt.NoFocus)

        self.command_area = QWidget()
        self.command_area.setLayout(QHBoxLayout())
        self.main_window.layout().setContentsMargins(0,0,0,0)
        self.main_window.layout().setSpacing(0)

        self.command_area.layout().addWidget(self.command_label)
        self.command_area.layout().addWidget(self.command_bar)
        self.main_window.layout().addWidget(self.command_area)

        self.command_area.setVisible(False)

        # set timer to sync email periodically
        if settings.sync_mail_interval != -1:
            timer = QTimer(self)
            timer.timeout.connect(self.sync_mail)
            timer.start(settings.sync_mail_interval * 1000)

        # open inbox and make un-closeable
        self.search('tag:inbox', keep_open=True)

    def show_help(self):
        self.help_window.show()

    def add_panel(self, panel, focus=True):
        self.tabs.addTab(panel, panel.title())
        if focus:
            self.tabs.setCurrentWidget(panel)
        panel.setFocus()

    def next_panel(self):
        i = self.tabs.currentIndex() + 1
        if i < self.tabs.count():
            self.tabs.setCurrentIndex(i)

    def previous_panel(self):
        i = self.tabs.currentIndex() - 1
        if i >= 0:
            self.tabs.setCurrentIndex(i)
    
    def close_panel(self, index=None):
        if not index:
            index = self.tabs.currentIndex()
        w = self.tabs.widget(index)
        if w and not w.keep_open:
            self.tabs.removeTab(index)

    def search(self, query, keep_open=False):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, search.SearchView) and w.q == query:
                self.tabs.setCurrentIndex(i)
                return

        p = search.SearchView(self, query, keep_open=keep_open)
        self.add_panel(p)

    def thread(self, thread_id):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, thread.ThreadView) and w.thread_id == thread_id:
                self.tabs.setCurrentIndex(i)
                return

        p = thread.ThreadView(self, thread_id)
        self.add_panel(p)

    def compose(self, reply_to=None, reply_to_all=True):
        p = compose.ComposeView(self, reply_to=reply_to, reply_to_all=reply_to_all)
        self.add_panel(p)

    def sync_mail(self, quiet=True):
        t = SyncMailThread(parent=self)

        def done():
            self.invalidate_panels()
            w = self.tabs.currentWidget()
            if w: w.refresh()
            if not quiet:
                title = self.main_window.windowTitle()
                self.main_window.setWindowTitle(title.replace(' [syncing]', ''))
            t.deleteLater()

        if not quiet:
            title = self.main_window.windowTitle()
            self.main_window.setWindowTitle(title + ' [syncing]')

        t.done.connect(done)
        t.start()


    def num_panels(self):
        return self.tabs.count()

    def invalidate_panels(self):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            w.dirty = True


