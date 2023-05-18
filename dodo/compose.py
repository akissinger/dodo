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
from typing import Optional, List, Set

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtWebEngineWidgets import *
import mailbox
import email
import email.utils
import email.parser
import mimetypes
import subprocess
from subprocess import PIPE, Popen, TimeoutExpired
import tempfile
import os
import re

from . import app
from . import panel
from . import keymap
from . import settings
from . import util

class ComposePanel(panel.Panel):
    """A panel for composing messages

    :param mode: Composition mode. Possible values are '', 'mailto', 'reply', 'replyall',
                 and 'forward'
    :param msg: A JSON message referenced in a reply or forward. If mode != '',
                this cannot be None.
    """

    def __init__(self, a: app.Dodo, mode: str='', msg: Optional[dict]=None, parent: Optional[QWidget]=None):
        super().__init__(a, keep_open=False, parent=parent)
        self.set_keymap(keymap.compose_keymap)
        self.mode = mode
        self.msg = msg
        self.message_view = QWebEngineView()
        self.message_view.setZoomFactor(1.2)
        self.layout().addWidget(self.message_view)
        self.status = f'<i style="color:{settings.theme["fg"]}">draft</i>'
        self.current_account = 0

        self.wrap_message = settings.wrap_message

        self.raw_message_string = f'From: {self.email_address()}\n'
        self.message_string = ''

        if msg and mode == 'mailto':
            if 'To' in msg['headers']:
                self.raw_message_string += f'To: {msg["headers"]["To"]}\n'

            if 'Subject' in msg['headers']:
                self.raw_message_string += f'Subject: {msg["headers"]["Subject"]}\n'
            else:
                self.raw_message_string += 'Subject: \n'

            self.raw_message_string += '\n\n\n'

        elif msg and (mode == 'reply' or mode == 'replyall'):
            send_to: List[str] = []
            email_sep = re.compile('\s*,\s*')

            if 'From' in msg['headers']:
                send_to.append(msg["headers"]["From"])
            if 'To' in msg['headers']:
                send_to += email_sep.split(msg['headers']['To'])
            if 'Cc' in msg['headers']:
                send_to += email_sep.split(msg['headers']['Cc'])

            send_to = [e for e in send_to if not util.email_is_me(e)]

            # put the first non-me email in To
            if len(send_to) != 0:
                self.raw_message_string += f'To: {send_to.pop(0)}\n'

            # for replyall, put the rest of the emails in Cc
            if len(send_to) != 0 and mode == 'replyall':
                self.raw_message_string += f'Cc: {", ".join(send_to)}\n'

            if 'Subject' in msg['headers']:
                subject = msg['headers']['Subject']
                if subject[0:3].upper() != 'RE:':
                    subject = 'RE: ' + subject
                self.raw_message_string += f'Subject: {subject}\n'

            self.raw_message_string += '\n\n\n' + util.quote_body_text(msg)

        elif msg and mode == 'forward':
            self.raw_message_string += f'To: \n'

            if 'Subject' in msg['headers']:
                subject = msg['headers']['Subject']
                if subject[0:3].upper() != 'FW:':
                    subject = 'FW: ' + subject
                self.raw_message_string += f'Subject: {subject}\n'

            # if the message has attachments, dump them to temp dir and attach them
            temp_dir, att = util.write_attachments(msg)
            if temp_dir: self.temp_dirs.append(temp_dir)
            for f in att: self.raw_message_string += f'A: {f}\n'

            self.raw_message_string += '\n\n\n---------- Forwarded message ---------\n'
            for h in ['From', 'Date', 'Subject', 'To']:
                if h in msg['headers']:
                    self.raw_message_string += f'{h}: {msg["headers"][h]}\n'

            self.raw_message_string += '\n' + util.body_text(msg) + '\n'

        else:
            self.raw_message_string += 'To: \nSubject: \n\n'

        self.editor_thread: Optional[EditorThread] = None
        self.sendmail_thread: Optional[SendmailThread] = None

        self.refresh()

    def title(self) -> str:
        return 'compose'

    def refresh(self) -> None:
        """Refresh the message text

        This gets called automatically after the external editor has closed."""

        # set message_string to be wrapped version of raw_message_string, depending on
        # preferences
        if self.wrap_message:
            self.message_string = util.wrap_message(self.raw_message_string)
        else:
            self.message_string = self.raw_message_string

        text = util.colorize_text(util.simple_escape(self.message_string), has_headers=True)

        if len(settings.smtp_accounts) > 1:
            account_str = f'<pre style="color: {settings.theme["fg_good"]}"><b>Account:</b> '
            for i,acct in enumerate(settings.smtp_accounts):
                if i == self.current_account:
                    account_str += f'[{acct}]'
                else:
                    account_str += f' {acct} '
            account_str += '</pre>'
        else:
            account_str = ''

        self.message_view.setHtml(f"""<html>
        <style type="text/css">
        {util.make_message_css()}
        </style>
        <body>
        {account_str}
        <p>{self.status}</p>
        <pre style="white-space: pre-wrap">{text}</pre>
        </body></html>""")

        super().refresh()

    def edit(self) -> None:
        """Edit the email message with an external text editor

        The editor is configured via :func:`dodo.settings.editor_command`."""

        # only open one editor at a time
        if self.editor_thread is None:
            self.editor_thread = EditorThread(self, parent=self)

            def done() -> None:
                if self.editor_thread:
                    self.editor_thread.deleteLater()
                    self.editor_thread = None
                self.refresh()
                self.app.raise_panel(self)

            self.editor_thread.finished.connect(done)
            self.editor_thread.start()

    def attach_file(self) -> None:
        """Attach a file

        Opens a file browser for selecting a file to attach. If a file is selected, add it using the "A:"
        pseudo-header. This will be translated into a proper attachment when the message is sent.

        This command can also use the optional setting file_picker_command to run an external file picker
        instead of Qt's built-in one."""

        if settings.file_picker_command == None:
            f = QFileDialog.getOpenFileName()
            if f[0]:
                self.raw_message_string = util.add_header_line(self.raw_message_string, 'A: ' + f[0])
                self.refresh()
        else:
            fd, file = tempfile.mkstemp()
            cmd = settings.file_picker_command.format(tempfile=file)
            subprocess.run(cmd, shell=True)

            with open(file, 'r') as f1:
                file_list = f1.read().split('\n')
            os.remove(file)

            for att in file_list:
                if att != '':
                    self.raw_message_string = util.add_header_line(self.raw_message_string, 'A: ' + att)
            self.refresh()


    def toggle_wrap(self) -> None:
        """Toggle message wrapping

        Tell Dodo to apply hard wrapping to message text for viewing and sending. This maintains an unwrapped
        copy of the text for editing."""

        self.wrap_message = not self.wrap_message
        self.refresh()

    def account_name(self) -> str:
        """Return the name of the current SMTP account"""

        return settings.smtp_accounts[self.current_account]

    def email_address(self) -> str:
        """Return email address that should be used in From: header"""

        if isinstance(settings.email_address, dict):
            return settings.email_address[self.account_name()]
        else:
            return settings.email_address

    def next_account(self) -> None:
        """Cycle to the next SMTP account in :func:`~dodo.settings.smtp_accounts`"""

        old_email = self.email_address()
        self.current_account = (self.current_account+1) % len(settings.smtp_accounts)

        if self.email_address() != old_email:
            self.raw_message_string = util.replace_header(self.raw_message_string, 'From', self.email_address())

        self.refresh()

    def previous_account(self) -> None:
        """Cycle to the previous SMTP account in :func:`~dodo.settings.smtp_accounts`"""

        old_email = self.email_address()
        self.current_account = (self.current_account-1) % len(settings.smtp_accounts)

        if self.email_address() != old_email:
            self.raw_message_string = util.replace_header(self.raw_message_string, 'From', self.email_address())

        self.refresh()

    def send(self) -> None:
        """Send the message

        Sends asynchronously using :class:`~dodo.compose.SendmailThread`. If one or more occurances of
        the "A:" pseudo-header are detected, these are converted into attachments."""

        # only try to send mail once at a time
        if self.sendmail_thread is None:
            self.status = f'<i style="color:{settings.theme["fg_bright"]}">sending</i>'
            self.refresh()
            self.sendmail_thread = SendmailThread(self, parent=self)

            def done() -> None:
                if self.sendmail_thread:
                    self.sendmail_thread.deleteLater()
                    self.sendmail_thread = None
                self.app.refresh_panels()

            self.sendmail_thread.finished.connect(done)
            self.sendmail_thread.start()


