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
from typing import List, Optional, Any, Union, Literal
from collections.abc import Generator, Iterable

from PyQt6.QtCore import *
from PyQt6.QtGui import QFont, QColor, QDesktopServices
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineCore import *
from PyQt6.QtWebEngineWidgets import *

import sys
import traceback
import subprocess
import json
import re
import email
import email.parser
import email.utils
import email.message
import itertools
import tempfile
import logging

from . import app
from . import settings
from . import util
from . import keymap
from . import panel

logger = logging.getLogger(__name__)

def flatten(collection: list) -> Generator:
    for elt in collection:
        if isinstance(elt, list):
            yield from flatten(elt)
        else:
            yield elt

def flat_thread(d: list) -> List[dict]:
    "Return the thread as a flattened list of messages, sorted by date."

    thread = list(flatten(d))
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
                        url.host() in settings.html_confirm_open_links_trusted_hosts or
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
                html = re.sub(r'(<meta(?!\s*(?:name|value)\s*=)[^>]*?charset\s*=[\s"\']*)([^\s"\'/>]*)',
                              r'\1utf-8', html, flags=re.M)
                if html: buf.write(html.encode('utf-8'))
            else:
                for filt in settings.message2html_filters:
                    try:
                        text = filt(self.message_json)
                    except Exception:
                        print(
                            f"Error in message2html filter {filt.__name__}, ignoring:",
                            file=sys.stderr
                        )
                        traceback.print_exc(file=sys.stderr)
                        continue
                    if text is not None:
                        break
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
            request.reply('text/html;charset=utf-8'.encode('latin1'), buf)
        else:
            request.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)


class EmbeddedImageHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.message: Optional[email.message.Message] = None

    def set_message(self, filename: str) -> None:
        with open(filename, 'rb') as f:
            self.message = email.parser.BytesParser().parse(f)

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

class RemoteBlockingUrlRequestInterceptor(QWebEngineUrlRequestInterceptor):
    def interceptRequest(self, info):
        if info.requestUrl().scheme() not in app.LOCAL_PROTOCOLS:
            info.block(settings.html_block_remote_requests)

RE_REGEX = re.compile('^R[Ee]: ')
class ThreadItem:
    def __init__(self, raw_data, parent: ThreadItem|None):
        self.msg = raw_data[0]
        self.parent = parent
        self.children = [ThreadItem(elt, self) for elt in raw_data[1]]

    def thread_string(self):
        from_hdr = self.msg.get('headers', {}).get('From', '(message) <>')
        name, addr = email.utils.parseaddr(from_hdr)
        if not name:
            name = addr
        if not self.parent:
            return name

        subject = self.msg.get('headers', {}).get('Subject', '')
        while RE_REGEX.match(subject):
            subject = RE_REGEX.sub('', subject)
        prev_subject = self.parent.msg.get('headers', {}).get('Subject', '')
        while RE_REGEX.match(prev_subject):
            prev_subject = RE_REGEX.sub('', prev_subject)

        if subject != prev_subject:
            return f"{name} — {subject}"
        else:
            return name

def make_thread_trees(raw_thread_data: list) -> list[ThreadItem]:
    "Return the set of roots for a given thread. If the thread is linear, then all messages are roots."
    def has_multiple_children(forest: list):
        while forest:
            if len(forest) > 1:
                return True
            forest = forest[0][1]

    if has_multiple_children(raw_thread_data):
        return [ThreadItem(root, None) for root in raw_thread_data]
    else:
        return [ThreadItem([msg, []], None) for msg in flatten(raw_thread_data)]

