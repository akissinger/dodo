from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

import subprocess
import json
import html
from lxml.html.clean import Cleaner
import html2text

from . import settings
from . import util
from . import keymap
from .panel import Panel


def flat_thread(d):
    "Return the thread as a flattened list of messages, sorted by date."

    thread = []
    def dfs(x):
        if isinstance(x, list):
            for y in x:
                dfs(y)
        else: thread.append(x)

    dfs(d)
    thread.sort(key=lambda m: m['timestamp'])
    return thread

def short_string(m):
    "Return a short string describing the current message."
    if 'headers' in m and 'From' in m['headers']:
        return m['headers']['From']

class ThreadModel(QAbstractItemModel):
    def __init__(self, thread_id):
        super().__init__()
        self.thread_id = thread_id
        self.refresh()

    def refresh(self):
        r = subprocess.run(['notmuch', 'show', '--format=json', '--include-html', self.thread_id],
                stdout=subprocess.PIPE, encoding='utf8')
        self.json_str = r.stdout
        self.d = json.loads(self.json_str)
        self.beginResetModel()
        self.thread = flat_thread(self.d)
        self.endResetModel()

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
            font = QFont(settings.search_font, settings.search_font_size)
            if 'tags' in m and 'unread' in m['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ForegroundRole:
            if 'tags' in m and 'unread' in m['tags']:
                return QColor(settings.theme['fg_subject_unread'])
            else:
                return QColor(settings.theme['fg'])

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

    def message_at(self, i):
        return self.thread[i]

    def default_message(self):
        """Return the index of either the oldest unread message or the last message
        in the thread."""

        for i, m in enumerate(self.thread):
            if 'tags' in m and 'unread' in m['tags']:
                return i

        return self.num_messages() - 1

    def num_messages(self):
        return len(self.thread)

class ThreadView(Panel):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(app, parent)
        window_settings = QSettings("dodo", "dodo")
        self.set_keymap(keymap.thread_keymap)
        self.model = ThreadModel(thread_id)
        self.thread_id = thread_id
        self.html_mode = settings.default_to_html

        self.subject = '(no subject)'
        self.current_message = -1

        self.splitter = QSplitter(Qt.Vertical)
        info_area = QWidget()
        info_area.setLayout(QHBoxLayout())

        self.thread_list = QListView()
        self.thread_list.setFocusPolicy(Qt.NoFocus)
        self.thread_list.setModel(self.model)
        self.thread_list.setFixedWidth(250)
        self.thread_list.clicked.connect(lambda ix: self.show_message(ix.row()))

        self.message_info = QTextBrowser()
        info_area.layout().addWidget(self.thread_list)
        info_area.layout().addWidget(self.message_info)
        self.splitter.addWidget(info_area)

        self.message_view = QWebEngineView()
        self.message_view.setZoomFactor(1.2)
        self.message_view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
        self.splitter.addWidget(self.message_view)

        self.layout().addWidget(self.splitter)
        state = window_settings.value("thread_splitter_state")
        self.splitter.splitterMoved.connect(
                lambda x: window_settings.setValue("thread_splitter_state", self.splitter.saveState()))
        if state: self.splitter.restoreState(state)

        self.show_message(self.model.default_message())


    def title(self):
        return util.chop_s(self.subject)

    def refresh(self):
        self.model.refresh()
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
            header_html += f'<table style="background-color: {settings.theme["bg"]}; color: {settings.theme["fg"]}; font-family: Fira Code; font-size: 14pt; width:100%">'
            for name in ['From', 'To', 'Subject', 'Date']:
                if name in m['headers']:
                    header_html += f"""<tr>
                      <td><b style="color: {settings.theme["fg_bright"]}">{name}:&nbsp;</b></td>
                      <td>{util.simple_escape(m["headers"][name])}</td>
                    </tr>"""
            if 'tags' in m:
                tags = ' '.join([settings.tag_icons[t] if t in settings.tag_icons else f'[{t}]' for t in m['tags']])
                header_html += f"""<tr>
                  <td><b style="color: {settings.theme["fg_bright"]}">Tags:&nbsp;</b></td>
                  <td><span style="color: {settings.theme["fg_tags"]}">{tags}</span></td>
                </tr>"""
            header_html += '</table>'
            self.message_info.setHtml(header_html)

        super().refresh()

    def show_message(self, i=-1):
        if i != -1: self.current_message = i

        if self.current_message >= 0 and self.current_message < self.model.num_messages():
            self.refresh()
            m = self.model.message_at(self.current_message)

            if 'unread' in m['tags']:
                self.tag_message('-unread')

            if self.html_mode:
                html = util.body_html(m)
                if html: self.message_view.setHtml(html)
            else:
                text = util.body_text(m)
                if text:
                    self.message_view.setHtml(f"""
                    <html>
                    <head>
                    <style type="text/css">
                    {settings.message_css.format(**settings.theme)}
                    </style>
                    </head>
                    <body>
                    <pre style="white-space: pre-wrap">{text}</pre>
                    </body>
                    </html>""")


    def next_message(self):
        self.show_message(min(self.current_message + 1, self.model.num_messages() - 1))

    def previous_message(self):
        self.show_message(max(self.current_message - 1, 0))

    def scroll_message(self, lines=None, pages=None, pos=None):
        if pos == 'top':
            self.message_view.page().runJavaScript(f'window.scrollTo(0, 0)',
                    QWebEngineScript.ApplicationWorld)
        elif pos == 'bottom':
            self.message_view.page().runJavaScript(f'window.scrollTo(0, document.body.scrollHeight)',
                    QWebEngineScript.ApplicationWorld)
        elif lines is not None:
            self.message_view.page().runJavaScript(f'window.scrollBy(0, {lines} * 20)',
                    QWebEngineScript.ApplicationWorld)
        elif pages is not None:
            self.message_view.page().runJavaScript(f'window.scrollBy(0, {pages} * 0.9 * window.innerHeight)',
                    QWebEngineScript.ApplicationWorld)


    def toggle_message_tag(self, tag):
        m = self.model.message_at(self.current_message)
        if m:
            if tag in m['tags']:
                tag_expr = '-' + tag
            else:
                tag_expr = '+' + tag
            self.tag_message(tag_expr)

    def tag_message(self, tag_expr):
        m = self.model.message_at(self.current_message)
        if m:
            if not ('+' in tag_expr or '-' in tag_expr):
                tag_expr = '+' + tag_expr
            r = subprocess.run(['notmuch', 'tag'] + tag_expr.split() + ['--', 'id:' + m['id']],
                    stdout=subprocess.PIPE)
            self.app.invalidate_panels()
            self.refresh()

    def toggle_html(self):
        self.html_mode = not self.html_mode
        self.show_message()

    def reply(self):
        self.app.compose(reply_to=self.model.message_at(self.current_message))


