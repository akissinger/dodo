from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt5.QtGui import QFont, QColor
import subprocess
import json

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
        if index.row() < 0 and index.row() >= len(self.d):
            return ""

        thread = self.d[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return thread['date_relative']
            elif col == 1:
                return thread['authors']
            elif col == 2:
                return thread ['subject']
            else:
                return ' '.join(thread['tags'])
        elif role == Qt.FontRole:
            font = QFont("Fira Code", 12)
            if 'unread' in thread['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            if 'unread' in thread['tags'] and col == 2:
                return QColor('#b48ead')
            else:
                return QColor('#d8dee9')

        else:
            return None

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if section == 0: return 'date'
            elif section == 1: return 'from'
            elif section == 2: return 'subject'
            else: return 'tags'
        else:
            return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index):
        return 4

    def rowCount(self, index):
        if not index.isValid(): return len(self.d)
        else: return 0

    def parent(self, index):
        return QModelIndex()
