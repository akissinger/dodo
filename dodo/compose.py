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

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
import mailbox
import email
import mimetypes
import subprocess
from subprocess import PIPE, Popen, TimeoutExpired
import tempfile
import os
import re

from .panel import Panel
from . import keymap
from . import settings
from . import util

class EditorThread(QThread):
    """A QThread used for editing mail with the external editor

    Used by the :func:`~dodo.compose.ComposePanel.edit` method."""

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel

    def run(self):
        fd, file = tempfile.mkstemp('.eml')
        f = os.fdopen(fd, 'w')
        f.write(self.panel.message_string)
        f.close()

        cmd = settings.editor_command + [file]
        subprocess.run(cmd)

        with open(file, 'r') as f:
            self.panel.message_string = f.read()
        os.remove(file)

class SendmailThread(QThread):
    """A QThread used for editing mail with the external editor

    Used by the :func:`~dodo.compose.ComposePanel.edit` method."""

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel

    def run(self):
        try:
            m = email.message_from_string(self.panel.message_string)
            eml = email.message.EmailMessage()
            attachments = []
            for h in m:
                if h == 'A':
                    attachments.append(m[h])
                else:
                    eml[h] = m[h]

            eml['Message-ID'] = email.utils.make_msgid()
            eml['User-Agent'] = 'Dodo'

            eml.set_content(m.get_payload())

            if not "Date" in eml:
                eml["Date"] = email.utils.formatdate(localtime=True)

            for att in attachments:
                mime, _ = mimetypes.guess_type(att)
                if mime and len(mime.split('/')) == 2:
                    ty = mime.split('/')
                else:
                    ty = ['application', 'octet-stream']

                try:
                    with open(os.path.expanduser(att), 'rb') as f:
                        data = f.read()
                        eml.add_attachment(data, maintype=ty[0], subtype=ty[1], filename=os.path.basename(att))
                except IOError:
                    print("Can't read attachment: " + a)

            sendmail = Popen(settings.send_mail_command, stdin=PIPE, encoding='utf8')
            sendmail.stdin.write(str(eml))
            sendmail.stdin.close()
            sendmail.wait(30)
            if sendmail.returncode == 0:
                # save to sent folder
                m = mailbox.MaildirMessage(str(eml))
                m.set_flags('S')
                key = mailbox.Maildir(settings.sent_dir).add(m)
                # print(f'add: {key}')

                subprocess.run(['notmuch', 'new'])

                if self.panel.mode == 'reply' or self.panel.mode == 'replyall' and 'id' in self.panel.msg:
                    subprocess.run(['notmuch', 'tag', '+replied', '--', 'id:' + self.panel.msg['id']])
                self.panel.app.invalidate_panels()
                self.panel.status = f'<i style="color:{settings.theme["fg_good"]}">sent</i>'
            else:
                self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">error</i>'
        except TimeoutExpired:
            self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">timed out</i>'


class ComposePanel(Panel):
    """A panel for composing messages

    :param msg: A JSON message referenced in a reply or forward
    :param mode: Composition mode. Possible values are '', 'reply', 'replyall',
                 and 'forward'
    """

    def __init__(self, app, mode='', msg=None, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.compose_keymap)
        self.mode = mode
        self.msg = msg
        self.message_view = QWebEngineView()
        self.message_view.setZoomFactor(1.2)
        self.layout().addWidget(self.message_view)
        self.status = f'<i style="color:{settings.theme["fg"]}">draft</i>'

        self.message_string = f'From: {settings.email_address}\n'

        if mode == 'reply' or mode == 'replyall':
            if 'From' in msg['headers']:
                self.message_string += f'To: {msg["headers"]["From"]}\n'

            if 'Subject' in msg['headers']:
                subject = msg['headers']['Subject']
                if subject[0:3].upper() != 'RE:':
                    subject = 'RE: ' + subject
                self.message_string += f'Subject: {subject}\n'

            if mode == 'replyall':
                cc = []
                email_sep = re.compile('\s*[;,]\s*')
                if 'To' in msg['headers']:
                    cc += email_sep.split(msg['headers']['To'])
                if 'Cc' in msg['headers']:
                    cc += email_sep.split(msg['headers']['Cc'])
                cc = [e for e in cc if not util.email_is_me(e)]
                if len(cc) != 0: self.message_string += f'Cc: {"; ".join(cc)}\n'

            if 'id' in msg:
                self.message_string += f'In-Reply-To: <{msg["id"]}>\n'

            self.message_string += '\n\n'

            if msg:
                self.message_string += '\n' + util.quote_body_text(msg)

        elif mode == 'forward':
            pass # TODO

        else:
            self.message_string += 'To: \nSubject: \n\n'

        self.editor_thread = None
        self.sendmail_thread = None

        self.refresh()

    def title(self):
        return 'compose'

    def refresh(self):
        """Refresh the message text

        This gets called automatically after the external editor has closed."""

        self.message_view.setHtml(f"""<html>
        <style type="text/css">
        {util.make_message_css()}
        </style>
        <body>
        <p>{self.status}</p>
        <pre style="white-space: pre-wrap">{util.simple_escape(self.message_string)}</pre>
        </body></html>""")

        super().refresh()

    def edit(self):
        """Edit the email message with an external text editor

        The editor is configured via :func:`dodo.settings.editor_command`."""

        # only open one editor at a time
        if self.editor_thread is None:
            self.editor_thread = EditorThread(self, parent=self)
            
            def done():
                self.editor_thread.deleteLater()
                self.editor_thread = None
                self.refresh()
                self.app.raise_panel(self)

            self.editor_thread.finished.connect(done)
            self.editor_thread.start()

    def attach_file(self):
        """Attach a file

        Opens a file browser for selecting a file to attach. If a file is selected, add it using the "A:"
        pseudo-header. This will be translated into a proper attachment when the message is sent."""
        f = QFileDialog.getOpenFileName()
        if f[0]:
            self.message_string = util.add_header_line(self.message_string, 'A: ' + f[0])
            self.refresh()

    def send(self):
        """Send the message

        Sends asynchronously using :class:`~dodo.compose.SendmailThread`. If one or more occurances of
        the "A:" pseudo-header are detected, these are converted into attachments."""

        # only try to send mail once at a time
        if self.sendmail_thread is None:
            self.status = f'<i style="color:{settings.theme["fg_bright"]}">sending</i>'
            self.refresh()
            self.sendmail_thread = SendmailThread(self, parent=self)

            def done():
                self.sendmail_thread.deleteLater()
                self.sendmail_thread = None
                self.refresh()

            self.sendmail_thread.finished.connect(done)
            self.sendmail_thread.start()

