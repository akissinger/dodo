# from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

import subprocess
import json
import html
import bleach
import html2text

from . import style
from . import util
from . import keymap
from .basewidgets import StackingTextView, Panel

# recursively search a message body for content of type `ty` and return in depth-first
# order
def find_content(m, ty):
    content = []

    def dfs(x):
        if isinstance(x, list):
            for y in x: dfs(y)
        elif isinstance(x, dict) and 'content-type' in x and 'content' in x:
            if x['content-type'] == ty:
                content.append(x['content'])
            elif isinstance(x['content'], list):
                for y in x['content']: dfs(y)

    dfs(m)
    return content

def flat_thread(d):
    thread = []

    def dfs(x):
        if isinstance(x, list):
            for y in x:
                dfs(y)
        else: thread.append(x)

    dfs(d)
    thread.sort(key=lambda m: m['timestamp'])
    return thread

class ThreadModel(QAbstractItemModel):
    def __init__(self, thread_id):
        self.thread_id = thread_id
        self.refresh()
        super().__init__()

    def refresh(self):
        r = subprocess.run(['notmuch', 'show', '--format=json', '--include-html', self.thread_id],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)

        # store a flattened version of the thread
        self.thread = flat_thread(self.d)

    def data(self, index, role):
        if index.row() >= len(self.thread):
            return None

        m = self.thread[index.row()]

        if role == Qt.DisplayRole:
            if 'headers' in m and 'From' in m["headers"]:
                return m['headers']['From']
            else:
                return '(message)'
        elif role == Qt.FontRole:
            font = QFont(style.search_font, style.search_font_size)
            if 'tags' in m and 'unread' in m['tags']:
                font.setBold(True)
            return font

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index):
        return 1

    def rowCount(self, index=QModelIndex()):
        if not index or not index.isValid(): return self.num_messages()
        else: return 0

    def parent(self, index):
        return QModelIndex()

    def message_at(self, row):
        if row >= 0 and row < len(self.thread):
            return self.thread[row]
        else:
            return None

    def num_messages(self):
        return len(self.thread)

class ThreadView(Panel):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.thread_keymap)
        self.model = ThreadModel(thread_id)

        self.subject = '(no subject)'
        self.current_message = -1

        self.splitter = QSplitter(Qt.Vertical)
        info_area = QWidget()
        info_area.setLayout(QHBoxLayout())

        self.thread_list = QListView()
        self.thread_list.setFocusPolicy(Qt.NoFocus)
        self.thread_list.setModel(self.model)
        self.thread_list.setFixedWidth(200)
        self.thread_list.clicked.connect(lambda ix: self.show_message(ix.row()))

        self.message_info = QTextBrowser()
        info_area.layout().addWidget(self.thread_list)
        info_area.layout().addWidget(self.message_info)
        self.splitter.addWidget(info_area)

        self.message_view = QWebEngineView()
        settings = self.message_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
        self.splitter.addWidget(self.message_view)

        self.layout().addWidget(self.splitter)
        self.show_message(0)

    def title(self):
        return util.chop_s(self.subject)


    def show_message(self, i=-1):
        if i != -1: self.current_message = i
        print("message: %s" % self.current_message)

        if self.current_message >= 0 and self.current_message < self.model.num_messages():
            ix = self.thread_list.model().index(self.current_message, 0)
            if self.thread_list.model().checkIndex(ix):
                self.thread_list.setCurrentIndex(ix)

            m = self.model.message_at(self.current_message)
            if 'headers' in m and 'Subject' in m['headers']:
                self.subject = m['headers']['Subject']
            else:
                self.subject = '(no subject)'

            if 'headers' in m:
                header_html = ''
                header_html += f'<table style="background-color: {style.theme["bg"]}; color: {style.theme["fg"]}; width:100%">'
                for name in ['From', 'To', 'Subject', 'Date']:
                    if name in m['headers']:
                        header_html += '<tr><td><b style="color: %s">%s:&nbsp;</b></td><td>%s</td></tr>' % (
                          style.theme['fg_bright'], name, util.simple_escape(m['headers'][name]))
                header_html += '</table>'
                self.message_info.setHtml(header_html)

            if 'body' in m:
                tc = find_content(m['body'], 'text/plain')
                hc = find_content(m['body'], 'text/html')
                text = None
                html = None

                if len(tc) != 0:
                    text = tc[0]
                elif len(hc) != 0:
                    c = html2text.HTML2Text()
                    c.ignore_emphasis = True
                    c.ignore_links = True
                    c.images_to_alt = True
                    text = c.handle(hc[0])
                    html = hc[0]

                if text:
                    self.message_view.setHtml("""<html>
                    <head>
                    <style type="text/css">
                        body { background-color: %s; color: %s }
                        a { color: %s }
                    </style>
                    </head>
                    <body>
                    <pre style="white-space: pre-wrap; font-size: %dpt; font-family: %s">%s</pre>
                    </body>
                    </html>
                    """ % (
                        style.theme["bg"],
                        style.theme["fg"],
                        style.theme["fg_bright"],
                        style.message_font_size,
                        style.message_font,
                        text,
                    ))


    def next_message(self):
        self.show_message(min(self.current_message + 1, self.model.num_messages() - 1))

    def previous_message(self):
        self.show_message(max(self.current_message - 1, 0))

