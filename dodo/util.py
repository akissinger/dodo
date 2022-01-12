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

from PyQt5.QtCore import Qt
import re
import os
import tempfile
import subprocess
import email

from . import settings

def clean_html2html(s):
    """Sanitize the given HTML string

    This cleans the input string using :class:`~lxml.html.clean.Cleaner` with the default
    settings. Set the global util.html2html to this function to enable.

    :param s: an HTML input string

    """
    from lxml.html.clean import Cleaner # type: ignore
    c = Cleaner()
    return c.clean_html(s)
    
# Pure python html2text, but results don't look nearly as good as w3m -dump
#
# def python_html2text(s):
#     from html2text import HTML2Text
#     c = HTML2Text()
#     c.ignore_emphasis = True
#     c.ignore_links = True
#     c.images_to_alt = True
#     return c.handle(s)

def w3m_html2text(s):
    """Convert HTML to plain text using "w3m -dump"

    :param s: an HTML input string
    :returns: plain text representation of the HTML
    """

    (fd, file) = tempfile.mkstemp(suffix='.html') 
    with os.fdopen(fd, 'w') as f:
        f.write(s)
    p = subprocess.run(['w3m', '-dump', file],
            stdout=subprocess.PIPE, encoding='utf8')
    os.remove(file)
    return p.stdout


html2html = lambda s : s
"""Function used to process HTML messages

This is the identity by default, but can be set to another function to
do HTML sanitization, (de)formatting, etc.
"""

html2text = w3m_html2text
"""Function used to convert HTML to plain text

This is set to :func:`~dodo.util.w3m_html2text` by default, but can be changed
by the user in "config.py".
"""

def simple_escape(s):
    """Provide (limited) HTML escaping

    This function only escapes &, <, and >."""

    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def colorize_text(s, has_headers=False):
    """Add some colors to HTML-escaped plaintext, for use inside <pre> tag
    """

    s1 = ""
    quoted = re.compile('^\s*&gt;')
    empty = re.compile('^\s*$')

    headers = has_headers
    for ln in s.splitlines():
        if headers:
            if empty.match(ln):
                headers = False
                s1 += '\n'
            elif ':' in ln:
                parts = ln.split(':', 1)
                s1 += f'<span class="headername">{parts[0]}:</span>'
                s1 += f'<span class="headertext">{parts[1]}</span>\n'
            else:
                s1 += ln + '\n'
        else:
            if quoted.match(ln):
                s1 += f'<span class="quoted">{ln}</span>\n'
            else:
                s1 += ln + '\n'

    return s1



def chop_s(s):
    if len(s) > 20:
        return s[0:20] + '...'
    else:
        return s

def message_parts(m):
    """
    Iterate over JSON message parts recursively, in depth-first order

    This is method roughly emulates the behavior of :func:`~email.message.Message.walk`, but
    for JSON representations of an email message rather than :class:`~email.message.Message`
    objects.

    Note that if parts are nested, their data will be returned multiple times, first
    as a sub-object of their parent, then as the part itself.

    :param m: a JSON message
    :returns: an iterator which returns each JSON-subobject corresponding
              to a message part.
    """

    if 'body' in m:
        for part in m['body']:
            yield from message_parts(part)
    elif 'content' in m:
        yield m
        if isinstance(m['content'], list):
            for part in m['content']:
                yield from message_parts(part)
    else:
        yield m

def find_content(m, content_type):
    """Return a flat list consisting of the 'content' field of each message
    part with the given content-type."""

    return [part['content'] for part in message_parts(m)
              if 'content' in part and part.get('content-type') == content_type]

def body_text(m):
    """Get the body text of a message

    Search a message recursively for the first part with content-type equal to
    "text/plain" and return it.

    :param m: a JSON message
    """

    global html2text
    tc = find_content(m, 'text/plain')
    if len(tc) != 0:
        return tc[0]
    else:
        hc = find_content(m, 'text/html')
        if len(hc) != 0:
            return html2text(hc[0])
    return ''

def body_html(m):
    """Get the body HTML of a message

    Search a message recursively for the first part with content-type equal to
    "text/html" and return it.

    :param m: a JSON message
    """

    global html2html
    hc = find_content(m, 'text/html')
    if len(hc) != 0: return hc[0]
    else: return ''

def quote_body_text(m):
    """Return the body text of the message, with '>' prepended to each line"""

    text = body_text(m)
    if not text: return ''
    return ''.join([f'> {ln}\n' for ln in text.splitlines()])

