from PyQt5.QtWidgets import QApplication, QTabWidget

from . import search
from . import style
from . import thread

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        self.setApplicationName('Dodo')
        style.apply_style(self)
        self.tabs = QTabWidget()
        self.tabs.resize(1024, 768)
        inbox = search.SearchView(self, 'tag:inbox', keep_open=True)
        self.tabs.addTab(inbox, 'inbox')

        test = thread.ThreadView(self, '00000000000016a0')
        self.tabs.addTab(test, 'test')

        inbox.setFocus()
        self.tabs.show()

