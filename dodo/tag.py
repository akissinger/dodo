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

from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex, QObject
from PyQt6.QtWidgets import QTreeView, QWidget
from PyQt6.QtGui import QFont, QColor
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

    def refresh(self, filter_tags: List[str]=None) -> None:
        """Refresh the model by (re-) running "notmuch search"."""
        self.beginResetModel()
        tag_query = ' AND '.join([f'tag:"{tag}"' for tag in filter_tags]) if filter_tags else ''
        search_args = [tag_query] if tag_query else ['*']
        cmd = ['notmuch', 'search', '--output=tags'] + search_args
        r = subprocess.run(cmd, stdout=subprocess.PIPE)
        tag_str = r.stdout.decode('utf-8')

        self.d: List[Tuple[str,str,str]] = []

        for t in tag_str.splitlines():
            if filter_tags and t in filter_tags:
                continue
            extra_query = (' AND ' + tag_query) if tag_query else ''
            cmd = ['notmuch', 'count', '--output=threads', '--', f'tag:"{t}"' + extra_query]
            r1 = subprocess.run(cmd, stdout=subprocess.PIPE)
            c = r1.stdout.decode('utf-8').strip()
            cmd = ['notmuch', 'count', '--output=threads', '--', f'tag:"{t}" AND tag:unread' + extra_query]
            r1 = subprocess.run(cmd, stdout=subprocess.PIPE)
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

    def data(self, index: QModelIndex, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a view with tags"""

        row = index.row()
        col = index.column()
        if row >= len(self.d) or index.column() > 1:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 1:
                return f'[{self.d[row][1]}/{self.d[row][2]}]'
            else:
                return self.d[row][0]
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont(settings.search_font, settings.search_font_size)
            if self.d[row][1] != '0':
                font.setBold(True)
            return font
        elif role == Qt.ItemDataRole.ForegroundRole:
            if self.d[row][1] != '0':
                return QColor(settings.theme['fg_subject_unread'])
            else:
                return QColor(settings.theme['fg'])

    def headerData(self, section: int, orientation: Qt.Orientation, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
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

    def __init__(self, a: app.Dodo, keep_open: bool=False, filter_tags: List[str]=None, parent: Optional[QWidget]=None):
        super().__init__(a, keep_open, parent)
        self.set_keymap(keymap.tag_keymap)
        self.tree = QTreeView()
        self.tree.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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

        self.filter_tags = filter_tags or []
        self.last_tag_row = []
        self.try_narrowing = False

    def refresh(self) -> None:
        """Refresh the search listing and restore the selection, if possible."""

        current = self.tree.currentIndex()
        self.model.refresh(self.filter_tags)
        
        if self.try_narrowing:
            self.try_narrowing = False
            # If we're narrowing and the result is zero tags, don't do the narrow and revert to previous state
            if self.model.num_tags() == 0:
                last_tag = self.filter_tags.pop()
                last_row = self.last_tag_row.pop()
                self.model.refresh(self.filter_tags)
                self.select_tag_or_nearby_row(last_tag, last_row)

                # also may be sensible to open the search after narrowing as far as possible
                self.search_current_tag()
                return

        if current.row() >= self.model.num_tags():
            self.last_tag()
        else:
            self.tree.setCurrentIndex(current)

        self.app.refresh_title()
        super().refresh()

    def title(self) -> str:
        """Return constant 'tags' and the list of narrowed tags"""
        t = 'tags'
        for tag in self.filter_tags:
            t += ' > ' + tag
        return t

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
        tags = [tag] + self.filter_tags
        tag_query = ' AND '.join([f'tag:"{tag}"' for tag in tags])
        if tags:
            self.app.open_search(tag_query)
    
    def search_current_view(self) -> None:
        """Opens a new search panel for the current narrowed view, not including current selection"""
        tags = self.filter_tags
        tag_query = ' AND '.join([f'tag:"{tag}"' for tag in tags])
        if tags:
            self.app.open_search(tag_query)
        else:
            self.app.open_search("*")

    def narrow_current_tag(self) -> None:
        """Refresh the view narrowing to the selected tag"""

        ix = self.tree.currentIndex()
        tag = self.model.tag(ix)
        if tag:
            self.filter_tags.append(tag)
            self.last_tag_row.append(ix.row())
            self.try_narrowing = True
            self.refresh()
    
    def open_current_tag(self) -> None:
        """Open a new tag panel narrowing to the selected tag"""
        ix = self.tree.currentIndex()
        tag = self.model.tag(ix)
        if tag:
            self.app.open_tags_narrowed(filter_tags=[tag] + self.filter_tags)
    
    def undo_narrow_tag(self) -> None:
        if self.filter_tags:
            last_tag = self.filter_tags.pop()
            last_row = self.last_tag_row.pop()
            self.refresh()
            self.select_tag_or_nearby_row(last_tag, last_row)

    def select_tag_or_nearby_row(self, last_tag, last_row):
        # select row if it matches the tag
        row = min((last_row, self.model.num_tags() - 1))
        ix = self.tree.model().index(row, 0)
        if self.model.tag(ix) == last_tag:
            self.tree.setCurrentIndex(ix)
            return

        # else index changed so find the matching tag
        for row in range(self.model.num_tags()):
            ix = self.tree.model().index(row, 0)
            if self.model.tag(ix) == last_tag:
                self.tree.setCurrentIndex(ix)
                return
        
        # else go back to the nearest index
        row = min((last_row, self.model.num_tags() - 1))
        ix = self.tree.model().index(row, 0)
        self.tree.setCurrentIndex(ix)