def write_attachments(m):
    """Write attachments out into temp directory and open with `settings.file_browser_command`

    Currently, this exports a new copy of the attachments every time it is called. Maybe it should
    do something smarter?

    :param m: message JSON
    :returns: Return a tuple consisting of the temp dir and a list of files. If no attachments,
              returns an empty string and empty list.
    """

    if not (m and 'filename' in m): return None
    temp_dir = tempfile.mkdtemp(prefix='dodo-')
    file_paths = []

    for filename in m['filename']:
        with open(filename, 'r') as f:
            msg = email.message_from_file(f)
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    p = temp_dir + '/' + part.get_filename()
                    with open(p, 'wb') as att:
                        att.write(part.get_payload(decode=True))
                    file_paths.append(p)

    if len(file_paths) == 0:
        os.rmdir(temp_dir)
        return ('', [])
    else:
        return (temp_dir, file_paths)

def strip_email_address(e):
    """Strip the display name, leaving just the email address

    E.g. "First Last <me@domain.com>" -> "me@domain.com"
    """

    head = re.compile('^.*<')
    tail = re.compile('>.*$')
    return tail.sub('', head.sub('', e))

def email_is_me(e):
    """Check whether the provided email is me

    This compares settings.email_address with the provided email, after calling
    :func:`strip_email_address` on both. This method is used e.g. by
    :class:`dodo.compose.Compose` to filter out the user's own email when forming
    a "reply-to-all" message.
    """

    return strip_email_address(settings.email_address) == strip_email_address(e)

def add_header_line(s, h):
    """Add the given string to the headers, i.e. before the first
    blank line, in the provided string."""

    out = ''
    headers = True
    for line in s.splitlines():
        if headers and line == '':
            out += h + '\n'
            headers = False
        out += line + '\n'
    return out

def make_message_css():
    """Fill placeholders in settings.message_css using the current theme
    and font settings."""

    d = settings.theme.copy()
    d["message_font"] = settings.message_font
    d["message_font_size"] = settings.message_font_size
    return settings.message_css.format(**d)

basic_keytab = {
  Qt.Key.Key_0: '0',
  Qt.Key.Key_1: '1',
  Qt.Key.Key_2: '2',
  Qt.Key.Key_3: '3',
  Qt.Key.Key_4: '4',
  Qt.Key.Key_5: '5',
  Qt.Key.Key_6: '6',
  Qt.Key.Key_7: '7',
  Qt.Key.Key_8: '8',
  Qt.Key.Key_9: '9',
  Qt.Key.Key_Ampersand: '&',
  Qt.Key.Key_Apostrophe: '\'',
  Qt.Key.Key_Asterisk: '*',
  Qt.Key.Key_At: '@',
  Qt.Key.Key_Backslash: '\\',
  Qt.Key.Key_Bar: '|',
  Qt.Key.Key_BraceLeft: '{',
  Qt.Key.Key_BraceRight: '}',
  Qt.Key.Key_BracketLeft: '[',
  Qt.Key.Key_BracketRight: ']',
  Qt.Key.Key_Colon: ':',
  Qt.Key.Key_Comma: ',',
  Qt.Key.Key_Dollar: '$',
  Qt.Key.Key_Equal: '=',
  Qt.Key.Key_Exclam: '!',
  Qt.Key.Key_Greater: '>',
  Qt.Key.Key_Less: '<',
  Qt.Key.Key_Minus: '-',
  Qt.Key.Key_NumberSign: '#',
  Qt.Key.Key_ParenLeft: '(',
  Qt.Key.Key_ParenRight: ')',
  Qt.Key.Key_Percent: '%',
  Qt.Key.Key_Period: '.',
  Qt.Key.Key_Plus: '+',
  Qt.Key.Key_Question: '?',
  Qt.Key.Key_QuoteDbl: '"',
  Qt.Key.Key_QuoteLeft: '`',
  Qt.Key.Key_Semicolon: ';',
  Qt.Key.Key_Slash: '/',
  Qt.Key.Key_A: 'a',
  Qt.Key.Key_B: 'b',
  Qt.Key.Key_C: 'c',
  Qt.Key.Key_D: 'd',
  Qt.Key.Key_E: 'e',
  Qt.Key.Key_F: 'f',
  Qt.Key.Key_G: 'g',
  Qt.Key.Key_H: 'h',
  Qt.Key.Key_I: 'i',
  Qt.Key.Key_J: 'j',
  Qt.Key.Key_K: 'k',
  Qt.Key.Key_L: 'l',
  Qt.Key.Key_M: 'm',
  Qt.Key.Key_N: 'n',
  Qt.Key.Key_O: 'o',
  Qt.Key.Key_P: 'p',
  Qt.Key.Key_Q: 'q',
  Qt.Key.Key_R: 'r',
  Qt.Key.Key_S: 's',
  Qt.Key.Key_T: 't',
  Qt.Key.Key_U: 'u',
  Qt.Key.Key_V: 'v',
  Qt.Key.Key_W: 'w',
  Qt.Key.Key_X: 'x',
  Qt.Key.Key_Y: 'y',
  Qt.Key.Key_Z: 'z',
}

