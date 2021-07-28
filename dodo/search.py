from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex, QTimer
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtGui import QFont, QColor
import subprocess
import json

from . import style
from . import keymap
from . import util

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

        thread = self.d[index.row()]
        col = columns[index.column()]

        if role == Qt.DisplayRole:
            if col == 'date':
                return thread['date_relative']
            elif col == 'from':
                return thread['authors']
            elif col == 'subject':
                return thread['subject']
            elif col == 'tags':
                return ' '.join(thread['tags'])
        elif role == Qt.FontRole:
            font = QFont("Fira Code", 12)
            if 'unread' in thread['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            color = 'fg_' + col
            unread_color = 'fg_' + col + '_unread'
            if 'unread' in thread['tags'] and unread_color in style.theme:
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
        return 4

    def rowCount(self, index=QModelIndex()):
        if not index or not index.isValid(): return len(self.d)
        else: return 0

    def parent(self, index):
        return QModelIndex()


class SearchView(QTreeView):
    def __init__(self, app, q, keep_open=False, parent=None):
        super().__init__(parent)
        self.app = app
        self.keep_open = keep_open
        self.setModel(SearchModel(q))
        # TODO fix for custom cols
        self.resizeColumnToContents(0)
        self.setColumnWidth(1, 150)
        self.setColumnWidth(2, 600)
        if self.model().rowCount() > 0:
            self.setCurrentIndex(self.model().index(0,0))

        # set up timer and prefix cache for handling keychords
        self._prefix = ""
        self._prefixes = set()
        self._prefix_timer = QTimer()
        self._prefix_timer.setSingleShot(True)
        self._prefix_timer.setInterval(500)
        self._prefix_timer.timeout.connect(self.prefix_timeout)
        for k in keymap.search_keymap:
            for i in range(1,len(k)):
                self._prefixes.add(k[0:-i])

    def prefix_timeout(self):
        # print("prefix fired: " + self._prefix)
        if self._prefix in keymap.search_keymap:
            keymap.search_keymap[self._prefix](self)
        elif self._prefix in keymap.global_keymap:
            keymap.global_keymap[self._prefix](self.app)
        self._prefix = ""

    def keyPressEvent(self, e):
        k = util.key_string(e)
        if not k: return None
        # print("key: " + util.key_string(e))
        cmd = self._prefix + " " + k if self._prefix != "" else k
        self._prefix_timer.stop()

        if cmd in self._prefixes:
            self._prefix = cmd
            self._prefix_timer.start()
        elif cmd in keymap.search_keymap:
            self._prefix = ""
            keymap.search_keymap[cmd](self)
        elif cmd in keymap.global_keymap:
            self._prefix = ""
            keymap.global_keymap[cmd](self.app)

    def next_thread(self):
        row = self.currentIndex().row() + 1
        if row >= 0 and row < self.model().rowCount():
            self.setCurrentIndex(self.model().index(row, 0))

    def previous_thread(self):
        row = self.currentIndex().row() - 1
        if row >= 0 and row < self.model().rowCount():
            self.setCurrentIndex(self.model().index(row, 0))

    def first_thread(self):
        ix = self.model().index(0, 0)
        if self.model().checkIndex(ix):
            self.setCurrentIndex(ix)

    def last_thread(self):
        ix = self.model().index(self.model().rowCount()-1, 0)
        if self.model().checkIndex(ix):
            self.setCurrentIndex(ix)

