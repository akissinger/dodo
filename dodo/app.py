from PyQt5.QtWidgets import QApplication, QTabWidget

from . import search
from . import style

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        self.setApplicationName('Dodo')
        style.apply_style(self)
        self.tabs = QTabWidget()
        self.tabs.resize(1024, 768)
        inbox = search.SearchView(self, 'tag:inbox', keep_open=True)
        self.add_panel(inbox)

        # inbox.setFocus()
        self.tabs.show()

    def add_panel(self, panel, focus=True):
        self.tabs.addTab(panel, panel.title())
        if focus:
            self.tabs.setCurrentWidget(panel)
        panel.setFocus()