class ThreadModel(QAbstractItemModel):
    """A model containing a thread, its messages, and some metadata

    This extends `QAbstractItemModel` to enable a tree view to give a summary of the messages, but also contains
    more data that the tree view doesn't care about (e.g. message bodies). Since this comes from calling
    "notmuch show --format=json", it contains information about attachments (e.g. filename), but not attachments
    themselves.

    :param thread_id: the unique thread identifier used by notmuch
    """

    matches: set[str]

    messageChanged = pyqtSignal(QModelIndex)

    def __init__(self, thread_id: str, search_query: str, mode: Literal['conversation','thread']) -> None:
        super().__init__()
        self.thread_id = thread_id
        self.query = search_query
        self.matches = set()
        self.raw_data = []
        self.roots = []
        self._mode: Literal['conversation','thread'] = mode

    @property
    def mode(self) -> Literal['conversation','thread']:
        return self._mode

    def toggle_mode(self):
        self.beginResetModel()
        if self._mode == 'conversation':
            self._mode = 'thread'
        else:
            self._mode = 'conversation'
        self.roots = self.compute_roots(self.raw_data)
        self.endResetModel()

    def compute_roots(self, raw_data):
        match self.mode:
            case 'conversation':
                return [ThreadItem([msg, []], None) for msg in flat_thread(raw_data)]
            case 'thread':
                return make_thread_trees(raw_data)

    def _fetch_full_thread(self) -> list:
        r = subprocess.run(['notmuch', 'show', '--exclude=false', '--format=json', '--verify', '--include-html', '--decrypt=true', self.thread_id],
                stdout=subprocess.PIPE, encoding='utf8')
        return json.loads(r.stdout)

    def _fetch_matching_ids(self) -> set[str]:
        r = subprocess.run(['notmuch', 'search', '--exclude=false', '--format=json', '--output=messages', f'thread:{self.thread_id} AND {self.query}'],
                stdout=subprocess.PIPE, encoding='utf8')
        return set(json.loads(r.stdout))

    def get_last_msg_idx(self, parent: QModelIndex=QModelIndex()) -> QModelIndex:
        children = parent.internalPointer().children
        if children:
            return self.get_last_msg_idx(self.index(len(children)-1, 0, parent))
        return parent

    def refresh(self) -> None:
        """Refresh the model by calling "notmuch show"."""

        logger.info("Full thread refresh")
        matches = self._fetch_matching_ids()
        data = self._fetch_full_thread()
        assert(len(data) == 1)
        data = data[0]
        roots = self.compute_roots(data)
        self.beginResetModel()
        self.raw_data = data
        self.roots = roots
        self.matches = matches
        self.endResetModel()

    def refresh_message(self, msg_id: str):
        idx = self.find(msg_id)
        assert idx.isValid()
        logger.info("Single message refresh: %s", msg_id)
        r = subprocess.run(['notmuch', 'show', '--entire-thread=false', '--exclude=false', '--format=json', '--verify', '--include-html', '--decrypt=true', f'id:{msg_id}'],
                stdout=subprocess.PIPE, encoding='utf8')
        msg = next(m for m in flatten(json.loads(r.stdout)) if m is not None)
        logger.info("refreshed tags: %s", str(msg['tags']))
        # We need to refresh the matches in case the message dropped out of the set
        matches = self._fetch_matching_ids()
        # Update the old message in-place to not invalidate existing indices
        old_msg = self.message_at(idx)
        old_msg.clear()
        old_msg.update(msg)
        self.matches = matches
        self.dataChanged.emit(idx, idx)

    def tag_message(self, idx: QModelIndex, tag_expr: str) -> None:
        """Apply the given tag expression to the current message

        A tag expression is a string consisting of one more statements of the form "+TAG"
        or "-TAG" to add or remove TAG, respectively, separated by whitespace."""

        if not idx.isValid():
            return
        m = self.message_at(idx)
        msg_id = m['id']
        if not ('+' in tag_expr or '-' in tag_expr):
            tag_expr = '+' + tag_expr
        r = subprocess.run(['notmuch', 'tag'] + tag_expr.split() + ['--', 'id:' + msg_id],
                stdout=subprocess.PIPE)
        self.messageChanged.emit(idx)

    def toggle_message_tag(self, idx: QModelIndex, tag: str) -> None:
        """Toggle the given tag on the current message"""

        m = self.message_at(idx)
        if tag in m['tags']:
            tag_expr = '-' + tag
        else:
            tag_expr = '+' + tag
        self.tag_message(idx, tag_expr)

    def mark_as_read(self, idx: QModelIndex) -> bool:
        "Marks a message as read. Returns False if nothing is to be done"
        m = self.message_at(idx)
        if 'unread' in m['tags']:
            self.tag_message(idx, '-unread')
            return True
        return False

    def message_at(self, idx: QModelIndex) -> dict:
        """A JSON object describing the i-th message in the (flattened) thread"""
        assert idx.isValid()
        return idx.internalPointer().msg

    def _children_at(self, idx: QModelIndex) -> list[ThreadItem]:
        if idx.isValid():
            return idx.internalPointer().children
        return self.roots

    def iterate_indices(self) -> Iterable[QModelIndex]:
        """Iterate indices in the topological order"""
        def rec_iterate_indices(node: QModelIndex) -> Iterable[QModelIndex]:
            yield node
            for i,c in enumerate(self._children_at(node)):
                yield from rec_iterate_indices(self.createIndex(i, 0, c))
        for i,r in enumerate(self.roots):
            yield from rec_iterate_indices(self.createIndex(i, 0, r))

    def find(self, msg_id: str) -> QModelIndex:
        return next((idx for idx in self.iterate_indices() if self.message_at(idx)['id'] == msg_id), QModelIndex())

    def default_message(self) -> QModelIndex:
        """Return the index of either the oldest matching message or the last message
        in the thread."""
        for idx in self.iterate_indices():
            if self.message_at(idx)['id'] in self.matches:
                return idx
        return self.get_last_msg_idx()

    def default_collapsed(self) -> set[str]:
        irrelevant_branches = set()
        def prune_irrelevant_branches(node: ThreadItem) -> bool:
            has_relevant_child = False
            msg_id = node.msg['id']
            if msg_id in self.matches:
                return True
            for c in node.children:
                has_relevant_child |= prune_irrelevant_branches(c)
            if not has_relevant_child:
                irrelevant_branches.add(msg_id)
            return has_relevant_child
        for root in self.roots:
            prune_irrelevant_branches(root)
        return irrelevant_branches

    def next_unread(self, current: QModelIndex) -> QModelIndex:
        """Show the next relevant unread message in the thread"""
        # We do a full iteration to be able to see sibling subthreads
        for idx in itertools.dropwhile(lambda idx: idx != current, self.iterate_indices()):
            msg = self.message_at(idx)
            if msg['id'] in self.matches and 'unread' in msg['tags']:
                return idx
        return QModelIndex()

    def data(self, index: QModelIndex, role: int=Qt.ItemDataRole.DisplayRole) -> Any:
        """Overrides `QAbstractItemModel.data` to populate a list view with short descriptions of
        messages in the thread.

        Currently, this just returns the message sender and makes it bold if the message is unread. Adding an
        emoji to show attachments would be good."""

        item: ThreadItem = index.internalPointer()
        m = item.msg
        if role == Qt.ItemDataRole.DisplayRole:
            return item.thread_string()
        elif role == Qt.ItemDataRole.FontRole:
            font = QFont(settings.search_font, settings.search_font_size)
            if m['id'] not in self.matches:
                font.setItalic(True)
            if 'tags' in m and 'unread' in m['tags']:
                font.setBold(True)
            return font
        elif role == Qt.ItemDataRole.ForegroundRole:
            if m['id'] not in self.matches:
                return QColor(settings.theme['fg_subject_irrelevant'])
            if 'tags' in m and 'unread' in m['tags']:
                return QColor(settings.theme['fg_subject_unread'])
            else:
                return QColor(settings.theme['fg'])

    def index(self, row: int, column: int, parent: QModelIndex=QModelIndex()) -> QModelIndex:
        """Construct a `QModelIndex` for the given row and (irrelevant) column"""
        children = self._children_at(parent)
        if row not in range(0, len(children)) or column != 0:
            return QModelIndex()
        return self.createIndex(row, column, children[row])

    def parent(self, child: QModelIndex=QModelIndex()) -> QModelIndex:
        data = child.internalPointer()
        if data is None or data.parent is None:
            return QModelIndex()
        aunties = data.parent.parent.children if data.parent.parent else self.roots
        for i,c in enumerate(aunties):
            if c == data.parent:
                return self.createIndex(i, 0, data.parent)

    def columnCount(self, index: QModelIndex=QModelIndex()) -> int:
        """Constant = 1"""
        return 1

    def rowCount(self, parent: QModelIndex=QModelIndex()) -> int:
        """The number of rows (for a given parent)"""
        return len(self._children_at(parent))


