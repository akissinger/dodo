from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout
import subprocess
import json
# from html_sanitizer import Sanitizer
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
    def __init__(self, text, html_message, headers, parent=None):
        super().__init__(parent)
        self.text = text
        self.html_message = html_message
        self.headers = headers
        self.header_html = ''

        self.display_header('From')
        self.display_header('Subject')
        self.display_header('Date')

        self.header_view = StackingTextView()
        self.text_view = StackingTextView()

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.header_view)
        layout.addWidget(self.text_view)
        self.header_view.setHtml(self.header_html)
        self.text_view.setText(text)

    def display_header(self, name):
        if name in self.headers:
            self.header_html += '<b style="color: %s">%s:</b> %s<br/>' % (style.theme['fg_bright'], name, html.escape(self.headers[name]))

class MessageStack(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.messages = []

    def add_message(self, m):
        tc = find_content(m['body'], 'text/plain')
        hc = find_content(m['body'], 'text/html')

        if len(tc) != 0:
            text = tc[0]
        elif len(hc) != 0:
            text = html2text(hc[0])
        else:
            text = ''

        html_message = hc[0] if len(hc) != 0 else ''

        headers = m['headers'] if 'headers' in m else {}

        b = MessageBlock(text, html_message, headers)
        self.messages.append(b)
        self.layout.addWidget(b)


class ThreadView(Panel):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.thread_keymap)
        self.thread_id = thread_id
        self.message_stack = MessageStack(self)
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
            self.message_stack.add_message(m)

        if not self.subject:
            self.subject = '(no subject)'

