from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QApplication, QTabWidget
import sys

from . import search
from . import thread
from . import compose
from . import settings
from . import themes

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        self.setApplicationName('Dodo')

        # find a load config.py
        self.config_file = QStandardPaths.locate(QStandardPaths.ConfigLocation, 'dodo/config.py')
        if self.config_file:
            exec(open(self.config_file).read())
        else:
            config_locs = QStandardPaths.standardLocations(QStandardPaths.ConfigLocation)
            print('No config.py found in:\n' + '\n'.join([f'  {d}/dodo' for d in config_locs]))
            sys.exit(1)

        # apply theme
        themes.apply_theme(self, settings.theme)

        # set up GUI
        self.tabs = QTabWidget()
        self.tabs.resize(1600, 800)

        def panel_focused(i):
            w = self.tabs.widget(i)
            if w:
                w.setFocus()
                w.refresh()

        self.tabs.currentChanged.connect(panel_focused)
        self.tabs.show()

        # open inbox and make un-closeable
        self.search('tag:inbox', keep_open=True)

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

    def search(self, query, keep_open=False):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, search.SearchView) and w.q == query:
                self.tabs.setCurrentIndex(i)
                return

        p = search.SearchView(self, query, keep_open=keep_open)
        self.add_panel(p)

    def open_thread(self, thread_id):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            if isinstance(w, thread.ThreadView) and w.thread_id == thread_id:
                self.tabs.setCurrentIndex(i)
                return

        p = thread.ThreadView(self, thread_id)
        self.add_panel(p)


    def compose(self, reply_to=None):
        p = compose.ComposeView(self, reply_to=reply_to)
        self.add_panel(p)

    def num_panels(self):
        return self.tabs.count()

