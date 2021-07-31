from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget, QTextBrowser, QSizePolicy, QVBoxLayout

from . import keymap
from . import util

class StackingTextView(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont('Fira Code', 12))
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum);
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);

    def sizeHint(self):
        return self.document().size().toSize()

    def resizeEvent(self, e):
        self.updateGeometry()
        super().resizeEvent(e)

class Panel(QWidget):
    def __init__(self, app, keep_open=False, parent=None):
        super().__init__(parent)
        self.app = app
        self.keep_open = keep_open
        self.keymap = None
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

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

    def title(self):
        return 'view'

    def set_keymap(self, mp):
        self.keymap = mp

    def prefix_timeout(self):
        # print("prefix fired: " + self._prefix)
        if self.keymap and self._prefix in self.keymap:
            self.keymap[self._prefix](self)
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
        elif self.keymap and cmd in self.keymap:
            self._prefix = ""
            self.keymap[cmd](self)
        elif cmd in keymap.global_keymap:
            self._prefix = ""
            keymap.global_keymap[cmd](self.app)
