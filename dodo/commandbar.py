from PyQt5.QtWidgets import *

from . import util
from . import keymap
from . import search
from . import thread

class CommandBar(QLineEdit):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mode = ''
        self.history = { 'search': [0, []], 'tag': [0, []] }

    def open(self, mode):
        self.mode = mode
        self.app.command_label.setText(mode)
        self.app.command_area.setVisible(True)
        self.setFocus()

    def close(self):
        if self.mode in self.history:
            h = self.history[self.mode]
            h[0] = len(h[1])

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

        if self.mode in self.history:
            self.history[self.mode][1].append(self.text())

        self.close()

    def history_previous(self):
        if self.mode in self.history:
            h = self.history[self.mode]
            if len(h[1]) != 0:
                i = max(h[0] - 1, 0)
                h[0] = i
                self.setText(h[1][i])

    def history_next(self):
        if self.mode in self.history:
            h = self.history[self.mode]
            if len(h[1]) != 0:
                i = min(h[0] + 1, len(h[1]) - 1)
                h[0] = i
                self.setText(h[1][i])


    def keyPressEvent(self, e):
        k = util.key_string(e)
        if k in keymap.command_bar_keymap:
            keymap.command_bar_keymap[k](self)
        else:
            super().keyPressEvent(e)
