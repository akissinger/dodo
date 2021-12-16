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

        def fix_focus(i):
            w = self.tabs.widget(i)
            if w: w.setFocus()

        self.tabs.currentChanged.connect(fix_focus)

        inbox = search.SearchView(self, 'tag:inbox', keep_open=True)
        self.add_panel(inbox)
        self.tabs.show()

    def add_panel(self, panel, focus=True):
        self.tabs.addTab(panel, panel.title())
        if focus:
            self.tabs.setCurrentWidget(panel)
        panel.setFocus()

    def next_panel(self):
        i = self.tabs.currentIndex() + 1
        if i < self.tabs.count():
            self.tabs.setCurrentIndex(i)

    def previous_panel(self):
        i = self.tabs.currentIndex() - 1
        if i >= 0:
            self.tabs.setCurrentIndex(i)
    
    def close_panel(self, index=None):
        if not index:
            index = self.tabs.currentIndex()
        w = self.tabs.widget(index)
        if w and not w.keep_open:
            self.tabs.removeTab(index)

    def num_panels(self):
        return self.tabs.count()

