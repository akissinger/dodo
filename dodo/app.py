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
from PyQt5.QtWebEngineCore import QWebEngineUrlScheme
import sys
import os
import subprocess

from . import search
from . import thread
from . import compose
from . import settings
from . import themes
from . import util
from . import keymap
from . import commandbar
from . import helpwindow
from . import panel

class SyncMailThread(QThread):
    """A QThread used for syncing local Maildir and notmuch with IMAP

    Called by the :func:`~dodo.app.Dodo.sync_mail` method."""

    def __init__(self, parent: QObject=None):
        super().__init__(parent)

    def run(self):
        """Run :func:`~dodo.settings.sync_mail_command` then `notmuch new`"""
        subprocess.run(settings.sync_mail_command, stdout=subprocess.PIPE, shell=True)
        subprocess.run(['notmuch', 'new'], stdout=subprocess.PIPE)

class Dodo(QApplication):
    """The main Dodo application

    There is always one instance of this class, and it contains methods for all of the global (i.e.
    not view-specific) commands. This includes running global opening/closing panels, opening the help
    window, and synchronizing mail with the IMAP server.
    """

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
        self.help_window = helpwindow.HelpWindow()

        # apply theme
        themes.apply_theme(self, settings.theme)

        # register URL scheme used by embedded images in HTML
        scheme = QWebEngineUrlScheme(b'cid')
        scheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
        QWebEngineUrlScheme.registerScheme(scheme)

        # set up GUI
        self.main_window = QWidget()

        icon = os.path.dirname(__file__) + '/dodo.svg'
        if os.path.exists(icon):
            self.main_window.setWindowIcon(QIcon(icon))
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
        """Show help window"""

        self.help_window.show()

    def raise_panel(self, p: panel.Panel):
        self.tabs.setCurrentWidget(p)
        self.main_window.setWindowState(self.main_window.windowState() ^ Qt.WindowActive)

    def add_panel(self, p: panel.Panel, focus=True):
        """Add a panel to the tab view

        This method is used by the :func:`search`, :func:`thread`, and :func:`compose`
        methods to open new panels. In general, this method shouldn't be called directly
        from key mappings."""

        self.tabs.addTab(p, p.title())
        if focus:
            self.tabs.setCurrentWidget(p)
        p.setFocus()

    def next_panel(self):
        """Go to the next panel"""

        i = self.tabs.currentIndex() + 1
        if i < self.tabs.count():
            self.tabs.setCurrentIndex(i)

    def previous_panel(self):
        """Go to the previous panel"""

        i = self.tabs.currentIndex() - 1
        if i >= 0:
            self.tabs.setCurrentIndex(i)
    
    def close_panel(self, index=None):
        """Close the panel at `index` (if provided) or the current panel

        If `index` is not provided, close the current panel. This will only close
        panels whose `keep_open` property is False."""

        if not index:
            index = self.tabs.currentIndex()
        w = self.tabs.widget(index)
        if w and not w.keep_open:
            if w.before_close():
                self.tabs.removeTab(index)

    def search(self, query, keep_open=False):
        """Open a search panel with the given query

        If a panel with this query is already open, switch to it rather than
        opening another copy."""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, search.SearchPanel) and w.q == query:
                self.tabs.setCurrentIndex(i)
                return

        p = search.SearchPanel(self, query, keep_open=keep_open)
        self.add_panel(p)

    def thread(self, thread_id):
        """Open a thread panel with the given thread_id

        If a panel with this thread_id is already open, switch to it rather than
        opening another copy."""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, thread.ThreadPanel) and w.thread_id == thread_id:
                self.tabs.setCurrentIndex(i)
                return

        p = thread.ThreadPanel(self, thread_id)
        self.add_panel(p)

    def compose(self, mode='', msg=None):
        """Open a compose panel

        If reply_to is provided, set populate the 'To' and 'In-Reply-To' headers
        appropriately, and quote the text in this message.

        :param msg: A JSON message referenced in a reply or forward
        :param mode: Composition mode. Possible values are '', 'reply', 'replyall',
                     and 'forward'
        """

        p = compose.ComposePanel(self, mode, msg)
        self.add_panel(p)

    def sync_mail(self, quiet=True):
        """Sync mail with IMAP server

        This method runs :func:`~dodo.settings.sync_mail_command`, then 'notmuch new'

        :param quiet: If this is True, do not give any visual cues that email is being synced.
                      This is less distracting if this is a periodic sync, rather than a
                      manual sync by the user."""

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

        t.finished.connect(done)
        t.start()


    def num_panels(self):
        """Returns the number of panels (i.e. tabs) currently open"""

        return self.tabs.count()

    def invalidate_panels(self):
        """Mark all panels as out of date

        This method gets called whenever tags have been changed or a new message has
        been sent. The refresh will happen the next time a panel is switched to."""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            w.dirty = True

    def quit(self):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if not w.before_close(): return
        super().quit()


def main():
    """Main entry point for Dodo"""

    dodo = Dodo()
    dodo.exec_()
