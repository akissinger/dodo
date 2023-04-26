#     Dodo - A graphical, hackable email client based on notmuch
#     Copyright (C) 2021 - Aleks Kissinger
#
# This file is part of Dodo
#
# Dodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Dodo. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations
from typing import List, Optional, Any, Union

from PyQt6.QtCore import *
from PyQt6.QtGui import QFont, QColor, QDesktopServices
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineCore import *
from PyQt6.QtWebEngineWidgets import *

import subprocess
import json
import html
import email
import email.message
import tempfile

from . import app
from . import settings
from . import util
from . import keymap
from . import panel


def flat_thread(d: dict) -> List[dict]:
    "Return the thread as a flattened list of messages, sorted by date."

    thread: List[dict] = []
    def dfs(x: Union[list, dict]) -> None:
        if isinstance(x, list):
            for y in x:
                dfs(y)
        else: thread.append(x)

    dfs(d)
    thread.sort(key=lambda m: m['timestamp'])
    return thread

def short_string(m: dict) -> str:
    """Return a short string describing the provided message

    Currently, this just returns the contents of the "From" header, but something like a first name and
    short/relative date might be more useful.

    :param m: A JSON message object"""

    if 'headers' in m and 'From' in m['headers']:
        return m['headers']['From']
    else:
        return '(message)'

class MessagePage(QWebEnginePage):
    def __init__(self, a: app.Dodo, profile: QWebEngineProfile, parent: Optional[QObject]=None):
        super().__init__(profile, parent)
        self.app = a

    def acceptNavigationRequest(self, url: QUrl, ty: QWebEnginePage.NavigationType, isMainFrame: bool) -> bool:
        # if the protocol is 'message' or 'cid', let the request through
        if url.scheme() in app.LOCAL_PROTOCOLS:
            return True
        else:
            if ty == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
                if url.scheme() == 'mailto':
                    query = QUrlQuery(url)
                    msg = {'headers':{'To': url.path(), 'Subject': query.queryItemValue('subject')}}
                    self.app.open_compose(mode='mailto', msg=msg)
                else:
                    if (not settings.html_confirm_open_links or
                        QMessageBox.question(None, 'Open link',
                            f'Open the following URL in browser?\n\n  {url.toString()}') == QMessageBox.StandardButton.Yes):
                        if settings.web_browser_command == '':
                            QDesktopServices.openUrl(url)
                        else:
                            subprocess.Popen([settings.web_browser_command, url.toString()],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
                return False
            if ty == QWebEnginePage.NavigationType.NavigationTypeRedirect:
                # never let a message do a <meta> redirect
                return False
            else:
                return settings.html_block_remote_requests


class MessageHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.message_json: Optional[dict] = None

    def requestStarted(self, request: QWebEngineUrlRequestJob) -> None:
        mode = request.requestUrl().toString()[len('message:'):]

        if self.message_json:
            buf = QBuffer(parent=self)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            if mode == 'html':
                html = util.body_html(self.message_json)
                if html: buf.write(html.encode('utf-8'))
            else:
                text = util.simple_escape(util.body_text(self.message_json))
                text = util.colorize_text(text)
                text = util.linkify(text)

                if text:
                    buf.write(f"""
                    <html>
                    <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
                    <style type="text/css">
                    {util.make_message_css()}
                    </style>
                    </head>
                    <body>
                    <pre style="white-space: pre-wrap">{text}</pre>
                    </body>
                    </html>""".encode('utf-8'))

            buf.close()
            request.reply('text/html'.encode('latin1'), buf)
        else:
            request.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)


class EmbeddedImageHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.message: Optional[email.message.Message] = None

    def set_message(self, filename: str) -> None:
        with open(filename) as f:
            self.message = email.message_from_file(f)

    def requestStarted(self, request: QWebEngineUrlRequestJob) -> None:
        cid = request.requestUrl().toString()[len('cid:'):]

        content_type = None
        if self.message:
            for part in self.message.walk():
                if "Content-id" in part and part["Content-id"] == f'<{cid}>':
                    content_type = part.get_content_type()
                    buf = QBuffer(parent=self)
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    buf.write(part.get_payload(decode=True))
                    buf.close()
                    request.reply(content_type.encode('latin1'), buf)
                    break

            # with open('/home/aleks/git/dodo/images/dodo-screen-inbox.png', 'rb') as f:
            #     buf.write(f.read())
            # buf.close()

        if not content_type:
            request.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)

