from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

from . import keymap
from . import util
from . import settings

class HelpWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.help_text = QTextBrowser()
        self.layout().addWidget(self.help_text)
        self.resize(400, 800)
        self.setWindowTitle('Dodo - Help')

        maps = [
            ("Global", keymap.global_keymap),
            ("Search view", keymap.search_keymap),
            ("Thread view", keymap.thread_keymap),
            ("Compose view", keymap.compose_keymap),
            ("Command bar", keymap.command_bar_keymap),
        ]

        s = ''

        for name, mp in maps:
            s += f'<h2>{name} key bindings</h2>\n'
            s += f'<table style="font-family: {settings.search_font}; font-size: {settings.search_font_size}pt">\n'
            for key,val in mp.items():
                if isinstance(val, tuple): desc = val[0]
                else: desc = '(no description)'
                s += f'<tr><td width="100" style="color: {settings.theme["fg_bright"]}">{util.simple_escape(key)}</td>\n'
                s += f'<td style="color: {settings.theme["fg"]}">{desc}</td></tr>\n'
            s += '</table><br />'

        s += '<br /><br />'

        self.help_text.setHtml(s)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(e)
