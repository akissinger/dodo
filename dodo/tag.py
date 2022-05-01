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
from typing import Optional, Any, overload, Literal, List, Tuple

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QObject
from PyQt5.QtWidgets import QTreeView, QWidget
from PyQt5.QtGui import QFont, QColor
import subprocess
import json

from . import app
from . import settings
from . import keymap
from . import thread
from . import panel

columns = ['date', 'from', 'subject', 'tags']

class TagModel(QAbstractItemModel):
    """A model containing all tags"""

    def __init__(self) -> None:
        super().__init__()
        self.refresh()

    def refresh(self) -> None:
        """Refresh the model by (re-) running "notmuch search"."""
        self.beginResetModel()
        r = subprocess.run(['notmuch', 'search', '--output=tags', '*'],
                stdout=subprocess.PIPE)
        tag_str = r.stdout.decode('utf-8')

        self.d: List[Tuple[str,str,str]] = []

        for t in tag_str.splitlines():
            r1 = subprocess.run(['notmuch', 'count', '--output=threads', '--', 'tag:'+t],
                    stdout=subprocess.PIPE)
            c = r1.stdout.decode('utf-8').strip()
            r1 = subprocess.run(['notmuch', 'count', '--output=threads', '--', f'tag:{t} AND tag:unread'],
                    stdout=subprocess.PIPE)
            cu = r1.stdout.decode('utf-8').strip()
            self.d.append((t, cu, c))

        self.endResetModel()

    def num_tags(self) -> int:
        """The number of tags in the database"""

        return len(self.d)

    def tag(self, index: QModelIndex) -> Optional[str]:
        """Return the tag name at the given model index"""

        row = index.row()
        if row >= 0 and row < len(self.d):
            return self.d[row][0]
        else:
            return None

    def data(self, index: QModelIndex, role: int=Qt.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with tags"""

        row = index.row()
        col = index.column()
        if row >= len(self.d) or index.column() > 1:
            return None

        if role == Qt.DisplayRole:
            if col == 1:
                return f'[{self.d[row][1]}/{self.d[row][2]}]'
            else:
                return self.d[row][0]
        elif role == Qt.FontRole:
            font = QFont(settings.search_font, settings.search_font_size)
            if self.d[row][1] != '0':
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            if self.d[row][1] != '0':
                return QColor(settings.theme['fg_subject_unread'])
            else:
                return QColor(settings.theme['fg'])

    def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.headerData` to populate a view with column names"""

        if section == 0:
            return 'Tag'
        else:
            return '#'

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index: QModelIndex=QModelIndex()) -> int:
        """The number of columns"""

        return 2

    def rowCount(self, index: QModelIndex=QModelIndex()) -> int:
        """The number of rows

        This is essentially an alias for :func:`num_tags`, but it also returns 0 if an index is
        given to tell Qt not to add any child items."""

        if not index or not index.isValid(): return self.num_tags()
        else: return 0

    def parent(self, child: QModelIndex=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""

        if not child: return super().parent()
        else: return QModelIndex()

class TagPanel(panel.Panel):
    """A panel showing all tags"""

    def __init__(self, a: app.Dodo, keep_open: bool=False, parent: Optional[QWidget]=None):
        super().__init__(a, keep_open, parent)
        self.set_keymap(keymap.tag_keymap)
        self.tree = QTreeView()
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.setStyleSheet(f'QTreeView::item {{ padding: {settings.search_view_padding}px }}')
        self.model = TagModel()
        self.tree.setModel(self.model)
        self.layout().addWidget(self.tree)

        self.tree.resizeColumnToContents(0)
        # self.tree.setColumnWidth(1, 900)
        # self.tree.setColumnWidth(2, 900)

        self.tree.doubleClicked.connect(self.search_current_tag)
        if self.tree.model().rowCount() > 0:
            self.tree.setCurrentIndex(self.tree.model().index(0,0))

    def refresh(self) -> None:
        """Refresh the search listing and restore the selection, if possible."""

        current = self.tree.currentIndex()
        self.model.refresh()
        
        if current.row() >= self.model.num_tags():
            self.last_tag()
        else:
            self.tree.setCurrentIndex(current)

        super().refresh()

    def title(self) -> str:
        """Return constant 'tags'"""

        return 'tags'

    def next_tag(self) -> None:
        """Select the next tag
        """

        row = self.tree.currentIndex().row() + 1
        if row >= self.model.num_tags(): return
        ix = self.tree.model().index(row, 0)
        self.tree.setCurrentIndex(ix)

    def previous_tag(self, unread: bool=False) -> None:
        """Select the previous tag
        """

        row = self.tree.currentIndex().row() - 1
        if row < 0: return
        ix = self.tree.model().index(row, 0)
        self.tree.setCurrentIndex(ix)

    def first_tag(self) -> None:
        """Select the first tag"""

        ix = self.model.index(0, 0)
        if self.model.checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def last_tag(self) -> None:
        """Select the last tag"""

        ix = self.model.index(self.tree.model().rowCount()-1, 0)
        if self.model.checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def search_current_tag(self) -> None:
        """Open a new search panel for the selected tag"""

        tag = self.model.tag(self.tree.currentIndex())
        if tag:
            self.app.open_search('tag:' + tag)
    
    def toggle_thread_tag(self, tag: str) -> None:
        """Toggle the given thread tag"""

        thread = self.model.thread_json(self.tree.currentIndex())
        if thread:
            if tag in thread['tags']:
                tag_expr = '-' + tag
            else:
                tag_expr = '+' + tag
            self.tag_thread(tag_expr)






