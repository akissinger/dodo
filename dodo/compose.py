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
    done = pyqtSignal()

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.done.connect(panel.edit_done)

    def run(self):
        try:
            fd, file = tempfile.mkstemp('.eml')
            f = os.fdopen(fd, 'w')
            f.write(self.panel.message_string)
            f.close()

            cmd = settings.editor_command + [file]
            subprocess.run(cmd)

            with open(file, 'r') as f:
                self.panel.message_string = f.read()
            os.remove(file)
        finally:
            self.done.emit()

class SendmailThread(QThread):
    done = pyqtSignal()

    def __init__(self, panel, parent=None):
        super().__init__(parent)
        self.panel = panel
        self.done.connect(panel.refresh)

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
                mailbox.Maildir(settings.sent_dir).add(m)
                subprocess.run(['notmuch', 'new'])
                self.panel.status = f'<i style="color:{settings.theme["fg_good"]}">sent</i>'
            else:
                self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">error</i>'
        except TimeoutExpired:
            self.panel.status = f'<i style="color:{settings.theme["fg_bad"]}">timed out</i>'
        finally:
            self.done.emit()


class ComposeView(Panel):
    def __init__(self, app, reply_to=None, parent=None):
        super().__init__(app, parent)
        self.set_keymap(keymap.compose_keymap)
        self.message_view = QWebEngineView()
        self.layout().addWidget(self.message_view)
        self.status = f'<i style="color:{settings.theme["fg"]}">draft</i>'

        to = ''
        subject = ''
        if reply_to:
            if 'Subject' in reply_to['headers']:
                subject = reply_to['headers']['Subject']
                if subject[0:3].upper() != 'RE:':
                    subject = 'RE: ' + subject
            if 'From' in reply_to['headers']:
                to = reply_to['headers']['From']

        self.message_string = f'From: {settings.email_address}\nTo: {to}\nSubject: {subject}\n'

        if reply_to and 'id' in reply_to:
            self.message_string += f'In-Reply-To: <{reply_to["id"]}>\n'

        self.message_string += '\n\n'

        self.editor_thread = None
        self.sendmail_thread = None
        self.reply_to = reply_to

        self.refresh()

    def title(self):
        return 'compose'

    def refresh(self):
        self.message_view.setHtml(f"""<html>
        <style type="text/css">
        {settings.message_css.format(**settings.theme)}
        </style>
        <body>
        <p>{self.status}</p>
        <pre style="white-space: pre-wrap">{util.simple_escape(self.message_string)}</pre>
        </body></html>""")

    def edit_done(self):
        self.editor_thread = None
        self.refresh()

    def edit(self):
        if self.editor_thread is None:
            self.editor_thread = EditorThread(self)
            self.editor_thread.start()

    def send(self):
        if self.sendmail_thread is None:
            self.status = f'<i style="color:{settings.theme["fg_bright"]}">sending</i>'
            self.refresh()
            self.sendmail_thread = SendmailThread(self)
            self.sendmail_thread.start()

