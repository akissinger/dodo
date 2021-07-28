from PyQt5.QtWidgets import QApplication

from . import search
from . import style

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        self.setApplicationName('Dodo')
        style.apply_style(self)
        self.inbox = search.SearchView(self, 'tag:inbox')
        self.inbox.resize(1024, 768)
        self.inbox.show()

