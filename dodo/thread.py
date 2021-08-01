# from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout
import subprocess
import json
from autolink import linkify
from html2text import html2text
import html

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


class MessageBlock(QWidget):
    def __init__(self, m, parent=None):
        super().__init__(parent)
        self.setStyleSheet('QWidget { background-color: %s }' % style.theme['bg_alt'])

        # save headers
        self.headers = m['headers']

        # extract plain text and html from message body JSON, if it is there
        tc = find_content(m['body'], 'text/plain')
        hc = find_content(m['body'], 'text/html')
        if len(tc) != 0: text = tc[0]
        elif len(hc) != 0: text = html2text(hc[0])
        else: text = ''
        self.html_message = hc[0] if len(hc) != 0 else ''


        # save a linkify'd copy of the full plaintext message and a version with the trailing quoted text clipped
        self.full_text = linkify(html.escape(text))
        short_text, removed = util.hide_quoted(text)
        self.short_text = '<pre style="white-space: pre-wrap">' + linkify(html.escape(short_text)) + '</pre>'

        if removed > 0:
            self.short_text += '<a href="#">[+%d lines quoted text]</a>' % removed


        # write out nicely formatted headers as linkify'd HTML
        self.header_html = '<table>'
        for name in ['From', 'To', 'Subject', 'Date']:
            if name in self.headers:
                self.header_html += '<tr><td><b style="color: %s">%s:&nbsp;</b></td><td>%s</td></tr>' % (
                  style.theme['fg_bright'], name, linkify(html.escape(self.headers[name])))
        self.header_html += '</table>'

        self.header_view = StackingTextView()
        self.text_view = StackingTextView()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.header_view)
        self.layout().addWidget(self.text_view)
        self.header_view.setHtml(self.header_html)
        self.text_view.setHtml(self.short_text)


class ThreadView(Panel):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.thread_keymap)
        self.thread_id = thread_id
        self.message_stack = QWidget(self)
        self.message_stack.setLayout(QVBoxLayout())
        self.refresh()

        self.scroll = QScrollArea()
        self.layout().addWidget(self.scroll)
        self.scroll.setWidget(self.message_stack)
        self.scroll.setWidgetResizable(True)

    def title(self):
        return util.chop_s(self.subject)

    def refresh(self):
        r = subprocess.run(['notmuch', 'show', '--format=json', '--include-html', self.thread_id],
                stdout=subprocess.PIPE)
        self.json_str = r.stdout.decode('utf-8')
        self.d = json.loads(self.json_str)

        # store a flattened version of the thread
        self.thread = flat_thread(self.d)
        print('thread of size: %d' % len(self.thread))

        self.subject = None
        for m in self.thread:
            if not self.subject and 'headers' in m and 'Subject' in m['headers']:
                self.subject = m['headers']['Subject']

            b = MessageBlock(m)
            self.message_stack.layout().addWidget(b)

        if not self.subject:
            self.subject = '(no subject)'

