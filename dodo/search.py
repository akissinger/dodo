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
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QFont, QColor
import subprocess
import json

from . import settings
from . import keymap
from . import thread
from .panel import Panel

columns = ['date', 'from', 'subject', 'tags']

class SearchModel(QAbstractItemModel):
    """A model containing the results of a search"""

    def __init__(self, q):
        super().__init__()
        self.q = q
        self.refresh()

    def refresh(self):
        """Refresh the model by (re-) running "notmuch search"."""
        self.beginResetModel()
        r = subprocess.run(['notmuch', 'search', '--format=json', self.q],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)
        self.endResetModel()

    def num_threads(self):
        """The number of threads returned by the search"""

        return len(self.d)

    def thread_json(self, index):
        """Return a JSON object associated with the thread at the given model index"""

        row = index.row()
        if row >= 0 and row < len(self.d):
            return self.d[row]
        else:
            return None

    def thread_id(self, index):
        """Return the notmuch thread id associated with the thread at the given model index"""

        thread = self.thread_json(index)
        if thread and 'thread' in thread:
            return thread['thread']
        else:
            return None

    def data(self, index, role):
        """Overrides `QAbstractItemModel.data` to populate a view with search results"""

        global columns
        if index.row() >= len(self.d) or index.column() >= len(columns):
            return None

        thread_d = self.d[index.row()]
        col = columns[index.column()]

        if role == Qt.DisplayRole:
            if col == 'date':
                return thread_d['date_relative']
            elif col == 'from':
                return thread_d['authors']
            elif col == 'subject':
                return thread_d['subject']
            elif col == 'tags':
                return ' '.join([settings.tag_icons[t] if t in settings.tag_icons else f'[{t}]' for t in thread_d['tags']])
        elif role == Qt.FontRole:
            font = QFont(settings.search_font, settings.search_font_size)
            if 'unread' in thread_d['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            color = 'fg_' + col
            unread_color = 'fg_' + col + '_unread'
            if 'unread' in thread_d['tags'] and unread_color in settings.theme:
                return QColor(settings.theme[unread_color])
            elif color in settings.theme:
                return QColor(settings.theme[color])
            else:
                return QColor(settings.theme['fg'])

    def headerData(self, section, orientation, role):
        """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

        global columns
        if role == Qt.DisplayRole and section <= len(columns):
            return columns[section]
        else:
            return None

    def index(self, row, column, parent=QModelIndex()):
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index):
        """The number of columns"""

        global columns
        return len(columns)

    def rowCount(self, index=QModelIndex()):
        """The number of rows

        This is essentially an alias for :func:`num_threads`, but it also returns 0 if an index is
        given to tell Qt not to add any child items."""

        if not index or not index.isValid(): return self.num_threads()
        else: return 0

    def parent(self, index):
        """Always return an invalid index, since there are no nested indices"""

        return QModelIndex()


class SearchPanel(Panel):
    """A panel showing the results of a search

    This is used as the main entry point for the GUI, i.e. a search for "tag:inbox"."""

    def __init__(self, app, q, keep_open=False, parent=None):
        super().__init__(app, keep_open, parent)
        self.set_keymap(keymap.search_keymap)
        self.q = q
        self.tree = QTreeView()
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet(f'QTreeView::item {{ padding: {settings.search_view_padding}px }}')
        self.model = SearchModel(q)
        self.tree.setModel(self.model)
        self.layout().addWidget(self.tree)
        # TODO fix for custom columns
        self.tree.resizeColumnToContents(0)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 900)
        self.tree.doubleClicked.connect(self.open_current_thread)
        if self.tree.model().rowCount() > 0:
            self.tree.setCurrentIndex(self.tree.model().index(0,0))

    def refresh(self):
        """Refresh the search listing and restore the selection, if possible."""

        current = self.tree.currentIndex()
        self.model.refresh()
        
        if current.row() >= self.model.num_threads():
            self.last_thread()
        else:
            self.tree.setCurrentIndex(current)

        super().refresh()

    def title(self):
        """Give the query as the tab title"""

        return self.q

    def next_thread(self):
        """Select the next thread in the search"""

        row = self.tree.currentIndex().row() + 1
        if row >= 0 and row < self.tree.model().rowCount():
            self.tree.setCurrentIndex(self.tree.model().index(row, 0))

    def previous_thread(self):
        """Select the previous thread in the search"""

        row = self.tree.currentIndex().row() - 1
        if row >= 0 and row < self.tree.model().rowCount():
            self.tree.setCurrentIndex(self.tree.model().index(row, 0))

    def first_thread(self):
        """Select the first thread in the search"""

        ix = self.model.index(0, 0)
        if self.model.checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def last_thread(self):
        """Select the last thread in the search"""

        ix = self.model.index(self.tree.model().rowCount()-1, 0)
        if self.model.checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def open_current_thread(self):
        """Open the selected thread"""

        thread_id = self.model.thread_id(self.tree.currentIndex())
        if thread_id:
            self.app.open_thread(thread_id)
    
    def toggle_thread_tag(self, tag):
        """Toggle the given thread tag"""

        thread = self.model.thread_json(self.tree.currentIndex())
        if thread:
            if tag in thread['tags']:
                tag_expr = '-' + tag
            else:
                tag_expr = '+' + tag
            self.tag_thread(tag_expr)


    def tag_thread(self, tag_expr):
        """Apply the given tag expression to the selected thread

        A tag expression is a string consisting of one more statements of the form "+TAG"
        or "-TAG" to add or remove TAG, respectively, separated by whitespace."""

        thread_id = self.model.thread_id(self.tree.currentIndex())
        if not ('+' in tag_expr or '-' in tag_expr):
            tag_expr = '+' + tag_expr
        
        if thread_id:
            subprocess.run(['notmuch', 'tag'] + tag_expr.split() + ['--', 'thread:' + thread_id])
            self.app.invalidate_panels()
            self.refresh()