class EditorThread(QThread):
    """A QThread used for editing mail with the external editor

    Used by the :func:`~dodo.compose.ComposePanel.edit` method."""

    def __init__(self, panel: ComposePanel, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.panel = panel

    def run(self) -> None:
        fd, file = tempfile.mkstemp('.eml')
        with os.fdopen(fd, 'w') as f:
            f.write(self.panel.raw_message_string)

        cmd = settings.editor_command.format(file=file)
        subprocess.run(cmd, shell=True)

        with open(file, 'r') as f1:
            self.panel.raw_message_string = f1.read()

        os.remove(file)

class SendmailThread(QThread):
    """A QThread used for editing mail with the external editor

    Used by the :func:`~dodo.compose.ComposePanel.edit` method."""

    def __init__(self, panel: ComposePanel, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.panel = panel

    def run(self) -> None:
        try:
            account = self.panel.account_name()
            m = email.message_from_string(self.panel.message_string)
            eml = email.message.EmailMessage()
            attachments: List[str] = m.get_all('A', [])

            # n.b. this kills duplicate headers. May want to revisit this if it causes problems.
            for h in m.keys():
                if h != 'A':
                    eml[h] = m[h]

            eml['Message-ID'] = email.utils.make_msgid()
            eml['User-Agent'] = 'Dodo'

            eml.set_content(m.get_payload())

            # add a date if it's missing
            if not "Date" in eml:
                eml["Date"] = email.utils.formatdate(localtime=True)

            # add "In-Reply-To" and "References" headers if there's an old message
            if self.panel.msg and 'id' in self.panel.msg:
                msg_id = f'<{self.panel.msg["id"]}>'
                eml["In-Reply-To"] = msg_id

                refs = [msg_id]
                if 'filename' in self.panel.msg and len(self.panel.msg['filename']) != 0:
                    try:
                        with open(self.panel.msg['filename'][0]) as f:
                            old_msg = email.parser.Parser().parse(f, headersonly=True)

                            if "References" in old_msg:
                                refs = old_msg["References"].split() + refs
                    except IOError:
                        print("Couldn't open message to get References")

                eml["References"] = ' '.join(refs)


            for att in attachments:
                mime, _ = mimetypes.guess_type(att)
                if mime and len(mime.split('/')) == 2:
                    ty = mime.split('/')
                else:
                    ty = ['application', 'octet-stream']

                try:
                    with open(os.path.expanduser(att), 'rb') as f1:
                        data = f1.read()
                        eml.add_attachment(data, maintype=ty[0], subtype=ty[1], filename=os.path.basename(att))
                except IOError:
                    print("Can't read attachment: " + att)

            cmd = settings.send_mail_command.replace('{account}', account)
            sendmail = Popen(cmd, stdin=PIPE, encoding='utf8', shell=True)
            if sendmail.stdin:
                sendmail.stdin.write(str(eml))
                sendmail.stdin.close()
            sendmail.wait(30)
            if sendmail.returncode == 0:
                # save to sent folder
                m = mailbox.MaildirMessage(str(eml))
                m.set_flags('S')
                if isinstance(settings.sent_dir, dict):
                    sent_dir = settings.sent_dir[account]
                else:
                    sent_dir = settings.sent_dir
                key = mailbox.Maildir(sent_dir).add(m)
                # print(f'add: {key}')

                subprocess.run(['notmuch', 'new', '--no-hooks'])

                if ((self.panel.mode == 'reply' or self.panel.mode == 'replyall') and
                        self.panel.msg and 'id' in self.panel.msg):
                    subprocess.run(['notmuch', 'tag', '+replied', '--', 'id:' + self.panel.msg['id']])
                self.panel.status = f'<i style="color:{settings.theme["fg_good"]}">sent</i>'
            else:
                self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">error</i>'
        except TimeoutExpired:
            self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">timed out</i>'