keytab = {
  Qt.Key.Key_Escape: 'escape',
  Qt.Key.Key_Tab: 'tab',
  Qt.Key.Key_Backtab: 'backtab',
  Qt.Key.Key_Backspace: 'backspace',
  Qt.Key.Key_Return: 'enter',
  Qt.Key.Key_Enter: 'enter',
  Qt.Key.Key_Insert: 'insert',
  Qt.Key.Key_Delete: 'delete',
  Qt.Key.Key_Pause: 'pause',
  Qt.Key.Key_Print: 'print',
  Qt.Key.Key_Clear: 'clear',
  Qt.Key.Key_Home: 'home',
  Qt.Key.Key_End: 'end',
  Qt.Key.Key_Left: 'left',
  Qt.Key.Key_Up: 'up',
  Qt.Key.Key_Right: 'right',
  Qt.Key.Key_Down: 'down',
  Qt.Key.Key_PageUp: 'pageup',
  Qt.Key.Key_PageDown: 'pagedown',
  Qt.Key.Key_CapsLock: 'capslock',
  Qt.Key.Key_NumLock: 'numlock',
  Qt.Key.Key_ScrollLock: 'scrolllock',
  Qt.Key.Key_F1: 'f1',
  Qt.Key.Key_F2: 'f2',
  Qt.Key.Key_F3: 'f3',
  Qt.Key.Key_F4: 'f4',
  Qt.Key.Key_F5: 'f5',
  Qt.Key.Key_F6: 'f6',
  Qt.Key.Key_F7: 'f7',
  Qt.Key.Key_F8: 'f8',
  Qt.Key.Key_F9: 'f9',
  Qt.Key.Key_F10: 'f10',
  Qt.Key.Key_F11: 'f11',
  Qt.Key.Key_F12: 'f12',
  Qt.Key.Key_F13: 'f13',
  Qt.Key.Key_F14: 'f14',
  Qt.Key.Key_F15: 'f15',
  Qt.Key.Key_F16: 'f16',
  Qt.Key.Key_F17: 'f17',
  Qt.Key.Key_F18: 'f18',
  Qt.Key.Key_F19: 'f19',
  Qt.Key.Key_F20: 'f20',
  Qt.Key.Key_F21: 'f21',
  Qt.Key.Key_F22: 'f22',
  Qt.Key.Key_F23: 'f23',
  Qt.Key.Key_F24: 'f24',
  Qt.Key.Key_F25: 'f25',
  Qt.Key.Key_F26: 'f26',
  Qt.Key.Key_F27: 'f27',
  Qt.Key.Key_F28: 'f28',
  Qt.Key.Key_F29: 'f29',
  Qt.Key.Key_F30: 'f30',
  Qt.Key.Key_F31: 'f31',
  Qt.Key.Key_F32: 'f32',
  Qt.Key.Key_F33: 'f33',
  Qt.Key.Key_F34: 'f34',
  Qt.Key.Key_F35: 'f35',
  Qt.Key.Key_Menu: 'menu',
  Qt.Key.Key_Help: 'help',
  Qt.Key.Key_Space: 'space',
}

def key_string(e):
    """Convert a Qt keycode plus modifiers into a human readable/writable string

    :param e: a QKeyEvent
    :returns: a string representing e.key() and its modifiers
    """

    global basic_keytab, keytab
    if e.key() in basic_keytab:
        cmd = basic_keytab[e.key()]
        shift_modifier = False
        if e.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier:
            cmd = cmd.upper()
    elif e.key() in keytab:
        shift_modifier = True
        cmd = '<' + keytab[e.key()] + '>'
    else:
        return None

    if shift_modifier and (e.modifiers() & Qt.ShiftModifier == Qt.ShiftModifier):
        cmd = 'S-' + cmd
    if e.modifiers() & Qt.AltModifier == Qt.AltModifier:
        cmd = 'M-' + cmd
    if e.modifiers() & Qt.ControlModifier == Qt.ControlModifier:
        cmd = 'C-' + cmd

    return cmd
