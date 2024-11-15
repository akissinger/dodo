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

"""
This module holds settings and sets their default values. The values set
here should be overridden by the user in `~/.config/dodo/config.py`. This
can be done as follows:

.. code-block:: python

  import dodo
  dodo.settings.email_address = 'First Last <me@domain.com>''
  dodo.settings.sent_dir = '~/mail/work/Sent'

The settings :func:`~dodo.settings.email_address` and
:func:`~dodo.settings.sent_dir` are required. Dodo may not work correctly
unless you set them properly. The rest of the settings have reasonable
defaults, as detailed below.
"""

from . import themes
from typing import Literal, Dict, Union

# functional
email_address: Union[str, Dict[str, str]] = ''
"""Your email address (REQUIRED)

This is used both to populate the 'From' field of emails and to (mostly)
avoid CC'ing yourself when replying to all. It can be given as 'NAME <ADDRESS@DOMAIN>'
format. For just one email address, this can be given as a string. From multiple
emails, use a dictionary mapping the account names in :func:`~dodo.settings.smtp_accounts`
to the associated email addresses.
"""

sent_dir = ''
"""Where to store sent messages (REQUIRED)

This will usually be a subdirectory of the Maildir sync'ed with
:func:`~dodo.settings.sync_mail_command`. This setting can be given either
as a string to use one global sent directory, or as a dictionary mapping
account names in :func:`~dodo.settings.smtp_accounts` to their own sent dirs.

A value of None, either standalone or as one of the dict value, can be used to
indicate the email should be discarded. This can be useful if the sendmail
command already has a mechanism for that feature.
"""

editor_command = "xterm -e vim '{file}'"
"""Command used to launch external text editor

This is a shell command, which additionally takes the `{file}` placeholder,
which is passed the name of a temp file being edited while composing an email.
"""

file_browser_command = "nautilus '{dir}'"
"""Command used to launch external file browser

This is a shell command, which additionally takes the `{dir}` placeholder. This
command is used when viewing attachments, which first dumps the attachments to a
temp directory given by `{dir}`, then opens that directory in a file browser.
"""

file_picker_command = None
"""Command used to launch external file picker

This is an optional shell command, which additionally takes the `{tempfile}` placeholder.
This command is used when picking files to attach to an email. The command should write
out the chosen files to {tempfile}, which will then be read and deleted, if it exists.

By default, this is set to None, in which case the built-in file picker will be used.
"""

web_browser_command = ''
"""Web browser to use when clicking links in emails

This should be a single command which expects a URL as its first argument. If this
is an empty string, Dodo will attempt to use the default web browser supplied by
the desktop environment, if it exists.
"""

send_mail_command = 'msmtp -a "{account}" -t'
"""Command used to send mail via SMTP

This is a shell command that expects a (sendmail-compatible) email message to be
written to STDIN. Note that it should read the destination from the `From:` header
of the message and not a command-line argument. Use the `{account}` placeholder
to read the currently selected account.
"""

smtp_accounts = ['default']
"""A list of SMTP account names recognised by `send_mail_command`

This setting allows switching SMTP accounts in the Compose panel. The first account
in the list is selected by default.
"""

sync_mail_command = 'offlineimap'
"""Command used to sync IMAP with local Maildir"""

sync_mail_interval = 300
"""Interval to run :func:`~dodo.settings.sync_mail_command` automatically, in seconds

Set this to -1 to disable automatic syncing.
"""

default_to_html = False
"""Open messages in HTML mode by default, rather than plaintext"""

wrap_message = True
"""Hard-wrap message text by default

You may wish to disable this if you don't want hard wraps in your email messages or
your text editor does hard wrapping already.
"""

wrap_column = 78
"""Wrap text to this column when composing emails
"""

remove_temp_dirs = 'ask'
"""Set whether to remove temporary directories when closing a panel

Thread panels create temporary directories to open attachments. These can be cleaned up
automatically when a panel (or Dodo) is closed. Possible values are: 'always', 'never',
or 'ask'.
"""

default_thread_list_mode: Literal['conversation', 'thread'] = 'conversation'
"""Set the way your thread should be listed.

Possible values are:
    * 'conversation': flat list, chronologically sorted
    * 'thread': tree view, following the various subthreads
"""

gnupg_home = None
"""Directory containg GnuPG keys

If set to None, GnuPG will use whatever directory is the default (consult the
GnuPG documentation for more information on what this might be).
"""

gnupg_keyid = None
"""The id of the key to be used for GnuPG-signing mail messages.

If set to the id of a valid GnuPG private signing key, sent messages will be
cryptographically signed according to rfc3156 using the GnuPG sotware, which
should be installed and configured.  Requires python-gnupg
(https://pypi.org/project/python-gnupg/)"""

init_queries = [ 'tag:inbox' ]
"""List of non closable queries open at startup

You can save query with `notmuch config set query:inbox "tag:inbox and not
tag:trash"` and use `query:inbox` as a search term.
"""

no_hooks_on_send = True
"""disable/enable calling notmuch hooks when sending email

When True, 'notmuch new' is called with --no-hooks when a message is sent. One
may not wanting to wait for the hooks on each sent email, for example when
calling mbsync on their notmuch hooks. Other users may set this to False, for
example when notmuch hooks are used to archive sent mail."""

