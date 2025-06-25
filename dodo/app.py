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
from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
import sys
import os
import subprocess
from typing import Optional, Literal
import logging

from . import search
from . import thread
from . import compose
from . import tag
from . import settings
from . import themes
from . import util
from . import keymap
from . import commandbar
from . import helpwindow
from . import panel
from . import mainwindow

LOCAL_PROTOCOLS = ['cid', 'message']

class SyncMailThread(QThread):
    """A QThread used for syncing local Maildir and notmuch with IMAP

    Called by the :func:`~dodo.app.Dodo.sync_mail` method."""

    def __init__(self, parent: QObject=None) -> None:
        super().__init__(parent)

    def run(self) -> None:
        """Run :func:`~dodo.settings.sync_mail_command` then `notmuch new`"""
        subprocess.run(settings.sync_mail_command, stdout=subprocess.PIPE, shell=True)
        subprocess.run(['notmuch', 'new'], stdout=subprocess.PIPE)


class Dodo(QApplication):
    """The main Dodo application

    There is always one instance of this class, and it contains methods for all of the global (i.e.
    not view-specific) commands. This includes running global opening/closing panels, opening the help
    window, and synchronizing mail with the IMAP server.
    """

    def __init__(self) -> None:
        super().__init__(sys.argv)
        if '--verbose' in sys.argv or '-v' in sys.argv:
            logging.basicConfig(level=logging.INFO)
        self.setApplicationName('Dodo')
        self.setDesktopFileName("dodo")

        # find a load config.py
        self.config_file = QStandardPaths.locate(QStandardPaths.StandardLocation.ConfigLocation, 'dodo/config.py')
        if self.config_file:
            exec(open(self.config_file).read())
        else:
            config_locs = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.ConfigLocation)
            print('No config.py found in:\n' + '\n'.join([f'  {d}/dodo' for d in config_locs]))
            sys.exit(1)

        # construct help window
        self.help_window = helpwindow.HelpWindow()

        # apply theme
        themes.apply_theme(settings.theme)

        # register custom URL schemes used by embedded HTML viewer
        for proto in LOCAL_PROTOCOLS:
            scheme = QWebEngineUrlScheme(proto.encode('utf-8'))
            scheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
            QWebEngineUrlScheme.registerScheme(scheme)

        # set up GUI
        self.panel_history = []
        self.main_window = mainwindow.MainWindow(self)
        self.tabs = self.main_window.tabs
        self.command_bar = self.main_window.command_bar
        self.lastWindowClosed.connect(self.quit)

        # set timer to sync email periodically
        if settings.sync_mail_interval != -1:
            self.sync_mail()
            timer = QTimer(self)
            timer.timeout.connect(self.sync_mail)
            timer.start(settings.sync_mail_interval * 1000)

        # open init_queries and make un-closeable
        #
        for query in settings.init_queries:
            self.open_search(query, keep_open=True)

    def show_help(self) -> None:
        """Show help window"""

        self.help_window.show()

    def raise_panel(self, p: panel.Panel) -> None:
        self.tabs.setCurrentWidget(p)
        self.main_window.activateWindow()
        # self.main_window.setWindowState(self.main_window.windowState() ^ Qt.WindowActive)

    def message(self, title, body) -> None:
        QMessageBox.warning(self.main_window, title, body)

    def add_panel(self, p: panel.Panel, focus: bool=True) -> None:
        """Add a panel to the tab view

        This method is used by the :func:`search`, :func:`thread`, and :func:`compose`
        methods to open new panels. In general, this method shouldn't be called directly
        from key mappings."""

        self.tabs.addTab(p, p.title())
        p.has_refreshed.connect(lambda: self.tabs.setTabText(self.tabs.indexOf(p), p.title()))

        if focus:
            self.tabs.setCurrentWidget(p)
            p.setFocus()

    def next_panel(self) -> None:
        """Go to the next panel"""

        i = self.tabs.currentIndex() + 1
        if i < self.tabs.count():
            self.tabs.setCurrentIndex(i)

    def previous_panel(self) -> None:
        """Go to the previous panel"""

        i = self.tabs.currentIndex() - 1
        if i >= 0:
            self.tabs.setCurrentIndex(i)

    def close_panel(self, index: Optional[int]=None) -> None:
        """Close the panel at `index` (if provided) or the current panel

        If `index` is not provided, close the current panel. This will only close
        panels whose `keep_open` property is False."""

        if not index:
            index = self.tabs.currentIndex()
        w = self.tabs.widget(index)
        if w and isinstance(w, panel.Panel) and not w.keep_open:
            if w.before_close():
                # remove this panel from the history
                if w in self.panel_history:
                    self.panel_history.remove(w)
                # focus the last focused panel
                if len(self.panel_history) > 0:
                    w0 = self.panel_history.pop()
                    self.tabs.setCurrentWidget(w0)
                # remove the panel itself
                self.tabs.removeTab(index)

    def open_search(self, query: str, keep_open: bool=False) -> None:
        """Open a search panel with the given query

        If a panel with this query is already open, switch to it rather than
        opening another copy."""
        if not query:
            return

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, search.SearchPanel) and w.q == query:
                self.tabs.setCurrentIndex(i)
                return

        p = search.SearchPanel(self, query, keep_open=keep_open)
        self.add_panel(p)

    def open_thread(self, thread_id: str, query: str) -> None:
        """Open a thread panel with the given thread_id

        If a panel with this thread_id is already open, switch to it rather than
        opening another copy."""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, thread.ThreadPanel) and w.thread_id == thread_id:
                self.tabs.setCurrentIndex(i)
                return

        p = thread.ThreadPanel(self, thread_id, query)
        self.add_panel(p)

    def open_compose(self, mode: str='', msg: Optional[dict]=None) -> None:
        """Open a compose panel

        If reply_to is provided, set populate the 'To' and 'In-Reply-To' headers
        appropriately, and quote the text in this message.

        :param msg: A JSON message referenced in a reply or forward
        :param mode: Composition mode. Possible values are '', 'reply', 'replyall',
                     and 'forward'
        """

        p = compose.ComposePanel(self, mode, msg)
        self.add_panel(p)

    def open_tags(self, keep_open: bool=False) -> None:
        """Open tag panel"""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, tag.TagPanel):
                w.keep_open = keep_open
                self.tabs.setCurrentIndex(i)
                return

        p = tag.TagPanel(self, keep_open)
        self.add_panel(p)

    def search_bar(self) -> None:
        """Open command bar for searching"""
        self.command_bar.open('search', callback=self.open_search)

    def tag_bar(self, mode: Literal['tag', 'tag marked']='tag') -> None:
        """Open command bar for tagging"""
        def callback(tag_expr: str) -> None:
            w = self.tabs.currentWidget()
            if w and isinstance(w, panel.Panel):
                if isinstance(w, search.SearchPanel): w.tag_thread(tag_expr, mode)
                elif isinstance(w, thread.ThreadPanel): w.tag_message(tag_expr)
                w.refresh()
        self.command_bar.open(mode, callback)

    def sync_mail(self, quiet: bool=True) -> None:
        """Sync mail with IMAP server

        This method runs :func:`~dodo.settings.sync_mail_command`, then 'notmuch new'

        :param quiet: If this is True, do not give any visual cues that email is being synced.
                      This is less distracting if this is a periodic sync, rather than a
                      manual sync by the user."""

        t = SyncMailThread(parent=self)

        def done() -> None:
            self.refresh_panels()
            if not quiet:
                title = self.main_window.windowTitle()
                self.main_window.setWindowTitle(title.replace(' [syncing]', ''))
                self.main_window.update()
            t.deleteLater()

        if not quiet:
            title = self.main_window.windowTitle()
            self.main_window.setWindowTitle(title + ' [syncing]')
            self.main_window.update()

        t.finished.connect(done)
        t.start()

    def num_panels(self) -> int:
        """Returns the number of panels (i.e. tabs) currently open"""

        return self.tabs.count()

    def refresh_panels(self) -> None:
        """Refresh current panel and mark the others as out of date

        This method gets called whenever tags have been changed or a new message has
        been sent. The refresh will happen the next time a panel is switched to."""

        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, panel.Panel):
                w.dirty = True

        w = self.tabs.currentWidget()
        if w and isinstance(w, panel.Panel): w.refresh()

    def update_single_thread(self, thread_id: str, msg_id: str|None=None):
        current = self.tabs.currentWidget()
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, panel.Panel):
                w.update_thread(thread_id, msg_id=msg_id)
                if w == current and w.dirty:
                    w.refresh()

    def prompt_quit(self) -> None:
        """A 'soft' quit function, which gives each open tab the opportunity to prompt
        the user and possible cancel closing."""
        self.main_window.close()


def main() -> None:
    """Main entry point for Dodo"""

    dodo = Dodo()
    dodo.exec()
