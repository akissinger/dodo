from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

from . import search
from . import thread
from . import compose
from . import settings
from . import themes
from . import util
from . import keymap

class CommandBar(QLineEdit):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mode = ''

    def open(self, mode):
        self.mode = mode
        self.app.command_label.setText(mode)
        self.app.command_area.setVisible(True)
        self.setFocus()

    def close(self):
        self.setText('')
        self.app.command_area.setVisible(False)
        w = self.app.tabs.currentWidget()
        if w: w.setFocus()

    def accept(self):
        if self.mode == 'search':
            self.app.search(self.text())
        elif self.mode == 'tag':
            w = self.app.tabs.currentWidget()
            if w:
                if isinstance(w, search.SearchView): w.tag_thread(self.text())
                elif isinstance(w, thread.ThreadView): w.tag_message(self.text())
                w.refresh()

        self.close()

    def keyPressEvent(self, e):
        k = util.key_string(e)
        if k in keymap.command_bar_keymap:
            keymap.command_bar_keymap[k](self)
        else:
            super().keyPressEvent(e)

class Dodo(QApplication):
    def __init__(self):
        super().__init__([])
        conf = QSettings('dodo', 'dodo')
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
        self.main_window = QWidget()
        self.main_window.setWindowIcon(QIcon('icons/dodo.svg'))
        self.main_window.setWindowTitle("Dodo")
        self.main_window.setLayout(QVBoxLayout())
        self.main_window.layout().setContentsMargins(0,0,0,0)
        self.main_window.resize(1600, 800)
        
        geom = conf.value("main_window_geometry")
        if geom: self.main_window.restoreGeometry(geom)
        self.aboutToQuit.connect(lambda:
                conf.setValue("main_window_geometry", self.main_window.saveGeometry()))

        self.tabs = QTabWidget()
        self.tabs.setFocusPolicy(Qt.NoFocus)
        # self.tabs.resize(1600, 800)
        self.main_window.layout().addWidget(self.tabs)

        def panel_focused(i):
            w = self.tabs.widget(i)
            if w:
                w.setFocus()
                if w.dirty: w.refresh()

        self.tabs.currentChanged.connect(panel_focused)
        self.main_window.show()

        self.command_label = QLabel("search")
        self.command_bar = CommandBar(self)
        self.command_bar.setFocusPolicy(Qt.NoFocus)

        self.command_area = QWidget()
        self.command_area.setLayout(QHBoxLayout())
        self.main_window.layout().setContentsMargins(0,0,0,0)
        self.main_window.layout().setSpacing(0)

        self.command_area.layout().addWidget(self.command_label)
        self.command_area.layout().addWidget(self.command_bar)
        self.main_window.layout().addWidget(self.command_area)

        self.command_area.setVisible(False)

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

    def thread(self, thread_id):
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

    def invalidate_panels(self):
        for i in range(self.num_panels()):
            w = self.tabs.widget(i)
            w.dirty = True