# security
html_block_remote_requests = True
"""Block remote requests for HTML messages

HTML messages, especially from dodgy senders, can display remote content or 'call home'
from embedded image tags or iframes. If set to True, Dodo will not allow these requests.
"""

html_confirm_open_links = True
"""Display a confirmation dialog before opening a link in browser

If this is True, Dodo will display a confirmation dialog showing the *actual* URL that
the web browser will request before opening. This is an extra measure against phishing
or emails opening your web browser without your permission.
"""

html_confirm_open_links_trusted_hosts = []
"""A list of trusted hosts for HTML links.

If a link is to a host in this list, it will be opened without confirmation, even if
:func:`~dodo.settings.html_confirm_open_links` is True.
"""

# visual
theme = themes.nord
"""The GUI theme

A theme is a dictionary mapping a dozen or so named colors to HEX values.
Several themes are defined in `dodo.themes`, based on the popular Nord,
Solarized and Gruvbox color palettes.
"""

search_font = 'DejaVu Sans Mono'
"""The font used for search output and various other list-boxes"""

search_font_size = 13
"""The font size used for search output and various other list-boxes"""

tag_font = 'DejaVu Sans Mono'
"""The font used for tags and tag icons"""

tag_font_size = 13
"""The font size used for tags and tag icons"""

message_font = 'DejaVu Sans Mono'
"""The font used for plaintext messages"""

message_font_size = 12
"""The font size used for plaintext messages"""

search_view_padding = 1
"""A bit of spacing around each line in the search panel"""

search_title_format = "{query} [{num_threads}]"
"""A Python format string for the tab title of search panels

The following placeholders can be used:

- {query}: the current search query
- {num_threads}: the number of threads returned by the search
"""

tag_icons = {
  'inbox': '',
  'unread': '',
  'attachment': '',
  'sent': '>',
  'replied': '',
  'flagged': '',
  'marked': '',
  'signed': '',
}
"""Tag icons

This is a dictionary of substitutions used to abbreviate common tag names as unicode
icons in the search and thread panels.
"""

hide_tags = ['unread', 'sent']
"""Tags to hide in search panel"""

message_css = """
pre {{
  font-family: {message_font};
  font-size: {message_font_size}pt;
}}

pre .quoted {{
  color: {fg_dim};
}}

pre .headername {{
  color: {fg_bright};
  font-weight: bold;
}}

pre .headertext {{
  color: {fg_bright};
}}

body {{
  background-color: {bg};
  color: {fg};
}}

::-webkit-scrollbar {{
  background: {bg};
}}

::-webkit-scrollbar-thumb {{
  background: {bg_button};
}}

::selection {{
  color: {bg};
  background: {fg};
}}

a {{
  color: {fg_bright};
}}
"""
"""CSS used in view and compose window

Placeholders may be included in curly brackets for any color named in the current theme, as
well as {message_font} and {message_font_size}. Literal curly braces should be doubled, i.e.
'{' should be '{{' and '}' should be '}}'.
"""

message2html_filters = []
"""A list of functions to extract text from a mail message JSON.

Every item in this list should be a function, which either returns a HTML string
(which gets formatted inside a ``<pre>`` tag), or returns ``None``. The first
function to return a non-``None`` value is used to render the message. If all functions
return ``None``, the default rendering is used.

The default rendering runs the following functions in order, which might also be useful
when writing your own filters:

- :func:`~dodo.util.body_text` (to get a body string from the JSON)
- :func:`~dodo.util.simple_escape` (to make the string HTML-safe)
- :func:`~dodo.util.colorize_text` (to colorize quoted text)
- :func:`~dodo.util.linkify` (to detect URLs)

Example configuration using this feature to highlight markdown syntax:

.. code-block:: python

  import pygments.formatters
  from dodo import util

  def render_github(msg):
      # Double imports needed due to how dodo runs config.py
      import pygments.lexers
      import pygments.formatters

      # If you use some sort of auto-tagging, you might want to match on
      # tags instead of headers.
      if "headers" not in msg or "From" not in msg["headers"]:
          return None
      if not msg["headers"]["From"].endswith("<notifications@github.com>"):
          return None

      text = util.body_text(msg)
      lexer = pygments.lexers.MarkdownLexer()
      formatter = pygments.formatters.HtmlFormatter(nowrap=True)
      highlighted = pygments.highlight(text, lexer, formatter)
      return util.linkify(highlighted)

  dodo.settings.message2html_filters = [render_github]

  # Available styles: https://pygments.org/styles/
  pygments_css = pygments.formatters.HtmlFormatter(style="gruvbox-dark").get_style_defs()
  dodo.settings.message_css += pygments_css.replace("{", "{{").replace("}", "}}")
"""

search_color_overrides = {}
"""A dictionary mapping tags to color dictionaries.

The color dictionaries map columns to override colors.
The available columns are:

- date
- from
- subject
- tags

For example, to show a red subject for messages tagged 'urgent',
using the built-in Gruvbox palette:

.. code-block:: python

  dodo.settings.search_color_overrides = {
      'urgent': {
          'subject': dodo.themes.gruvbox_p['neutral_red'],
      }
  }
"""