class ThreadPanel(panel.Panel):
    """A panel showing an email thread

    This is the panel used for email viewing.

    :param app: the unique instance of the :class:`~dodo.app.Dodo` app class
    :param thread_id: the unique ID notmuch uses to identify this thread
    """

    def __init__(self, a: app.Dodo, thread_id: str, search_query: str, parent: Optional[QWidget]=None):
        super().__init__(a, parent=parent)
        self.set_keymap(keymap.thread_keymap)
        self.model = ThreadModel(thread_id, search_query, settings.default_thread_list_mode)
        self.thread_id = thread_id
        self.html_mode = settings.default_to_html
        self._saved_msg = None
        self._saved_collapsed = None

        self.subject = '(no subject)'

        self.thread_list = QTreeView()
        self.thread_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.thread_list.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.thread_list.header().setStretchLastSection(False)
        self.thread_list.setHeaderHidden(True)
        self.thread_list.setRootIsDecorated(False)
        self.thread_list.setModel(self.model)
        self.thread_list.clicked.connect(self._select_index)
        self.model.modelAboutToBeReset.connect(self._prepare_reset)
        self.model.modelReset.connect(self._do_reset)
        self.model.dataChanged.connect(lambda _a,_b: self.refresh_view())
        self.model.messageChanged.connect(lambda idx: self.app.update_single_thread(self.thread_id, msg_id=self.model.message_at(idx)['id']))

        self.message_info = QTextBrowser()

        # TODO: this leaks memory, but stops Qt from cleaning up the profile too soon
        self.message_profile = QWebEngineProfile(self.app)

        self.image_handler = EmbeddedImageHandler(self)
        self.message_profile.installUrlSchemeHandler(b'cid', self.image_handler)

        self.message_handler = MessageHandler(self)
        self.message_profile.installUrlSchemeHandler(b'message', self.message_handler)
        self.message_profile.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, False)

        # The interceptor must not be garbage collected, so keep a reference
        self.url_interceptor = RemoteBlockingUrlRequestInterceptor()
        self.message_profile.setUrlRequestInterceptor(self.url_interceptor)

        self.message_view = QWebEngineView(self)
        page = MessagePage(self.app, self.message_profile, self.message_view)
        self.message_view.setPage(page)
        self.message_view.setZoomFactor(1.2)

        self.layout_panel()

    def _get_collapsed(self) -> set[str]:
        collapsed = set()
        for idx in self.model.iterate_indices():
            if not self.thread_list.isExpanded(idx):
                collapsed.add(self.model.message_at(idx)['id'])
        return collapsed

    def _restore_collapsed(self, collapsed: set[str]):
        self.thread_list.expandAll()
        for idx in self.model.iterate_indices():
            msg_id = self.model.message_at(idx)['id']
            if msg_id in collapsed:
                self.thread_list.setExpanded(idx, False)

    def _prepare_reset(self):
        if self.current_index.isValid():
            self._saved_msg = self.current_message['id']
            self._saved_collapsed = self._get_collapsed()

    def _do_reset(self):
        idx = QModelIndex()
        if self._saved_msg:
            idx = self.model.find(self._saved_msg)
            self._saved_msg = None
        if idx.isValid():
            self._select_index(idx)
        else:
            self._select_index(self.model.default_message())
        if self._saved_collapsed is None:
            collapsed = self.model.default_collapsed()
        else:
            collapsed = self._saved_collapsed
            self._saved_collapsed = None
        self._restore_collapsed(collapsed)

    def toggle_list_mode(self):
        self.model.toggle_mode()

    def _select_index(self, index: QModelIndex):
        if not index.isValid():
            return
        self.thread_list.setCurrentIndex(index)
        # We only refresh the view if there was no tagging
        if not self.model.mark_as_read(index):
            self.refresh_view()

    def layout_panel(self):
        """Method for laying out various components in the ThreadPanel"""

        splitter = QSplitter(Qt.Orientation.Vertical)
        info_area = QSplitter(Qt.Orientation.Horizontal)
        #self.thread_list.setFixedWidth(250)
        info_area.addWidget(self.thread_list)
        info_area.addWidget(self.message_info)
        splitter.addWidget(info_area)
        splitter.addWidget(self.message_view)
        self.layout().addWidget(splitter)

        # save splitter positions
        window_settings = QSettings("dodo", "dodo")
        main_state = window_settings.value("thread_splitter_state")
        splitter.splitterMoved.connect(
                lambda x: window_settings.setValue("thread_splitter_state", splitter.saveState()))
        if main_state: splitter.restoreState(main_state)

        info_area.splitterMoved.connect(
                lambda x: window_settings.setValue("thread_info_state", info_area.saveState()))
        info_state = window_settings.value("thread_info_state")
        if info_state: info_area.restoreState(info_state)

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

        super().refresh()
        self.model.refresh()

    def refresh_view(self):
        """Refresh the UI, without refreshing the underlying content"""
        m = self.current_message

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

            # Show pgp-Signature Status
            if 'signed' in m['crypto']:
                for sig in m['crypto']['signed']['status']:
                    header_html += f"""<tr>
                      <td><b style="color: {settings.theme["fg_bright"]}">Pgp-signed:&nbsp;</b></td>
                      <td>{sig['status']}: """
                    if sig['status'] == 'error':
                        header_html += f"{' '.join(sig['errors'].keys())} (keyid={sig['keyid']})"
                    elif sig['status'] == 'good':
                        header_html += f"{sig.get('userid')} ({sig['fingerprint']})"
                    elif sig['status'] == 'bad':
                        header_html += f"keyid={sig['keyid']}"
                    header_html += "</td></tr>"

            # Show Decryption status
            if 'decrypted' in m['crypto']:
                header_html += f"""<tr>
                  <td><b style="color: {settings.theme["fg_bright"]}">Decryption:&nbsp;</b></td>
                  <td>{m['crypto']['decrypted']['status']}"""
                header_html += "</td></tr>"
            header_html += '</table>'
            self.message_info.setHtml(header_html)

        self.message_handler.message_json = m

        if self.html_mode:
            if 'filename' in m and len(m['filename']) != 0:
                self.image_handler.set_message(m['filename'][0])
            self.message_view.page().setUrl(QUrl('message:html'))
        else:
            self.message_view.page().setUrl(QUrl('message:plain'))
        self.scroll_message(pos = 'top')
        self.has_refreshed.emit()


    def update_thread(self, thread_id: str, msg_id: str|None=None):
        if self.model.thread_id == thread_id:
            if msg_id and self.model.find(msg_id).isValid():
                self.model.refresh_message(msg_id)
            else:
                self.dirty = True

    def next_message(self) -> None:
        """Show the next message in the thread"""
        self._select_index(self.thread_list.indexBelow(self.current_index))

    def previous_message(self) -> None:
        """Show the previous message in the thread"""
        self._select_index(self.thread_list.indexAbove(self.current_index))

    def next_unread(self) -> None:
        self._select_index(self.model.next_unread(self.current_index))

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

    @property
    def current_index(self) -> QModelIndex:
        return self.thread_list.currentIndex()

    @property
    def current_message(self) -> dict:
        return self.model.message_at(self.current_index)

    def toggle_message_tag(self, tag: str) -> None:
        return self.model.toggle_message_tag(self.current_index, tag)

    def tag_message(self, tag_expr: str) -> None:
        return self.model.tag_message(self.current_index, tag_expr)

    def toggle_html(self) -> None:
        """Toggle between HTML and plain text message view"""

        self.html_mode = not self.html_mode
        self.refresh_view()

    def reply(self, to_all: bool=True) -> None:
        """Open a :class:`~dodo.compose.ComposePanel` populated with a reply

        This uses the current message as the message to reply to. This should probably do something
        smarter if the current message is from the user (e.g. reply to the previous one instead).

        :param to_all: if True, do a reply to all instead (see `~dodo.compose.ComposePanel`)
        """

        self.app.open_compose(mode='replyall' if to_all else 'reply',
                              msg=self.current_message)

    def forward(self) -> None:
        """Open a :class:`~dodo.compose.ComposePanel` populated with a forwarded message
        """

        self.app.open_compose(mode='forward', msg=self.current_message)

    def open_attachments(self) -> None:
        """Write attachments out into temp directory and open with `settings.file_browser_command`

        Currently, this exports a new copy of the attachments every time it is called. Maybe it should
        do something smarter?
        """

        m = self.current_message
        temp_dir, _ = util.write_attachments(m)

        if temp_dir:
            self.temp_dirs.append(temp_dir)
            cmd = settings.file_browser_command.format(dir=temp_dir)
            subprocess.Popen(cmd, shell=True)
