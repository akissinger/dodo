from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QFont, QColor
import subprocess
import json

from . import style
from . import keymap
from . import thread
from .basewidgets import Panel

columns = ['date', 'from', 'subject', 'tags']

class SearchModel(QAbstractItemModel):
    def __init__(self, q):
        self.q = q
        self.refresh()
        super().__init__()

    def refresh(self):
        r = subprocess.run(['notmuch', 'search', '--format=json', self.q],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)

    def data(self, index, role):
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
                return ' '.join(thread_d['tags'])
        elif role == Qt.FontRole:
            font = QFont(style.search_font, style.search_font_size)
            if 'unread' in thread_d['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            color = 'fg_' + col
            unread_color = 'fg_' + col + '_unread'
            if 'unread' in thread_d['tags'] and unread_color in style.theme:
                return QColor(style.theme[unread_color])
            elif color in style.theme:
                return QColor(style.theme[color])
            else:
                return QColor(style.theme['fg'])

    def headerData(self, section, orientation, role):
        global columns
        if role == Qt.DisplayRole and section <= len(columns):
            return columns[section]
        else:
            return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index):
        global columns
        return len(columns)

    def rowCount(self, index=QModelIndex()):
        if not index or not index.isValid(): return len(self.d)
        else: return 0

    def parent(self, index):
        return QModelIndex()

    def thread_id_at(self, index):
        row = index.row()
        if row >= 0 and row < len(self.d):
            return self.d[row]['thread']
        else:
            return None


class SearchView(Panel):
    def __init__(self, app, q, keep_open=False, parent=None):
        super().__init__(app, keep_open, parent)
        self.set_keymap(keymap.search_keymap)
        self.q = q
        self.tree = QTreeView()
        self.tree.setFocusPolicy(Qt.NoFocus)
        self.layout().addWidget(self.tree)
        self.tree.setModel(SearchModel(q))
        # TODO fix for custom cols
        self.tree.resizeColumnToContents(0)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 600)
        self.tree.doubleClicked.connect(self.open_current_thread)
        if self.tree.model().rowCount() > 0:
            self.tree.setCurrentIndex(self.tree.model().index(0,0))

    def title(self):
        return self.q

    def next_thread(self):
        row = self.tree.currentIndex().row() + 1
        if row >= 0 and row < self.tree.model().rowCount():
            self.tree.setCurrentIndex(self.tree.model().index(row, 0))

    def previous_thread(self):
        row = self.tree.currentIndex().row() - 1
        if row >= 0 and row < self.tree.model().rowCount():
            self.tree.setCurrentIndex(self.tree.model().index(row, 0))

    def first_thread(self):
        ix = self.tree.model().index(0, 0)
        if self.tree.model().checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def last_thread(self):
        ix = self.tree.model().index(self.tree.model().rowCount()-1, 0)
        if self.tree.model().checkIndex(ix):
            self.tree.setCurrentIndex(ix)

    def open_current_thread(self):
        thread_id = self.tree.model().thread_id_at(self.tree.currentIndex())
        if thread_id:
            self.app.add_panel(thread.ThreadView(self.app, thread_id))

