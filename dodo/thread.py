# from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

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


# class MessageBlock(QWidget):
#     def __init__(self, m, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet('QWidget { background-color: %s }' % style.theme['bg_alt'])
#
#         # save headers
#         self.headers = m['headers']
#
#         # extract plain text and html from message body JSON, if it is there
#         tc = find_content(m['body'], 'text/plain')
#         hc = find_content(m['body'], 'text/html')
#         if len(tc) != 0: text = tc[0]
#         elif len(hc) != 0: text = html2text(hc[0])
#         else: text = ''
#         self.html_message = hc[0] if len(hc) != 0 else ''
#
#
#         # save a linkify'd copy of the full plaintext message and a version with the trailing quoted text clipped
#         self.full_text = linkify(html.escape(text))
#         short_text, removed = util.hide_quoted(text)
#         self.short_text = '<pre style="white-space: pre-wrap">' + linkify(util.simple_escape(short_text)) + '</pre>'
#
#         if removed > 0:
#             self.short_text += '<a href="#">[+%d lines quoted text]</a>' % removed
#
#
#         # write out nicely formatted headers as linkify'd HTML
#         self.header_html = '<table>'
#         for name in ['From', 'To', 'Subject', 'Date']:
#             if name in self.headers:
#                 self.header_html += '<tr><td><b style="color: %s">%s:&nbsp;</b></td><td>%s</td></tr>' % (
#                   style.theme['fg_bright'], name, linkify(util.simple_escape(self.headers[name])))
#         self.header_html += '</table>'
#
#         self.header_view = StackingTextView()
#         self.text_view = StackingTextView()
#
#         self.setLayout(QVBoxLayout())
#         self.layout().addWidget(self.header_view)
#         self.layout().addWidget(self.text_view)
#         self.header_view.setHtml(self.header_html)
#         self.text_view.setHtml(self.short_text)


class ThreadView(Panel):
    def __init__(self, app, thread_id, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.thread_keymap)
        self.thread_id = thread_id
        self.subject = '(no subject)'
        self.current_message = -1

        self.splitter = QSplitter(Qt.Vertical)
        info_area = QWidget()
        info_area.setLayout(QHBoxLayout())

        self.thread_list = QListView()
        self.thread_list.setModel(QStringListModel())
        self.message_info = QTextBrowser()
        info_area.layout().addWidget(self.thread_list)
        info_area.layout().addWidget(self.message_info)
        self.splitter.addWidget(info_area)

        self.message_view = QWebEngineView()
        settings = self.message_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
        self.splitter.addWidget(self.message_view)

        self.layout().addWidget(self.splitter)

        self.refresh()

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

        data = []
        for m in self.thread:
            if 'headers' in m and 'From' in m['headers']:
                data.append(m['headers']['From'])
            else:
                data.append('message')
        self.thread_list.model().setStringList(data)

        if self.current_message == -1:
            # TODO: should be set to first unread
            self.current_message = 0

        self.show_message()

    def show_message(self):
        if self.current_message >= 0 and self.current_message < len(self.thread):
            m = self.thread[self.current_message]
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
                html = '<html><body style="font-family: mononoki nerd font">'
                hc = find_content(m['body'], 'text/html')

                if len(hc) != 0:
                    html += hc[0]
                else:
                    tc = find_content(m['body'], 'text/plain')
                    if len(tc) != 0:
                        html += f'<pre style="white-space: pre-wrap; font-size: 14pt; font-family: mononoki nerd font">{tc[0]}</pre>'
                self.message_view.setHtml(html)