class ThreadModel(QAbstractItemModel):
    """A model containing a thread, its messages, and some metadata

    This extends `QAbstractItemModel` to enable a tree view to give a summary of the messages, but also contains
    more data that the tree view doesn't care about (e.g. message bodies). Since this comes from calling
    "notmuch show --format=json", it contains information about attachments (e.g. filename), but not attachments
    themselves.

    :param thread_id: the unique thread identifier used by notmuch
    """

    def __init__(self, thread_id: str) -> None:
        super().__init__()
        self.thread_id = thread_id
        self.refresh()

    def refresh(self) -> None:
        """Refresh the model by calling "notmuch show"."""

        r = subprocess.run(['notmuch', 'show', '--format=json', '--verify', '--include-html', self.thread_id],
                stdout=subprocess.PIPE, encoding='utf8')
        self.json_str = r.stdout
        self.d = json.loads(self.json_str)
        self.beginResetModel()
        self.message_list = flat_thread(self.d)
        self.endResetModel()

    def message_at(self, i: int) -> dict:
        """A JSON object describing the i-th message in the (flattened) thread"""

        return self.message_list[i]

    def default_message(self) -> int:
        """Return the index of either the oldest unread message or the last message
        in the thread."""

        for i, m in enumerate(self.message_list):
            if 'tags' in m and 'unread' in m['tags']:
                return i

        return self.num_messages() - 1

    def num_messages(self) -> int:
        """The number of messages in the thread"""

        return len(self.message_list)

    def data(self, index: QModelIndex, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a list view with short descriptions of
        messages in the thread.

        Currently, this just returns the message sender and makes it bold if the message is unread. Adding an
        emoji to show attachments would be good."""

        if index.row() >= len(self.message_list):
            return None

        m = self.message_list[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            if 'headers' in m and 'From' in m["headers"]:
                return m['headers']['From']
            else:
                return '(message)'
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont(settings.search_font, settings.search_font_size)
            if 'tags' in m and 'unread' in m['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ItemDataRole.ForegroundRole:
            if 'tags' in m and 'unread' in m['tags']:
                return QColor(settings.theme['fg_subject_unread'])
            else:
                return QColor(settings.theme['fg'])

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and (irrelevant) column"""

        if not self.hasIndex(row, column, parent): return QModelIndex()
        else: return self.createIndex(row, column, None)

    def columnCount(self, index: QModelIndex=QModelIndex()) -> int:
        """Constant = 1"""

        return 1

    def rowCount(self, index: QModelIndex=QModelIndex()) -> int:
        """The number of rows

        This is essentially an alias for :func:`num_messages`, but it also returns 0 if an index is
        given to tell Qt not to add any child items."""

        if not index or not index.isValid(): return self.num_messages()
        else: return 0

    def parent(self, child: QModelIndex=None) -> Any:
        """Always return an invalid index, since there are no nested indices"""

        if not child: return super().parent()
        else: return QModelIndex()


class ThreadPanel(panel.Panel):
    """A panel showing an email thread

    This is the panel used for email viewing.

    :param app: the unique instance of the :class:`~dodo.app.Dodo` app class
    :param thread_id: the unique ID notmuch uses to identify this thread
    """

    def __init__(self, a: app.Dodo, thread_id: str, parent: Optional[QWidget]=None):
        super().__init__(a, parent=parent)
        self.set_keymap(keymap.thread_keymap)
        self.model = ThreadModel(thread_id)
        self.thread_id = thread_id
        self.html_mode = settings.default_to_html

        self.subject = '(no subject)'
        self.current_message = -1

        self.thread_list = QListView()
        self.thread_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.thread_list.setModel(self.model)
        self.thread_list.clicked.connect(lambda ix: self.show_message(ix.row()))

        self.message_info = QTextBrowser()

        # TODO: this leaks memory, but stops Qt from cleaning up the profile too soon
        self.message_profile = QWebEngineProfile(self.app)

        self.image_handler = EmbeddedImageHandler(self)
        self.message_profile.installUrlSchemeHandler(b'cid', self.image_handler)

        self.message_handler = MessageHandler(self)
        self.message_profile.installUrlSchemeHandler(b'message', self.message_handler)
        self.message_profile.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, False)

        self.message_view = QWebEngineView(self)
        page = MessagePage(self.app, self.message_profile, self.message_view)
        self.message_view.setPage(page)
        self.message_view.setZoomFactor(1.2)

        self.layout_panel()

        self.show_message(self.model.default_message())

    def layout_panel(self):
        """Method for laying out various components in the ThreadPanel"""

        splitter = QSplitter(Qt.Orientation.Vertical)
        info_area = QWidget()
        info_area.setLayout(QHBoxLayout())
        self.thread_list.setFixedWidth(250)
        info_area.layout().addWidget(self.thread_list)
        info_area.layout().addWidget(self.message_info)
        splitter.addWidget(info_area)
        splitter.addWidget(self.message_view)
        self.layout().addWidget(splitter)

        # save splitter position
        window_settings = QSettings("dodo", "dodo")
        state = window_settings.value("thread_splitter_state")
        splitter.splitterMoved.connect(
                lambda x: window_settings.setValue("thread_splitter_state", splitter.saveState()))
        if state: splitter.restoreState(state)

    def title(self) -> str:
        """The tab title

        The title is given as the (shortened) subject of the currently visible message.
        """
        return util.chop_s(self.subject)

    def refresh(self) -> None:
        """Refresh the panel using the output of "notmuch show"

        Note the view of the message body is not refreshed, as this would pop the user back to
        the top of the message every time it happens. To refresh the current message body, use
        :func:`show_message` wihtout any arguments."""

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
            header_html += f'<table style="background-color: {settings.theme["bg"]}; color: {settings.theme["fg"]}; font-family: {settings.search_font}; font-size: {settings.search_font_size}pt; width:100%">'
            for name in ['Subject', 'Date', 'From', 'To', 'Cc']:
                if name in m['headers']:
                    header_html += f"""<tr>
                      <td><b style="color: {settings.theme["fg_bright"]}">{name}:&nbsp;</b></td>
                      <td>{util.simple_escape(m["headers"][name])}</td>
                    </tr>"""
            if 'tags' in m:
                tags = ' '.join([settings.tag_icons[t] if t in settings.tag_icons else f'[{t}]' for t in m['tags']])
                header_html += f"""<tr>
                  <td><b style="color: {settings.theme["fg_bright"]}">Tags:&nbsp;</b></td>
                  <td><span style="color: {settings.theme["fg_tags"]}; font-family: {settings.tag_font}; font-size: {settings.tag_font_size}">{tags}</span></td>
                </tr>"""
            attachments = [f'[{part["filename"]}]' for part in util.message_parts(m)
                    if part.get('content-disposition') == 'attachment' and 'filename' in part]

            if len(attachments) != 0:
                header_html += f"""<tr>
                  <td><b style="color: {settings.theme["fg_bright"]}">Attachments:&nbsp;</b></td>
                  <td><span style="color: {settings.theme["fg_tags"]}">{' '.join(attachments)}</span></td>
                </tr>"""

            # pgp-Signature Status
            for body in m['body']:
                if 'sigstatus' in body:
                    for sig in body['sigstatus']:
                        header_html += f"""<tr>
                          <td><b style="color: {settings.theme["fg_bright"]}">Pgp-signed:&nbsp;</b></td>
                          <td>{sig['status']}: """
                        if sig['status'] == 'error':
                            header_html += f"{' '.join(sig['errors'].keys())} (keyid={sig['keyid']})"
                        elif sig['status'] == 'good':
                            header_html += f"{sig['userid']} ({sig['fingerprint']})"
                        elif sig['status'] == 'bad':
                            header_html += f"keyid={sig['keyid']}"
                        header_html += "</td></tr>"

            header_html += '</table>'
            self.message_info.setHtml(header_html)

        super().refresh()

    def show_message(self, i: int=-1) -> None:
        """Show a message

        If an index is provided, switch the current message to that index, otherwise refresh
        the view of the current message.
        """
        if i != -1: self.current_message = i

        if self.current_message >= 0 and self.current_message < self.model.num_messages():
            self.refresh()
            m = self.model.message_at(self.current_message)
            if 'unread' in m['tags']:
                # this might change the filename, so we should refresh the model
                self.tag_message('-unread')
                self.refresh()
                m = self.model.message_at(self.current_message)

            self.message_handler.message_json = m

            if self.html_mode:
                if 'filename' in m and len(m['filename']) != 0:
                    self.image_handler.set_message(m['filename'][0])
                self.message_view.page().setUrl(QUrl('message:html'))
            else:
                self.message_view.page().setUrl(QUrl('message:plain'))


    def next_message(self) -> None:
        """Show the next message in the thread"""

        self.show_message(min(self.current_message + 1, self.model.num_messages() - 1))

    def previous_message(self) -> None:
        """Show the previous message in the thread"""

        self.show_message(max(self.current_message - 1, 0))

    def scroll_message(self,
            lines: Optional[int]=None,
            pages: Optional[Union[float,int]]=None,
            pos: Optional[str]=None) -> None:
        """Scroll the message body

        This operates in 3 different modes, depending on which arguments are given. Precisely one of the
        three arguments `lines`, `pages`, and `pos` should be provided.

        :param lines: scroll up/down the given number of 20-pixel increments. Negative numbers scroll up.
        :param pages: scroll up/down the given number of pages. Negative numbers scroll up.
        :param pos: scroll to the given position (possible values are 'top' and 'bottom')
        """
        if pos == 'top':
            self.message_view.page().runJavaScript(f'window.scrollTo(0, 0)',
                    QWebEngineScript.ScriptWorldId.ApplicationWorld)
        elif pos == 'bottom':
            self.message_view.page().runJavaScript(f'window.scrollTo(0, document.body.scrollHeight)',
                    QWebEngineScript.ScriptWorldId.ApplicationWorld)
        elif lines is not None:
            self.message_view.page().runJavaScript(f'window.scrollBy(0, {lines} * 20)',
                    QWebEngineScript.ScriptWorldId.ApplicationWorld)
        elif pages is not None:
            self.message_view.page().runJavaScript(f'window.scrollBy(0, {pages} * 0.9 * window.innerHeight)',
                    QWebEngineScript.ScriptWorldId.ApplicationWorld)

    def toggle_message_tag(self, tag: str) -> None:
        """Toggle the given tag on the current message"""

        m = self.model.message_at(self.current_message)
        if m:
            if tag in m['tags']:
                tag_expr = '-' + tag
            else:
                tag_expr = '+' + tag
            self.tag_message(tag_expr)

    def tag_message(self, tag_expr: str) -> None:
        """Apply the given tag expression to the current message

        A tag expression is a string consisting of one more statements of the form "+TAG"
        or "-TAG" to add or remove TAG, respectively, separated by whitespace."""

        m = self.model.message_at(self.current_message)
        if m:
            if not ('+' in tag_expr or '-' in tag_expr):
                tag_expr = '+' + tag_expr
            r = subprocess.run(['notmuch', 'tag'] + tag_expr.split() + ['--', 'id:' + m['id']],
                    stdout=subprocess.PIPE)
            self.app.refresh_panels()

    def toggle_html(self) -> None:
        """Toggle between HTML and plain text message view"""

        self.html_mode = not self.html_mode
        self.show_message()

    def reply(self, to_all: bool=True) -> None:
        """Open a :class:`~dodo.compose.ComposePanel` populated with a reply

        This uses the current message as the message to reply to. This should probably do something
        smarter if the current message is from the user (e.g. reply to the previous one instead).

        :param to_all: if True, do a reply to all instead (see `~dodo.compose.ComposePanel`)
        """

        self.app.open_compose(mode='replyall' if to_all else 'reply',
                              msg=self.model.message_at(self.current_message))

    def forward(self) -> None:
        """Open a :class:`~dodo.compose.ComposePanel` populated with a forwarded message
        """

        self.app.open_compose(mode='forward', msg=self.model.message_at(self.current_message))

    def open_attachments(self) -> None:
        """Write attachments out into temp directory and open with `settings.file_browser_command`

        Currently, this exports a new copy of the attachments every time it is called. Maybe it should
        do something smarter?
        """

        m = self.model.message_at(self.current_message)
        temp_dir, _ = util.write_attachments(m)

        if temp_dir:
            self.temp_dirs.append(temp_dir)
            cmd = settings.file_browser_command.format(dir=temp_dir)
            subprocess.Popen(cmd, shell=True)
